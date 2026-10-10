from unittest.mock import MagicMock

import pytest

from src.application.orchestrator import ChatOrchestrator
from src.domain.interfaces.ITextClassifier import ITextClassifier
from src.infrastructure.preprocessing.preprocessing import TextPreprocessor


def test_orchestrator_flow_and_interactions():
    fake_intent_classifier = MagicMock(spec=ITextClassifier)
    fake_sentiment_classifier = MagicMock(spec=ITextClassifier)
    fake_preprocessor = MagicMock(spec=TextPreprocessor)

    fake_preprocessor.preprocess.return_value = "clean text"
    fake_intent_classifier.predict.return_value = {"intent": "place_order", "confidence": 0.9}
    fake_sentiment_classifier.predict.return_value = {"feeling": "neutral", "confidence": 0.9}

    orchestra = ChatOrchestrator(
        intent_model=fake_intent_classifier, sentiment_model=fake_sentiment_classifier, preprocessor=fake_preprocessor
    )

    raw_text = "   i WANT to place order PLZ!!!  "
    result = orchestra.execute(raw_text)

    fake_preprocessor.preprocess.assert_called_once_with(raw_text)

    fake_intent_classifier.predict.assert_called_once_with("clean text")
    fake_sentiment_classifier.predict.assert_called_once_with("clean text")

    assert result["intent_result"]["intent"] == "place_order"
    assert result["sentiment_result"]["feeling"] == "neutral"


def test_orchestrator_handles_intent_model_failure():
    fake_intent_classifier = MagicMock(spec=ITextClassifier)
    fake_sentiment_classifier = MagicMock(spec=ITextClassifier)
    fake_preprocessor = MagicMock(spec=TextPreprocessor)

    fake_preprocessor.preprocess.return_value = "clean text"

    fake_intent_classifier.predict.side_effect = RuntimeError("ONNX Runtime error")

    orchestra = ChatOrchestrator(fake_intent_classifier, fake_sentiment_classifier, fake_preprocessor)

    with pytest.raises(RuntimeError):
        orchestra.execute("some text")


def test_orchestrator_with_empty_preprocessed_text():
    fake_intent_classifier = MagicMock(spec=ITextClassifier)
    fake_sentiment_classifier = MagicMock(spec=ITextClassifier)
    fake_preprocessor = MagicMock(spec=TextPreprocessor)

    fake_preprocessor.preprocess.return_value = ""
    fake_intent_classifier.predict.return_value = {"intent": "unknown", "confidence": 0.0}
    fake_sentiment_classifier.predict.return_value = {"feeling": "neutral", "confidence": 0.0}

    orchestra = ChatOrchestrator(fake_intent_classifier, fake_sentiment_classifier, fake_preprocessor)
    result = orchestra.execute("!@#$%^&*")

    assert result["intent_result"]["intent"] == "unknown"
