from typing import Any

import numpy as np
import onnxruntime
from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer

from src.domain.interfaces.ITextClassifier import ITextClassifier


class SentimentClassifier(ITextClassifier):
    def __init__(self, model_path: str, tokenizer_path: str, labels: dict, ort: onnxruntime.SessionOptions):

        self.model = ORTModelForSequenceClassification.from_pretrained(
            model_path,
            providers=["CPUExecutionProvider"],
            session_options=ort,
            file_name="sentiment_quantized_onnx.onnx",
        )
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        self.labels = labels

    def predict(self, text) -> dict[str, Any]:

        inputs = self.tokenizer(text, return_tensors="np", padding=True, truncation=True, max_length=128)

        tokens = {key: np.int64(value) for key, value in inputs.items()}

        outputs = self.model(**tokens)

        logits = outputs.logits[0]

        exp_logits = np.exp(logits - np.max(logits))

        probabilities = exp_logits / exp_logits.sum()

        ind = np.argmax(probabilities)

        confidence = probabilities[ind]

        feeling = self.labels.get(int(ind), "unknown")

        return {"feeling": feeling, "confidence": float(confidence)}
