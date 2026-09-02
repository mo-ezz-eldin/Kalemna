from langchain_core.tools import tool
from src.domain.interfaces.IDatabase import IDatabase


def get_tools(db: IDatabase):
    # بنعرف الأداة هنا عشان تكون شايفة الـ db عن طريق الـ Closure
    @tool
    async def read_from_db(user_id: str, extracted_entities: list) -> str:
        """use this tool when user_id is given and extracted_entities not empty to read all details of user from database"""
        try:
            # الـ db هنا متاح ومتعرف جواه بفضل الـ Closure
            user_info = await db.get_user(int(user_id))
            user_orders = await db.get_orders_by_user(int(user_id))

            if not user_info:
                return "User not found in the database."

            return f"User Details: {user_info}\nUser Orders: {user_orders}"

        except Exception as e:
            return f"Error reading from database: {str(e)}"


    @tool
    async def cancel_order( order_id: int) -> str:
        """Use this tool to cancel or delete an entire order.
        It requires a valid integer 'order_id' extracted from the user's request."""
        result = await db.delete_order(order_id)

        if result:
            return f"Order {order_id} has been successfully deleted."
        else:
            return f"Could not delete order {order_id}. It may not exist or there was a system error. Please clarify with the user."

    # هنا بنرجع اللستة وفيها الأداة وهي جاهزة ومربوطة بالـ db
    return [read_from_db]



