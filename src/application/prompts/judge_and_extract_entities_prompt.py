from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.config.Constant import INTENT_LABELS, SENTIMENT_LABELS
from src.config.intents_metadata import Meta_Data_Intents
from src.application.graphs.schemas import JudgeExtractSchema

judge_extract_parser = JsonOutputParser(pydantic_object=JudgeExtractSchema)

judge_and_extract_entities_template = ChatPromptTemplate.from_template(
    """You are an expert Quality Assurance Judge and Named Entity Recognition (NER) specialist for a production-grade Customer Support AI system. 

Your position is the "Line of Defense 2". You receive the customer's raw query along with initial, fast predictions from underlying Machine Learning models. Your mission is to audit these predictions and extract vital operational parameters.

Execute your task based on the following instructions:

### 1. JUDGEMENT & CORRECTION AUDIT:
- Evaluate whether the 'Predicted Intent' and 'Predicted Sentiment' accurately reflect the customer's 'Raw Query'.
- If the ML models are correct, confirm them by setting them as they are. 
- If the ML models are incorrect (e.g., the customer is shifting context, expressing underlying anger not caught by the model, or trying to cancel an order while the model flagged it as tracking), you MUST override them and determine the true final intent and sentiment. 
- You must follow these intents only and don't choose other intents except these: {intents_list}
- You must follow these sentiments only and don't choose other sentiments except these: {sentiments_list}
- If the customer's query is things that are in the scope of customer support or intents that listed above and u can't catch details or there is some troubles in user query ,however you know the intent flag it immediately as a misunderstanding (is_misunderstanding: True) , Note that queries like 'how are u' or how you can help or what does this website for. all these are understood.
- If you are confident that the true intent or sentiment does not exist in the allowed list, mark it as "UNKNOWN".

client = Client()
judge_and_extract_entities_template = client.pull_prompt(
    "judge_and_extract_prompt:staging"
)

judge_and_extract_entities_template = judge_and_extract_entities_template.partial(
    format_instructions=judge_extract_parser.get_format_instructions(),
    intents_list=list(INTENT_LABELS.values()),
    sentiments_list=list(SENTIMENT_LABELS.values()),
    meta_data_intents=Meta_Data_Intents
)

