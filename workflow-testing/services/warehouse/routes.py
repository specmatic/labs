from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import select

from common.config import Settings
from common.models import InventoryLevel, Order, Product
from warehouse import SessionDep

warehouse_router = APIRouter()
settings = Settings()


@warehouse_router.put("/inventory", status_code=status.HTTP_200_OK)
async def update_inventory(order_id: Annotated[int, Query(alias="orderId")], session: SessionDep):
    order = session.exec(select(Order).where(Order.order_id == order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    product = session.exec(select(Product).where(Product.product_id == order.product_id)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    inventory_level = session.exec(
        select(InventoryLevel).where(InventoryLevel.product_id == product.product_id)
    ).first()
    if not inventory_level or inventory_level.inventory < order.inventory:
        raise HTTPException(status_code=404, detail="Product out of stock")

    inventory_level.inventory -= order.inventory
    session.add(inventory_level)
    session.commit()
    await notify_order_placed(order_id)


async def notify_order_placed(order_id: int):
    url = f"http://order:{settings.order_service_port}/orders"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json={"order_id": order_id})
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=400, detail=f"Order service rejected request: {e.response.text}") from e
        except httpx.RequestError as e:
            raise HTTPException(status_code=400, detail=f"Failed to connect to order service: {e!s}") from e
