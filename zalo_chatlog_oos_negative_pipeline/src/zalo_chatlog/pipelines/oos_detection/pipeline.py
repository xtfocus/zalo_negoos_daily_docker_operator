from kedro.pipeline import Pipeline, node, pipeline

from extras.torch_model import torch_binary_cls_predict

from .nodes import oos_feature_extraction, oos_write


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=oos_feature_extraction,
                inputs=["chatlog.organic.refined"],
                outputs="oos.features",
                name="oos.feature.extract",
            ),
            node(
                func=torch_binary_cls_predict,
                inputs=["oos.features", "oos.model"],
                outputs="oos.prediction",
                name="oos.predict",
            ),
            node(
                func=oos_write,
                inputs=["oos.prediction", "chatlog.organic.refined"],
                name="oos.write",
                outputs="oos.prediction.session",
            ),
        ]
    )
