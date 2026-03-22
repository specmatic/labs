#!/bin/bash

# This script initializes LocalStack with required resources
# It will be automatically executed when LocalStack is ready

echo "Initializing LocalStack resources..."

# Create main SQS queue with a long visibility timeout so messages consumed
# in one scenario do not reappear during later retry/DLQ scenarios.
awslocal sqs create-queue \
  --queue-name place-order-queue \
  --attributes VisibilityTimeout=180

# Get queue URL
QUEUE_URL=$(awslocal sqs get-queue-url --queue-name place-order-queue --query 'QueueUrl' --output text)

echo "Main SQS Queue created: $QUEUE_URL"
echo "LocalStack initialization complete!"
