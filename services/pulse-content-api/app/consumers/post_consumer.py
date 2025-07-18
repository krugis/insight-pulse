import json
from kafka import KafkaConsumer
from app.core.config import settings
from app.db import opensearch_client
from common_models.post import StandardPost

def consume_posts():
    """Connects to Kafka and consumes messages from the posts topic."""
    consumer = KafkaConsumer(
        settings.KAFKA_POSTS_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='earliest',
        group_id='post-indexer-group'
    )
    
    print("Kafka consumer started. Waiting for messages...")
    for message in consumer:
        try:
            post_data = json.loads(message.value.decode('utf-8'))
            post = StandardPost(**post_data)
            
            # Asynchronously index the post
            import asyncio
            asyncio.run(opensearch_client.index_post(post))
            
        except Exception as e:
            print(f"Error processing message: {e}")
