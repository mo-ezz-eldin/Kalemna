from typing import Optional,Dict, Any,List
from src.infrastructure.databases.orm_models import base
from src.domain.interfaces.IDatabase import IDatabase

from sqlalchemy.ext.asyncio import create_async_engine

from sqlalchemy import text

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


    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        async with self.engine.begin() as conn:
            Query=text('SELECT * FROM users WHERE username = :username')
            result=await conn.execute(Query, {'username':username})
            row=result.fetchone()
            if row:
                return dict(row._mapping)
            else:
                return None

    async def create_order(self, user_id: int, order_data: Dict[str, Any]) -> int:
        async with self.engine.begin() as conn:
            User= await self.get_user(user_id)
            if not User:
                raise ValueError(f"User with ID {user_id} not found!")

            shipping_address = order_data.get('shipping_address', User.get('default_address'))


            cr_query = text('''
                        INSERT INTO orders (user_id, status, expected_delivery_date, shipping_address, total_amount) 
                        VALUES (:u_id, :st, :exp_del_date, :ship_addr, :tot_amount) 
                        RETURNING order_id
                    ''')

            params = {
                'u_id': user_id,
                'st': order_data.get('status', 'Pending'),
                'exp_del_date': order_data.get('expected_delivery_date'),
                'ship_addr': shipping_address,
                'tot_amount': order_data.get('total_amount')
            }

            result = await conn.execute(cr_query, params)
            row = result.fetchone()

            if row:
                return row.order_id
            else:
                return 0


    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        async with self.engine.begin() as conn:
            Query=text('SELECT * FROM orders WHERE order_id = :o_id')
            result=await conn.execute(Query, {'o_id':order_id})
            row=result.fetchone()
            if row:
                return dict(row._mapping)
            else:
                return None

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



    async def get_invoice_details(self, order_id: int) -> Optional[Dict[str, Any]]:
        async with self.engine.begin() as conn:
            query = text("SELECT * FROM invoices WHERE order_id = :o_id")
            result = await conn.execute(query, {'o_id': order_id})
            row = result.fetchone()

            if row:
                return dict(row._mapping)
            return None


    async def get_refund_status(self, order_id: int) -> Optional[Dict[str, Any]]:
        async with self.engine.begin() as conn:
            query = text("SELECT * FROM refunds WHERE order_id = :o_id")
            result = await conn.execute(query, {'o_id': order_id})
            row = result.fetchone()

            if row:
                return dict(row._mapping)
            return None

    async def create_ticket(self, user_id: int, issue_type: str, order_id: Optional[int] = None) -> int:
        async with self.engine.begin() as conn:
            # استخدمنا RETURNING هنا كمان عشان نرجع رقم التيكت اللي اتكريت
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

    async def delete_order_item(self, order_id: int, product_id: int):
        async with self.engine.begin() as conn:
            stmt = delete(OrderItem).where(
                OrderItem.order_id == order_id,
                OrderItem.product_id == product_id
            )
            await conn.execute(stmt)


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