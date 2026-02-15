#!/bin/sh
set -e

# Wait for Kafka broker to be ready
until /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list > /dev/null 2>&1; do
  echo 'Kafka not ready yet, retrying in 2s...'
  sleep 2
done

echo 'Creating topics...'
TOPICS="new-orders wip-orders to-be-cancelled-orders cancelled-orders accepted-orders out-for-delivery-orders"

for topic in $TOPICS; do
  /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 \
    --create --if-not-exists \
    --topic "$topic" \
    --partitions 3 \
    --replication-factor 1
done

echo 'Topic creation done.'