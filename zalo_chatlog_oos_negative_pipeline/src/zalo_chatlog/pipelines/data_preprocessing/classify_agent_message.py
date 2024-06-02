import logging

null = None

logger = logging.getLogger(__name__)


def categorize_agent_message_row(row):
    """
    Parameters:
    -----------
        row: pandas row

    Return:
    -------
        Categorization of agent message: agent_file, confirm_order,
            or others (agent_text_other a.k.a organic)

    """
    if not (row["email"]):
        return null
    else:
        if row["message_type"] == "file":
            return "agent_file"

        elif row["message_type"] == "text":
            if all(
                [
                    text in row["message"]
                    for text in ("Người đặt", "Tổng tiền", "thanh toán")
                ]
            ):
                return "agent_text_confirmorder"

            else:
                return "agent_text_other"  # Organic
        else:
            # Warning if message_type not recognized
            warning = f"message_type {row['message_typ']} is not recognized"
            logger.warning(warning)
            raise null
