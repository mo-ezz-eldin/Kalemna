import pytest

from src.application.decision_maker import DecisionMaker


@pytest.mark.parametrize(
    "intent , action",
    [
        ("place_order", "llm_reply"),
        ("get_invoice", "llm_reply"),
        ("track_order", "llm_reply"),
        ("get_refund", "llm_reply"),
        ("contact_customer_service", "human_escalation"),
        ("delivery_options", "llm_reply"),
        ("complaint", "human_escalation"),
        ("change_shipping_address", "llm_reply"),
        ("check_cancellation_fee", "llm_reply"),
        ("track_refund", "llm_reply"),
        ("delivery_period", "llm_reply"),
        ("check_refund_policy", "llm_reply"),
        ("change_order", "llm_reply"),
        ("cancel_order", "llm_reply"),
        ("review", "llm_reply"),
        ("greeting", "llm_reply"),
        ("needing guidance", "llm_reply"),
    ],
)
def test_decision_maker(intent, action):
    decision_maker = DecisionMaker()

    response = decision_maker.get_action(intent)

    assert response["action"] == action
