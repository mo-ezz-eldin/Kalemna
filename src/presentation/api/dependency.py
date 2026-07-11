from fastapi import Request,Depends

from src.application.decision_maker import DecisionMaker
from src.domain.interfaces.ITextClassifier import ITextClassifier
from src.infrastructure.preprocessing.preprocessing import TextPreprocessor
from src.application.orchestrator import ChatOrchestrator
def get_intent_classifier(request:Request) -> ITextClassifier:
    return request.app.state.intent_model

def get_sentiment_classifier(request:Request) -> ITextClassifier:
    return request.app.state.sentiment_model


def get_chatorchestra(intent:ITextClassifier=Depends(get_intent_classifier),
sentiment:ITextClassifier =Depends(get_sentiment_classifier))->ChatOrchestrator:
    return ChatOrchestrator(
        intent_model = intent,
        sentiment_model = sentiment,
        preprocessor=TextPreprocessor()
    )


def decide(Orechstra:ChatOrchestrator = Depends(get_chatorchestra))->DecisionMaker:
    return DecisionMaker(orchestrator=Orechstra)
