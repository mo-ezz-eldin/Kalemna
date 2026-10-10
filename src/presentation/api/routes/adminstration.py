from fastapi import APIRouter, Depends, HTTPException, status

from src.domain.interfaces.IDatabase import IDatabase
from src.infrastructure.security.user_security_credentials import get_current_user
from src.presentation.api.dependency import get_db
from src.presentation.api.schemas import ProductSchema

db_management_router = APIRouter()


@db_management_router.post(
    "/add_product", status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)]
)
async def add_product(product_data: ProductSchema, db: IDatabase = Depends(get_db)):

    product = await db.get_product_by_name(product_data.name)
    if product:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product with that name already exists")

    product_id = await db.create_product(**product_data.model_dump())

    return {"message": f"New Product added successfully with ID {product_id}"}


@db_management_router.get("/get_all_products", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)])
async def get_all_products(db: IDatabase = Depends(get_db)):
    products = await db.get_all_products()

    return products


@db_management_router.put("/update_product", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)])
async def update_product(product_data: ProductSchema, db: IDatabase = Depends(get_db)):
    existing_product = await db.get_product_by_name(product_data.name)

    if existing_product:
        new_product = {
            "product_name": product_data.name,
            "description": product_data.description,
            "price": product_data.price,
        }
        await db.update_product(existing_product["product_id"], new_product)

        return {"message": f"Product {product_data.name} updated successfully"}

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")


@db_management_router.delete(
    "/delete_product/{product_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)]
)
async def delete_product(product_id: int, db: IDatabase = Depends(get_db)):
    is_deleted = await db.delete_product(product_id)

    if not is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {product_id} not found.")

    return {"message": f"Product with ID {product_id} deleted successfully"}
