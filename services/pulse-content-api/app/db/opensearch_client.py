from opensearchpy import OpenSearch, NotFoundError
from app.core.config import settings
from common_models.post import StandardPost

# Configure the OpenSearch client
client = OpenSearch(
    hosts=[{'host': settings.OPENSEARCH_HOST, 'port': settings.OPENSEARCH_PORT}],
    http_auth=('user', 'password'), # Replace with your auth
    use_ssl=False,
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
)

POSTS_INDEX_NAME = "posts"

async def create_index_if_not_exists():
    """Creates the 'posts' index in OpenSearch if it doesn't already exist."""
    try:
        client.indices.get(index=POSTS_INDEX_NAME)
        print("Index 'posts' already exists.")
    except NotFoundError:
        client.indices.create(index=POSTS_INDEX_NAME)
        print("Created index 'posts'.")

async def index_post(post: StandardPost):
    """Indexes a StandardPost document into OpenSearch."""
    client.index(
        index=POSTS_INDEX_NAME,
        body=post.model_dump(),
        id=post.post_id,
        refresh=True
    )
    print(f"Indexed post {post.post_id} into OpenSearch.")
