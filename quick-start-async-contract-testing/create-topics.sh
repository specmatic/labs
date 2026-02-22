#!/bin/sh
set -e

BOOTSTRAP_SERVER="${KAFKA_BOOTSTRAP_SERVER:-kafka:9092}"

echo "Creating Kafka topics on ${BOOTSTRAP_SERVER}..."
/opt/kafka/bin/kafka-topics.sh --bootstrap-server "${BOOTSTRAP_SERVER}" --create --if-not-exists --topic new-orders --partitions 3 --replication-factor 1
/opt/kafka/bin/kafka-topics.sh --bootstrap-server "${BOOTSTRAP_SERVER}" --create --if-not-exists --topic wip-orders --partitions 3 --replication-factor 1
/opt/kafka/bin/kafka-topics.sh --bootstrap-server "${BOOTSTRAP_SERVER}" --list
echo "Kafka topics ready."
