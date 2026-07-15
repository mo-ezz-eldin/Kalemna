from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class IDatabase(ABC):

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def create_order(self, user_id: int, order_data: Dict[str, Any]) -> int:
        pass

    @abstractmethod
    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_orders_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def update_order_status(self, order_id: int, new_status: str) -> bool:
        pass

    @abstractmethod
    async def update_shipping_address(self, order_id: int, new_address: str) -> bool:
        pass

    @abstractmethod
    async def get_invoice_details(self, order_id: int) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_refund_status(self, order_id: int) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def create_ticket(self, user_id: int, issue_type: str, order_id: Optional[int] = None) -> int:
        pass