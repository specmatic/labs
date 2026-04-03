import json
import logging
import os
import threading
import time
import traceback
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import boto3
from kafka import KafkaConsumer, KafkaProducer


CORRELATION_ID_HEADER = "CorrelationId"


class MessageTransformationException(Exception):
    pass


class DirectToDlqMessageTransformationException(MessageTransformationException):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def csv_setting(name: str, default: list[str] | None = None) -> list[str]:
    value = os.getenv(name, "")
    if not value:
        return list(default or [])
    return [item.strip() for item in value.split(",") if item.strip()]


def bool_setting(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() == "true"


@dataclass
class AppConfig:
    kafka_topic: str
    sqs_queue_url: str
    retry_topic: str
    dlq_topic: str
    max_retries: int
    sqs_endpoint: str
    kafka_bootstrap_servers: str
    enable_test_failure_scenarios: bool
    fail_once_order_ids: list[str]
    always_fail_order_ids: list[str]
    direct_dlq_order_ids: list[str]
    kafka_main_group_id: str
    kafka_retry_group_id: str
    sqs_send_delay_ms: int
    sqs_visibility_timeout_seconds: int
    ready_file: str
    startup_timeout_seconds: int

    @classmethod
    def load(cls) -> "AppConfig":
        enable_test_failure_scenarios = bool_setting("ENABLE_TEST_FAILURE_SCENARIOS")
        default_fail_once_ids = ["ORD-RETRY-90001"] if enable_test_failure_scenarios else []
        default_always_fail_ids = ["ORD-DLQ-90001"] if enable_test_failure_scenarios else []
        default_direct_dlq_ids = ["ORD-RECEIVE-DLQ-90001"] if enable_test_failure_scenarios else []

        return cls(
            kafka_topic=os.getenv("KAFKA_TOPIC", "place-order-topic"),
            sqs_queue_url=os.getenv(
                "SQS_QUEUE_URL",
                "http://localstack:4566/000000000000/place-order-queue",
            ),
            retry_topic=os.getenv("RETRY_TOPIC", "place-order-retry-topic"),
            dlq_topic=os.getenv("DLQ_TOPIC", "place-order-dlq-topic"),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            sqs_endpoint=os.getenv("SQS_ENDPOINT", "http://localstack:4566"),
            kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            enable_test_failure_scenarios=enable_test_failure_scenarios,
            fail_once_order_ids=csv_setting("FAIL_ONCE_ORDER_IDS", default_fail_once_ids),
            always_fail_order_ids=csv_setting("ALWAYS_FAIL_ORDER_IDS", default_always_fail_ids),
            direct_dlq_order_ids=csv_setting("DIRECT_DLQ_ORDER_IDS", default_direct_dlq_ids),
            kafka_main_group_id=os.getenv("KAFKA_MAIN_GROUP_ID", "kafka-to-sqs-bridge-group"),
            kafka_retry_group_id=os.getenv("KAFKA_RETRY_GROUP_ID", "retry-consumer-group"),
            sqs_send_delay_ms=int(os.getenv("SQS_SEND_DELAY_MS", "0")),
            sqs_visibility_timeout_seconds=int(os.getenv("SQS_VISIBILITY_TIMEOUT_SECONDS", "600")),
            ready_file=os.getenv("READY_FILE", "/tmp/provider-ready"),
            startup_timeout_seconds=int(os.getenv("STARTUP_TIMEOUT_SECONDS", "60")),
        )


class MessageTransformer:
    def __init__(
        self,
        fail_once_order_ids: Iterable[str] | None = None,
        always_fail_order_ids: Iterable[str] | None = None,
        direct_dlq_order_ids: Iterable[str] | None = None,
    ) -> None:
        self.fail_once_order_ids = set(fail_once_order_ids or [])
        self.always_fail_order_ids = set(always_fail_order_ids or [])
        self.direct_dlq_order_ids = set(direct_dlq_order_ids or [])
        self.retry_attempts: dict[str, int] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def transform_message(self, message_body: str) -> str:
        try:
            order_message = json.loads(message_body)
            order_id = self.extract_message_key(order_message)

            if order_id in self.direct_dlq_order_ids:
                raise DirectToDlqMessageTransformationException(
                    f"Simulated non-retryable transformation failure for order: {order_id}"
                )

            if order_id in self.fail_once_order_ids:
                attempts = self.retry_attempts.get(order_id, 0) + 1
                self.retry_attempts[order_id] = attempts
                if attempts == 1:
                    raise MessageTransformationException(
                        f"Simulated transformation failure for order: {order_id} (first attempt)"
                    )
                self.logger.info("Order %s succeeded on retry attempt %s", order_id, attempts)
                self.fail_once_order_ids.discard(order_id)

            if order_id in self.always_fail_order_ids:
                raise MessageTransformationException(
                    f"Simulated transformation failure for order: {order_id}"
                )

            transformed_message = self._transform(order_message)
            return json.dumps(transformed_message)
        except MessageTransformationException:
            raise
        except Exception as exc:
            raise MessageTransformationException("Failed to transform message") from exc

    def _transform(self, order_message: dict) -> dict:
        order_type = order_message["orderType"]

        if order_type == "STANDARD":
            return {
                "orderId": order_message["orderId"],
                "itemsCount": len(order_message.get("items", [])),
                "status": "WIP",
                "processingStartedAt": now_iso(),
            }

        if order_type == "PRIORITY":
            return {
                "orderId": order_message["orderId"],
                "itemsCount": len(order_message.get("items", [])),
                "status": "DELIVERED",
                "deliveredAt": now_iso(),
                "deliveryLocation": "Delivery location from logistics system",
            }

        if order_type == "BULK":
            total_items_count = sum(len(order.get("items", [])) for order in order_message.get("orders", []))
            return {
                "batchId": order_message["batchId"],
                "itemsCount": total_items_count,
                "status": "COMPLETED",
                "completedAt": now_iso(),
                "customerConfirmation": True,
            }

        raise MessageTransformationException(f"Unsupported orderType: {order_type}")

    def extract_message_key(self, order_message: dict) -> str:
        if order_message.get("orderType") == "BULK":
            return order_message.get("batchId", "unknown")
        return order_message.get("orderId", "unknown")

    def extract_message_key_from_json(self, message_body: str) -> str:
        try:
            return self.extract_message_key(json.loads(message_body))
        except Exception:
            return "unknown"


def header_value(headers: list[tuple[str, bytes]] | None, key: str) -> str | None:
    for header_key, header_value_bytes in headers or []:
        if header_key == key and header_value_bytes:
            return header_value_bytes.decode("utf-8")
    return None


def correlation_id_from(headers: list[tuple[str, bytes]] | None) -> str:
    return header_value(headers, CORRELATION_ID_HEADER) or str(uuid.uuid4())


def correlation_headers(correlation_id: str) -> list[tuple[str, bytes]]:
    return [(CORRELATION_ID_HEADER, correlation_id.encode("utf-8"))]


def sqs_correlation_attributes(correlation_id: str) -> dict:
    return {
        CORRELATION_ID_HEADER: {
            "StringValue": correlation_id,
            "DataType": "String",
        }
    }


class BridgeApplication:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig.load()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.transformer = MessageTransformer(
            fail_once_order_ids=self.config.fail_once_order_ids,
            always_fail_order_ids=self.config.always_fail_order_ids,
            direct_dlq_order_ids=self.config.direct_dlq_order_ids,
        )
        self.running = threading.Event()
        self.running.set()
        self.ready_file = Path(self.config.ready_file)
        self.threads: list[threading.Thread] = []
        self.producer: KafkaProducer | None = None
        self.main_consumer: KafkaConsumer | None = None
        self.retry_consumer: KafkaConsumer | None = None
        self.sqs_client = boto3.client(
            "sqs",
            endpoint_url=self.config.sqs_endpoint,
            region_name="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )

    def log_configuration(self) -> None:
        self.logger.info("=" * 60)
        self.logger.info("Python Kafka to SQS Bridge with Retry & DLQ")
        self.logger.info("=" * 60)
        self.logger.info("Kafka Topic (Input): %s", self.config.kafka_topic)
        self.logger.info("SQS Queue URL (Output): %s", self.config.sqs_queue_url)
        self.logger.info("Retry Topic: %s", self.config.retry_topic)
        self.logger.info("DLQ Topic: %s", self.config.dlq_topic)
        self.logger.info("Max Retries: %s", self.config.max_retries)
        self.logger.info("SQS Visibility Timeout Seconds: %s", self.config.sqs_visibility_timeout_seconds)
        self.logger.info("Startup Timeout Seconds: %s", self.config.startup_timeout_seconds)
        self.logger.info("Kafka Bootstrap Servers: %s", self.config.kafka_bootstrap_servers)
        self.logger.info(
            "Test Failure Scenarios Enabled: %s",
            self.config.enable_test_failure_scenarios,
        )
        self.logger.info("=" * 60)

    def create_consumer(self, topic: str, group_id: str) -> KafkaConsumer:
        return KafkaConsumer(
            topic,
            bootstrap_servers=[self.config.kafka_bootstrap_servers],
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            group_id=group_id,
            consumer_timeout_ms=1000,
            value_deserializer=lambda value: value.decode("utf-8"),
            key_deserializer=lambda value: value.decode("utf-8") if value else None,
        )

    def create_producer(self) -> KafkaProducer:
        return KafkaProducer(
            bootstrap_servers=[self.config.kafka_bootstrap_servers],
            acks="all",
            retries=3,
            value_serializer=lambda value: value.encode("utf-8"),
            key_serializer=lambda value: value.encode("utf-8") if value else None,
        )

    def start(self) -> None:
        self._clear_ready_file()
        self._initialize_dependencies()

        self.threads = [
            threading.Thread(target=self._run_main_bridge, name="MainBridge", daemon=True),
            # Lab fix: uncomment the retry consumer to process messages from place-order-retry-topic and complete the retry/DLQ flow.
            # threading.Thread(target=self._run_retry_consumer, name="RetryConsumer", daemon=True),
        ]

        for thread in self.threads:
            thread.start()

        self._mark_ready()

        while self.running.is_set():
            time.sleep(1)

    def _initialize_dependencies(self) -> None:
        deadline = time.monotonic() + self.config.startup_timeout_seconds
        last_error: Exception | None = None

        while time.monotonic() < deadline and self.running.is_set():
            try:
                self.producer = self.create_producer()
                self.main_consumer = self.create_consumer(self.config.kafka_topic, self.config.kafka_main_group_id)
                self.retry_consumer = self.create_consumer(self.config.retry_topic, self.config.kafka_retry_group_id)

                self._wait_for_kafka()
                self.sqs_client.set_queue_attributes(
                    QueueUrl=self.config.sqs_queue_url,
                    Attributes={"VisibilityTimeout": str(self.config.sqs_visibility_timeout_seconds)},
                )
                return
            except Exception as exc:
                last_error = exc
                self.logger.warning("Provider dependencies are not ready yet: %s", exc)
                self._close_kafka_clients()
                time.sleep(2)

        raise RuntimeError("Provider failed to initialize dependencies") from last_error

    def _wait_for_kafka(self) -> None:
        assert self.producer is not None
        assert self.main_consumer is not None
        assert self.retry_consumer is not None

        if not self.producer.bootstrap_connected():
            raise RuntimeError("Kafka producer is not connected")

        self.main_consumer.topics()
        self.retry_consumer.topics()

    def _mark_ready(self) -> None:
        self.ready_file.write_text("ready\n", encoding="utf-8")

    def _clear_ready_file(self) -> None:
        self.ready_file.unlink(missing_ok=True)

    def _close_kafka_clients(self) -> None:
        for consumer in (self.main_consumer, self.retry_consumer):
            if consumer is not None:
                consumer.close()
        self.main_consumer = None
        self.retry_consumer = None

        if self.producer is not None:
            self.producer.close()
        self.producer = None

    def stop(self) -> None:
        self.running.clear()
        self._clear_ready_file()
        if self.producer is not None:
            self.producer.flush()
        self._close_kafka_clients()
        for thread in self.threads:
            thread.join(timeout=5)

    def _run_main_bridge(self) -> None:
        assert self.main_consumer is not None
        while self.running.is_set():
            try:
                batches = self.main_consumer.poll(timeout_ms=1000, max_records=10)
                if not batches:
                    continue

                for records in batches.values():
                    for record in records:
                        self._process_main_record(record)

                self.main_consumer.commit()
            except Exception:
                if self.running.is_set():
                    self.logger.exception("Error processing main topic messages")
                    time.sleep(2)

    def _run_retry_consumer(self) -> None:
        assert self.retry_consumer is not None
        while self.running.is_set():
            try:
                batches = self.retry_consumer.poll(timeout_ms=1000, max_records=10)
                if not batches:
                    continue

                for records in batches.values():
                    for record in records:
                        self._process_retry_record(record)

                self.retry_consumer.commit()
            except Exception:
                if self.running.is_set():
                    self.logger.exception("Error processing retry topic messages")
                    time.sleep(2)

    def _process_main_record(self, record) -> None:
        correlation_id = correlation_id_from(record.headers)
        message_body = record.value

        try:
            transformed_message = self.transformer.transform_message(message_body)
            message_key = self.transformer.extract_message_key_from_json(message_body)
            self.send_to_sqs(transformed_message, message_key, correlation_id)
            self.logger.info("Forwarded message to SQS for key %s", message_key)
        except DirectToDlqMessageTransformationException as exc:
            self.logger.warning("Direct DLQ for key %s", record.key)
            self.send_to_dlq(message_body, 0, correlation_id, exc)
        except MessageTransformationException as exc:
            self.logger.warning("Retrying message for key %s", record.key)
            self.send_to_retry_topic(message_body, 0, None, correlation_id, exc)

    def _process_retry_record(self, record) -> None:
        retryable_message = json.loads(record.value)
        correlation_id = correlation_id_from(record.headers)
        retry_count = retryable_message["retryCount"]
        delay_ms = self.calculate_backoff(retry_count)
        time.sleep(delay_ms / 1000)

        if retry_count >= self.config.max_retries:
            self.logger.warning(
                "Max retries exceeded for %s, routing to DLQ",
                retryable_message["messageKey"],
            )
            self.send_retryable_to_dlq(retryable_message, correlation_id)
            return

        try:
            transformed_message = self.transformer.transform_message(
                json.dumps(retryable_message["originalMessage"])
            )
            self.send_to_sqs(
                transformed_message,
                retryable_message["messageKey"],
                correlation_id,
            )
            self.logger.info(
                "Retry succeeded for %s on attempt %s",
                retryable_message["messageKey"],
                retry_count + 1,
            )
        except MessageTransformationException as exc:
            self.send_back_to_retry_topic(retryable_message, correlation_id, exc)
        except Exception as exc:
            self.send_back_to_retry_topic(retryable_message, correlation_id, exc)

    def send_to_sqs(self, message: str, message_key: str, correlation_id: str) -> None:
        if self.config.sqs_send_delay_ms > 0:
            time.sleep(self.config.sqs_send_delay_ms / 1000)

        request = {
            "QueueUrl": self.config.sqs_queue_url,
            "MessageBody": message,
            "MessageAttributes": sqs_correlation_attributes(correlation_id),
        }

        if self.config.sqs_queue_url.endswith(".fifo"):
            request["MessageGroupId"] = message_key

        self.sqs_client.send_message(**request)

    def send_to_retry_topic(
        self,
        original_message: str,
        current_retry_count: int,
        first_attempt_timestamp: str | None,
        correlation_id: str,
        error: Exception,
    ) -> None:
        assert self.producer is not None
        original_message_object = json.loads(original_message)
        message_key = self.transformer.extract_message_key_from_json(original_message)
        timestamp = now_iso()
        retryable_message = {
            "originalMessage": original_message_object,
            "messageKey": message_key,
            "retryCount": current_retry_count,
            "firstAttemptTimestamp": first_attempt_timestamp or timestamp,
            "lastAttemptTimestamp": timestamp,
            "errorMessage": str(error),
            "errorStackTrace": traceback.format_exc(),
        }
        self.producer.send(
            self.config.retry_topic,
            key=message_key,
            value=json.dumps(retryable_message),
            headers=correlation_headers(correlation_id),
        ).get(timeout=10)

    def send_back_to_retry_topic(
        self,
        retryable_message: dict,
        correlation_id: str,
        error: Exception,
    ) -> None:
        assert self.producer is not None
        updated_retry_message = dict(retryable_message)
        updated_retry_message["retryCount"] = retryable_message["retryCount"] + 1
        updated_retry_message["lastAttemptTimestamp"] = now_iso()
        updated_retry_message["errorMessage"] = str(error)
        updated_retry_message["errorStackTrace"] = traceback.format_exc()

        self.producer.send(
            self.config.retry_topic,
            key=retryable_message["messageKey"],
            value=json.dumps(updated_retry_message),
            headers=correlation_headers(correlation_id),
        ).get(timeout=10)

    def send_to_dlq(
        self,
        original_message: str,
        total_retries: int,
        correlation_id: str,
        error: Exception,
    ) -> None:
        assert self.producer is not None
        original_message_object = json.loads(original_message)
        message_key = self.transformer.extract_message_key_from_json(original_message)
        timestamp = now_iso()
        dlq_message = {
            "originalMessage": original_message_object,
            "messageKey": message_key,
            "totalRetries": total_retries,
            "firstAttemptTimestamp": timestamp,
            "failedTimestamp": timestamp,
            "finalErrorMessage": str(error),
            "finalErrorStackTrace": traceback.format_exc(),
        }
        self.producer.send(
            self.config.dlq_topic,
            key=message_key,
            value=json.dumps(dlq_message),
            headers=correlation_headers(correlation_id),
        ).get(timeout=10)

    def send_retryable_to_dlq(self, retryable_message: dict, correlation_id: str) -> None:
        assert self.producer is not None
        dlq_message = {
            "originalMessage": retryable_message["originalMessage"],
            "messageKey": retryable_message["messageKey"],
            "totalRetries": retryable_message["retryCount"],
            "firstAttemptTimestamp": retryable_message["firstAttemptTimestamp"],
            "failedTimestamp": now_iso(),
            "finalErrorMessage": retryable_message.get("errorMessage") or "Max retries exceeded",
            "finalErrorStackTrace": retryable_message.get("errorStackTrace"),
        }
        self.producer.send(
            self.config.dlq_topic,
            key=retryable_message["messageKey"],
            value=json.dumps(dlq_message),
            headers=correlation_headers(correlation_id),
        ).get(timeout=10)

    @staticmethod
    def calculate_backoff(retry_count: int) -> int:
        return min(1000 * (2 ** min(retry_count, 5)), 30000)


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    application = BridgeApplication()
    application.log_configuration()
    try:
        application.start()
    except KeyboardInterrupt:
        pass
    finally:
        application.stop()


if __name__ == "__main__":
    main()
