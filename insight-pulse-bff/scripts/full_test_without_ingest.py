import json
import time
import httpx
from kafka import KafkaProducer

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "new_posts"
LOCAL_DATA_FILE = "/home/ipd1/test_data/apify_output.json"

EMBEDDING_API_URL = "http://localhost:8005/run-batch"
AI_CORE_API_URL = "http://localhost:8002/generate-newspaper"

# --- Helper Functions ---
def publish_to_kafka():
    """Reads local data and publishes it to the Kafka topic."""
    print(f"📦 Publishing test data from '{LOCAL_DATA_FILE}' to Kafka topic '{KAFKA_TOPIC}'...")

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    with open(LOCAL_DATA_FILE, 'r') as f:
        posts = json.load(f)

    for post in posts:
        if post:
            producer.send(KAFKA_TOPIC, value=post)

    producer.flush()
    producer.close()
    print(f"✅ Published {len(posts)} posts to Kafka.")

def trigger_service(name: str, url: str):
    """Makes a POST request to trigger a service."""
    print(f"🚀 Triggering {name} service at {url}...")
    try:
        with httpx.Client() as client:
            response = client.post(url, timeout=30.0)
            response.raise_for_status()
        print(f"✅ {name} service triggered successfully.")
    except httpx.RequestError as e:
        print(f"❌ Error triggering {name} service: {e}")
        raise

# --- Main Test Workflow ---
def run_test():
    try:
        # Step 1: Simulate ingestion by publishing directly to Kafka
        publish_to_kafka()

        # Step 2: Wait for pulse-content-api to process and save
        print("⏳ Waiting 15 seconds for content API to save posts...")
        time.sleep(15)

        # Step 3: Trigger the embedding service
        trigger_service("Embedding", EMBEDDING_API_URL)

        # Step 4: Wait for embeddings to be generated
        print("⏳ Waiting 30 seconds for embedding job to complete...")
        time.sleep(30)

        # Step 5: Trigger the AI core service
        trigger_service("AI Core", AI_CORE_API_URL)

        print("\n🎉 Full pipeline test triggered successfully!")
        print("Monitor 'docker compose logs -f' to see the services at work.")
        print("Check your PostgreSQL database for the final 'daily_digests' entry.")

    except Exception as e:
        print(f"\n🔥 Test script failed: {e}")

if __name__ == "__main__":
    run_test()