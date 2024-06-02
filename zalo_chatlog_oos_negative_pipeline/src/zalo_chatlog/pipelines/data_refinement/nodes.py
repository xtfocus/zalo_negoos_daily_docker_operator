import asyncio
import json
import logging
import os
import re
from typing import Dict, List

import aiohttp
from numpy import outer
from pandas import DataFrame, to_datetime
from tqdm import tqdm

from .intent_classification import make_async_request
from .pool_events import get_event

tqdm.pandas()

logger = logging.getLogger(__name__)


def connecting_sessions(chatlog: DataFrame) -> DataFrame:
    """
    Sometimes two sessions are just one conversation broken into multiple sessions,
        maybe due to inactivity or whatever quirks. In such cases, we want to connect
        them. Here's how: a conversation = [senderid + the day]

        E.g., senderid = 1234, datetime is 2024-01-01
        --> daily_session_code = 123420240101

    This approach is not sophisticated enough when the user actually opens multiple sessions
        for unrelated needs. But it should be good enough
    """

    chatlog["daily_session_code"] = chatlog["sender_id"].astype(str) + chatlog[
        "created_time"
    ].astype(str).str.slice(0, 10).str.replace("-", "")
    chatlog = chatlog.sort_values(["sender_id", "created_time"])
    return chatlog


def create_time_column(chatlog: DataFrame) -> DataFrame:
    """
    Create a column named `time_diff` to measure the time from the start of the conversation
        to the current message row (in minutes, rounded to 2nd decimal digit)
    """

    chatlog["datetime"] = to_datetime(chatlog["created_time"])

    # Calculate the time difference in minutes from each row to the first row within each session
    chatlog["time_diff"] = chatlog.groupby("daily_session_code")[
        "datetime"
    ].progress_transform(lambda x: round((x - x.min()).dt.total_seconds() / 60, 2))

    # Calculate the time difference in minutes from each row to the next row within each session
    chatlog["time_interval"] = chatlog.groupby("daily_session_code")[
        "time_diff"
    ].progress_transform(lambda x: round(x.diff(), 2))

    return chatlog.drop("datetime", axis=1)


def pool_events(chatlog: DataFrame, events: List[str]) -> DataFrame:
    """
    Create a new column named `all_classified`, True if all messages
        are classified, False if at least one message is either
        - cus_text_other; or
        - agent_text_other

    Create an `events` columnn which is a list of events
    """

    # Pool the event into a single column
    chatlog["event"] = chatlog.progress_apply(lambda x: get_event(x, events), axis=1)

    # Grouping event into a list of events
    chatlog["events"] = chatlog.groupby(["daily_session_code"])[
        "event"
    ].progress_transform(lambda x: [x.tolist()] * len(x))

    # If all event are classified, mark as all_classified
    chatlog["all_classified"] = chatlog["events"].progress_apply(
        lambda x: all(
            [(event not in ("cus_text_other", "agent_text_other")) for event in x]
        )
    )
    # Warning when un-defined events exist
    if sum(chatlog["event"].isna()):
        warning = "Exists messages that are not categorized"
        logger.warning(warning)

        logger.warning("Converting them to `nan`")
        # Make convert null events to nan
        chatlog["event"] = chatlog["event"].fillna("nan")

    return chatlog


def categorize_organic_sessions(
    chatlog: DataFrame, organic_requirements: Dict[str, int]
):
    """
    1. Marking if a text is organic or not

    (What's an organic text? It has to be a text (meaning not payload/sticker/file), and
        it's not an automated response e.g., The order confirmation text
    Specifically, the 'organic' texts has already been labeled as cus_text_other and agent_text_other
    )

    2. Then filter out only organic sessions

    organic_requirements is a dict that contains the requirement for a session to be
        considered organic. For instance:
        - at least 2 organic texts from the agent
        - at least 2 organic texts from the customer

    """

    minimum_cus_texts = organic_requirements["customer"]
    minimum_agent_texts = organic_requirements["agent"]

    chatlog["n_org_cus"] = chatlog.groupby(["daily_session_code"])[
        "event"
    ].progress_transform(lambda x: sum(x == "cus_text_other"))

    chatlog["n_org_agent"] = chatlog.groupby(["daily_session_code"])[
        "event"
    ].progress_transform(lambda x: sum(x == "agent_text_other"))

    chatlog["is_organic"] = chatlog.apply(
        lambda x: (x["n_org_cus"] >= minimum_cus_texts)
        & (x["n_org_agent"] >= minimum_agent_texts),
        axis=1,
    )

    chatlog = chatlog[chatlog["is_organic"]].reset_index(drop=True)

    # readable_event is the organic text or the classified event

    url_pattern = r"(https?://(?:www\.)?[\w.-]+(?:\.[\w.-]+)+(?:[\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?|www\.[\w.-]+(?:\.[\w.-]+)+|[\w.-]+\.[a-z]{2,6})"

    chatlog["readable_event"] = chatlog.apply(
        lambda x: (
            json.loads(x["message"])["content"]["text"]
            if x["event"] in ("cus_text_other", "agent_text_other")
            else (
                re.findall(url_pattern, str(x["message"]))[0]
                if x["event"] in ("cus_file", "agent_file")
                else x["event"]
            )
        ),
        axis=1,
    )

    try:
        assert len(chatlog) > 0
    except AssertionError:
        message = "No organic session found."
        logger.error(message)
        raise ValueError(message)

    return chatlog


def export_organic_message_data(
    chatlog: DataFrame, fillers: List, synonyms: List[Dict]
) -> DataFrame:
    """
    Refined organic data for NLP tasks:
        OOS detection
        negative detection

    Export the the organic texts + files (images) from organic sessions only. Then:
    - remove filler messages
    - normalize abbreviations (as synonyms)
    """

    keep = ["cus_text_other", "agent_text_other"]
    # Keep some 'classified' messages for context
    keep += ["cus_text_phone", "agent_text_confirmorder", "cus_file", "agent_file"]

    chatlog = chatlog[chatlog["event"].isin(keep)]

    def expand_abbreviations(abbreviation_dict, input_string):
        pattern = re.compile(
            r"\b(?:"
            + "|".join(
                re.escape(abbrev)
                for full, abbrev_list in abbreviation_dict.items()
                for abbrev in abbrev_list
            )
            + r")\b"
        )
        expanded_string = pattern.sub(
            lambda match: next(
                full
                for full, abbrev_list in abbreviation_dict.items()
                if match.group() in abbrev_list
            ),
            input_string,
        )

        return expanded_string

    # Abbreviation
    for abbreviation_dict in synonyms:

        chatlog["readable_event"] = chatlog.progress_apply(
            lambda x: (
                expand_abbreviations(abbreviation_dict, x["readable_event"])
                if x["event"] in ("cus_text_other", "agent_text_other")
                else x["readable_event"]
            ),
            axis=1,
        )

    # Remove most common fillers.
    chatlog = chatlog[
        ~chatlog["readable_event"].str.lower().isin(fillers["exact"])
    ].reset_index(drop=True)

    chatlog = chatlog[
        ~chatlog["readable_event"]
        .str.lower()
        .str.contains("|".join(fillers["contains"]))
    ]

    chatlog["sender"] = chatlog.progress_apply(
        lambda x: "Nhân viên" if x["email"] else "Khách hàng", axis=1
    )

    result = chatlog[
        [
            "daily_session_code",
            "session_id",
            "sender",
            "readable_event",
            "event",
            "time_diff",
            "time_interval",
        ]
    ].reset_index(drop=True)

    return result
