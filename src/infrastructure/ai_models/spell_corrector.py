from sympy.physics.units import temperature

from src.domain.interfaces.ITextCorrector import ITextCorrector
from transformers import AutoModelForSeq2SeqLM,AutoTokenizer
import torch

class SpellCorrector(ITextCorrector):
    def __init__(self,model_path,tokenizer_path):
        self.device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model=AutoModelForSeq2SeqLM.from_pretrained(model_path)
        self.model.to(self.device).eval()
        self.tokenizer=AutoTokenizer.from_pretrained(tokenizer_path)


    def predict(self,text)->str:
        input_ids=self.tokenizer(text,return_tensors="pt",padding=True,truncation=True)['input_ids'].to(self.device)
        output=self.model.generate(input_ids,max_length=512,do_sample=True,temperature=0.5)
        generated_text=self.tokenizer.batch_decode(output,skip_special_tokens=True)
        return generated_text
