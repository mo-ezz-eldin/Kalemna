from fastapi import Request
from fastapi.security import OAuth2PasswordBearer

from src.domain.interfaces.IDatabase import IDatabase
from src.domain.interfaces.ITextClassifier import ITextClassifier
from src.infrastructure.monitoring.adding_custom_metrics import WAITING_REQUESTS
import asyncio

chat_semaphore = asyncio.Semaphore(10)


def get_intent_classifier(request: Request) -> ITextClassifier:
    return request.app.state.intent_model


def get_sentiment_classifier(request: Request) -> ITextClassifier:
    return request.app.state.sentiment_model


def get_db(request: Request) -> IDatabase:
    return request.app.state.rel_db


def get_agent_graph(request: Request):
    return request.app.state.graph


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_limitation(request: Request):
    return request.app.state.limiter


async def limit_concurrency_and_track_waiting(request: Request):
    WAITING_REQUESTS.inc()
    try:
        async with chat_semaphore:
            WAITING_REQUESTS.dec()

            yield

    except asyncio.CancelledError:
        WAITING_REQUESTS.dec()
        raise


