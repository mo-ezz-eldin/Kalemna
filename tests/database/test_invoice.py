import pytest

from src.domain.interfaces.IDatabase import IDatabase


@pytest.mark.asyncio(loop_scope="session")
async def test_get_invoice_details(db: IDatabase, create_user, order_example, create_order):
    user_id, _ = create_user
    order_id = await create_order(user_id, order_example)

    invoice = await db.get_invoice_details(user_id, order_id)

    assert invoice is None
