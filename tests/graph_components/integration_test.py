from contextlib import AsyncExitStack
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from src.application.decision_maker import DecisionMaker
from src.application.graphs.customer_graph import build_customer_support_graph
from src.application.orchestrator import ChatOrchestrator
from src.domain.interfaces.ILlm import ILlm
from src.infrastructure.preprocessing.preprocessing import TextPreprocessor


@pytest.mark.requires_models
@pytest.mark.asyncio(loop_scope="session")
async def test_integration(db, intent_model, sentiment_model):

    query = "how are you"

    inputs = {
        "user_id": 9823,
        "user_query": query,
        "messages": [HumanMessage(content=query)],
    }
    config = {"configurable": {"thread_id": "test"}}

    orchestrator = ChatOrchestrator(intent_model, sentiment_model, TextPreprocessor())
    decision_maker = DecisionMaker()

    mock_llm = AsyncMock(spec=ILlm)
    mock_llm.generate.side_effect = [
        {
            "final_intent": "greeting",
            "final_sentiment": "neutral",
            "extracted_entities": {},
            "reasoning": "test reasoning",
            "is_misunderstanding": False,
        },
        "Hello! How can I help you today?",
    ]
    checkpoint = MemorySaver()

    graph = build_customer_support_graph(orchestrator, decision_maker, db, checkpoint, mock_llm)

    route = []
    final_state = {}

    async for event in graph.astream(inputs, config, stream_mode="updates"):
        for node_name, state_update in event.items():
            route.append(node_name)
            final_state.update(state_update)

    assert route == ["intent_sentiment", "judge", "finalize"]

    current_state = await graph.aget_state(config)
    results = current_state.values

    assert results["final_intent"] == "greeting"
    assert results["final_sentiment"] == "neutral"
    assert results["extracted_entities"] == {}
    assert results["is_misunderstanding"] == False
    assert results["action"] == decision_maker.get_action("greeting").get("action")
    assert results["messages"][-1].content == "Hello! How can I help you today?"
    assert mock_llm.generate.call_args.kwargs["details"]["missing_entities"] == []


@pytest.mark.asyncio(loop_scope="session")
async def test_integration_missing_entity(db, intent_model, sentiment_model):
    query = "please cancel my order"

    inputs = {
        "user_id": 9823,
        "user_query": query,
        "messages": [HumanMessage(content=query)],
    }
    config = {"configurable": {"thread_id": "test_missing_entity"}}

    orchestrator = ChatOrchestrator(intent_model, sentiment_model, TextPreprocessor())
    decision_maker = DecisionMaker()

    mock_llm = AsyncMock(spec=ILlm)

    mock_llm.generate.side_effect = [
        {
            "final_intent": "cancel_order",
            "final_sentiment": "neutral",
            "extracted_entities": {},  # Missing order_id!
            "reasoning": "User wants to cancel but didn't provide order ID",
            "is_misunderstanding": False,
        },
        "Please provide your order ID so I can cancel it for you.",
    ]

    graph = build_customer_support_graph(orchestrator, decision_maker, db, MemorySaver(), mock_llm)

    route = []
    async for event in graph.astream(inputs, config, stream_mode="updates"):
        for node_name, state_update in event.items():
            route.append(node_name)

    assert route == ["intent_sentiment", "judge", "finalize"]

    current_state = await graph.aget_state(config)
    results = current_state.values

    assert results["final_intent"] == "cancel_order"

    assert "order_id" in mock_llm.generate.call_args.kwargs["details"]["missing_entities"]
    assert results["messages"][-1].content == "Please provide your order ID so I can cancel it for you."


@pytest.mark.requires_models
@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "query, intent, extracted_entities, tool_name, tool_args, mock_db_setup, expected_db_method, expected_db_args, final_llm_msg",
    [
        # ==========================================
        # 1. Cancel Order Scenario (Happy Path)
        # ==========================================
        (
            "Cancel my order 12345 because it's delayed",
            "cancel_order",
            {"order_id": 12345, "cancellation_reason": "delayed"},  # 👈 مطابقة لـ Meta_Data_Intents
            "cancel_order",
            {"order_id": 12345},
            {"delete_order": True},  # الـ DB method اللي هنعملها Mock والـ Return بتاعها
            "delete_order",  # اسم الـ DB Method اللي المفروض تتنادى عشان نـ Assert عليها
            (9823, 12345),  # (user_id, order_id)
            "Your order 12345 has been successfully cancelled.",
        ),
        # ==========================================
        # 2. Track Order Scenario
        # ==========================================
        (
            "Where is my order 9999?",
            "track_order",
            {"order_id": 9999},
            "track_order",
            {"order_id": 9999},
            {
                "get_order": {
                    "status": "Shipped",
                    "expected_delivery_date": "Tomorrow",
                    "shipping_address": "Cairo",
                    "total_amount": 100,
                }
            },
            "get_order",
            (9823, 9999),
            "Your order 9999 is Shipped and will arrive Tomorrow.",
        ),
        # ==========================================
        # 3. Get Invoice Scenario
        # ==========================================
        (
            "I need the invoice for order 777",
            "get_invoice",
            {"order_id": 777},  #
            "get_invoice",
            {"order_id": 777},
            {"get_invoice_details": {"total_amount": 500, "created_at": "2026-10-01", "status": "Paid"}},
            "get_invoice_details",
            (9823, 777),
            "Here is your invoice for order 777.",
        ),
        # ==========================================
        # 4. Check Refund Policy (No DB interaction)
        # ==========================================
        (
            "What is your refund policy?",
            "check_refund_policy",
            {},  # 👈 مفيش metadata مطلوبة هنا
            "check_refund_policy",
            {},
            {},  # 👈 التوول دي مش بتكلم الـ DB أصلاً
            None,
            None,
            "Our refund policy allows returns within 14 days.",
        ),
    ],
)
async def test_integration_all_tools_happy_path(
    db,
    intent_model,
    sentiment_model,
    setup_all_tools,
    query,
    intent,
    extracted_entities,
    tool_name,
    tool_args,
    mock_db_setup,
    expected_db_method,
    expected_db_args,
    final_llm_msg,
):

    tool_instance = await setup_all_tools(tool_name)
    assert tool_instance is not None, f"Tool '{tool_name}' is missing in the system!"

    user_id = 9823
    inputs = {
        "user_id": user_id,
        "user_query": query,
        "messages": [HumanMessage(content=query)],
    }
    config = {"configurable": {"thread_id": f"test_{intent}"}}

    orchestrator = ChatOrchestrator(intent_model, sentiment_model, TextPreprocessor())
    decision_maker = DecisionMaker()

    mock_llm = AsyncMock(spec=ILlm)

    mock_llm.generate.side_effect = [
        {
            "final_intent": intent,
            "final_sentiment": "neutral",
            "extracted_entities": extracted_entities,
            "reasoning": f"Testing parameterization for {intent}",
            "is_misunderstanding": False,
        },
        final_llm_msg,
    ]

    mock_tool_call_message = AIMessage(
        content="", tool_calls=[{"name": tool_name, "args": tool_args, "id": "call_mock123"}]
    )
    mock_llm.execute_tools.return_value = mock_tool_call_message

    graph = build_customer_support_graph(orchestrator, decision_maker, db, MemorySaver(), mock_llm)
    async with AsyncExitStack() as stack:
        for method_name, return_val in mock_db_setup.items():
            # ده بيضمن إن الـ Mock يشتغل هنا بس، ويختفي بعد ما الـ block يخلص
            stack.enter_context(
                patch.object(db, method_name, new_callable=AsyncMock, return_value=return_val)
        )
        route = []
        async for event in graph.astream(inputs, config, stream_mode="updates"):
            for node_name, state_update in event.items():
                route.append(node_name)

        assert "tools" in route, f"Graph didn't route to tools for intent: {intent}. Current route: {route}"

        if expected_db_method:
            mocked_method = getattr(db, expected_db_method)
            mocked_method.assert_called_once_with(*expected_db_args)

    current_state = await graph.aget_state(config)
    results = current_state.values
    assert results["final_intent"] == intent
    assert results["messages"][-1].content == final_llm_msg
