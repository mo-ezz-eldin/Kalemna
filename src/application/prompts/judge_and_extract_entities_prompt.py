from langchain_core.output_parsers import JsonOutputParser
from langsmith import Client

from src.application.graphs.graph_schemas import JudgeExtractSchema
from src.config.Constant import INTENT_LABELS, SENTIMENT_LABELS
from src.config.intents_metadata import Meta_Data_Intents

judge_extract_parser = JsonOutputParser(pydantic_object=JudgeExtractSchema)


client = Client()
judge_and_extract_entities_template = client.pull_prompt("judge_and_extract_prompt:staging")

judge_and_extract_entities_template = judge_and_extract_entities_template.partial(
    format_instructions=judge_extract_parser.get_format_instructions(),
    intents_list=list(INTENT_LABELS.values()),
    sentiments_list=list(SENTIMENT_LABELS.values()),
    meta_data_intents=Meta_Data_Intents,
)
