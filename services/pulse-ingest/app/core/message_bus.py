import json
from kafka import KafkaProducer
from app.core.config import settings
from common_models.post import StandardPost

producer = KafkaProducer(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

async def publish_post(post: StandardPost):
    """Publishes a standardized post to the Kafka topic."""
    try:
        producer.send(settings.KAFKA_POSTS_TOPIC, value=post.model_dump(mode='json'))
        producer.flush() # Ensure the message is sent
        print(f"✅ Published post {post.post_id} to Kafka topic '{settings.KAFKA_POSTS_TOPIC}'.")
    except Exception as e:
        print(f"❌ Failed to publish post {post.post_id} to Kafka. Error: {e}")
