from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode,tools_condition
from src.application.graphs.state import Customer_State
from src.domain.interfaces.IDatabase import IDatabase

def get_tools(db: IDatabase):
    @tool
    async def read_from_db(user_id:str,extracted_entities:list): #not completed yet since we dont know all deatils of the user
        "use this tool when user_id is given and extracted_entities not empty to read all details of user from database"
        try:

            user_info = await db.get_user(int(user_id))


            user_orders = await db.get_orders_by_user(int(user_id))

            if not user_info:
                return "User not found in the database."

            return f"User Details: {user_info}\nUser Orders: {user_orders}"

        except Exception as e:
            return f"Error reading from database: {str(e)}"

        return [read_from_db]



