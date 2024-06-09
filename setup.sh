#!/bin/bash

# Wait until Kafka is ready
while ! nc -z kafka 9092; do
  sleep 0.1
done

# List existing topics
kafka-topics.sh --list --bootstrap-server kafka:9092

# Delete existing topics
kafka-topics.sh --bootstrap-server kafka:9092 --delete --topic incoming-order

# Create new topics
kafka-topics.sh --create --topic incoming-order --bootstrap-server kafka:9092

# List topics to verify
kafka-topics.sh --list --bootstrap-server kafka:9092

# Keep the script running
tail -f /dev/null
