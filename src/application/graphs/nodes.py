from src.application.graphs.state import Customer_State
from src.application.orchestrator import ChatOrchestrator
from src.application.prompts.judge_and_extract_entities_prompt import judge_extract_parser, judge_and_extract_entities_template
from src.application.prompts.decide_excute_prompt import decide_execute_prompt
from src.application.prompts.finalize_prompt import FINALIZE_PROMPT
from src.config.intents_metadata import Meta_Data_Intents
from src.application.decision_maker import DecisionMaker
from langchain_core.messages import HumanMessage
class Intent_Sentiment_Node():
    def __init__(self,orchestrator: ChatOrchestrator):
        self.orchestrator=orchestrator
    def __call__(self,state: Customer_State):
        models_predictions=self.orchestrator.execute(state['user_query'])
        return {'predicted_intent':models_predictions['intent_result']['intent'],
            'predicted_sentiment':models_predictions['sentiment_result']['feeling'],
            'nodes_info':['models predicted successfully'],
            'Messages':[HumanMessage(content=state['user_query'])]
                }

class judge_and_extract_entities():
    def __init__(self,decision_maker: DecisionMaker):
        """until we test the appropriate llm"""
        self.decision_maker=decision_maker
    def __call__(self,state: Customer_State):
        chain = judge_and_extract_entities_template | "llm" | judge_extract_parser
        results=chain.invoke({"user_query":state['user_query'],
                          "predicted_intent":state['predicted_intent'],
                          "predicted_sentiment":state['predicted_sentiment']})

        return {"final_intent":results['final_intent'],
                "final_sentiment": results['final_sentiment'],
                "extracted_entities": results['extracted_entities'],
                "nodes_info":["judge_and_extract_entities was successful"],
                "num_of_mis_understanding": int(results['is_misunderstanding']) + state.get('num_of_mis_understanding',0),
                "action":self.decision_maker.get_action(results['final_intent']).get('action'),
                "is_misunderstanding": results['is_misunderstanding']
            }


class decide_excute():
    def __init__(self):
        pass

    def __call__(self, state: Customer_State):
        current_intent = state.get('final_intent', '')

        chain = decide_execute_prompt | "llm"
        response = chain.invoke({
            "final_intent": current_intent,

            "extracted_entities": state.get('extracted_entities', {}).get(current_intent, []),

            "user_id": state.get('user_id', 'Unknown'),
            "Messages": state['Messages']
        })

        return {"messages": [response]}




class finalize_node():
        def __init__(self):
            self.chain = FINALIZE_PROMPT | 'llm'

        def __call__(self, state: Customer_State):
            action = state.get('action')
            final_intent = state.get('final_intent', '')

            final_sentiment = state.get('final_sentiment', '')

            required_keys = Meta_Data_Intents.get(final_intent, {}).get("required_metadata", [])
            extracted_values = state.get('extracted_entities', {}).get(final_intent, [])

            missing_entities = []
            for key, value in zip(required_keys, extracted_values):
                if value is None or str(value).strip() == "":
                    missing_entities.append(key)

            if len(required_keys) > len(extracted_values):
                missing_entities.extend(required_keys[len(extracted_values):])

            if state.get('num_of_mis_understanding', 0) >= 3 or state.get('is_misunderstanding'):
                action = "human_escalation"

            if action != "human_escalation" and not missing_entities:
                return {}

            response = self.chain.invoke({
                "action": action,
                "missing_entities": missing_entities,
                "final_intent": final_intent,
                "final_sentiment": final_sentiment,
                "messages": state['Messages']
            })

            return {"messages": [response]}


