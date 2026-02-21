from typing import Annotated

from fastapi import APIRouter, Query
from sqlmodel import select

from common.models import Product
from product import SessionDep
from product.models import ProductInfo

products_router = APIRouter()


@products_router.get("/products", response_model=list[ProductInfo])
async def get_location(session: SessionDep, location_code: Annotated[str, Query(alias="locationCode", strict=True)]):
    statement = select(Product).where(Product.location_code == location_code)
    products = session.exec(statement).all()
    return [
        ProductInfo.model_validate(
            {"name": p.name, "price": p.price, "product_id": p.product_id, "inventory": p.inventory_levels.inventory},
        )
        for p in products
    ]
