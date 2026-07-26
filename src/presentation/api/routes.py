import time
from fastapi.responses import StreamingResponse
import uvicorn
from fastapi import Depends,APIRouter,Request
from langgraph.graph.state import CompiledStateGraph
from src.domain.interfaces.ITextClassifier import ITextClassifier
from src.presentation.api.schemas import ChatRequest
from src.presentation.api.dependency import get_intent_classifier, get_sentiment_classifier
from langchain_core.messages import HumanMessage

router = APIRouter()

async def stream_tokens(thread_id:str,user_query:str,graph:CompiledStateGraph):
    inputs ={'user_id':thread_id,
            'user_query':user_query,
            'messages':[HumanMessage(content=user_query)],
             }

    config = {'configurable':{'thread_id':thread_id}}

    async for event in graph.astream_events(inputs,config,version='v2'):
        kind_of_event = event['event']

        if kind_of_event == 'on_chat_model_stream':
            token=event['data']['chunk'].content
            if token:
                yield f"data: {token}\n\n"


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


@router.post('/chat')
async def chat(request_message:ChatRequest,graph_app:Request):
    graph = graph_app.app.state.graph

    thread_id = request_message.user_id

    user_query= request_message.text

    return StreamingResponse(stream_tokens(thread_id,
                                           user_query,
                                           graph),
                             media_type='text/event-stream')


