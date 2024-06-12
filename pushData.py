import pandas as pd
import re
from kafka import KafkaProducer, errors
import json
import logging
import asyncio
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_data_from_files():
    comments = []
    base_dirs = ['data_test/test/neg', 'data_test/test/pos']

    for base_dir in base_dirs:
        if not os.path.exists(base_dir):
            logger.error(f"Directory {base_dir} does not exist.")
            continue
        for filename in os.listdir(base_dir):
            if filename.endswith('.txt'):
                with open(os.path.join(base_dir, filename), 'r', encoding='utf-8') as file:
                    comment = file.read().strip()
                    comments.append(comment)
    
    return comments

def remove_special_chars(input_string):
    pattern = r'[^a-zA-Z\sàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]'
    return re.sub(pattern, '', input_string)

async def create_kafka_producer(retries=5, delay=5):
    for i in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers='kafka:9092',  # Kafka service name within Docker network
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),  # Serialize JSON messages
                request_timeout_ms=60000,  # 60 seconds
                linger_ms=1000  # 1 second
            )
            logging.info("Connected to Kafka broker")
            return producer
        except errors.NoBrokersAvailable as e:
            logging.error(f"No brokers available, retrying in {delay} seconds... ({i+1}/{retries})")
            await asyncio.sleep(delay)
    raise errors.NoBrokersAvailable("Could not connect to Kafka broker after several retries")

async def push_to_kafka(producer):
    topic = 'incoming-order'

    comments = read_data_from_files()
    logger.info(f"Loaded {len(comments)} comments from files")
    
    if not comments:
        logger.warning("No comments found to send to Kafka")
        return

    cleaned_comments = [remove_special_chars(comment) for comment in comments]
    df = pd.DataFrame(cleaned_comments, columns=['comment'])
    df.to_csv('/app/data/comments.csv', index=False)

    for comment in cleaned_comments:
        message = {'comment': comment}
        logger.info(f"message: {message}")
        producer.send(topic, value=message)
        producer.flush()
        logger.info(f"Sent: {message}")
        await asyncio.sleep(0)  # Allow other tasks to run

async def main():
    producer = await create_kafka_producer()
    await push_to_kafka(producer)
    producer.close()

if __name__ == "__main__":
    asyncio.run(main())
