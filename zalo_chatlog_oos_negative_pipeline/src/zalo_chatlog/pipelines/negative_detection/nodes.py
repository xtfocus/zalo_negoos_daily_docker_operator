from pandas import DataFrame

from zalo_chatlog.pipelines.data_preprocessing.nodes import ENGINES

cred_type = "seventy_eight"
PREDICTION_TABLE_NAME = "NEGATIVE_PREDICTION"
ENGINE = ENGINES[cred_type]


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


def negative_write(prediction_df: DataFrame, sessions: DataFrame) -> DataFrame:
    prediction_df = prediction_df[["daily_session_code", "prediction", "probs_pos"]]
    sessions = sessions[
        ["daily_session_code", "session_id", "readable_event"]
    ].drop_duplicates()

    df = sessions.merge(prediction_df, how="left", on="daily_session_code")
    df["session_ids"] = df["daily_session_code"].map(
        df.groupby("daily_session_code")["session_id"].agg(list)
    )
    df["session_ids"] = df["session_ids"].apply(lambda x: "_".join(x))
    df = df.drop_duplicates("daily_session_code")
    df.to_sql(PREDICTION_TABLE_NAME, con=ENGINE, if_exists="append", index=False)
    return df
