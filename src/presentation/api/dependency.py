from fastapi import Request
from src.application.decision_maker import DecisionMaker
from src.domain.interfaces.ITextClassifier import ITextClassifier
from src.application.orchestrator import ChatOrchestrator
from src.domain.interfaces.IDatabase import IDatabase
def get_intent_classifier(request:Request) -> ITextClassifier:
    return request.app.state.intent_model

def get_sentiment_classifier(request:Request) -> ITextClassifier:
    return request.app.state.sentiment_model


def get_db(request:Request) -> IDatabase:
    return request.app.state.rel_db


def get_agent_graph(request: Request):
    return request.app.state.graph
