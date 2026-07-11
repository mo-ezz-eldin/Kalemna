from src.config.intents_actions import Action_For_Intents
from src.application.orchestrator import ChatOrchestrator


class DecisionMaker:
    def __init__(self, orchestrator: ChatOrchestrator):
        self.orchestrator = orchestrator
        # self.llm_judge = LangChainAgent(...)  <-- هيتضاف هنا مستقبلاً

    def get_action(self, text: str) -> dict:
        # 1. المايسترو بيطلع التوقع المبدئي (السريع)
        raw_prediction = self.orchestrator.execute(text)

        # =========================================================
        # 2. السحر بتاعك (LLM as a Judge & Slot Filling)
        # =========================================================
        # الـ LLM هياخد النص بتاع اليوزر، وتوقع المايسترو، ويقرر:
        # - هل المايسترو صح؟
        # - هل في بيانات ناقصة (Metadata)؟
        #
        # verified_result = self.llm_judge.verify_and_extract(text, raw_prediction)
        #
        # هنفترض إن الـ LLM صلح الـ Intent أو أكده:
        # target_intent = verified_result.get('intent')
        # =========================================================

        target_intent = raw_prediction.get('intent_result', {}).get('intent', 'UNKNOWN')  # ده مؤقتا لحد الـ LLM

        # 3. الأكشن النهائي بناءً على النتيجة الموثقة من الـ LLM
        action = Action_For_Intents.get(target_intent, "human_escalation")

        return {
            "final_prediction": raw_prediction,
            "action": action
        }