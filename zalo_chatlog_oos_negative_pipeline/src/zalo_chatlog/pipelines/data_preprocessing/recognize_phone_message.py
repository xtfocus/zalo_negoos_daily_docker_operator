import json
import logging
import re

null = None

logger = logging.getLogger(__name__)


def recognize_customer_phone_row(row, pattern):
    if (row["message_type"] != "text") or (row["source"] != 1):
        return null
    else:
        text = json.loads(row["message"])["content"]["text"].strip()
        match = re.match(pattern, text)
        if match:
            return "cus_send_phone_number"
    return null
