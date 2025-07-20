import time
from opensearchpy import OpenSearch, NotFoundError
from opensearchpy.exceptions import ConnectionError
from app.core.config import settings
from common_models.post import StandardPost

# Configure the OpenSearch client
client = OpenSearch(
    hosts=[{'host': settings.OPENSEARCH_HOST, 'port': settings.OPENSEARCH_PORT}],
    use_ssl=False,
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
)

POSTS_INDEX_NAME = "posts"

async def create_index_if_not_exists():
    """
    Creates the 'posts' index with explicit mappings if it doesn't already exist.
    Retries connection on failure.
    """
    # --- THIS BODY DEFINES THE CORRECT FIELD TYPES ---
    index_body = {
        "settings": {"index": {"knn": True}},
        "mappings": {
            "properties": {
                "content_vector": {
                    "type": "knn_vector", "dimension": 384
                },
                "embedding_processed": {
                    "type": "boolean"
                }
            }
        },
    }
    # ---------------------------------------------------

    retries = 20
    while retries > 0:
        try:
            if not client.indices.exists(index=POSTS_INDEX_NAME):
                # Use the index_body when creating the index
                client.indices.create(index=POSTS_INDEX_NAME, body=index_body)
                print("✅ Created index 'posts' with explicit mappings.")
            else:
                print("✅ Index 'posts' already exists.")
            return
        except ConnectionError:
            retries -= 1
            print(f"❌ OpenSearch not available. Retrying in 5 seconds... ({retries} retries left)")
            time.sleep(5)
    raise Exception("Could not connect to OpenSearch after multiple retries.")


async def index_post(post: StandardPost):
    """Indexes a StandardPost document and adds the embedding_processed flag."""
    doc = post.model_dump(mode='json')
    doc["embedding_processed"] = False
    
    client.index(
        index=POSTS_INDEX_NAME,
        body=doc,
        id=post.post_id,
        refresh=True
    )
    print(f"Indexed post {post.post_id} into OpenSearch (without vector).")