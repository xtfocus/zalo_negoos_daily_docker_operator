import json
import logging
import re

null = None

logger = logging.getLogger(__name__)


def categorize_customer_message_row(row):
    """
    Parameters:
    -----------
        row: pandas row

    Return:
    -------
        Categorization of customer message: cus_file, cus_sticker, cus_text_phone,
            or others (cus_text_other)
        Return null if the message_type is payload or not recognized

    """

    if (row["source"] != 1) or (row["message_type"] == "payload"):
        return null

    elif row["message_type"] == "sticker":
        return "cus_sticker"

    elif row["message_type"] == "file":
        return "cus_file"

    elif row["message_type"] == "user_send_location":
        return "cus_location"

    elif row["message_type"] == "text":
        text = json.loads(row["message"])["content"]["text"].strip()

        phone_pattern = r"^[\d\s\+\-]{7,}$"
        match = re.match(phone_pattern, text)

        if match:
            return "cus_text_phone"
        else:
            return "cus_text_other"  # other kinds of texts

    else:
        warning = f"message_type {row['message_typ']} is not recognized"
        logger.warning(warning)

        return null


def categorize_customer_payload_row(row):
    """
    If row's message_type is not customer's payload, return null
    Otherwiser eturn cus_payload_<payload's name>.
    """
    if (row["message_type"] != "payload") or (row["source"] != 1):
        return null
    else:
        # pattern = r'"text":"(.*?)#.*?"'
        # There are cases where # is not in payload. Weird
        pattern = r'"text":"(.*?)"'

        match = re.search(pattern, row["message"])

        if match:
            result = match.group(1)
            return "cus_payload_" + result.replace(" ", "")
        else:
            # logger.warning(f"Non-classified user payload: {row['message']}")
            return "cus_payload_unknown"
