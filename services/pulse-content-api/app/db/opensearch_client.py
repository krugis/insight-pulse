import time
from opensearchpy import OpenSearch, NotFoundError
from opensearchpy.exceptions import ConnectionError
from app.core.config import settings
from common_models.post import StandardPost

# Configure the OpenSearch client
client = OpenSearch(
    hosts=[{'host': settings.OPENSEARCH_HOST, 'port': settings.OPENSEARCH_PORT}],
    # http_auth=('user', 'password'), # Replace with your auth if needed
    use_ssl=False,
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
)

POSTS_INDEX_NAME = "posts"

async def create_index_if_not_exists():
    """
    Creates the 'posts' index in OpenSearch if it doesn't already exist.
    Retries connection on failure to handle startup race condition.
    """
    retries = 20
    while retries > 0:
        try:
            if not client.indices.exists(index=POSTS_INDEX_NAME):
                client.indices.create(index=POSTS_INDEX_NAME)
                print("✅ Created index 'posts'.")
            else:
                print("✅ Index 'posts' already exists.")
            return  # Success, exit the function
        except ConnectionError:
            retries -= 1
            print(f"❌ OpenSearch not available. Retrying in 5 seconds... ({retries} retries left)")
            time.sleep(5)
    raise Exception("Could not connect to OpenSearch after multiple retries.")


async def index_post(post: StandardPost):
    """Indexes a StandardPost document into OpenSearch."""
    client.index(
        index=POSTS_INDEX_NAME,
        body=post.model_dump(mode='json'),
        id=post.post_id,
        refresh=True
    )
    print(f"Indexed post {post.post_id} into OpenSearch.")
