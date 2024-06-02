from pandas import DataFrame

from zalo_chatlog.pipelines.data_preprocessing.nodes import ENGINES


def negative_feature_extraction(chatlog: DataFrame) -> DataFrame:
    """
    Extract features needed for negative detection
    """

    chatlog = chatlog[
        (chatlog["sender"] == "Khách hàng") & (chatlog["event"] == "cus_text_other")
    ].reset_index(drop=True)

    chatlog["readable_event"] = chatlog["readable_event"].str.lower()

    chatlog = chatlog.groupby("daily_session_code")["readable_event"].apply(list)
    chatlog = DataFrame(chatlog).reset_index()
    chatlog["features"] = chatlog["readable_event"].apply(lambda x: "\n".join(x))

    return chatlog[["daily_session_code", "features"]]
