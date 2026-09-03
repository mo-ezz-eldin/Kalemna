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
    async def get_order(self, user_id , order_id: int) -> Optional[Dict[str, Any]]:
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
    async def get_invoice_details(self, user_id : int ,order_id: int) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_refund_status(self, user_id : int , order_id: int) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def create_ticket(self, user_id: int, issue_type: str, order_id: Optional[int] = None) -> int:
        pass

    @abstractmethod
    async def setup_db(self):
        pass
    @abstractmethod
    async def create_user(self,user_details : Dict):
        pass

    @abstractmethod
    async def create_order_items(self  , order_id :int , product_id : int ,quantity: int, unit_price: float ):
        pass

    @abstractmethod
    async def delete_order_item(self , order_id : int  , product_id : int):
        pass
    @abstractmethod
    async def create_product(self ,description : str  , price : float ):
        pass

    @abstractmethod
    async def get_product(self ,product_id : int):
        pass
    @abstractmethod
    async def update_product(self , product_id : int , product_details : Dict):
        pass

    @abstractmethod
    async def delete_product(self ,product_id : int):
        pass

    @abstractmethod
    async def get_all_products(self):
        pass

    @abstractmethod
    async def get_product_by_name(self, product_name: str):
        pass


    @abstractmethod
    async def delete_order(self, user_id : int , order_id: int)->bool:
        pass

    @abstractmethod
    async def delete_order_items(self , order_id : int)->bool:
        pass

    @abstractmethod
    async def modify_order_items(self, order_id: int, items_to_add: List[Dict[str, Any]],
                                 removed_product_ids: List[int]) -> tuple[bool, str]:
        pass