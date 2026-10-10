from unittest.mock import MagicMock, patch

import pytest

from src.application.graphs.routes import (
    route_after_decide,
    route_whether_to_final_or_tools,
)


@pytest.mark.parametrize(
    "action, final_intent",
    [
        ("human_escalation", "some_intent"),
        ("some_action", "greeting"),
        ("some_action", "needing guidance"),
    ],
)
def test_route_direct_finalize(action, final_intent):

    dummy_state = {"action": action, "final_intent": final_intent}

    result = route_whether_to_final_or_tools(dummy_state)
    assert result == "finalize"


@pytest.mark.parametrize(
    "state_override",
    [
        {"is_misunderstanding": True},
        {"final_intent": "unknown_random_intent_not_in_list"},
        {"num_of_mis_understanding": 3},
        {"final_sentiment": "anger"},
        {"final_sentiment": "disgust"},
    ],
)
@patch("src.config.Constant.INTENT_LABELS", {"intent_1": "track_order", "intent_2": "cancel_order"})
def test_route_validation_failures(state_override):

    dummy_state = {
        "action": "normal",
        "final_intent": "track_order",
        "is_misunderstanding": False,
        "num_of_mis_understanding": 0,
        "final_sentiment": "neutral",
        "extracted_entities": {"order_id": "123"},
    }

    dummy_state.update(state_override)

    result = route_whether_to_final_or_tools(dummy_state)
    assert result == "finalize"


@patch("src.application.graphs.routes.Meta_Data_Intents", {"track_order": {"required_metadata": ["order_id", "email"]}})
@patch("src.config.Constant.INTENT_LABELS", {"intent_1": "track_order"})
def test_route_missing_required_entities():

    dummy_state = {"final_intent": "track_order", "extracted_entities": {"order_id": "12345", "email": "none"}}

    result = route_whether_to_final_or_tools(dummy_state)
    assert result == "finalize"


@patch("src.config.intents_metadata.Meta_Data_Intents", {"track_order": {"required_metadata": ["order_id"]}})
@patch("src.config.Constant.INTENT_LABELS", {"intent_1": "track_order"})
def test_route_happy_path():

    dummy_state = {
        "action": "process",
        "final_intent": "track_order",
        "final_sentiment": "positive",
        "is_misunderstanding": False,
        "num_of_mis_understanding": 0,
        "extracted_entities": {"order_id": "12345"},
    }

    result = route_whether_to_final_or_tools(dummy_state)
    assert result == "decide"


def test_route_after_decide_with_tools():

    mock_message = MagicMock()
    mock_message.tool_calls = [{"name": "cancel_order_tool"}]

    dummy_state = {"messages": [mock_message]}

    result = route_after_decide(dummy_state)
    assert result == "tools"


@pytest.mark.parametrize(
    "mock_tool_calls_value",
    [
        [],
        None,
    ],
)
def test_route_after_decide_no_tools(mock_tool_calls_value):

    mock_message = MagicMock()

    if mock_tool_calls_value is None:
        del mock_message.tool_calls
    else:
        mock_message.tool_calls = mock_tool_calls_value

    dummy_state = {"messages": [mock_message]}

    result = route_after_decide(dummy_state)
    assert result == "finalize"
