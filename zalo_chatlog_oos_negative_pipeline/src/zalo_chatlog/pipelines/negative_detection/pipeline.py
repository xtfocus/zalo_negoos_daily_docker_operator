from kedro.pipeline import Pipeline, node, pipeline

from extras.torch_model import torch_binary_cls_predict

from .nodes import negative_feature_extraction, negative_write


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
                func=negative_write,
                inputs=["negative.prediction", "chatlog.organic.refined"],
                name="negative.write",
                outputs="negative.prediction.session",
            ),
        ]
    )
