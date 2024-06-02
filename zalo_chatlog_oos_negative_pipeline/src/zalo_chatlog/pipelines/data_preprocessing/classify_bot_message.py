import logging
from typing import Dict, List

null = None

logger = logging.getLogger(__name__)


def request_human_support_success_row(row):
    """
    Parameters:
    -----------
        row: pandas row

    Return:
    -------
        If a row is request_human_support:
            if success: return bot_requesthuman_success
            otherwise: return bot_requesthuman_failure

        If a row is not a request_human_support, return null
    """

    if row["message_type"] != "request_human_support":
        return null
    elif "so_dien_thoai" in row["message"]:
        return "bot_requesthuman_success"
    else:
        return "bot_requesthuman_failure"


def categorize_bot_text_row(row, bot_text_pattern: Dict[str, List[str]]):
    """
    Parameters:
    -----------
        row: pandas row
        bot_text_pattern: patterns to recognize bot text content

    Return:
    -------
        If a row is bot text, categorize it. Otherwise return null
        If the bot text doesn't match any patterns, warn and return `bot_text_unknown`
    """

    if (row["source"] == 1) or (row["email"]) or (row["message_type"] != "text"):
        return null
    else:
        for key, values in bot_text_pattern.items():
            if all([value in row["message"] for value in values]):
                return key

        # logger.warning(f"Non-classified bot text: {row['message']}")

        return "bot_text_unknown"


def categorize_bot_img_row(row, bot_img_pattern: Dict[str, List[str]]):
    """
    Parameters:
    -----------
        row: pandas row
        bot_img_pattern: patterns to recognize bot img content

    Return:
    -------
        If a row is bot text, categorize it. Otherwise return null
        If the bot image doesn't match any patterns, return unknown
    """
    if (
        (row["source"] == 1)
        or (row["email"])
        or ((row["message_type"] != "image") and (row["message_type"] != "carousel"))
    ):
        return null
    else:
        for key, values in bot_img_pattern.items():
            if all([value in row["message"] for value in values]):
                return "bot_img_" + key

        # logger.warning(f"Non-classified bot img: {row['message']}")
        return "bot_img_unknown"
