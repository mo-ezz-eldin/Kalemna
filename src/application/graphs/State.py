from typing import Annotated, TypedDict

from langgraph.graph import add_messages


class Customer_State(TypedDict):
    user_id: str
    user_query: str
    messages: Annotated[list, add_messages]
    is_misunderstanding: bool
    num_of_mis_understanding: int
    predicted_intent: str
    predicted_sentiment: str
    final_intent: str
    final_sentiment: str
    extracted_entities: dict[str, list[str]]
    action: str
    final_response: str
