from .models import StandardPost

async def publish_post(post: StandardPost):
    """
    Simulates publishing a standardized post to a message bus like RabbitMQ or Kafka.
    """
    print(f"✅ [Message Bus] Publishing post {post.post_id} from {post.source.upper()}...")
    # In a real app, this would use a library like Pika (RabbitMQ) or kafka-python
    # to send post.model_dump_json() to a specific topic or queue.
    print("✅ [Message Bus] Published successfully.")
