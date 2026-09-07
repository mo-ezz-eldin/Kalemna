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
        with torch.no_grad():
            input_ids=self.tokenizer(text,return_tensors='pt',padding=True,truncation=True,max_length=128)['input_ids'].to(self.device)
            outputs = self.model(input_ids)
            logits = outputs.logits
            prob=torch.nn.functional.softmax(logits, dim=-1)
            confidence,ind=torch.max(prob,dim=-1)
            feeling=self.labels.get(ind.item(),'unknown')
            return {'feeling':feeling,'confidence':confidence.item()}

