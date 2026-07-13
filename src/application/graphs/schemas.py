from pydantic import BaseModel, Field
from typing import Dict, List

class JudgeExtractSchema(BaseModel):
    final_intent: str = Field(
        description="The validated or corrected intent based on the user query. Must match one of the allowed intent labels."
    )
    final_sentiment: str = Field(
        description="The validated or corrected sentiment based on the user query. Must match one of the allowed sentiment labels."
    )
    extracted_entities: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Key-value pairs of extracted metadata fields from the user query mapped to their values based on the intent metadata requirement."
    )
    is_misunderstanding: bool = Field(
        description="Set to true if the user query is completely ambiguous, vague, or nonsensical context-wise; otherwise false."
    )