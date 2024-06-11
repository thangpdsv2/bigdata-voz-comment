import pandas as pd
import re
from kafka import KafkaProducer, errors
import requests
from bs4 import BeautifulSoup
import json
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
    'Referer': 'https://tiki.vn/?src=header_tiki',
    'x-guest-token': '8jWSuIDBb2NGVzr6hsUZXpkP1FRin7lY',
    'Connection': 'keep-alive',
    'TE': 'Trailers',
}

def get_page_data(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    comments = soup.find_all('div', itemprop='text')

    comment_texts = []
    for comment in comments:
        if not comment.find_parent('blockquote'):
            text = ' '.join(comment.stripped_strings)
            if not re.search(r'\bsaid\b', text) and len(text) <= 250:
                comment_texts.append(text)
    return comment_texts

base_url = "https://voz.vn/t/nhap-ngu-thi-xac-dinh-mat-nguoi-yeu.154776"

def get_data_from_multiple_pages(base_url, num_pages):
    all_comments = []
    for page_num in range(1, num_pages + 1):
        url = f"{base_url}/page-{page_num}"
        comments_on_page = get_page_data(url)
        all_comments.extend(comments_on_page)
    return all_comments

def remove_special_chars(input_string):
    pattern = r'[^a-zA-Z\sàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]'
    return re.sub(pattern, '', input_string)

# Retry mechanism for Kafka Producer
def create_kafka_producer(retries=5, delay=5):
    for i in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers='kafka:9092',  # Internal Kafka address
                value_serializer=lambda v: json.dumps(v).encode('utf-8')  # Serialize JSON messages
            )
            logger.info("Connected to Kafka broker")
            return producer
        except errors.NoBrokersAvailable as e:
            logger.error(f"No brokers available, retrying in {delay} seconds... ({i+1}/{retries})")
            time.sleep(delay)
    raise errors.NoBrokersAvailable("Could not connect to Kafka broker after several retries")

producer = create_kafka_producer()

# Function to send messages to Kafka
def send_message(topic, value):
    producer.send(topic, value=value)
    producer.flush()
    logger.info(f"Sent: {value}")

# Define the topic
topic = 'incoming-order'

# Number of pages to scrape
num_pages = 16
comments = get_data_from_multiple_pages(base_url, num_pages)

# Process and send comments to Kafka
for comment in comments:
    processed_comment = remove_special_chars(comment)
    message = {'comment': processed_comment}
    send_message(topic, message)

# Close the producer
producer.close()
