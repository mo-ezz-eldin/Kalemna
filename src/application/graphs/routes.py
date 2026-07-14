from src.application.graphs.state import Customer_State
from src.config.Constant import INTENT_LABELS
from src.config.intents_metadata import Meta_Data_Intents

def route_whether_to_final_or_tools(State: Customer_State):
    final_intent = State.get('final_intent', '').lower()

    if State.get('action') == "human_escalation":
        return "finalize"

    num_of_mis_understanding = State.get('num_of_mis_understanding', 0)
    mis_understand = State.get('is_misunderstanding', False)
    final_sentiment = State.get('final_sentiment', '').lower()

    list_intents = [intent.lower() for intent in INTENT_LABELS.values()]

    required_entities = Meta_Data_Intents.get(final_intent, {}).get("required_metadata", [])
    extracted_entities_for_intent = State.get('extracted_entities', {}).get(final_intent, [])

    is_missing_required_data = False

    for req, ext in zip(required_entities, extracted_entities_for_intent):
        if ext is None or str(ext).strip() == "":
            is_missing_required_data = True
            break

    if len(required_entities) > len(extracted_entities_for_intent):
        is_missing_required_data = True

    if (mis_understand or
            final_intent not in list_intents or
            num_of_mis_understanding >= 3 or
            is_missing_required_data or
            final_sentiment in ['anger', 'disgust']):

        return 'finalize'
    else:
        return 'decide'
def route_after_decide(State:Customer_State):
    last_message = State['Messages'][-1]
    if hasattr(last_message,'tools_calls') and len(last_message.tools_call) > 0:
        return 'tools'
    else:
        return 'finalize'
