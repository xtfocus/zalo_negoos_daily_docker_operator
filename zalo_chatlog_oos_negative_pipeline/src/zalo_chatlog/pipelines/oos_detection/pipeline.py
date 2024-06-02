from kedro.pipeline import Pipeline, node, pipeline

from extras.torch_model import torch_binary_cls_predict

from .nodes import df_write, oos_feature_extraction


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
                func=df_write,
                inputs=[
                    "oos.prediction",
                    "params:OOS_TABLE",
                    "chatlog.organic.refined",
                ],
                name="oos.write",
                outputs="oos.prediction.session",
            ),
        ]
    )
