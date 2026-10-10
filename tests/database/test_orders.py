import pytest

from src.domain.interfaces.IDatabase import IDatabase


@pytest.mark.asyncio(loop_scope="session")
async def test_create_order_user_Not_found(db: IDatabase, order_example, create_order):
    with pytest.raises(ValueError) as e:
        user_id = 1000
        error = await create_order(user_id, order_example)

        assert error in str(e)


@pytest.mark.asyncio(loop_scope="session")
async def test_create_order_success(db: IDatabase, create_user, order_example, create_order):

    user_id, user_details = create_user

    order_id = await create_order(user_id, order_example)

    assert order_id > 0


@pytest.mark.asyncio(loop_scope="session")
async def test_get_order_by_users_success(db: IDatabase, create_user, order_example, create_order):
    user_id, user_details = create_user

    await create_order(user_id, order_example)

    await create_order(user_id, order_example)

    orders_per_user = await db.get_orders_by_user(user_id)

    assert len(orders_per_user) > 1


@pytest.mark.asyncio(loop_scope="session")
async def test_get_order_success(db: IDatabase, create_user, order_example, create_order):
    user_id, user_details = create_user
    order_id = await create_order(user_id, order_example)
    order = await db.get_order(user_id, order_id)
    assert order is not None
    assert order["user_id"] == user_id
    assert order["order_id"] == order_id


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_order(db: IDatabase, create_user, order_example, create_order):
    user_id, user_details = create_user

    order_id = await create_order(user_id, order_example)

    deleted = await db.delete_order(user_id, order_id)

    assert deleted == True

    order = await db.get_order(user_id, order_id)

    assert order is None


@pytest.mark.asyncio(loop_scope="session")
async def test_update_order_status(db: IDatabase, create_user, order_example, create_order):

    user_id, user_details = create_user

    order_id = await create_order(user_id, order_example)

    is_done = await db.update_order_status(order_id, "Shipped")

    assert is_done == True

    order = await db.get_order(user_id, order_id)

    assert order["status"] == "Shipped"


@pytest.mark.asyncio(loop_scope="session")
async def test_update_shipping_address(db: IDatabase, create_user, order_example, create_order):
    user_id, user_details = create_user

    order_id = await create_order(user_id, order_example)

    is_done = await db.update_shipping_address(order_id, "cairo")

    assert is_done == True

    order = await db.get_order(user_id, order_id)

    assert order["shipping_address"] == "cairo"


@pytest.mark.asyncio(loop_scope="session")
async def test_modify_items_with_invalid_status(db: IDatabase, create_user, order_example, create_order):
    user_id, user_details = create_user
    order_id = await create_order(user_id, order_example)

    await db.update_order_status(order_id, "Shipped")

    add_items = [{}]

    items_to_remove = [{}]

    is_ok, mssg = await db.modify_order_items(order_id, add_items, items_to_remove)

    order = await db.get_order(user_id, order_id)

    assert is_ok == False

    assert order["status"] == "Shipped"


@pytest.mark.asyncio(loop_scope="session")
async def test_modify_items_remove(db: IDatabase, create_user, create_order):
    user_id, user_details = create_user
    products = [
        {"name": "test_product_v2", "description": "this is the description of test_product", "price": 999.99},
        {"name": "test_product2", "description": "this is the description of test_product2", "price": 34},
        {"name": "test_product3", "description": "this is the description of test_product3", "price": 45},
    ]
    first_product_id = await db.create_product(**products[0])

    second_product_id = await db.create_product(**products[1])

    third_product_id = await db.create_product(**products[2])

    first_product = await db.get_product(first_product_id)

    await db.get_product(second_product_id)

    third_product = await db.get_product(third_product_id)

    add_items = [{}]

    items_to_remove = [{"product_id": third_product["product_id"], "quantity": 6}]

    items = [
        {"product_id": third_product_id, "quantity": 3, "unit_price": third_product["price"]},
        {"product_id": first_product_id, "quantity": 1, "unit_price": first_product["price"]},
    ]

    order_details = {
        "items": items,
        "status": "pending",
        "shipping_address": "test_address",
        "total_amount": (1 * first_product["price"]) + (3 * third_product["price"]),
    }

    order_id = await db.create_order(user_id, order_details)

    is_ok, mssg = await db.modify_order_items(order_id, add_items, items_to_remove)

    assert is_ok == False

    assert mssg == f"cannot change quantity of order {order_id} because its quantity is {-3} and user already has {6}."


@pytest.mark.asyncio(loop_scope="session")
async def test_modify_order_add_and_remove(db: IDatabase, create_user, create_order):
    user_id, user_details = create_user
    products = [
        {"name": "test_product_v2", "description": "this is the description of test_product", "price": 999.99},
        {"name": "test_product2", "description": "this is the description of test_product2", "price": 34},
        {"name": "test_product3", "description": "this is the description of test_product3", "price": 45},
    ]

    first_product_id = await db.create_product(**products[0])

    second_product_id = await db.create_product(**products[1])

    third_product_id = await db.create_product(**products[2])

    first_product = await db.get_product(first_product_id)

    second_product = await db.get_product(second_product_id)

    third_product = await db.get_product(third_product_id)

    add_items = [
        {"product_id": first_product_id, "quantity": 3, "unit_price": first_product["price"]},
        {"product_id": second_product_id, "quantity": 2, "unit_price": second_product["price"]},
    ]

    items_to_remove = [{"product_id": third_product_id, "quantity": 1, "unit_price": third_product["price"]}]

    items = [{"product_id": third_product_id, "quantity": 3, "unit_price": third_product["price"]}]

    order_details = {
        "items": items,
        "status": "pending",
        "shipping_address": "test_address",
        "total_amount": (3 * third_product["price"]),
    }

    order_id = await db.create_order(user_id, order_details)

    is_ok, mssg = await db.modify_order_items(order_id, add_items, items_to_remove)

    assert is_ok == True

    assert mssg == "Success"

    order = await db.get_order(user_id, order_id)

    assert order["total_amount"] == (2 * third_product["price"]) + (3 * first_product["price"]) + (
        2 * second_product["price"]
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_single_order_item(db: IDatabase, create_user, create_order, create_product, product_example):
    user_id, _ = create_user

    prod1_id, p1_details = await create_product(product_example)
    prod2_id, p2_details = await create_product({"name": "P2", "description": "Desc", "price": 100})

    items = [
        {"product_id": prod1_id, "quantity": 1, "unit_price": p1_details["price"]},
        {"product_id": prod2_id, "quantity": 1, "unit_price": 100},
    ]
    order_details = {
        "items": items,
        "status": "pending",
        "shipping_address": "cairo",
        "total_amount": p1_details["price"] + 100,
    }
    order_id = await create_order(user_id, order_details)

    deleted = await db.delete_order_item(order_id, prod1_id)
    assert deleted is True


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_all_order_items(db: IDatabase, create_user, order_example, create_order):
    user_id, _ = create_user
    order_id = await create_order(user_id, order_example)

    # مسح كل العناصر
    deleted = await db.delete_order_items(order_id)
    assert deleted is True
