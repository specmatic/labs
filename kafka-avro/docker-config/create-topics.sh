#!/bin/sh
set -e

# Create SASL/PLAIN client config for authentication
cat <<EOF > /tmp/client.properties
security.protocol=SASL_PLAINTEXT
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username="test" password="test-secret";
EOF

echo 'Waiting for Kafka broker to be ready...'
until kafka-topics --bootstrap-server broker:9093 --command-config /tmp/client.properties --list > /dev/null 2>&1; do
  echo 'Kafka not ready yet, retrying in 2s...'
  sleep 2
done

echo 'Creating topics...'
TOPICS="new-orders wip-orders"

for topic in $TOPICS; do
  kafka-topics --bootstrap-server broker:9093 \
    --command-config /tmp/client.properties \
    --create --if-not-exists \
    --topic "$topic" \
    --partitions 3 \
    --replication-factor 1
done

echo 'Topic creation done.'
