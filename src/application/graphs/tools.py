from typing import Dict, List, Any, Optional, Annotated
from langgraph.prebuilt import InjectedState
from langchain_core.tools import tool
from loguru import logger

from src.application.graphs.schemas import Place_Order_Schema, Change_Order_Schema, ItemToAdd, ItemToRemove
from src.domain.interfaces.IDatabase import IDatabase


def get_tools(db: IDatabase):

    @tool
    async def cancel_order( user_id : Annotated[int , InjectedState('user_id')],order_id: int) -> str:
        """Use this tool to cancel or delete an entire order.
        It requires a valid integer 'order_id' extracted from the user's request."""
        result = await db.delete_order(user_id , order_id)

        if result:
                logger.info(f"Cancel Order: {order_id} with  items")
                return f"Order {order_id} has been successfully deleted."
        else:
            return f"Could not delete order {order_id}. It may not exist or there was a system error. Please clarify with the user."

    @tool
    async def track_order(user_id :Annotated[int , InjectedState('user_id')] , order_id : int) -> str:
        """Use this tool when the user wants to track the status of an order.
    It requires a valid integer 'order_id' extracted from the user's request."""
        result = await db.get_order(user_id , order_id)
        if result:
            status = result.get('status', 'Unknown')
            delivery_date = result.get('expected_delivery_date', 'Not specified')
            total = result.get('total_amount', '0.0')
            address = result.get('shipping_address', 'Not specified')

            return (f"Order {order_id} details:\n"
                    f"- Status: {status}\n"
                    f"- Expected Delivery: {delivery_date}\n"
                    f"- Shipping Address: {address}\n"
                    f"- Total Amount: {total}")
        else:
            return f"could not find order {order_id}. Please clarify with the user."


    @tool
    async def get_invoice(user_id :Annotated[int , InjectedState('user_id')] , order_id: int) -> str:
        """
        Use this tool to retrieve invoice details for a specific order.
        It requires a valid integer 'order_id'.
        """
        invoice = await db.get_invoice_details(user_id,order_id)

        if invoice:
            amount = invoice.get('total_amount', 'Unknown')
            date = invoice.get('created_at', 'Unknown date')
            status = invoice.get('status', 'Unknown status')
            return f"Invoice found for Order {order_id}. Amount: {amount}, Date: {date}, Status: {status}."
        else:
            return f"Could not find an invoice for order {order_id}. Please inform the user."

    @tool
    async def change_shipping_address(user_id : Annotated[int , InjectedState('user_id')] ,order_id: int, new_address: str) -> str:
        """
        Use this tool to update or change the shipping address of an existing order.
        It requires a valid integer 'order_id' and a string 'new_address'.
        """
        order = await db.get_order(user_id , order_id)
        if not order:
            return f"Order {order_id} does not exist."

        if order.get('status') in ['Shipped', 'Delivered']:
            return f"Cannot change address. Order {order_id} is already {order.get('status')}."

        is_updated = await db.update_shipping_address(order_id, new_address)

        if is_updated:
            return f"Successfully updated the shipping address for order {order_id} to: {new_address}."
        else:
            return f"Failed to update the shipping address for order {order_id} due to a system error."

    @tool
    async def track_refund(user_id: Annotated[int , InjectedState('user_id')] , order_id: int) -> str:
        """
        Use this tool to check the status of a refund for a specific order.
        It requires a valid integer 'order_id'.
        """
        refund = await db.get_refund_status(user_id ,order_id)

        if refund:
            amount = refund.get('refund_amount', 'Unknown')
            status = refund.get('status', 'Processing')
            return f"Refund for Order {order_id} is currently '{status}'. Amount: {amount}."
        else:
            return f"No refund records found for order {order_id}."

    @tool
    async def check_refund_policy() -> str:
        """Use this tool when the user asks about the refund policy, rules, or cancellation fees."""
        return (
            "Refund Policy: You can return items within 14 days of delivery. "
            "Cancellation Fee: No fee if cancelled before shipping. "
            "Delivery Period: Typically 3-5 business days."
        )

    @tool
    async def retrieve_all_products()->Any:
        """this tool is used to retrieve all products. since the user wants to place order"""
        products = await db.get_all_products()
        if products:
            return products
        else:
            return 'No products found.'



    @tool(args_schema=Place_Order_Schema)

    async def place_order( user_id :Annotated[int , InjectedState('user_id')] , items : List[Dict[str , str | int]] , shipping_address : str) -> str:
        """Use this tool to place a new order. Requires items list and shipping address."""
        db_items = []
        total_amount_of_order = 0.0


        for item in items:
            p_name = item.get('product_name')
            qty = int(item.get('quantity', 1))


            product = await db.get_product_by_name(p_name)


            if not product:
                return f"Product '{p_name}' was not found in the catalog. Please clarify with the user."

            unit_price = float(product['price'])
            db_items.append({
                "product_id": product['product_id'],
                "quantity": qty,
                "unit_price": unit_price
            })
            total_amount_of_order += (qty * unit_price)


        order_details = {
            'shipping_address': shipping_address,
            'total_amount': total_amount_of_order,
            'items': db_items
        }

        try:
            order_id = await db.create_order(user_id, order_details)

            if order_id:
                return f"Successfully placed order. Order ID is {order_id}. Total amount: {total_amount_of_order}."
            else:
                return "Failed to place the order due to a system error."

        except Exception as e:

            return f"Could not create order due to an error: {str(e)}"


    @tool(args_schema=Change_Order_Schema )
    async def change_order(user_id : Annotated[int , InjectedState('user_id')] , order_id: int, items_to_add: Optional[List[ItemToAdd]] = None,
                           items_to_remove: Optional[List[ItemToRemove]] = None ) -> str:
        """Use this tool to add or remove items from an existing order."""
        is_found = await db.get_order(user_id, order_id)
        if is_found:
            items_to_add = items_to_add or []
            items_to_remove = items_to_remove or []

            if not items_to_add and not items_to_remove:
                return "No changes requested by the user."

            added_products_list = []
            removed_product_ids = []


            for item in items_to_add:

                product = await db.get_product_by_name(item.product_name)
                if not product:
                    return f"Cannot add item. Product '{item.product_name}' was not found in our catalog."

                added_products_list.append({
                'product_id': product['product_id'],
                'quantity': item.quantity,
                'unit_price': product['price']
                })

            for item in items_to_remove:
                product = await db.get_product_by_name(item.product_name)
                if not product:
                    return f"Cannot remove item. Product '{item.product_name}' was not found in our catalog."

                removed_product_ids.append(product['product_id'])


            success, msg = await db.modify_order_items(
            order_id=order_id,
            items_to_add=added_products_list,
            removed_product_ids=removed_product_ids
            )

            if success:
                return f"Order {order_id} has been successfully updated with the requested changes."
            else:
                return f"Failed to update order {order_id}. Reason: {msg}"
        else:
            return f"could not find any orders with this order_id : {order_id} or user_id : {user_id}."




    return [  cancel_order , track_order , get_invoice ,change_shipping_address ,track_refund ,check_refund_policy , place_order , change_order , retrieve_all_products]



