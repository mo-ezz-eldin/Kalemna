import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_create_product(db, create_product, product_example):

    product_id, product_details = await create_product(product_example)

    assert product_id > 0


@pytest.mark.asyncio(loop_scope="session")
async def test_get_product_by_id_success(db, create_product, product_example):

    product_id, product_details = await create_product(product_example)

    product = await db.get_product(product_id)

    assert product is not None


@pytest.mark.asyncio(loop_scope="session")
async def test_get_product_by_id_not_found(db):
    non_existing_id = 999999

    product = await db.get_product(non_existing_id)

    assert product is None


@pytest.mark.asyncio(loop_scope="session")
async def test_get_product_by_name(db, create_product, product_example):

    product_id, product_details = await create_product(product_example)

    not_found_name = "not_found_product"

    product_name_not_exist = await db.get_product_by_name(not_found_name)

    product_name = await db.get_product_by_name(product_details["name"])

    assert product_name is not None

    assert product_name_not_exist is None


@pytest.mark.asyncio(loop_scope="session")
async def test_get_all_products(db, create_product):

    first_product_details = {"name": "Pixel Pro Smartphone", "description": "desc1", "price": 799.99}

    second_product_details = {"name": "CloudStride Running Shoes", "description": "desc2", "price": 129.50}

    await create_product(first_product_details)

    await create_product(second_product_details)

    products = await db.get_all_products()

    assert len(products) == 2


@pytest.mark.asyncio(loop_scope="session")
async def test_update_product(db, create_product, product_example):

    product_id, product_details = await create_product(product_example)

    product_details["name"] = product_details["name"].upper()

    product_details["price"] = product_details["price"] + 1000

    new_product = {
        "product_name": product_details["name"],
        "description": product_details["description"],
        "price": product_details["price"],
    }

    await db.update_product(product_id, new_product)

    product = await db.get_product(product_id)

    assert product["product_name"] == product_details["name"]

    assert float(product["price"]) == product_details["price"]


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_product(db, create_product, product_example):
    product_id, product_details = await create_product(product_example)

    is_delete = await db.delete_product(product_id)

    assert is_delete is True

    deleted_product = await db.get_product(product_id)
    assert deleted_product is None
