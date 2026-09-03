from typing import Optional,Dict, Any,List
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from src.infrastructure.databases.orm_models import base, Product, Order, OrderItem, Invoice, Refund
from src.domain.interfaces.IDatabase import IDatabase

from sqlalchemy.ext.asyncio import create_async_engine

from sqlalchemy import text, select, delete, insert, update, func


class PosgresDb(IDatabase):
    def __init__(self,config):
        self.config = config
        self.engine = create_async_engine(self.config, echo=False)


    async def setup_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(base.metadata.create_all)


    async def disconnect(self) -> None:
        await self.engine.dispose()


    async def create_user(self, user_details : Dict) -> int:
        async with self.engine.begin() as conn:

            user_query = text('''
                        INSERT INTO users (username, hashed_password, email, phone, default_address) 
                        VALUES (:u_name, :hp, :email, :phone, :def_add) 
                        RETURNING user_id
                    ''')

            params = {
                'u_name': user_details.get('username'),
                'hp': user_details.get('hashed_password'),
                'email': user_details.get('email'),
                'phone': user_details.get('phone'),
                'def_add': user_details.get('default_address','NO_address')
            }

            result = await conn.execute(user_query, params)
            row = result.fetchone()

            if row:
                return row.user_id
            else:
                return 0


    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        async with self.engine.begin() as conn:
            Query=text('SELECT * FROM users WHERE user_id = :user_id')
            result=await conn.execute(Query, {'user_id':user_id})
            row=result.fetchone()
            if row:
                return dict(row._mapping)
            else:
                return None

    async def get_order(self, user_id , order_id: int) -> Optional[Dict[str, Any]]:
        async with self.engine.begin() as conn:
            stmt = select(Order).where(Order.user_id == user_id , Order.order_id == order_id)
            result=await conn.execute(stmt)
            row=result.fetchone()
            if row:
                return dict(row._mapping)
            else:
                return None

    async def delete_order(self ,user_id:int , order_id : int):
        try:

            async with self.engine.begin() as conn:
                request = delete(Order).where(Order.order_id == order_id , Order.user_id == user_id)
                result = await conn.execute(request)
                return result.rowcount > 0

        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting order {order_id}: {e}")

            return False


    async def get_orders_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        async with self.engine.begin() as conn:
            query = text("SELECT * FROM orders WHERE user_id = :u_id")
            result = await conn.execute(query, {'u_id': user_id})
            rows = result.fetchall()

            return [dict(row._mapping) for row in rows]


    async def update_order_status(self, order_id: int, new_status: str) -> bool:
        async with self.engine.begin() as conn:
            query = text("UPDATE orders SET status = :st WHERE order_id = :o_id")
            result = await conn.execute(query, {'st': new_status, 'o_id': order_id})

            return result.rowcount > 0


    async def update_shipping_address(self, order_id: int, new_address: str) -> bool:
        async with self.engine.begin() as conn:
            query = text("UPDATE orders SET shipping_address = :addr WHERE order_id = :o_id")
            result = await conn.execute(query, {'addr': new_address, 'o_id': order_id})

            return result.rowcount > 0



    async def get_invoice_details(self, user_id :int , order_id: int) -> Optional[Dict[str, Any]]:
        async with self.engine.begin() as conn:
            query = select(Invoice).join(Order).where(Invoice.order_id == order_id, Order.user_id == user_id)
            result = await conn.execute(query)
            row = result.fetchone()

            if row:
                return dict(row._mapping)
            return None


    async def get_refund_status(self, user_id:int ,order_id: int) -> Optional[Dict[str, Any]]:
        async with self.engine.begin() as conn:
            query = select(Refund).join(Order).where(Refund.order_id == order_id, Order.user_id == user_id)
            result = await conn.execute(query, {'o_id': order_id})
            row = result.fetchone()

            if row:
                return dict(row._mapping)
            return None

    async def create_ticket(self, user_id: int, issue_type: str, order_id: Optional[int] = None) -> int:
        async with self.engine.begin() as conn:

            query = text("""
                INSERT INTO tickets (user_id, order_id, issue_type) 
                VALUES (:u_id, :o_id, :i_type) 
                RETURNING ticket_id
            """)

            result = await conn.execute(query, {
                'u_id': user_id,
                'o_id': order_id,
                'i_type': issue_type
            })
            row = result.fetchone()

            if row:
                return row.ticket_id
            return 0

    async def create_product(self, description: str, price: float) -> int:
        async with self.engine.begin() as conn:

            stmt = insert(Product).values(description=description, price=price).returning(Product.product_id)
            result = await conn.execute(stmt)
            return result.scalar()

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        async with self.engine.begin() as conn:
            stmt = select(Product).where(Product.product_id == product_id)
            result = await conn.execute(stmt)
            row = result.fetchone()
            return dict(row._mapping) if row else None

    async def get_all_products(self):
        products_dict = []
        try:
            async with self.engine.begin() as conn:
                stmt = select(Product)
                result = await conn.execute(stmt)
                rows = result.fetchall()
                return [dict(row) for row in result.mappings()]
        except SQLAlchemyError as e:
            logger.error(e)

    async def get_product_by_name(self, product_name: str):
        try:
            async with self.engine.begin() as conn:
                stmt= select(Product).where(Product.product_name==product_name)
                result = await conn.execute(stmt)
                row = result.fetchone()
                if row:
                    return dict(row._mapping)
        except SQLAlchemyError as e:
            logger.error(e)
            return None






    async def update_product(self, product_id: int, product_details: Dict):
        if not product_details:
            return
        async with self.engine.begin() as conn:
            stmt = update(Product).where(Product.product_id == product_id).values(**product_details)
            await conn.execute(stmt)

    async def delete_product(self, product_id: int):
        async with self.engine.begin() as conn:
            stmt = delete(Product).where(Product.product_id == product_id)
            await conn.execute(stmt)

    async def create_order_items(self, order_id: int, product_id: int, quantity: int, unit_price: float):
        async with self.engine.begin() as conn:
            stmt = insert(OrderItem).values(
                order_id=order_id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price
            )
            await conn.execute(stmt)

    async def delete_order_item(self, order_id: int, product_id: int) -> bool:
        try:
            async with self.engine.begin() as conn:
                stmt = delete(OrderItem).where(
                OrderItem.order_id == order_id,
                    OrderItem.product_id == product_id
                )
                result = await conn.execute(stmt)

                return result.rowcount > 0
        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting order_item order_id : {order_id} and product_id : {product_id}: {e}")
            return False

    async def delete_order_items(self, order_id: int) -> bool:
        try:
            async with self.engine.begin() as conn:
                stmt = delete(OrderItem).where(
                    OrderItem.order_id == order_id
                )
                result = await conn.execute(stmt)

                return result.rowcount > 0
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while deleting order_items order_id : {order_id} -->{e}")
            return False

    async def create_order(self, user_id: int, order_data: Dict[str, Any]) -> int:
        async with self.engine.begin() as conn:
            User = await self.get_user(user_id)
            if not User:
                raise ValueError(f"User with ID {user_id} not found!")

            shipping_address = order_data.get('shipping_address', User.get('default_address'))


            order_stmt = insert(Order).values(
                user_id=user_id,
                status=order_data.get('status', 'Pending'),
                expected_delivery_date=order_data.get('expected_delivery_date'),
                shipping_address=shipping_address,
                total_amount=order_data.get('total_amount', 0.0)
            ).returning(Order.order_id)

            result = await conn.execute(order_stmt)
            new_order_id = result.scalar()

            if not new_order_id:
                return 0


            items = order_data.get('items', [])
            if items:

                items_data = [{
                    "order_id": new_order_id,
                    "product_id": item['product_id'],
                    "quantity": item.get('quantity', 1),
                    "unit_price": item['unit_price']
                } for item in items]


                await conn.execute(insert(OrderItem), items_data)

            return new_order_id

    async def modify_order_items(self, order_id: int, items_to_add: List[Dict[str, Any]],
                                 removed_product_ids: List[int]) -> tuple[bool, str]:
        try:
            async with self.engine.begin() as conn:

                stmt = select(Order).where(Order.order_id == order_id)
                result = await conn.execute(stmt)
                order = result.fetchone()

                if not order:
                    return False, f"Order {order_id} not found."
                if order.status in ['Shipped', 'Delivered', 'Cancelled']:
                    return False, f"Cannot change order {order_id} because its status is '{order.status}'."


                if removed_product_ids:
                    del_stmt = delete(OrderItem).where(
                        OrderItem.order_id == order_id,
                        OrderItem.product_id.in_(removed_product_ids)
                    )
                    await conn.execute(del_stmt)


                for item in items_to_add:
                    pid = item['product_id']
                    qty = item['quantity']
                    price = item['unit_price']


                    check_stmt = select(OrderItem).where(OrderItem.order_id == order_id, OrderItem.product_id == pid)
                    chk_res = await conn.execute(check_stmt)
                    existing_item = chk_res.fetchone()

                    if existing_item:

                        new_qty = existing_item.quantity + qty
                        upd_stmt = update(OrderItem).where(
                            OrderItem.order_id == order_id, OrderItem.product_id == pid
                        ).values(quantity=new_qty)
                        await conn.execute(upd_stmt)
                    else:

                        ins_stmt = insert(OrderItem).values(
                            order_id=order_id, product_id=pid, quantity=qty, unit_price=price
                        )
                        await conn.execute(ins_stmt)


                sum_stmt = select(func.sum(OrderItem.quantity * OrderItem.unit_price)).where(
                    OrderItem.order_id == order_id)
                sum_res = await conn.execute(sum_stmt)
                new_total = sum_res.scalar() or 0.0

                #
                upd_order_stmt = update(Order).where(Order.order_id == order_id).values(total_amount=new_total)
                await conn.execute(upd_order_stmt)

                return True, "Success"

        except SQLAlchemyError as e:
            logger.error(f"Database error while modifying order {order_id}: {e}")
            return False, "System database error occurred."
        except Exception as e:
            logger.error(f"Unexpected error modifying order {order_id}: {e}")
            return False, str(e)