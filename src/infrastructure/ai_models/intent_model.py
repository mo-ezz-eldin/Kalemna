import torch
from src.domain.interfaces.ITextClassifier import ITextClassifier
from transformers import AutoTokenizer, AutoModelForSequenceClassification


class IntentModel(ITextClassifier):
    def __init__(self, model_path: str, labels_map: dict,tokenizer_path: str):

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.model = AutoModelForSequenceClassification.from_pretrained(model_path).to(self.device)

        self.model =  ORTModelForSequenceClassification.from_pretrained(model_path)

        self.model.eval()

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

        with torch.no_grad():
            outputs = self.model(input_ids)
            logits = outputs.logits

            probabilities = torch.nn.functional.softmax(logits, dim=-1)

            confidence, index = torch.max(probabilities[0], dim=-1)

            intent_label = self.labels_map.get(index.item(), "Unknown")

            return {
                'intent': intent_label,
                'confidence': confidence.item()
            }