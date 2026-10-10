# ruff: noqa: E402
import os
import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

from dotenv import load_dotenv

load_dotenv()

import onnxruntime
import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.messages import AIMessage

from src.application.decision_maker import DecisionMaker
from src.application.graphs.tools import get_tools
from src.config.Constant import INTENT_LABELS, SENTIMENT_LABELS
from src.config.settings import settings
from src.domain.interfaces.IDatabase import IDatabase
from src.domain.interfaces.ILlm import ILlm
from src.infrastructure.ai_models.intent_model import IntentModel
from src.infrastructure.ai_models.sentiment_model import SentimentClassifier
from src.infrastructure.databases.posgres_db import PosgresDb
from src.infrastructure.security.user_security_credentials import (
    create_access_token,
    get_current_user,
)
from src.presentation.api.app import app
from src.presentation.api.dependency import get_db


def pytest_collection_modifyitems(config, items):
    if os.getenv("GITHUB_ACTIONS"):
        for item in items:
            if "requires_models" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="Requires models"))


@pytest.fixture(scope="session")
async def db_instance():
    db: IDatabase = PosgresDb(config=settings.test_db_conn)
    await db.setup_db()

    yield db

    await db.drop_db()
    await db.disconnect()


@pytest.fixture(scope="function")
async def db(db_instance: PosgresDb):
    real_engine = db_instance.engine

    async with real_engine.connect() as conn:
        trans = await conn.begin()

        class MockEngine:
            @asynccontextmanager
            async def begin(self):

                nested = await conn.begin_nested()
                try:
                    yield conn
                    await nested.commit()
                except Exception:
                    await nested.rollback()
                    raise

        db_instance.engine = MockEngine()

        yield db_instance

        db_instance.engine = real_engine

        await trans.rollback()


@pytest.fixture
async def create_user(db: IDatabase):
    unique_suffix = str(uuid.uuid4())[:8]
    user_details = {
        "username": f"user_{unique_suffix}",
        "email": f"test_{unique_suffix}@test.com",
        "hashed_password": "12345560",
        "phone": "01019440379",
    }

    user_id = await db.create_user(user_details)

    yield user_id, user_details


@pytest.fixture
def product_example():
    product_details = {
        "name": "test_product",
        "description": "this is the description of test_product",
        "price": 999.99,
    }
    return product_details


@pytest.fixture
async def create_product(db: IDatabase):
    async def details(product_details):
        product_id = await db.create_product(**product_details)
        return product_id, product_details

    yield details


@pytest.fixture
async def create_order(db: IDatabase):
    async def details(user_id, order_details):
        order_id = await db.create_order(user_id, order_details)
        return order_id

    yield details


@pytest.fixture
async def order_example(create_product, product_example):
    product_id, product_details = await create_product(product_example)
    items = [{"product_id": product_id, "quantity": 2, "unit_price": product_details["price"]}]

    order_details = {
        "items": items,
        "status": "pending",
        "shipping_address": "test_address",
        "total_amount": 2 * product_details["price"],
    }

    return order_details


@pytest.fixture
def user_auth():
    return {"user_id": 1000, "username": "test_user"}


@pytest.fixture
async def client(db: IDatabase, user_auth):
    app.dependency_overrides[get_current_user] = lambda: user_auth
    app.dependency_overrides[get_db] = lambda: db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        yield http_client

        app.dependency_overrides.clear()


@pytest.fixture
async def create_token():
    payload = {"sub": "test_user", "user_id": 10}
    token = create_access_token(payload)
    return token


@pytest.fixture(scope="session")
def ort_setup():
    ort = onnxruntime.SessionOptions()

    ort.enable_profiling = False
    ort.log_severity_level = 3
    ort.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL

    return ort


@pytest.fixture(scope="session")
async def intent_model(ort_setup):
    intent_classifier_model = IntentModel(
        model_path=r"D:\PycharmProjects\JupyterProject\onnx_intent_model", labels_map=INTENT_LABELS, ort=ort_setup
    )

    yield intent_classifier_model

    intent_classifier_model = None


@pytest.fixture(scope="session")
async def sentiment_model(ort_setup):

    sentiment_classifier_model = SentimentClassifier(
        r"D:\PycharmProjects\JupyterProject\onnx_sentiment_model",
        settings.sentiment_tokenizer,
        labels=SENTIMENT_LABELS,
        ort=ort_setup,
    )

    yield sentiment_classifier_model

    sentiment_classifier_model = None


@pytest.fixture
def mock_dependencies():

    mock_llm = AsyncMock(spec=ILlm)
    mock_decision_maker = MagicMock(spec=DecisionMaker)
    return mock_llm, mock_decision_maker


@pytest.fixture
def mock_llm():

    llm = AsyncMock()
    llm_with_tools = AsyncMock()
    llm.bind_tools.return_value = llm_with_tools

    llm_with_tools.ainvoke.return_value = AIMessage(content="Order cancel requested.")
    llm.ainvoke.return_value = AIMessage(content="Hello! How can I help?")

    return llm, llm_with_tools


@pytest.fixture
def mock_llm_proxy():

    proxy = AsyncMock()
    proxy.generate.return_value = "هذا هو الرد النهائي المعتمد للمستخدم"
    return proxy


@pytest.fixture
def setup_all_tools(db):

    tools = get_tools(db)

    async def search_for_tool(name):
        for tool in tools:
            if tool.name == name:
                return tool

        return None

    yield search_for_tool

    tools = None
