from pandas import DataFrame

from zalo_chatlog.pipelines.data_preprocessing.nodes import ENGINES

cred_type = "seventy_eight"
PREDICTION_TABLE_NAME = "OOS_PREDICTION"
ENGINE = ENGINES[cred_type]


def oos_feature_extraction(chatlog: DataFrame) -> DataFrame:
    """
    Extract features needed for out-of-stock detection
    """

    chatlog = chatlog[
        (chatlog["sender"] == "Nhân viên") & (chatlog["event"] == "agent_text_other")
    ].reset_index(drop=True)

    chatlog["readable_event"] = chatlog["readable_event"].str.lower()

    # Remove likely irrelevant texts
    chatlog = chatlog[
        ~chatlog["readable_event"].str.contains(
            "chào|xin phép|đợi em|chờ em|cảm ơn|cám ơn|người đặt"
        )
    ].reset_index()

    chatlog = chatlog.groupby("daily_session_code")["readable_event"].apply(list)
    chatlog = DataFrame(chatlog).reset_index()
    chatlog["features"] = chatlog["readable_event"].apply(lambda x: "\n".join(x))

    return chatlog[["daily_session_code", "features"]]


def oos_write(prediction_df: DataFrame, sessions: DataFrame) -> DataFrame:
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
