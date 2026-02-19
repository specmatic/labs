import json
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable

from common.config import Settings
from common.singleton import SingletonMeta

logger = logging.getLogger("uvicorn.error")


class EventType(str, Enum):
    ORDER_CREATED = "order.created"
    ORDER_PENDING = "order.pending"
    ORDER_ACCEPTED = "order.accepted"
    ORDER_DELIVERY = "order.delivery"


@dataclass
class Event:
    event_type: EventType
    data: dict
    headers: dict | None = None


class EventBus(metaclass=SingletonMeta):
    TOPICS: ClassVar[dict[EventType, str]] = {
        EventType.ORDER_CREATED: "new-orders",
        EventType.ORDER_PENDING: "wip-orders",
        EventType.ORDER_ACCEPTED: "accepted-orders",
        EventType.ORDER_DELIVERY: "out-for-delivery-orders",
    }

    def __init__(self):
        self.producer = None
        self.settings = Settings()
        self.consumers: dict[EventType, KafkaConsumer] = {}
        self.handlers: dict[EventType, list[Callable]] = {}
        self._consumer_threads: dict[EventType, threading.Thread] = {}
        self._connect()

    def _connect(self):
        retries = 0
        max_retries = 15
        while retries < max_retries:
            try:
                logger.info(f"Attempting to connect to Kafka (Attempt {retries + 1})...")
                self.producer = KafkaProducer(
                    bootstrap_servers=self.settings.kafka_bootstrap_servers.split(","),
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    api_version_auto_timeout_ms=2000,
                )
                logger.info("Successfully connected to Kafka!")
                return
            except NoBrokersAvailable:
                retries += 1
                logger.info(f"Kafka not ready. Retrying in 2 seconds... ({retries}/{max_retries})")
                time.sleep(2)
            except Exception as e:
                logger.info(f"Unexpected Kafka error: {e}")
                time.sleep(2)
                retries += 1

        raise Exception("Failed to connect to Kafka after multiple attempts")

    def publish(self, event: Event) -> bool:
        if not self.producer:
            logger.error("Kafka producer unavailable")
            return False

        try:
            topic = self.TOPICS[event.event_type]
            kafka_headers = []
            if event.headers:
                kafka_headers = [
                    (k, str(v).encode("utf-8") if not isinstance(v, bytes) else v) for k, v in event.headers.items()
                ]
            self.producer.send(topic, value=event.data, headers=kafka_headers)
            self.producer.flush()
            logger.info(f"Published {event.event_type} to {topic}")
            return True
        except KeyError:
            logger.error(f"Unknown event type: {event.event_type}")
            return False
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False

    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        if event_type not in self.handlers:
            self.handlers[event_type] = []

        self.handlers[event_type].append(handler)
        logger.debug(f"Handler registered for {event_type}")

    def start_consumer(self, event_type: EventType) -> None:
        if not self.producer:
            logger.warning("Kafka unavailable, skipping consumer")
            return

        if event_type in self.consumers:
            logger.debug(f"Consumer already started for {event_type}")
            return

        thread = threading.Thread(
            target=self._consume_events,
            args=(event_type,),
            daemon=True,
            name=f"consumer-{event_type}",
        )
        self._consumer_threads[event_type] = thread
        thread.start()

    def _consume_events(self, event_type: EventType) -> None:
        topic = self.TOPICS[event_type]
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.settings.kafka_bootstrap_servers.split(","),
                value_deserializer=self.safe_json_deserializer,
                auto_offset_reset="earliest",
                group_id=self.settings.kafka_consumer_group,
            )

            self.consumers[event_type] = consumer
            logger.info(f"Started consuming from {topic}")

            for message in consumer:
                self._invoke_handlers(event_type, message)

        except Exception as e:
            logger.error(f"Consumer error for {event_type}: {e}")
        finally:
            if event_type in self.consumers:
                self.consumers[event_type].close()
                del self.consumers[event_type]

    def _invoke_handlers(self, event_type: EventType, message) -> None:
        logger.debug(
            f"Message received for {event_type}: key={message.key} value={message.value}, headers={message.headers}"
        )
        handlers = self.handlers.get(event_type, [])

        if not handlers:
            logger.debug(f"No handlers for {event_type}")
            return

        for handler in handlers:
            try:
                handler(message, self)
            except Exception as e:
                logger.error(f"Handler failed for {event_type}: {e}", exc_info=True)

    def stop(self) -> None:
        if self.producer:
            self.producer.close()
            logger.info("Producer closed")

        for event_type, consumer in self.consumers.items():
            consumer.close()
            logger.debug(f"Consumer closed for {event_type}")

        for event_type, thread in self._consumer_threads.items():
            thread.join(timeout=5)
            logger.debug(f"Consumer thread stopped for {event_type}")

        self.consumers.clear()
        self._consumer_threads.clear()

    @staticmethod
    def safe_json_deserializer(message: bytes | None):
        if message is None:
            return None
        content = message.decode("utf-8")
        if not content.strip():
            return None
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON payload: %r", content)
            return None
