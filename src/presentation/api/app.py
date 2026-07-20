from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from contextlib import asynccontextmanager

from src.application.decision_maker import DecisionMaker
from src.application.graphs.customer_graph import build_customer_support_graph
from src.application.orchestrator import ChatOrchestrator
from src.config.settings import settings
from src.config.Constant import SENTIMENT_LABELS,INTENT_LABELS
from src.infrastructure.ai_models.intent_model import IntentModel
from src.infrastructure.ai_models.sentiment_model import SentimentClassifier
from src.presentation.api.routes import router
from src.infrastructure.preprocessing.preprocessing import TextPreprocessor
from src.infrastructure.databases.posgres_db import PosgresDb
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan_context(app: FastAPI):

    app.state.intent_model = IntentModel(
        model_path=settings.intent_model_path,
        labels_map=INTENT_LABELS,
        tokenizer_path=settings.intent_tokenizer
    )

    app.state.sentiment_model = SentimentClassifier(
        model_path=settings.sentiment_model_path,
        tokenizer_path=settings.sentiment_tokenizer,
        labels=SENTIMENT_LABELS
    )

    app.state.preprocessor = TextPreprocessor()

    # 1. بنضيف autocommit وبنقوله متفتحش الاتصال أوتوماتيك عشان التحذير
    app.state.pool = AsyncConnectionPool(
        conninfo=settings.postgres_db_conn.replace("+asyncpg", ""),
        kwargs={"autocommit": True},
        open=False
    )

    # 2. بنفتح الاتصال إحنا بشكل Async نظيف
    await app.state.pool.open()

    # 3. بنبني الجداول والجراف
    app.state.checkpointer = AsyncPostgresSaver(app.state.pool)
    await app.state.checkpointer.setup()

    app.state.rel_db = PosgresDb(config=settings.postgres_db_conn)


    app.state.graph = build_customer_support_graph(
        orchestrator=ChatOrchestrator(
            intent_model=app.state.intent_model,
            sentiment_model=app.state.sentiment_model,
            preprocessor=app.state.preprocessor
        ),
        decision_maker=DecisionMaker(),
        db=app.state.rel_db,
        chckpointer=app.state.checkpointer
    )

    logger.info("✅ Models, Database, and Graph loaded successfully!")

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
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(router)



if __name__ == '__main__':
    uvicorn.run("src.presentation.api.main:app", host="127.0.0.1", port=8000, reload=True)