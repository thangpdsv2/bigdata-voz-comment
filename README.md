# start spark
start-spark
# start zoo keeper
start-zookeeper
# start kafka
start-kafka


# Test
kafka-topics.sh --list --bootstrap-server localhost:9092
# If topics exist, delete them first
kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic incoming-order
# Create topics incoming-order
kafka-topics.sh --create --topic incoming-order --bootstrap-server localhost:9092
# Make sure we have topics: 
incoming-order

# Console incoming order
kafka-console-producer.sh --broker-list localhost:9092 --topic incoming-order


# Download model to local source code
https://drive.google.com/drive/u/3/folders/1tQ2xjhThTElK4G1ybuh4h71hxG1vnXNr



# Docker running guideline
## If change config or code
- docker-compose down 

## Start docker-compose
- docker-compose up -d --build
## Monitor log of spark ml prediction
- docker logs -f spark-submit 

## Remote to kafka to send test message to sparkML
docker exec -it kafka /bin/bash
kafka-console-producer.sh --broker-list localhost:9092 --topic incoming-order

> send test message and monitor prediction on spark-submit console

## Verify kafka incoming message
docker run --rm -it --network=doan_spark_kafka_network confluentinc/cp-kafka:latest kafka-console-consumer --bootstrap-server kafka:9092 --topic incoming-order --from-beginning


