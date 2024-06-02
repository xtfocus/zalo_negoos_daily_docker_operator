"""
This is a boilerplate pipeline 'data_separation'
generated using Kedro 0.18.14
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    categorize_organic_sessions,
    connecting_sessions,
    create_time_column,
    export_organic_message_data,
    pool_events,
)


def define_separation_nodes():
    return [
        node(
            func=connecting_sessions,
            inputs=["chatlog.agent.event"],
            outputs="chatlog.connected.session",
            name="connect.session",
        ),
        node(
            func=create_time_column,
            inputs=["chatlog.connected.session"],
            outputs="chatlog.time.feature",
            name="create.time.feature",
        ),
        node(
            func=pool_events,
            inputs=["chatlog.time.feature", "params:event_columns"],
            outputs="chatlog.pool.events",
            name="pool.events",
        ),
        node(
            func=categorize_organic_sessions,
            inputs=["chatlog.pool.events", "params:organic_requirements"],
            outputs="chatlog.organic.session",
            name="organic.session",
        ),
        node(
            func=export_organic_message_data,
            inputs=["chatlog.organic.session", "params:fillers", "params:synonyms"],
            outputs="chatlog.organic.refined",
            name="refined.organic.messages",
        ),
    ]


def create_pipeline(**kwargs) -> Pipeline:
    nodes = []
    nodes += define_separation_nodes()
    return pipeline(nodes)
