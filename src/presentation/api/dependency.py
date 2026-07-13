from fastapi import Request,Depends
from src.presentation.api.app import app
from src.application.decision_maker import DecisionMaker
from src.domain.interfaces.ITextClassifier import ITextClassifier
from src.application.orchestrator import ChatOrchestrator
def get_intent_classifier(request:Request) -> ITextClassifier:
    return request.app.state.intent_model

def get_sentiment_classifier(request:Request) -> ITextClassifier:
    return request.app.state.sentiment_model


def get_chatorchestra(request:Request) -> ChatOrchestrator:

    return ChatOrchestrator(
        intent_model = app.state.intent_model,
        sentiment_model = app.state.sentiment_model,
        preprocessor=app.state.preprocessor
    )


def decide(Orechstra:ChatOrchestrator = Depends(get_chatorchestra))->DecisionMaker:
    return DecisionMaker(orchestrator=Orechstra)
