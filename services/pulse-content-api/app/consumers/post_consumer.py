import json
import time
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from app.core.config import settings
from app.db import opensearch_client
from common_models.post import StandardPost

def get_kafka_consumer():
    """
    Creates a Kafka consumer, retrying connection on failure.
    """
    retries = 5
    while retries > 0:
        try:
            consumer = KafkaConsumer(
                settings.KAFKA_POSTS_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                auto_offset_reset='earliest',
                group_id='post-indexer-group'
            )
            print("✅ Successfully connected to Kafka.")
            return consumer
        except NoBrokersAvailable:
            retries -= 1
            print(f"❌ Kafka not available for consumer. Retrying in 5 seconds... ({retries} retries left)")
            time.sleep(5)
    raise Exception("Could not connect to Kafka for consumer after multiple retries.")

def consume_posts():
    """Consumes messages from the posts topic and indexes them."""
    consumer = get_kafka_consumer()
    
    print("Kafka consumer started. Waiting for messages...")
    for message in consumer:
        try:
            post_data = json.loads(message.value.decode('utf-8'))
            post = StandardPost(**post_data)
            
            import asyncio
            asyncio.run(opensearch_client.index_post(post))
            
        except Exception as e:
            print(f"Error processing message: {e}")
