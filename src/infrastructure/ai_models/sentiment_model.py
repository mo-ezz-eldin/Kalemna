from src.domain.interfaces.ITextClassifier import ITextClassifier
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
class SentimentClassifier(ITextClassifier):
    def __init__(self,model_path:str,labels:dict,tokenizer_path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
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

