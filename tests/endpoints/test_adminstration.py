import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_add_product_success(client, db, product_example):

    response = await client.post("/add_product", json=product_example)

    assert response.status_code == 201

    product = await db.get_product_by_name(product_example["name"])

    assert product["product_name"] == product_example["name"]
    assert product["description"] == product_example["description"]
    assert float(product["price"]) == product_example["price"]


@pytest.mark.asyncio(loop_scope="session")
async def test_product_exist(client, product_example, create_product):
    product_id, product_details = await create_product(product_example)

    response = await client.post("/add_product", json=product_details)

    assert response.status_code == 409


@pytest.mark.asyncio(loop_scope="session")
async def test_get_all_products(client, create_product):
    first_product_details = {"name": "Pixel Pro Smartphone", "description": "desc1", "price": 799.99}

    second_product_details = {"name": "CloudStride Running Shoes", "description": "desc2", "price": 129.50}

    await create_product(first_product_details)
    await create_product(second_product_details)

    response = await client.get("/get_all_products")

    assert response.status_code == 200

    assert response.content is not None


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_product(client, db, create_product, product_example):
    product_id, details = await create_product(product_example)
    response = await client.delete(f"/delete_product/{product_id}")

    assert response.status_code == 200

    assert await db.get_product(product_id) is None


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_product_not_found(client):
    response = await client.delete(f"/delete_product/{7}")

    assert response.status_code == 404


@pytest.mark.asyncio(loop_scope="session")
async def test_update_product(client, create_product, product_example):
    await create_product(product_example)
    product_example["description"] = "this is a test product description"
    product_example["price"] = 34

    response = await client.put("/update_product", json=product_example)

    assert response.status_code == 200

    assert response.json() == {"message": f"Product {product_example['name']} updated successfully"}


@pytest.mark.asyncio(loop_scope="session")
async def test_update_product_not_found(client, product_example):
    product_example["description"] = "this is a test product description"
    product_example["price"] = 34

    response = await client.put("/update_product", json=product_example)

    assert response.status_code == 404
