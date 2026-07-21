from src.domain.interfaces.ITextClassifier import ITextClassifier
from src.infrastructure.preprocessing.preprocessing import TextPreprocessor
from langsmith import traceable
class ChatOrchestrator():
    def __init__(self,intent_model:ITextClassifier,sentiment_model:ITextClassifier,preprocessor:TextPreprocessor):
        self.intent_model = intent_model
        self.sentiment_model = sentiment_model
        self.preprocessor = preprocessor
    @traceable(name='ChatOrchestrator')
    def execute(self,text:str)->dict:

        text=self.preprocessor.preprocess(text)


        intent_result=self.intent_model.predict(text)

        sentiment_result=self.sentiment_model.predict(text)

        return {"intent_result":intent_result,"sentiment_result":sentiment_result}