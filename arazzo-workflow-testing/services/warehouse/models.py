from typing import Annotated

from pydantic import BaseModel, Strict
from pydantic.alias_generators import to_camel


class ProductInventory(BaseModel):
    order_id: Annotated[int, Strict]

    class Config:
        alias_generator = to_camel
        populate_by_name = True
        from_attributes = True
