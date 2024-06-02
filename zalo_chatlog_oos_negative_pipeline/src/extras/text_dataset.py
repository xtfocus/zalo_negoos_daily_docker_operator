from datasets import load_dataset
from torch.utils.data import DataLoader, Dataset


class TextDataset(Dataset):
    """
    TextDataset for the inference
    """

    def __init__(self, session_text_df, tokenizer, max_len):
        self.texts = list(session_text_df["features"])
        self.uuid = list(session_text_df["daily_session_code"])
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, item):

        text = self.texts[item]
        uuid = self.uuid[item]

        # Encoding documentation
        # https://huggingface.co/docs/transformers/v4.38.1/en/internal/tokenization_utils#transformers.PreTrainedTokenizerBase.encode_plus
        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            truncation=True,
            padding="max_length",  # Truncate to `max_length`
            return_token_type_ids=False,  # token Type IDs is only relevant when input includes 2 sequences (such as for QA problem. See https://huggingface.co/docs/transformers/v4.38.1/en/glossary#token-type-ids)
            return_attention_mask=True,
            return_tensors="pt",  # return pytorch tensors
        )

        return {
            "text": text,
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "uuid": uuid,
        }


def create_data_loader(session_text_df, tokenizer, max_len, batch_size):
    ds = TextDataset(
        session_text_df=session_text_df,
        tokenizer=tokenizer,
        max_len=max_len,
    )

    return DataLoader(ds, batch_size=batch_size, num_workers=4)
