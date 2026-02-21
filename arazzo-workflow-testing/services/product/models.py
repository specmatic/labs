from typing import Annotated

from pydantic import BaseModel, Strict
from pydantic.alias_generators import to_camel


class ProductInfo(BaseModel):
    name: Annotated[str, Strict]
    price: Annotated[float, Strict]
    inventory: Annotated[int, Strict]
    product_id: Annotated[int, Strict]

    class Config:
        alias_generator = to_camel
        populate_by_name = True
        from_attributes = True
