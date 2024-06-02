"""
This is a boilerplate pipeline 'data_preprocessing'
generated using Kedro 0.18.14
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import pandas as pd
from kedro.config import OmegaConfigLoader
from kedro.framework.project import settings
from pandas import DataFrame
from tqdm import tqdm

from .classify_agent_message import categorize_agent_message_row
from .classify_bot_message import (
    categorize_bot_img_row,
    categorize_bot_text_row,
    request_human_support_success_row,
)
from .classify_customer_message import (
    categorize_customer_message_row,
    categorize_customer_payload_row,
)
from .data_connector import construct_engine

null = None


DAY_REQUEST = os.environ.get("DAY_REQUEST", "2024-05-01")


def get_day_minus_two(date_str):
    # Parse the date string into a datetime object
    date = datetime.strptime(date_str, "%Y-%m-%d")
    # Subtract two days from the date
    date_minus_two = date - timedelta(days=2)
    # Format the new date back to a string
    return date_minus_two.strftime("%Y-%m-%d")


DAY_REQUEST = get_day_minus_two(DAY_REQUEST)

# Substitute <project_root> with the [root folder for your project](https://docs.kedro.org/en/stable/tutorial/spaceflights_tutorial.html#terminology)
CONF_PATH = str(Path(".") / settings.CONF_SOURCE)
CONF_LOADER = OmegaConfigLoader(conf_source=CONF_PATH, env="local")
CREDENTIALS = CONF_LOADER["credentials"]

ENGINES = {
    cred_type: construct_engine(CREDENTIALS[cred_type]) for cred_type in CREDENTIALS
}


logger = logging.getLogger(__name__)
tqdm.pandas()


# def download_new_chatlog(date: str):


def read_query_from_path(path: Path) -> str:
    with open(path, "r") as h:
        content = h.read()
    return content


def query_table(params: Dict) -> DataFrame:
    """
    Query table defined in params (which contains a query) from LC's azr prod server
    Parameters
    ----------
    azr_queries: the query
    credential_dict: server, database, username, password

    Return
    ------
    DataFrame
    """

    for column in ["cred_type", "query_filepath"]:
        try:
            assert column in params
        except AssertionError as missing_column:
            message = f"Column {column} not found"
            raise ValueError(message) from missing_column

    query = read_query_from_path(Path(params["query_filepath"])).format(
        day_request=DAY_REQUEST
    )
    cred_type = params["cred_type"]
    engine = ENGINES[cred_type]

    logger.info(f"Executing {cred_type}:{query}")
    result = pd.read_sql(query, engine)
    logger.info(f"N_rows = {result.shape[0]}")

    if len(result) == 0:
        message = f"No row found for {DAY_REQUEST}"
        logger.error(message)
        raise ValueError(message)

    return result


def json_drop_message(chatlog_df: DataFrame):
    """
    Drop any rows not in correct json format
    Usually caused by lengthy responses (abnormality)
    """

    # We don't use these columns
    to_drop = (
        [
            "id",
            "app_code",
            "live_support_log_id",
            "_id",
        ],
    )

    for col in to_drop:
        try:
            chatlog_df = chatlog_df.drop(
                col,
                axis=1,
            )
        except:
            pass

    def json_loads(row):
        try:
            return json.loads(row["message"])
        except json.JSONDecodeError as e:
            message = str(e)
            logger.warning(message + row["message"])
            return null

    chatlog_df["message_dict"] = chatlog_df.progress_apply(json_loads, axis=1)
    rows_before = chatlog_df.shape[0]
    chatlog_df = chatlog_df.dropna(subset=["message_dict"])
    rows_after = chatlog_df.shape[0]

    if rows_before != rows_after:
        logger.warning(
            f"Dropping {rows_before - rows_after} rows due to invalid json response format"
        )
    chatlog_df = chatlog_df.drop("message_dict", axis=1)
    return chatlog_df


def sorting_chatlog_by_time(chatlog_df: DataFrame) -> DataFrame:
    return chatlog_df.sort_values(["session_id", "created_time"])


def remove_negative_status(chatlog_df: DataFrame) -> DataFrame:
    """
    Remove messages sent with status=-1 (errorneous)
    """
    return chatlog_df[chatlog_df["status"] != -1]


def create_request_success_feature(chatlog_df: DataFrame) -> DataFrame:
    """
    Create a new column named request_human_success:
        - bot_requesthuman_success if request succeed
        - bot_requesthuman_failure otherwise
    """
    chatlog_df["request_human_success"] = chatlog_df.progress_apply(
        request_human_support_success_row, axis=1
    )
    return chatlog_df


def categorize_bot_text(
    chatlog_df: DataFrame, bot_text_pattern: Dict[str, List]
) -> DataFrame:
    """
    Create a new column named bot_text_summary to summarize content
        of robot's automated text messages such as:
        - Greeting
        - Ask for phone number
        - Closing time notification
        etc.
    """
    chatlog_df["bot_text_summary"] = chatlog_df.progress_apply(
        lambda x: categorize_bot_text_row(x, bot_text_pattern), axis=1
    )

    return chatlog_df


def categorize_bot_image(
    chatlog_df: DataFrame, bot_img_pattern: Dict[str, List]
) -> DataFrame:
    """
    Create a new column named bot_image_summary to summarize content
        of robot's automated image messages such as:
        - Ask for phone number for vax program
        - Song khoe
        - Recommendation
        etc.
    """
    chatlog_df["bot_image_summary"] = chatlog_df.progress_apply(
        lambda x: categorize_bot_img_row(x, bot_img_pattern), axis=1
    )

    return chatlog_df


def classify_customer_payload(chatlog_df: DataFrame):
    """
    Create a new column named cus_payload to summarize content
        of customer's payload messages such as:
        - Welcome_flow
        - Diemcuatoi
        - Muathuoc
        - Goodbye_unfollow
        etc.
    """

    chatlog_df["cus_payload"] = chatlog_df.progress_apply(
        categorize_customer_payload_row, axis=1
    )
    return chatlog_df


def categorize_customer_message(chatlog_df: DataFrame):
    """
    Create a new column named cus_event to summarize content
        of customer's messages other than payloads, such as:
        - File (e.g., screenshots)
        - Phone number
        - Location
        - Sticker
        - Just text
    """
    chatlog_df["cus_event"] = chatlog_df.progress_apply(
        categorize_customer_message_row, axis=1
    )

    return chatlog_df


def categorize_agent_message(chatlog_df: DataFrame):
    """
    Create a new column named agent_event to summarize content
        of agent's messages, such as:
        - File (e.g., screenshots)
        - Order confirmation
        - Just text

    """
    chatlog_df["agent_event"] = chatlog_df.progress_apply(
        categorize_agent_message_row, axis=1
    )

    chatlog_df = chatlog_df.drop(
        [
            "source",
            "type",
            "status",
        ],
        axis=1,
    )

    return chatlog_df
