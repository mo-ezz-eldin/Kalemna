import pytest

from src.domain.interfaces.IDatabase import IDatabase


@pytest.mark.asyncio
async def test_create_user(db: IDatabase, create_user):

    user_id, _ = create_user

    assert user_id > 0


@pytest.mark.asyncio(loop_scope="session")
async def test_get_user_by_username_not_exist(db: IDatabase):

    username = "non_existing_user_999"

    user = await db.get_user_by_username(username)
    assert user is None


@pytest.mark.asyncio(loop_scope="session")
async def test_get_user_by_existing_username(db: IDatabase, create_user):

    user_id, user_details = create_user

    user = await db.get_user_by_username(user_details["username"])

    assert user is not None
    assert user["user_id"] == user_id


@pytest.mark.asyncio(loop_scope="session")
async def test_get_user_by_user_id_not_found(db: IDatabase):

    non_existing_id = 999999

    user = await db.get_user(non_existing_id)
    assert user is None


@pytest.mark.asyncio(loop_scope="session")
async def test_get_user_by_existing_user_id(db: IDatabase, create_user):

    user_id, _ = create_user

    user = await db.get_user(user_id)
    assert user
