from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_cancel_order_success(setup_all_tools, db, create_order, create_user, order_example):
    user_id, user_details = create_user
    order_id = await create_order(user_id, order_example)
    tool = await setup_all_tools("cancel_order")

    assert await db.get_order(user_id, order_id) is not None

    result = await tool.coroutine(user_id=user_id, order_id=order_id)

    assert result == f"Order {order_id} has been successfully deleted."

    assert await db.get_order(user_id, order_id) is None


@pytest.mark.asyncio(loop_scope="session")
async def test_cacel_order_not_found(setup_all_tools, db):
    user_id = 92938
    order_id = 94844
    tool = await setup_all_tools("cancel_order")

    assert await db.get_order(user_id, order_id) is None
    result = await tool.coroutine(user_id=user_id, order_id=order_id)
    assert (
        result
        == f"Could not delete order {order_id}. It may not exist or there was a system error. Please clarify with the user."
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_track_order_success(setup_all_tools, db, create_order, create_user, order_example):
    user_id, user_details = create_user

    order_id = await create_order(user_id, order_example)

    tool = await setup_all_tools("track_order")

    order = await db.get_order(user_id, order_id)

    assert order is not None

    result = await tool.coroutine(user_id=user_id, order_id=order_id)

    assert result == (
        f"Order {order_id} details:\n"
        f"- Status: {order['status']}\n"
        f"- Expected Delivery: {order['expected_delivery_date']}\n"
        f"- Shipping Address: {order['shipping_address']}\n"
        f"- Total Amount: {order['total_amount']}"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_track_order_not_found(setup_all_tools, db):
    user_id = 92938
    order_id = 94844
    tool = await setup_all_tools("track_order")

    order = await db.get_order(user_id, order_id)

    assert order is None

    result = await tool.coroutine(user_id=user_id, order_id=order_id)

    assert result == f"could not find order {order_id}. Please clarify with the user."


@pytest.mark.asyncio(loop_scope="session")
async def test_get_invoice_success(setup_all_tools, db, create_user, create_order, order_example):
    user_id, _ = create_user
    order_id = await create_order(user_id, order_example)
    tool = await setup_all_tools("get_invoice")

    result = await tool.coroutine(user_id=user_id, order_id=order_id)
    invoice = await db.get_invoice_details(user_id, order_id)

    if invoice:
        assert f"Invoice found for Order {order_id}" in result
    else:
        assert result == f"Could not find an invoice for order {order_id}. Please inform the user."


@pytest.mark.asyncio(loop_scope="session")
async def test_get_invoice_not_found(setup_all_tools):
    user_id, order_id = 99999, 88888
    tool = await setup_all_tools("get_invoice")

    result = await tool.coroutine(user_id=user_id, order_id=order_id)
    assert result == f"Could not find an invoice for order {order_id}. Please inform the user."


@pytest.mark.asyncio(loop_scope="session")
async def test_change_shipping_address_success(setup_all_tools, db, create_user, create_order, order_example):
    user_id, _ = create_user
    order_id = await create_order(user_id, order_example)
    tool = await setup_all_tools("change_shipping_address")

    new_address = "123 Cairo St, Egypt"

    result = await tool.coroutine(user_id=user_id, order_id=order_id, new_address=new_address)
    assert result == f"Successfully updated the shipping address for order {order_id} to: {new_address}."

    updated_order = await db.get_order(user_id, order_id)
    assert updated_order["shipping_address"] == new_address


@pytest.mark.asyncio(loop_scope="session")
async def test_change_shipping_address_order_not_found(setup_all_tools):
    user_id, order_id = 99999, 88888
    tool = await setup_all_tools("change_shipping_address")

    result = await tool.coroutine(user_id=user_id, order_id=order_id, new_address="Some Address")
    assert result == f"Order {order_id} does not exist."


@pytest.mark.asyncio(loop_scope="session")
async def test_change_shipping_address_already_shipped_or_delivered(
    setup_all_tools, db, create_user, create_order, order_example
):
    user_id, _ = create_user
    order_id = await create_order(user_id, order_example)

    if hasattr(db, "update_order_status"):
        await db.update_order_status(order_id, "Shipped")

    tool = await setup_all_tools("change_shipping_address")

    order = await db.get_order(user_id, order_id)
    result = await tool.coroutine(user_id=user_id, order_id=order_id, new_address="Some Address")

    if order.get("status") in ["Shipped", "Delivered"]:
        assert result == f"Cannot change address. Order {order_id} is already {order.get('status')}."


@pytest.mark.asyncio(loop_scope="session")
async def test_track_refund_not_found(setup_all_tools):
    user_id, order_id = 99999, 88888
    tool = await setup_all_tools("track_refund")

    result = await tool.coroutine(user_id=user_id, order_id=order_id)
    assert result == f"No refund records found for order {order_id}."


@pytest.mark.asyncio(loop_scope="session")
async def test_track_refund_success(setup_all_tools, db, create_user, create_order, order_example):
    user_id, _ = create_user
    order_id = await create_order(user_id, order_example)
    tool = await setup_all_tools("track_refund")

    result = await tool.coroutine(user_id=user_id, order_id=order_id)
    refund = await db.get_refund_status(user_id, order_id)

    if refund:
        assert f"Refund for Order {order_id} is currently" in result
    else:
        assert result == f"No refund records found for order {order_id}."


@pytest.mark.asyncio(loop_scope="session")
async def test_check_refund_policy(setup_all_tools):
    tool = await setup_all_tools("check_refund_policy")
    result = await tool.coroutine()

    assert "Refund Policy:" in result
    assert "14 days" in result


@pytest.mark.asyncio(loop_scope="session")
async def test_retrieve_all_products(setup_all_tools, db):
    tool = await setup_all_tools("retrieve_all_products")
    result = await tool.coroutine()
    products = await db.get_all_products()

    if products:
        assert result == products
    else:
        assert result == "No products found."


@pytest.mark.asyncio(loop_scope="session")
async def test_place_order_success(setup_all_tools, db, create_user, create_product, product_example):
    user_id, _ = create_user
    tool = await setup_all_tools("place_order")

    await create_product(product_example)

    products = await db.get_all_products()
    assert products, "من فضلك تأكد إن الداتا بيز فيها منتجات في الفيكتشرز"
    valid_product_name = products[0]["product_name"]

    result = await tool.coroutine(
        user_id=user_id, items=[{"product_name": valid_product_name, "quantity": 2}], shipping_address="Cairo, Egypt"
    )
    assert "Successfully placed order." in result
    assert "Total amount:" in result


@pytest.mark.asyncio(loop_scope="session")
async def test_place_order_product_not_found(setup_all_tools, create_user):
    user_id, _ = create_user
    tool = await setup_all_tools("place_order")

    result = await tool.coroutine(
        user_id=user_id,
        items=[{"product_name": "Non_Existent_Product_12345", "quantity": 1}],
        shipping_address="Cairo, Egypt",
    )
    assert result == "Product 'Non_Existent_Product_12345' was not found in the catalog. Please clarify with the user."


@pytest.mark.asyncio(loop_scope="session")
async def test_place_order_system_error_returns_none(setup_all_tools, db, create_user, create_product, product_example):
    user_id, _ = create_user
    tool = await setup_all_tools("place_order")
    await create_product(product_example)
    products = await db.get_all_products()
    valid_product_name = products[0]["product_name"]

    with patch.object(db, "create_order", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = None
        result = await tool.coroutine(
            user_id=user_id,
            items=[{"product_name": valid_product_name, "quantity": 1}],
            shipping_address="Cairo, Egypt",
        )
        assert result == "Failed to place the order due to a system error."


@pytest.mark.asyncio(loop_scope="session")
async def test_place_order_exception_handling(setup_all_tools, db, create_user, create_product, product_example):
    user_id, _ = create_user
    tool = await setup_all_tools("place_order")
    await create_product(product_example)
    products = await db.get_all_products()
    valid_product_name = products[0]["product_name"]

    with patch.object(db, "create_order", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = Exception("Database connection lost")
        result = await tool.coroutine(
            user_id=user_id,
            items=[{"product_name": valid_product_name, "quantity": 1}],
            shipping_address="Cairo, Egypt",
        )
        assert result == "Could not create order due to an error: Database connection lost"


@pytest.mark.asyncio(loop_scope="session")
async def test_change_order_success(setup_all_tools, db, create_user, create_order, order_example):
    user_id, _ = create_user
    order_id = await create_order(user_id, order_example)
    tool = await setup_all_tools("change_order")

    products = await db.get_all_products()
    valid_product_name = products[0]["product_name"]

    args = {
        "user_id": user_id,
        "order_id": order_id,
        "items_to_add": [{"product_name": valid_product_name, "quantity": 1}],
        "items_to_remove": [],
    }

    result = await tool.ainvoke(args)
    assert result == f"Order {order_id} has been successfully updated with the requested changes."


@pytest.mark.asyncio(loop_scope="session")
async def test_change_order_not_found(setup_all_tools):
    user_id, order_id = 99999, 88888
    tool = await setup_all_tools("change_order")

    args = {"user_id": user_id, "order_id": order_id, "items_to_add": [{"product_name": "Any Product", "quantity": 1}]}

    result = await tool.ainvoke(args)
    assert result == f"could not find any orders with this order_id : {order_id} or user_id : {user_id}."


@pytest.mark.asyncio(loop_scope="session")
async def test_change_order_no_changes_requested(setup_all_tools, create_user, create_order, order_example):
    user_id, _ = create_user
    order_id = await create_order(user_id, order_example)
    tool = await setup_all_tools("change_order")

    args = {"user_id": user_id, "order_id": order_id, "items_to_add": [], "items_to_remove": []}

    result = await tool.ainvoke(args)
    assert result == "No changes requested by the user."


@pytest.mark.asyncio(loop_scope="session")
async def test_change_order_add_invalid_product(setup_all_tools, create_user, create_order, order_example):
    user_id, _ = create_user
    order_id = await create_order(user_id, order_example)
    tool = await setup_all_tools("change_order")

    args = {
        "user_id": user_id,
        "order_id": order_id,
        "items_to_add": [{"product_name": "Unknown_Add_Product", "quantity": 1}],
    }

    result = await tool.ainvoke(args)
    assert result == "Cannot add item. Product 'Unknown_Add_Product' was not found in our catalog."


@pytest.mark.asyncio(loop_scope="session")
async def test_change_order_remove_invalid_product(setup_all_tools, create_user, create_order, order_example):
    user_id, _ = create_user
    order_id = await create_order(user_id, order_example)
    tool = await setup_all_tools("change_order")

    args = {
        "user_id": user_id,
        "order_id": order_id,
        "items_to_remove": [{"product_name": "Unknown_Remove_Product", "quantity": 1}],
    }

    result = await tool.ainvoke(args)
    assert result == "Cannot remove item. Product 'Unknown_Remove_Product' was not found in our catalog."


@pytest.mark.asyncio(loop_scope="session")
async def test_change_order_modify_db_fails(setup_all_tools, db, create_user, create_order, order_example):
    user_id, _ = create_user
    order_id = await create_order(user_id, order_example)
    tool = await setup_all_tools("change_order")

    products = await db.get_all_products()
    valid_product_name = products[0]["product_name"]

    args = {
        "user_id": user_id,
        "order_id": order_id,
        "items_to_add": [{"product_name": valid_product_name, "quantity": 1}],
    }

    with patch.object(db, "modify_order_items", new_callable=AsyncMock) as mock_modify:
        mock_modify.return_value = (False, "Out of stock")
        result = await tool.ainvoke(args)
        assert result == f"Failed to update order {order_id}. Reason: Out of stock"
