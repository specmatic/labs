from typing import Annotated

from pydantic import BaseModel, Strict
from pydantic.alias_generators import to_camel


class OrderRequest(BaseModel):
    user_id: Annotated[int, Strict]
    product_id: Annotated[int, Strict]
    inventory: Annotated[int, Strict]

    class Config:
        alias_generator = to_camel
        populate_by_name = True
        from_attributes = True


class InventoryReserverRequest(BaseModel):
    order_id: Annotated[int, Strict]

    class Config:
        alias_generator = to_camel
        populate_by_name = True
        from_attributes = True


class OrderDeliveryRequest(BaseModel):
    order_id: Annotated[int, Strict]

    class Config:
        alias_generator = to_camel
        populate_by_name = True
        from_attributes = True
