from src.application.graphs.state import Customer_State
from src.application.orchestrator import ChatOrchestrator
from src.application.prompts.judge_and_extract_entities_prompt import judge_extract_parser, judge_and_extract_entities_template
from src.application.prompts.decide_excute_prompt import decide_execute_prompt
from src.application.prompts.finalize_prompt import FINALIZE_PROMPT
from src.config.Constant import INTENT_LABELS
from src.config.intents_metadata import Meta_Data_Intents
from src.application.decision_maker import DecisionMaker
from langchain_google_genai import ChatGoogleGenerativeAI
from src.application.guardrails.output_safety_layer import safety_json_output


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key="",
    temperature=0.0
)
class Intent_Sentiment_Node():
    def __init__(self,orchestrator: ChatOrchestrator):
        self.orchestrator=orchestrator
    async def __call__(self,state: Customer_State,config: dict):
        models_predictions=self.orchestrator.execute(state['user_query'])
        return {
            'predicted_intent':models_predictions['intent_result']['intent'],

            'predicted_sentiment':models_predictions['sentiment_result']['feeling']

                }


class judge_and_extract_entities():
    def __init__(self, decision_maker: DecisionMaker):

        self.decision_maker = decision_maker

    async def __call__(self, state: Customer_State, config: dict):
        history_msgs = state['messages'][:-1]
        chat_history = "\n".join([f"{'User' if m.type == 'human' else 'AI'}: {m.content}" for m in history_msgs])

        if not chat_history.strip():
            chat_history = "No prior conversation history."

        chain = judge_and_extract_entities_template | llm | safety_json_output | judge_extract_parser

        results = await chain.ainvoke({
            "user_query": state['user_query'],
            "predicted_intent": state['predicted_intent'],
            "predicted_sentiment": state['predicted_sentiment'],
            "chat_history": chat_history
        }, config=config)

        return {
            "final_intent": results['final_intent'],
            "final_sentiment": results['final_sentiment'],
            "extracted_entities": results['extracted_entities'],
            "num_of_mis_understanding": int(results['is_misunderstanding']) + state.get('num_of_mis_understanding', 0),
            "action": self.decision_maker.get_action(results['final_intent']).get('action'),
            "is_misunderstanding": results['is_misunderstanding']
        }


class decide_excute():
    def __init__(self,tools_list):
        self.llm_with_tools=llm.bind_tools(tools_list)

    async def __call__(self, state: Customer_State,config:dict):
        current_intent = state.get('final_intent', '')

        chain = decide_execute_prompt | self.llm_with_tools
        response = await chain.ainvoke({
            "final_intent": current_intent,

            "extracted_entities": state.get('extracted_entities', {}).get(current_intent, []),

            "user_id": state.get('user_id', 'Unknown'),
            "messages": state['messages']
        },config=config)


        return {"messages": [response]}


class finalize_node():
    def __init__(self):
        self.chain = (FINALIZE_PROMPT | llm).with_config({"tags": ["final_responder"]})

    async def __call__(self, state: Customer_State, config: dict):
        action = state.get('action')
        final_intent = state.get('final_intent', '')
        final_sentiment = state.get('final_sentiment', '')


        required_keys = Meta_Data_Intents.get(final_intent, {}).get("required_metadata", [])


        extracted_entities_dict = state.get('extracted_entities', {})

        missing_entities = []


        for key in required_keys:
            value = extracted_entities_dict.get(key)


            if not value or (isinstance(value, list) and len(value) == 0) or (
                    isinstance(value, str) and str(value).strip() == ""):
                missing_entities.append(key)

        if state.get('num_of_mis_understanding', 0) >= 3:
            action = "human_escalation"


        response = await self.chain.ainvoke({
            "action": action,
            "missing_entities": missing_entities,
            "final_intent": final_intent,
            "final_sentiment": final_sentiment,
            "num_of_mis_understanding": state.get('num_of_mis_understanding', 0),
            "intents_list" : list(INTENT_LABELS.values()) ,
            "messages": state['messages']
        }, config=config)

        return {"messages": [response]}

