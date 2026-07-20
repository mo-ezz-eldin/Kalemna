import time

import uvicorn
from fastapi import Depends,APIRouter
from src.domain.interfaces.ITextClassifier import ITextClassifier
from src.presentation.api.schemas import ChatRequest
from src.presentation.api.dependency import get_intent_classifier, get_sentiment_classifier
from src.application.orchestrator import ChatOrchestrator
from src.application.decision_maker import DecisionMaker

router = APIRouter()

@router.post('/predict_intent')
async def predict_intent(
        request: ChatRequest,

        classifier: ITextClassifier = Depends(get_intent_classifier)
):
    result = classifier.predict(request.text)

    return {"status": "success", "data": result}

@router.post('/predict_feeling')
async def predict_feeling(
        request: ChatRequest,
        classifier: ITextClassifier = Depends(get_sentiment_classifier)
)-> dict[str, str]:

    result = classifier.predict(request.text)

    return {"status": "success", "data": result}


@router.post('/final_prediction')
async def chat_orcherstra(
        request: ChatRequest
)->str:

    return request.text