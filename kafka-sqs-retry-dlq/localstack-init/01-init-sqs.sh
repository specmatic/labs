#!/bin/bash

# This script initializes LocalStack with required resources
# It will be automatically executed when LocalStack is ready

echo "Initializing LocalStack resources..."

# Create main SQS queue
awslocal sqs create-queue --queue-name place-order-queue

# Get queue URL
QUEUE_URL=$(awslocal sqs get-queue-url --queue-name place-order-queue --query 'QueueUrl' --output text)

echo "Main SQS Queue created: $QUEUE_URL"
echo "LocalStack initialization complete!"

