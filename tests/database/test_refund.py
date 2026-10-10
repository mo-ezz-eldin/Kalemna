import pytest

from src.domain.interfaces.IDatabase import IDatabase


@pytest.mark.asyncio(loop_scope="session")
async def test_get_refund_status(db: IDatabase, create_user, order_example, create_order):
    user_id, _ = create_user
    order_id = await create_order(user_id, order_example)

    refund = await db.get_refund_status(user_id, order_id)

    assert refund is None


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.skip("not implemented right now")
async def test_tickets_lifecycle(db: IDatabase, create_user):
    pass
