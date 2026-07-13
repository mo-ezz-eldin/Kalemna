from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode,tools_condition
from src.application.graphs.state import Customer_State

@tool
def read_from_db(user_id:str,extracted_entities:list):
    "use this tool when user_id is given and extracted_entities not empty to read all details of user from database"
    return ''
