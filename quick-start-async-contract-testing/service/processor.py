import json
import os
import time

from kafka import KafkaConsumer, KafkaProducer


BOOTSTRAP_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVER", "broker:9092")
INPUT_TOPIC = "new-orders"
OUTPUT_TOPIC = "wip-orders"
GROUP_ID = "quick-start-async-processor"


def create_consumer():
    return KafkaConsumer(
        INPUT_TOPIC,
        bootstrap_servers=[BOOTSTRAP_SERVER],
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id=GROUP_ID,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )


def create_producer():
    return KafkaProducer(
        bootstrap_servers=[BOOTSTRAP_SERVER],
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


def extract_header(headers, key):
    for header_key, header_value in headers:
        if header_key == key:
            return header_value.decode("utf-8") if header_value else ""
    return ""


def process_message(payload):
    total_amount = 0.0
    for item in payload.get("orderItems", []):
        quantity = item.get("quantity", 0)
        price = item.get("price", 0)
        total_amount += quantity * price

    return {
        "id": payload.get("id"),
        "totalAmount": round(total_amount, 2),
        # Intentional mismatch for the exercise. Should be INITIATED.
        "status": "STARTED",
    }


def main():
    while True:
        try:
            consumer = create_consumer()
            producer = create_producer()
            print(f"Connected to Kafka at {BOOTSTRAP_SERVER}")

            for message in consumer:
                correlation_id = extract_header(message.headers, "orderCorrelationId")
                response_payload = process_message(message.value)

                headers = [("orderCorrelationId", correlation_id.encode("utf-8"))] if correlation_id else []
                producer.send(OUTPUT_TOPIC, value=response_payload, headers=headers)
                producer.flush()

                print(
                    "Processed order",
                    message.value.get("id"),
                    "and produced response:",
                    response_payload,
                )
        except Exception as e:
            print(f"Processor error: {e}. Retrying in 2 seconds...")
            time.sleep(2)


if __name__ == "__main__":
    main()
