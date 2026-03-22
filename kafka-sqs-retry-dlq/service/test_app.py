import json
import unittest

from app import BridgeApplication, MessageTransformationException, MessageTransformer


class MessageTransformerTest(unittest.TestCase):
    def test_standard_order_becomes_wip(self):
        transformer = MessageTransformer()
        message = json.dumps(
            {
                "orderType": "STANDARD",
                "orderId": "ORD-1",
                "customerId": "CUST-1",
                "items": [{"productId": "PROD-1", "quantity": 1, "price": 10.0}],
                "totalAmount": 10.0,
                "orderDate": "2026-01-19T10:00:00Z",
            }
        )

        result = json.loads(transformer.transform_message(message))

        self.assertEqual("ORD-1", result["orderId"])
        self.assertEqual(1, result["itemsCount"])
        self.assertEqual("WIP", result["status"])

    def test_fail_once_order_succeeds_on_second_attempt(self):
        transformer = MessageTransformer(fail_once_order_ids=["ORD-RETRY-90001"])
        message = json.dumps(
            {
                "orderType": "STANDARD",
                "orderId": "ORD-RETRY-90001",
                "customerId": "CUST-1",
                "items": [{"productId": "PROD-1", "quantity": 1, "price": 10.0}],
                "totalAmount": 10.0,
                "orderDate": "2026-01-19T10:00:00Z",
            }
        )

        with self.assertRaises(MessageTransformationException):
            transformer.transform_message(message)

        result = json.loads(transformer.transform_message(message))

        self.assertEqual("WIP", result["status"])

    def test_backoff_is_capped(self):
        self.assertEqual(1000, BridgeApplication.calculate_backoff(0))
        self.assertEqual(2000, BridgeApplication.calculate_backoff(1))
        self.assertEqual(30000, BridgeApplication.calculate_backoff(8))


if __name__ == "__main__":
    unittest.main()
