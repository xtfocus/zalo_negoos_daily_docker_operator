import logging
from typing import List

logger = logging.getLogger(__name__)

null = None


def get_event(row, events: List[str]):
    """
    Make sure the row contains no more than one event. If this is violated,
        raise error

    If no event detected, raise warning and return null
    If a single detected, return that event
    """
    event = []
    for column in events:
        if row[column] is not null:
            event.append(row[column])

    try:
        assert len(event) <= 1
    except AssertionError as e:
        message = f"More than one event detected for {row['session_id']} {event}\nConsider reviewing patterns or event definition"
        logger.error(message)
        raise ValueError(message) from e

    if event:
        return event[0]
    else:
        logger.warning(f"No event detected for {row['message']}")
        return null
