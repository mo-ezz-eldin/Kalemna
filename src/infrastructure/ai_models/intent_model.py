import numpy as np
import onnxruntime
from optimum.onnxruntime import ORTModelForSequenceClassification
from src.domain.interfaces.ITextClassifier import ITextClassifier
from transformers import AutoTokenizer


class IntentModel(ITextClassifier):
    def __init__(self, model_path: str, labels_map: dict , ort : onnxruntime.SessionOptions):


        self.model =  ORTModelForSequenceClassification.from_pretrained(model_path ,
                      providers=[ "CPUExecutionProvider"] ,session_options=ort , file_name='model_quantized.onnx')

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)


        self.labels_map = labels_map

    def predict(self, text: str) -> dict:

        inputs = self.tokenizer(
            text,
            return_tensors="np",
            truncation=True,
            padding=True,
            max_length=128
        )


        outputs = self.model(**inputs)


        logits = outputs.logits[0]

        exp_logits = np.exp(logits - np.max(logits))
        probabilities = exp_logits / exp_logits.sum()

        index = np.argmax(probabilities)
        confidence = probabilities[index]

        intent_label = self.labels_map.get(int(index), "Unknown")

        return {
            'intent': intent_label,
            'confidence': float(confidence)
        }