from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.application.graphs.Nodes import (
    Intent_Sentiment_Node,
    decide_excute,
    finalize_node,
    judge_and_extract_entities,
)
from src.application.orchestrator import ChatOrchestrator
from src.infrastructure.preprocessing.preprocessing import TextPreprocessor


@pytest.mark.requires_models
@pytest.mark.asyncio(loop_scope="module")
async def test_Intent_Sentiment_Node(intent_model, sentiment_model):
    chat = ChatOrchestrator(intent_model, sentiment_model, TextPreprocessor())

    node1 = Intent_Sentiment_Node(chat)

    config = {"configurable": {"thread_id": "test"}}

    dummy_state = {"user_query": "plz i want to place order"}

    result = await node1(dummy_state, config)

    assert "predicted_intent" in result
    assert "predicted_sentiment" in result
    assert result["predicted_intent"] != ""
    assert result["predicted_sentiment"] != ""


@pytest.mark.asyncio
async def test_intent_sentiment_node_unit_with_mock():

    mock_orchestrator = MagicMock()
    mock_orchestrator.execute.return_value = {
        "intent_result": {"intent": "cancel_order"},
        "sentiment_result": {"feeling": "negative"},
    }

    node = Intent_Sentiment_Node(mock_orchestrator)
    dummy_state = {"user_query": "I want to cancel"}

    result = await node(dummy_state, {})

    assert result == {"predicted_intent": "cancel_order", "predicted_sentiment": "negative"}
    mock_orchestrator.execute.assert_called_once_with("I want to cancel")


@pytest.mark.requires_models
@pytest.mark.asyncio
async def test_intent_sentiment_node_empty_query(intent_model, sentiment_model):
    chat = ChatOrchestrator(intent_model, sentiment_model, TextPreprocessor())
    node = Intent_Sentiment_Node(chat)

    result = await node({"user_query": ""}, {})

    assert "predicted_intent" in result


@pytest.mark.asyncio
async def test_judge_node_happy_path(mock_dependencies):
    mock_llm, mock_decision_maker = mock_dependencies

    mock_llm.generate.return_value = {
        "final_intent": "cancel_order",
        "final_sentiment": "negative",
        "extracted_entities": {"order_id": "12345"},
        "is_misunderstanding": False,
    }

    mock_decision_maker.get_action.return_value = {"action": "llm_reply"}

    node = judge_and_extract_entities(decision_maker=mock_decision_maker, llm_proxy=mock_llm)

    dummy_state = {
        "user_query": "I want to cancel order 12345",
        "predicted_intent": "cancel_order",
        "predicted_sentiment": "neutral",
        "messages": [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi! How can I help?"),
            HumanMessage(content="I want to cancel order 12345"),
        ],
        "num_of_mis_understanding": 0,
    }

    result = await node(dummy_state, config={})

    assert result["final_intent"] == "cancel_order"
    assert result["extracted_entities"] == {"order_id": "12345"}
    assert result["action"] == "llm_reply"
    assert result["num_of_mis_understanding"] == 0

    called_details = mock_llm.generate.call_args.kwargs["details"]
    assert "User: Hello\nAI: Hi! How can I help?" in called_details["chat_history"]

    mock_decision_maker.get_action.assert_called_once_with("cancel_order")


@pytest.mark.asyncio
async def test_judge_node_empty_history(mock_dependencies):
    mock_llm, mock_decision_maker = mock_dependencies

    mock_llm.generate.return_value = {
        "final_intent": "greeting",
        "final_sentiment": "positive",
        "extracted_entities": {},
        "is_misunderstanding": False,
    }
    mock_decision_maker.get_action.return_value = {"action": "llm_reply"}

    node = judge_and_extract_entities(decision_maker=mock_decision_maker, llm_proxy=mock_llm)

    dummy_state = {
        "user_query": "Hi",
        "predicted_intent": "greeting",
        "predicted_sentiment": "positive",
        "messages": [HumanMessage(content="Hi")],
    }

    await node(dummy_state, config={})

    called_details = mock_llm.generate.call_args.kwargs["details"]
    assert called_details["chat_history"] == "No prior conversation history."


@pytest.mark.asyncio
async def test_judge_node_misunderstanding_accumulation(mock_dependencies):
    mock_llm, mock_decision_maker = mock_dependencies

    mock_llm.generate.return_value = {
        "final_intent": "unknown",
        "final_sentiment": "frustrated",
        "extracted_entities": {},
        "is_misunderstanding": True,
    }
    mock_decision_maker.get_action.return_value = {"action": "clarify"}

    node = judge_and_extract_entities(decision_maker=mock_decision_maker, llm_proxy=mock_llm)

    dummy_state = {
        "user_query": "asdfghj",
        "predicted_intent": "unknown",
        "predicted_sentiment": "neutral",
        "messages": [HumanMessage(content="asdfghj")],
        "num_of_mis_understanding": 2,
    }

    result = await node(dummy_state, config={})

    assert result["num_of_mis_understanding"] == 3
    assert result["is_misunderstanding"] is True


@pytest.mark.asyncio
async def test_decide_execute_correct_tool_mapping(mock_llm):
    llm, llm_with_tools = mock_llm

    mock_cancel_tool = MagicMock()
    mock_cancel_tool.name = "cancel_order"
    tools_list = [mock_cancel_tool]

    llm.execute_tools.return_value = "Order cancelled successfully"

    node = decide_excute(llm_proxy=llm, tools_list=tools_list)

    dummy_state = {"final_intent": "cancel_order", "messages": [HumanMessage(content="Cancel my order 123")]}

    result = await node(dummy_state, config={})

    assert result["messages"][-1] == "Order cancelled successfully"


@pytest.mark.asyncio
async def test_finalize_node_with_ai_message_draft(mock_llm_proxy):

    node = finalize_node(llm_proxy=mock_llm_proxy)

    messages = [HumanMessage(content="عايز ألغي أوردر"), AIMessage(content="مسودة رد: تم إلغاء الطلب رقم 123")]

    state = {
        "action": "cancel",
        "final_intent": "cancel_order",
        "final_sentiment": "neutral",
        "messages": messages,
        "extracted_entities": {},
        "num_of_mis_understanding": 0,
    }

    config = {}

    result = await node(state, config)

    mock_llm_proxy.generate.assert_called_once()

    call_kwargs = mock_llm_proxy.generate.call_args.kwargs
    details = call_kwargs["details"]

    assert details["draft_response"] == "مسودة رد: تم إلغاء الطلب رقم 123"
    assert details["messages"] == [messages[0]]
    assert "final_responder" in config["tags"]

    assert isinstance(result["messages"][0], AIMessage)
    assert result["messages"][0].content == "هذا هو الرد النهائي المعتمد للمستخدم"


@pytest.mark.asyncio
async def test_finalize_node_without_ai_message_draft(mock_llm_proxy):

    node = finalize_node(llm_proxy=mock_llm_proxy)

    messages = [HumanMessage(content="Hi")]
    state = {"action": "greeting", "final_intent": "greeting", "messages": messages}

    await node(state, config={})

    details = mock_llm_proxy.generate.call_args.kwargs["details"]
    assert "No draft provided" in details["draft_response"]
    assert details["messages"] == messages


@pytest.mark.asyncio
async def test_finalize_node_missing_entities_calculation(mock_llm_proxy):

    node = finalize_node(llm_proxy=mock_llm_proxy)

    state = {
        "final_intent": "track_order",
        "messages": [HumanMessage(content="فين أوردري")],
        "extracted_entities": {
            "order_id": "none",
        },
    }

    await node(state, config={})

    details = mock_llm_proxy.generate.call_args.kwargs["details"]
    assert details["missing_entities"] == ["order_id"]


@pytest.mark.asyncio
async def test_finalize_node_escalation_threshold(mock_llm_proxy):

    node = finalize_node(llm_proxy=mock_llm_proxy)

    state = {"action": "ask_clarification", "messages": [HumanMessage(content="???")], "num_of_mis_understanding": 3}

    await node(state, config={})

    details = mock_llm_proxy.generate.call_args.kwargs["details"]
    assert details["action"] == "human_escalation"
