import json
import logging

from sqlmodel import Session, select

from common.database import Database
from common.models import InventoryLevel, Order, OrderStatus, Product
from order.event_bus import Event, EventBus, EventType
from order.models import OrderDeliveryRequest, OrderRequest

logger = logging.getLogger("uvicorn.error")
database = Database()


def validate_product_information(product_id: int, quantity: int):
    with Session(database.engine) as session:
        product_exists = session.exec(select(Product).where(Product.product_id == product_id)).first()

    if not product_exists:
        msg = f"Product with id {product_id} not found"
        raise Exception(msg)

    with Session(database.engine) as session:
        inventory_level = session.exec(select(InventoryLevel).where(InventoryLevel.product_id == product_id)).first()

    if not inventory_level:
        msg = f"Product with id {product_id} is out of stock"
        raise Exception(msg)

    if inventory_level.inventory < quantity:
        msg = f"Product with id {product_id} is out of stock"
        raise Exception(msg)


def validate_order_request(order_request: dict) -> OrderRequest | None:
    try:
        order = OrderRequest.model_validate(order_request)
        validate_product_information(order.product_id, order.inventory)
    except Exception as e:
        print("Invalid Order Request, skipping:", e)
        return None
    else:
        return order


def validate_order_delivery(order_request: dict) -> OrderDeliveryRequest | None:
    try:
        order = OrderDeliveryRequest.model_validate(order_request)
    except Exception as e:
        print("Invalid Order Delivery Request, skipping:", e)
        return None
    else:
        return order


def place_order(correlation_id: str, order_request: OrderRequest) -> Order:
    order = Order(
        user_id=order_request.user_id,
        product_id=order_request.product_id,
        inventory=order_request.inventory,
        order_request_id=correlation_id,
    )

    with Session(database.engine) as session:
        session.add(order)
        session.commit()
        session.refresh(order)
    return order


def get_header(headers: list, key: str) -> str | None:
    if not headers:
        return None
    for k, v in headers:
        if k == key:
            val = v.decode("utf-8") if isinstance(v, bytes) else v
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return val
    return None


def handle_order_created(message, event_bus: EventBus) -> None:
    correlation_id = get_header(message.headers, "requestId")
    if not correlation_id:
        logger.error("Missing correlation ID in ORDER CREATION REQUEST")
        return

    order_request = validate_order_request(message.value)
    if not order_request:
        logger.error(f"Invalid ORDER CREATION REQUEST (CorrelationID: {correlation_id})")
        return

    logger.info(f"Received ORDER CREATION REQUEST (CorrelationID: {correlation_id})")
    order = place_order(correlation_id, order_request)
    event = Event(
        event_type=EventType.ORDER_PENDING,
        data={"orderId": order.order_id, "status": order.status.value},
        headers={"requestId": correlation_id},
    )

    success = event_bus.publish(event)
    if success:
        logger.info(f"Published ORDER WIP EVENT (CorrelationID: {correlation_id})")
    else:
        logger.error(f"Failed to publish ORDER WIP EVENT (CorrelationID: {correlation_id})")


def handle_order_delivery(message, event_bus: EventBus) -> None:
    correlation_id = get_header(message.headers, "requestId")
    if not correlation_id:
        logger.error("Missing correlation ID in ORDER CREATION REQUEST")
        return

    order_delivery_request = validate_order_delivery(message.value)
    if not order_delivery_request:
        logger.error(f"Invalid ORDER DELIVERY REQUEST (CorrelationID: {correlation_id})")
        return

    with Session(database.engine) as session:
        order = session.exec(
            select(Order).where(
                Order.order_id == order_delivery_request.order_id,
                Order.order_request_id == correlation_id,
            ),
        ).first()
        if not order:
            logger.error(f"Order with order ID {order_delivery_request.order_id} and correlation ID {correlation_id} not found")
            return

        order.status = OrderStatus.OUT_FOR_DELIVERY
        session.add(order)
        session.commit()

    logger.info(f"Marked order {order_delivery_request.order_id} as {OrderStatus.OUT_FOR_DELIVERY} (CorrelationID: {correlation_id})")


def setup_event_handlers(event_bus: EventBus) -> None:
    event_bus.subscribe(EventType.ORDER_CREATED, handle_order_created)
    event_bus.subscribe(EventType.ORDER_DELIVERY, handle_order_delivery)
    logger.info("✅ All event handlers registered")
