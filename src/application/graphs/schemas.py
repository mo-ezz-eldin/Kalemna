from pydantic import BaseModel, Field
from typing import Dict, List

class JudgeExtractSchema(BaseModel):
    final_intent: str = Field(
        description="The validated or corrected intent based on the user query. Must match one of the allowed intent labels."
    )
    final_sentiment: str = Field(
        description="The validated or corrected sentiment based on the user query. Must match one of the allowed sentiment labels."
    )
    extracted_entities: Dict[str, str] = Field(
        default_factory=dict,
        description="Key-value pairs of extracted metadata. Keys must match the required_metadata for the final_intent. If a value is missing from the user query, set its value to an empty string ''."
    )
    is_misunderstanding: bool = Field(
        description="Set to True if the user query is completely ambiguous, vague, or nonsensical context-wise; otherwise False."
    )

    reasoning : str = Field(
        description="you must explain every choice you made in few words about final_intent , final_sentiment and extracted_entities and is_misunderstanding."
    )