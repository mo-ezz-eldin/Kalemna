from src.domain.interfaces.ITextClassifier import ITextClassifier
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
class SentimentClassifier(ITextClassifier):
    def __init__(self,model_path:str,labels:dict,tokenizer_path):

        self.model = ORTModelForSequenceClassification.from_pretrained(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.labels = labels
        self.model.eval()
    def predict(self,text)->dict:

            inputs=self.tokenizer(text,return_tensors='np',padding=True,truncation=True,max_length=128)

            outputs = self.model(**inputs)

            logits = outputs.logits[0]

            exp_logits = np.exp(logits - np.max(logits))

            probabilities = exp_logits / exp_logits.sum()

            ind=np.argmax(probabilities)

            confidence = probabilities[ind]

            feeling=self.labels.get(int(ind),'unknown')

            return {'feeling':feeling,'confidence':confidence.item()}

