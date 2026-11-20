from fastapi import APIRouter, HTTPException, Response, status
from sqlmodel import select

from common.models import Order, OrderStatus
from order import KafkaDep, SessionDep
from order.event_bus import Event, EventType
from order.models import InventoryReserverRequest, OrderResponse

order_routes = APIRouter()


@order_routes.post("/orders", status_code=status.HTTP_200_OK)
async def inventory_reserver(request: InventoryReserverRequest, session: SessionDep, event_bus: KafkaDep) -> Response:
    order = session.exec(select(Order).where(Order.order_id == request.order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Order is not in pending state")

    order.status = OrderStatus.ACCEPTED
    session.add(order)
    session.commit()

    event = Event(
        event_type=EventType.ORDER_ACCEPTED,
        data={"status": order.status.value},
        headers={"requestId": order.order_request_id},
    )
    event_bus.publish(event)
    return Response(status_code=status.HTTP_200_OK)


@order_routes.get("/orders/{order_id}", status_code=status.HTTP_200_OK, response_model=OrderResponse)
async def get_order(order_id: int, session: SessionDep):
    order = session.exec(select(Order).where(Order.order_id == order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order
