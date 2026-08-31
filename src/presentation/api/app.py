from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from loguru import logger

from src.infrastructure.ai_models.llm_proxy import LLMProxy
from src.infrastructure.logging.logger_setup import setup_logging
from contextlib import asynccontextmanager

from src.infrastructure.security.rate_limit import limiter
from src.presentation.exceptions.exception_handlers import exception_handler
from src.application.decision_maker import DecisionMaker
from src.application.graphs.customer_graph import build_customer_support_graph
from src.application.orchestrator import ChatOrchestrator
from src.config.settings import settings
from src.config.Constant import SENTIMENT_LABELS,INTENT_LABELS
from src.infrastructure.ai_models.intent_model import IntentModel
from src.infrastructure.ai_models.sentiment_model import SentimentClassifier
from src.presentation.api.routes.chat import router
from src.presentation.api.routes.auth import auth_router
from src.infrastructure.preprocessing.preprocessing import TextPreprocessor
from src.infrastructure.databases.posgres_db import PosgresDb
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded




@asynccontextmanager
async def lifespan_context(app: FastAPI):
    setup_logging()
    try:


        logger.info('DB, AI Models , LLM and Graph are starting.....')
        app.state.intent_model = IntentModel(
        model_path=settings.intent_model_path,
        labels_map=INTENT_LABELS,
        tokenizer_path=settings.intent_tokenizer
        )
        logger.info('Intent model loaded successfully!')

        app.state.sentiment_model = SentimentClassifier(
        model_path=settings.sentiment_model_path,
        tokenizer_path=settings.sentiment_tokenizer,
        labels=SENTIMENT_LABELS
        )
        logger.info('Sentiment model loaded successfully!')

        app.state.preprocessor = TextPreprocessor()


        app.state.pool = AsyncConnectionPool(
        conninfo=settings.postgres_db_conn.replace("+asyncpg", ""),
        kwargs={"autocommit": True},
        open=False
        )


        await app.state.pool.open()




        app.state.checkpointer = AsyncPostgresSaver(app.state.pool)
        await app.state.checkpointer.setup()

        app.state.rel_db = PosgresDb(config=settings.postgres_db_conn)

        await app.state.rel_db.setup_db()

        logger.info('DB with short memory and long memory loaded successfully!')

        app.state.llm_proxy = LLMProxy(primary_provider='google_gemini' , fallback_provider='cohere' ,
                                       primary_api_key=settings.gemini_api_key , fallback_api_key=settings.cohere_api_key ,
                                       temperature=0.0)

        logger.info('LLM proxy loaded successfully!')

        app.state.graph = build_customer_support_graph(
        orchestrator=ChatOrchestrator(
            intent_model=app.state.intent_model,
            sentiment_model=app.state.sentiment_model,
            preprocessor=app.state.preprocessor
        ),
        decision_maker=DecisionMaker(),
        db=app.state.rel_db,
        chckpointer=app.state.checkpointer ,
            llm_proxy= app.state.llm_proxy
        )

        logger.info("Graph loaded successfully!")
    except Exception as e:
        logger.exception(f'failed to start application: {e}')
        raise e

    yield

    logger.info("🛑 Shutting down: Cleaning up memory and DB connections...")


    app.state.intent_model = None
    app.state.sentiment_model = None
    app.state.preprocessor = None
    app.state.graph = None

    if hasattr(app.state, "pool"):
        await app.state.pool.close()

    if hasattr(app.state, "rel_db"):
        await app.state.rel_db.disconnect()

    logger.info("✅ Clean up complete!")

app = FastAPI(lifespan=lifespan_context)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])

app.state.limiter = limiter

app.include_router(router , tags=["Authentication"])
app.include_router(auth_router ,tags=["AI Support System"] )

app.add_exception_handler(Exception, exception_handler)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if __name__ == '__main__':
    uvicorn.run("src.presentation.api.app:app", host="127.0.0.1", port=8000, reload=True)