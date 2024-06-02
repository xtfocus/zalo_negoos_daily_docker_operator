"""
This is a boilerplate pipeline 'data_preprocessing'
generated using Kedro 0.18.14
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    categorize_agent_message,
    categorize_bot_image,
    categorize_bot_text,
    categorize_customer_message,
    classify_customer_payload,
    create_request_success_feature,
    json_drop_message,
    query_table,
    remove_negative_status,
    sorting_chatlog_by_time,
)


def define_preprocessing_nodes():
    return [
        node(
            func=query_table,
            inputs=["params:chatlog.source"],
            outputs="chatlog",
            name="get.daily.chatlog",
        ),
        node(
            func=json_drop_message,
            inputs=["chatlog"],
            outputs="chatlog.json.drop",
            name="json.drop.message",
        ),
        node(
            func=sorting_chatlog_by_time,
            inputs=["chatlog.json.drop"],
            outputs="chatlog.sorted",
            name="sort.chatlog",
        ),
        node(
            func=remove_negative_status,
            inputs=["chatlog.sorted"],
            outputs="chatlog.positive",
            name="filter.status.positive",
        ),
        node(
            func=create_request_success_feature,
            inputs=["chatlog.positive"],
            outputs="chatlog.request.human.status",
            name="request.human.status",
        ),
        node(
            func=categorize_bot_text,
            inputs=["chatlog.request.human.status", "params:bot_text_pattern"],
            outputs="chatlog.bot.text.classified",
            name="classify.bot.text",
        ),
        node(
            func=categorize_bot_image,
            inputs=["chatlog.bot.text.classified", "params:bot_img_pattern"],
            outputs="chatlog.bot.img.classified",
            name="classify.bot.img",
        ),
        node(
            func=classify_customer_payload,
            inputs=["chatlog.bot.img.classified"],
            outputs="chatlog.customer.payload",
            name="classify.customer.payload",
        ),
        node(
            func=categorize_customer_message,
            inputs=["chatlog.customer.payload"],
            outputs="chatlog.customer.event",
            name="recognize.customer.phone",
        ),
        node(
            func=categorize_agent_message,
            inputs=["chatlog.customer.event"],
            outputs="chatlog.agent.event",
            name="recognize.agent.event",
        ),
    ]


def create_pipeline(**kwargs) -> Pipeline:
    nodes = []
    nodes += define_preprocessing_nodes()
    return pipeline(nodes)
