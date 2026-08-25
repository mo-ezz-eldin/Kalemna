from fastapi.responses import StreamingResponse , JSONResponse
from fastapi import Depends,APIRouter,Request
from langgraph.graph.state import CompiledStateGraph

from src.domain.interfaces.ITextClassifier import ITextClassifier
from src.presentation.api.schemas import ChatRequest
from src.presentation.api.dependency import get_intent_classifier, get_sentiment_classifier, get_agent_graph , oauth2_scheme
from langchain_core.messages import HumanMessage
from loguru import logger


router = APIRouter()


async def stream_tokens(thread_id: str, user_query: str, graph: CompiledStateGraph):
    try:
        inputs = {
        'user_id': thread_id,
        'user_query': user_query,
        'messages': [HumanMessage(content=user_query)],
    }
        config = {'configurable': {'thread_id': thread_id}}

        logger.info("--- STREAM STARTING ---")

        logger.info(f" Serving {thread_id} \n User_query : {user_query}")

        async for event in graph.astream_events(inputs, config, version='v2'):
            kind_of_event = event['event']
            if kind_of_event == 'on_chat_model_stream':
                tags = event.get('tags', [])
                metadata = event.get('metadata', {})
                node_name = metadata.get('langgraph_node', '')


                if node_name == 'finalize' and 'final_responder' in tags:
                    raw_token = event['data']['chunk'].content

                    if isinstance(raw_token, list):
                        token = "".join([t.get("text", "") if isinstance(t, dict) else str(t) for t in raw_token])
                    else:
                        token = str(raw_token)

                    if token:
                        lines = token.split('\n')
                        for line in lines:
                            if line:
                                yield f"data: {line}\n\n"
                            else:
                                yield "data: \n\n"

        logger.info(" --- STREAM FINISHED ---")

    except Exception as e:
        logger.exception(f"there is error in :{e}")
        raise e


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
async def chat(request_message:ChatRequest,
               graph_app: CompiledStateGraph = Depends(get_agent_graph) ,
               token : str =  Depends(oauth2_scheme)):
    graph = graph_app

    thread_id = request_message.user_id

    user_query= request_message.text

    return StreamingResponse(stream_tokens(thread_id,
                                           user_query,
                                           graph),
                             media_type='text/event-stream')


@router.post('/test_chat_without_streaming')
async def test_chat_without_streaming(request_message:ChatRequest,graph_app:Request):
    graph = graph_app.app.state.graph

    thread_id = request_message.user_id

    user_query = request_message.text

    inputs = {
        'user_id': thread_id,
        'user_query': user_query,
        'messages': [HumanMessage(content=user_query)],
    }
    config = {'configurable': {'thread_id': thread_id}}

    print("Checkpointer type:", type(graph.checkpointer))

    results = await graph.ainvoke(input = inputs, config = config)

    saved_state = await graph.aget_state(config=config)

    print("Saved State from Checkpointer:", saved_state)

    return {"results": results}





