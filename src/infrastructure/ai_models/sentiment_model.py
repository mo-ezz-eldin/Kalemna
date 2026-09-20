from typing import Any

import onnxruntime

from src.domain.interfaces.ITextClassifier import ITextClassifier
import numpy as np
from transformers import  AutoTokenizer
from optimum.onnxruntime import ORTModelForSequenceClassification

class SentimentClassifier(ITextClassifier):
    def __init__(self,model_path:str,tokenizer_path : str , labels:dict  , ort : onnxruntime.SessionOptions):

        self.model = ORTModelForSequenceClassification.from_pretrained(model_path ,
                     providers=["CPUExecutionProvider"] , session_options=ort ,file_name='sentiment_quantized_onnx.onnx')
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        self.labels = labels
    def predict(self,text)->dict[str , Any]:

            inputs=self.tokenizer(text,return_tensors='np',padding=True,truncation=True,max_length=128)

            outputs = self.model(**inputs)

            logits = outputs.logits[0]

            exp_logits = np.exp(logits - np.max(logits))

            probabilities = exp_logits / exp_logits.sum()

            ind=np.argmax(probabilities)

            confidence = probabilities[ind]

            feeling=self.labels.get(int(ind),'unknown')

            return {'feeling':feeling,'confidence':float(confidence)}

