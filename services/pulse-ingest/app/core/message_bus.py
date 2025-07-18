import json
import time
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from app.core.config import settings
from common_models.post import StandardPost

def create_kafka_producer():
    """
    Creates a Kafka producer, retrying connection on failure.
    This handles the race condition where the app starts before Kafka is ready.
    """
    retries = 5
    while retries > 0:
        try:
            producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("✅ Successfully connected to Kafka.")
            return producer
        except NoBrokersAvailable:
            retries -= 1
            print(f"❌ Kafka not available. Retrying in 5 seconds... ({retries} retries left)")
            time.sleep(5)
    raise Exception("Could not connect to Kafka after multiple retries.")

producer = create_kafka_producer()

async def publish_post(post: StandardPost):
    """Publishes a standardized post to the Kafka topic."""
    try:
        producer.send(settings.KAFKA_POSTS_TOPIC, value=post.model_dump(mode='json'))
        producer.flush()
        print(f"✅ Published post {post.post_id} to Kafka topic '{settings.KAFKA_POSTS_TOPIC}'.")
    except Exception as e:
        print(f"❌ Failed to publish post {post.post_id} to Kafka. Error: {e}")
