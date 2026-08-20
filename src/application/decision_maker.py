from src.config.intents_actions import Action_For_Intents


class DecisionMaker:
    def __init__(self):
        pass


    def get_action(self, intent: str) -> dict:
        intent_data = Action_For_Intents.get(intent.lower(), {})


        action_name = intent_data.get('action', "human_escalation")

        return {"action": action_name}