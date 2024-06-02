from os.path import isfile
from typing import Any, Dict

import numpy as np
import torch
from kedro.io import AbstractDataset
from pandas import DataFrame
from torch import nn
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer

from extras.text_dataset import create_data_loader

MODEL_NAME = "uitnlp/visobert"


class BinaryClassifierFromPretrainedWrapper(AbstractDataset):
    """
    Torch model loading & saving using `state_dict` rather than pickle
    """

    def _describe(self) -> Dict[str, Any]:
        return dict(filepath=self._filepath)

    def __init__(self, filepath: str, **kwargs) -> None:
        self._filepath = filepath
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _exists(self) -> bool:
        return isfile(self._filepath)

    def _save(self, model) -> None:
        torch.save(model.state_dict(), self._filepath)

    def _load(self):
        model = BinaryClassifierFromPretrained()
        model.load_state_dict(torch.load(self._filepath))
        return model


class BinaryClassifierFromPretrained(nn.Module):
    """
    a BERT model + nn.Linear using pooled_output
    freeze_until: Number of initial training steps to freeze
    """

    def __init__(self, n_classes=2, freeze_until=0):
        super(BinaryClassifierFromPretrained, self).__init__()

        self.bert = AutoModel.from_pretrained(MODEL_NAME)
        self.freeze_until = freeze_until

        for child in self.bert.children():
            for param in child.parameters():
                param.requires_grad = False

        self.drop = nn.Dropout(p=0.5)

        self.out = nn.Linear(self.bert.config.hidden_size, n_classes)

    def forward(self, input_ids, attention_mask):

        self.freeze_until -= 1

        # Execute once
        if self.freeze_until == 0:
            for child in self.bert.children():
                for param in child.parameters():
                    param.requires_grad = True

        last_hidden_state, pooled_output = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=False,  # https://stackoverflow.com/questions/65082243/dropout-argument-input-position-1-must-be-tensor-not-str-when-using-bert
        )

        dropped = self.drop(pooled_output)

        return self.out(dropped)


def torch_binary_cls_predict(features: DataFrame, model):
    MAX_LEN = 150
    BATCH_SIZE = 128

    ARRAY_SIZE = len(features)
    device = "cuda"

    model.to(device)
    model.eval()

    ptr_tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    dataset = create_data_loader(features, ptr_tokenizer, MAX_LEN, BATCH_SIZE)

    ARRAY_SIZE = len(features)
    predictions = np.zeros(ARRAY_SIZE, dtype=int)
    prediction_probs = np.zeros(
        (ARRAY_SIZE, 2)
    )  # Assuming model.num_labels gives the number of classes

    # Index to keep track of the position in the numpy array
    index = 0

    # Iterate through the dataset
    for d in tqdm(dataset, desc="Processing", unit="batch"):
        input_ids = d["input_ids"].to(device)
        attention_mask = d["attention_mask"].to(device)

        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)

        # Get predicted labels (whichever class of higher probability) and predicted probabilities
        _, preds = torch.max(outputs, dim=1)
        probs = torch.nn.functional.softmax(outputs, dim=1)

        # Get the current batch size (it might be less than BATCH_SIZE for the last batch)
        batch_size = input_ids.size(0)

        # Populate the numpy arrays
        predictions[index : index + batch_size] = preds.cpu().numpy()
        prediction_probs[index : index + batch_size] = probs.cpu().numpy()

        # Update the index
        index += batch_size

    features["prediction"] = predictions
    features["probs_pos"] = [i[1] for i in prediction_probs]

    return features
