from typing import Optional,Dict, Any,List

from src.domain.interfaces.IDatabase import IDatabase

from sqlalchemy.ext.asyncio import create_async_engine

from sqlalchemy import text

class PosgresDb(IDatabase):
    def __init__(self,config):
        self.config = config
        self.engine = create_async_engine(self.config, echo=False)


    async def disconnect(self) -> None:
        await self.engine.dispose()

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        async with self.engine.begin() as conn:
            Query=text('SELECT * FROM users WHERE user_id = :u_id')
            result=await conn.execute(Query, {'u_id':user_id})
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