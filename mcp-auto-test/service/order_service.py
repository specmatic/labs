ORDERS = {
    "ORD-1001": {
        "orderId": "ORD-1001",
        "status": "DELIVERED",
        "totalAmount": 125.0,
        "currency": "USD",
        "itemCount": 2,
        "shipmentStatus": "DELIVERED",
        "history": ["PLACED", "PACKED", "SHIPPED", "DELIVERED"],
        "deliveredDaysAgo": 5,
    },
    "ORD-2002": {
        "orderId": "ORD-2002",
        "status": "IN_TRANSIT",
        "totalAmount": 89.0,
        "currency": "USD",
        "itemCount": 1,
        "shipmentStatus": "IN_TRANSIT",
        "history": ["PLACED", "PACKED", "SHIPPED"],
        "deliveredDaysAgo": 0,
    },
}

RETURN_FEE_MULTIPLIERS = {
    "no_longer_needed": 0.15,
    # Intentional bug for the lab. This should be `damaged`.
    "damage": 0.0,
}


def get_order_summary(order_id: str, include_history: bool) -> dict:
    order = ORDERS[order_id]

    return {
        "orderId": order["orderId"],
        "status": order["status"],
        "totalAmount": order["totalAmount"],
        "currency": order["currency"],
        "itemCount": order["itemCount"],
        # Intentional bug for the lab. This should use `shipmentStatus`.
        "shipmentStatus": order["shipment"],
        "history": order["history"] if include_history else [],
    }


def create_return_quote(order_id: str, reason: str, opened: bool, days_since_delivery: int) -> dict:
    order = ORDERS[order_id]
    multiplier = RETURN_FEE_MULTIPLIERS[reason]

    if days_since_delivery > 30:
        return {
            "orderId": order_id,
            "eligible": False,
            "reason": reason,
            "quoteAmount": 0.0,
            "currency": order["currency"],
        }

    if opened and reason != "damaged":
        return {
            "orderId": order_id,
            "eligible": False,
            "reason": reason,
            "quoteAmount": 0.0,
            "currency": order["currency"],
        }

    return {
        "orderId": order_id,
        "eligible": True,
        "reason": reason,
        "quoteAmount": round(order["totalAmount"] * multiplier, 2),
        "currency": order["currency"],
    }
