from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.db import opensearch_client
from app.consumers import post_consumer
import threading

# A function to run the Kafka consumer in a separate thread
def run_consumer_in_background():
    consumer_thread = threading.Thread(target=post_consumer.consume_posts, daemon=True)
    consumer_thread.start()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    await opensearch_client.create_index_if_not_exists()
    run_consumer_in_background()
    yield
    # On shutdown (if needed)

app = FastAPI(
    title="Pulse Content API",
    description="Provides an API to search for content and consumes new posts from Kafka.",
    lifespan=lifespan
)

@app.get("/")
def read_root():
    return {"message": "Pulse Content API is running."}

# You would add your search endpoints here, for example:
# @app.get("/posts/search")
# async def search_posts(query: str):
#     # Add search logic here
#     return {"results": []}
