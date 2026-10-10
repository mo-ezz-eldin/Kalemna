from abc import ABC, abstractmethod
from typing import Any


class IDatabase(ABC):
    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def return_engine(self):
        pass

    @abstractmethod
    async def get_user_by_username(self, username: str) -> dict | None:
        pass

    @abstractmethod
    async def get_user(self, user_id: int) -> dict[str, Any] | None:
        pass

    @abstractmethod
    async def create_order(self, user_id: int, order_data: dict[str, Any]) -> int:
        pass

    @abstractmethod
    async def get_order(self, user_id, order_id: int) -> dict[str, Any] | None:
        pass

    @abstractmethod
    async def get_orders_by_user(self, user_id: int) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def update_order_status(self, order_id: int, new_status: str) -> bool:
        pass

    @abstractmethod
    async def update_shipping_address(self, order_id: int, new_address: str) -> bool:
        pass

    @abstractmethod
    async def get_invoice_details(self, user_id: int, order_id: int) -> dict[str, Any] | None:
        pass

    @abstractmethod
    async def get_refund_status(self, user_id: int, order_id: int) -> dict[str, Any] | None:
        pass

    @abstractmethod
    async def create_ticket(self, user_id: int, issue_type: str, order_id: int | None = None) -> int:
        pass

    @abstractmethod
    async def setup_db(self):
        pass

    @abstractmethod
    async def drop_db(self):
        pass

    @abstractmethod
    async def create_user(self, user_details: dict):
        pass

    @abstractmethod
    async def create_order_items(self, order_id: int, product_id: int, quantity: int, unit_price: float):
        pass

    @abstractmethod
    async def delete_order_item(self, order_id: int, product_id: int):
        pass

    @abstractmethod
    async def create_product(self, name: str, description: str, price: float):
        pass

    @abstractmethod
    async def get_product(self, product_id: int):
        pass

    @abstractmethod
    async def update_product(self, product_id: int, product_details: dict):
        pass

    @abstractmethod
    async def delete_product(self, product_id: int) -> bool:
        pass

    @abstractmethod
    async def get_all_products(self):
        pass

    @abstractmethod
    async def get_product_by_name(self, product_name: str):
        pass

    @abstractmethod
    async def delete_order(self, user_id: int, order_id: int) -> bool:
        pass

    @abstractmethod
    async def delete_order_items(self, order_id: int) -> bool:
        pass

    @abstractmethod
    async def modify_order_items(
        self, order_id: int, items_to_add: list[dict[str, Any]], removed_product_list: list[dict[str, Any]]
    ) -> tuple[bool, str]:
        pass
