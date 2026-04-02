#!/bin/sh
set -e

SCHEMA_REGISTRY_URL="http://schema-registry:8085"
SCHEMA_REGISTRY_USER="admin"
SCHEMA_REGISTRY_PASSWORD="admin-secret"

# Wait for Schema Registry to be up
echo "Waiting for Schema Registry to be ready..."
until curl -u "$SCHEMA_REGISTRY_USER:$SCHEMA_REGISTRY_PASSWORD" -fsS ${SCHEMA_REGISTRY_URL}/subjects > /dev/null; do
  sleep 2
done
echo "Schema Registry is up."

cd /usr/src/app/schemas

# Read and escape the schema JSON
escape_json() {
  cat "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | tr -d '\n' | tr -d '\r'
}

NEW_ORDERS_SCHEMA=$(escape_json NewOrders.avsc)
WIP_ORDERS_SCHEMA=$(escape_json WipOrders.avsc)

curl -u "$SCHEMA_REGISTRY_USER:$SCHEMA_REGISTRY_PASSWORD" -fsS -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data "{\"schema\":\"${NEW_ORDERS_SCHEMA}\"}" \
  ${SCHEMA_REGISTRY_URL}/subjects/new-orders-value/versions

curl -u "$SCHEMA_REGISTRY_USER:$SCHEMA_REGISTRY_PASSWORD" -fsS -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data "{\"schema\":\"${WIP_ORDERS_SCHEMA}\"}" \
  ${SCHEMA_REGISTRY_URL}/subjects/wip-orders-value/versions

echo "Schemas registered."
