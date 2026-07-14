from src.config.intents_actions import Action_For_Intents


class DecisionMaker:
    def __init__(self):
        pass


    def get_action(self, intent: str) -> dict:

        action = Action_For_Intents.get(intent.lower()).get('action', "human_escalation")

        return {
            "action": action
        }