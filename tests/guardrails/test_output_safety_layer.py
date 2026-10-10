import json
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from src.application.guardrails.output_safety_layer import safety_json_output

SAFE_FALLBACK = (
    '{"final_intent": "UNKNOWN", "final_sentiment": "neutral", "extracted_entities": {}, "is_misunderstanding": true}'
)


def test_output_safety_layer_success():
    valid_data = {
        "final_intent": "test_intent",
        "final_sentiment": "test_sentiment",
        "extracted_entities": {"key": "test_entities"},
        "is_misunderstanding": False,
        "reason": "test_reason",
    }

    json_string = json.dumps(valid_data)

    content = AIMessage(content=json_string)

    result = safety_json_output(content)

    assert result.content == json_string


def test_safety_layer_embedded_json():

    valid_data = {
        "final_intent": "Technical_Support",
        "final_sentiment": "neutral",
        "extracted_entities": {},
        "is_misunderstanding": False,
    }
    json_string = json.dumps(valid_data)

    noisy_content = f"Here is the JSON you requested:\n```json\n{json_string}\n```\nHope this helps!"
    content = AIMessage(content=noisy_content)

    result = safety_json_output(content)
    assert result.content == json_string


def test_safety_layer_list_content():
    valid_data = {
        "final_intent": "Cancel_Subscription",
        "final_sentiment": "sad",
        "extracted_entities": {},
        "is_misunderstanding": False,
    }
    json_string = json.dumps(valid_data)

    list_content = [{"type": "text", "text": "Analyzing intent... "}, json_string, {"content": " Finished."}]
    content = AIMessage(content=list_content)

    result = safety_json_output(content)

    assert result.content == json_string


def test_safety_layer_missing_final_intent():

    invalid_data = {"some_other_key": "Refund", "final_sentiment": "angry"}
    content = AIMessage(content=json.dumps(invalid_data))

    result = safety_json_output(content)
    assert result.content == SAFE_FALLBACK


def test_safety_layer_invalid_json_syntax():

    broken_json = '{"final_intent": "Refund", "final_sentiment": "angry"'
    content = AIMessage(content=broken_json)

    result = safety_json_output(content)
    assert result.content == SAFE_FALLBACK


def test_safety_layer_empty_or_whitespace_string():

    content = AIMessage(content="   \n   \t  ")
    result = safety_json_output(content)
    assert result.content == SAFE_FALLBACK


def test_safety_layer_unsupported_type():

    content = AIMessage(content=404)
    result = safety_json_output(content)
    assert result.content == SAFE_FALLBACK


def test_safety_layer_multiple_json_blocks():

    valid_data = {
        "final_intent": "Valid_Intent",
        "final_sentiment": "happy",
        "extracted_entities": {},
        "is_misunderstanding": False,
    }
    valid_json = json.dumps(valid_data)

    complex_content = f"Bad JSON: {{'final_intent': broken}} \n Good JSON: {valid_json}"
    content = AIMessage(content=complex_content)

    result = safety_json_output(content)

    assert result.content == valid_json


def test_safety_layer_line_18_list_with_other_types():

    msg = MagicMock(spec=AIMessage)

    msg.content = ["text block", 12345]

    result = safety_json_output(msg)
    assert result.content == SAFE_FALLBACK


def test_safety_layer_lines_22_23_none_content_with_mock():

    mock_message = MagicMock(spec=AIMessage)
    mock_message.content = None

    result = safety_json_output(mock_message)
    assert result.content == SAFE_FALLBACK


def test_safety_layer_lines_24_25_unsupported_raw_content_type():

    mock_message = MagicMock(spec=AIMessage)
    mock_message.content = 99999

    result = safety_json_output(mock_message)
    assert result.content == SAFE_FALLBACK


def test_safety_layer_lines_49_50_json_decode_error():

    malformed_candidate = '{"final_intent": unquoted_invalid_value}'
    content = AIMessage(content=malformed_candidate)
    result = safety_json_output(content)

    assert result.content == SAFE_FALLBACK
