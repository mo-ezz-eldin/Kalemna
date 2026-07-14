from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.config.Constant import INTENT_LABELS, SENTIMENT_LABELS
from src.config.intents_metadata import Meta_Data_Intents

from src.application.graphs.schemas import JudgeExtractSchema

judge_extract_parser = JsonOutputParser(pydantic_object=JudgeExtractSchema)

judge_and_extract_entities_template = ChatPromptTemplate.from_template(
    f"""You are an expert Quality Assurance Judge and Named Entity Recognition (NER) specialist for a production-grade Customer Support AI system. 

Your position is the "Line of Defense 2". You receive the customer's raw query along with initial, fast predictions from underlying Machine Learning models. Your mission is to audit these predictions and extract vital operational parameters.

Execute your task based on the following instructions:

### 1. JUDGEMENT & CORRECTION AUDIT:
- Evaluate whether the 'Predicted Intent' and 'Predicted Sentiment' accurately reflect the customer's 'Raw Query'.
- If the ML models are correct, confirm them by setting them as they are. 
- If the ML models are incorrect (e.g., the customer is shifting context, expressing underlying anger not caught by the model, or trying to cancel an order while the model flagged it as tracking), you MUST override them and determine the true final intent and sentiment.
- If the customer's query is completely vague, ambiguous, or nonsensical, flag it immediately as a misunderstanding (is_misunderstanding: True).
- You must follow these intents only and don't choose other intents except these: {list(INTENT_LABELS.values())}
- You must follow these sentiments only and don't choose other sentiments except these: {list(SENTIMENT_LABELS.values())}
- If you are confident that the true intent or sentiment does not exist in the allowed list, mark it as "UNKNOWN".

### 2. NAMED ENTITY EXTRACTION (NER):
- Scan the customer's 'Raw Query' for any specific operational metadata required to fulfill their request.
- Based on the final intent you determine, extract key entities using these mappings only: {Meta_Data_Intents}
- Do not hallucinate or guess any entity values. If an entity is not explicitly mentioned, leave it empty.

### 3. FORMAT INSTRUCTIONS:
{{format_instructions}}

### 4. INPUT DATA TO ANALYZE:
- Customer Raw Query: {{user_query}}
- Predicted Intent by ML Model: {{predicted_intent}}
- Predicted Sentiment by ML Model: {{predicted_sentiment}}""",
    input_variables=['user_query', 'predicted_intent', 'predicted_sentiment'],
    partial_variables={{
        "format_instructions": judge_extract_parser.get_format_instructions()
    }}
)

