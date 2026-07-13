from typing import TypedDict,List, Dict,Annotated
from langgraph.graph import add_messages

class Customer_State(TypedDict):
    user_id: str
    user_query: str
    Messages : Annotated[List,add_messages]
    is_misunderstanding:bool
    num_of_mis_understanding:int
    predicted_intent: str
    predicted_sentiment: str
    final_intent: str
    final_sentiment: str
    extracted_entities: Dict[str,List[str]]
    action : str
    nodes_info: List[str]
    final_response: str