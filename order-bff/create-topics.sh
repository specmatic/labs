#!/bin/sh
set -e

# Wait for Kafka broker to be ready
until /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list > /dev/null 2>&1; do
  echo 'Kafka not ready yet, retrying in 2s...'
  sleep 2
done

echo 'Creating product-queries topic...'

/opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 \
  --create --if-not-exists \
  --topic product-queries \
  --partitions 3 \
  --replication-factor 1

echo 'product-queries topic creation done.'
