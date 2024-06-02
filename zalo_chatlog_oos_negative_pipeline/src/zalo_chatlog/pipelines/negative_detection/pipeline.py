from kedro.pipeline import Pipeline, node, pipeline

from extras.torch_model import torch_binary_cls_predict
from zalo_chatlog.pipelines.oos_detection.nodes import df_write

from .nodes import negative_feature_extraction


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=negative_feature_extraction,
                inputs=["chatlog.organic.refined"],
                outputs="negative.features",
                name="negative.feature.extract",
            ),
            node(
                func=torch_binary_cls_predict,
                inputs=["negative.features", "negative.model"],
                outputs="negative.prediction",
                name="negative.predict",
            ),
            node(
                func=df_write,
                inputs=[
                    "negative.prediction",
                    "params:NEGATIVE_TABLE",
                    "chatlog.organic.refined",
                ],
                name="negative.write",
                outputs="negative.prediction.session",
            ),
        ]
    )
