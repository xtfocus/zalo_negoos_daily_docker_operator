import logging
from typing import Dict, Text

import sqlalchemy as sa

log = logging.getLogger(__name__)


def construct_engine(credential_dict: Dict[Text, Text]) -> Text:
    """
    Generate connection url with crediential dict

    Parameters
    ----------
    credential_dict: server, database, username, password

    Return
    ------
    Connection url

    """
    for key in ["server", "database", "username", "password"]:
        try:
            assert key in credential_dict
        except AssertionError as field_missing:
            message = f"Field {key} not found"
            log.error(message)
            raise KeyError(message) from field_missing

    connection_url = sa.engine.URL.create(
        "mssql+pyodbc",
        username=credential_dict["username"],
        password=credential_dict["password"],
        host=credential_dict["server"],
        database=credential_dict["database"],
        query={
            "driver": "ODBC Driver 17 for SQL Server",
            "autocommit": "True",
        },
    )

    engine = sa.create_engine(connection_url)

    return engine
