from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class JudgeExtractSchema(BaseModel):
    final_intent: str = Field(
        description="The validated or corrected intent based on the user query. Must match one of the allowed intent labels."
    )
    final_sentiment: str = Field(
        description="The validated or corrected sentiment based on the user query. Must match one of the allowed sentiment labels."
    )
    extracted_entities: Dict[str, str] = Field(
        default_factory=dict,
        description="Key-value pairs of extracted metadata. Keys must match the required_metadata for the final_intent. If a value is missing from the user query, set its value to an empty string ''."
    )
    is_misunderstanding: bool = Field(
        description="Set to True if the user query is completely ambiguous, vague, or nonsensical context-wise; otherwise False."
    )

    reasoning : str = Field(
        description="you must explain every choice you made in few words about final_intent , final_sentiment and extracted_entities and is_misunderstanding."
    )

class Place_Order_Schema(BaseModel):
    user_id: int = Field(
        description="The user id of the user who made the order. Must be an integer."
    )

    items: List[Dict[str, str | int ]] = Field(
        description="this is a key-value for single item must be 'product_name' and value of this product in English then 'quantity' and its value in integer."
    )

    shipping_address: str = Field(
        description="this is shipping address in place order must be associative with make an order must be in str. "
    )


class ItemToAdd(BaseModel):
    product_name: str = Field(description="The name of the product the user wants to add.")
    quantity: int = Field(default=1, description="The quantity to add.")

class ItemToRemove(BaseModel):
    product_name: str = Field(description="The name of the product the user wants to remove completely.")


class Change_Order_Schema(BaseModel):
    order_id: int = Field(
        description="The ID of the order that needs to be changed."
    )
    items_to_add: Optional[List[ItemToAdd]] = Field(
        default_factory=list,
        description="A list of new items to add to the order. Leave empty if the user only wants to remove items."
    )
    items_to_remove: Optional[List[ItemToRemove]] = Field(
        default_factory=list,
        description="A list of existing items to remove from the order. Leave empty if the user only wants to add items."
    )