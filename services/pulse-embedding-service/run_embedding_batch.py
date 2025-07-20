import os
from opensearchpy import OpenSearch
from sentence_transformers import SentenceTransformer

print("--- Minimal test script running. If you see this, the container works. ---")

# --- Configuration ---
OPENSEARCH_HOST = "opensearch"
POSTS_INDEX_NAME = "posts"
MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'

# --- Client and Model Initialization ---
client = OpenSearch(
    hosts=[{'host': OPENSEARCH_HOST, 'port': 9200}],
    use_ssl=False,
    verify_certs=False
)
model = SentenceTransformer(MODEL_NAME)

def find_posts_without_embeddings():
    """Query OpenSearch for documents where embedding_processed is false."""
    # This query is more robust for finding boolean flags.
    query = {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"embedding_processed": False}}
                ]
            }
        }
    }
    print("Searching for posts with 'embedding_processed: false'...")
    response = client.search(index=POSTS_INDEX_NAME, body=query, size=100)
    print(f"Found {len(response['hits']['hits'])} posts to process.")
    return response['hits']['hits']

def generate_and_update_embeddings():
    """Finds posts, generates embeddings, and updates them in OpenSearch."""
    print("Starting batch embedding job...")
    posts_to_process = find_posts_without_embeddings()

    if not posts_to_process:
        print("No new posts to embed. Job finished.")
        return

    print(f"Found {len(posts_to_process)} posts to embed.")
    for hit in posts_to_process:
        post_id = hit['_id']
        content = hit['_source'].get('content')
        vector = [0.0] * 384 # Default zero vector

        if content:
            vector = model.encode(content).tolist()
        
        try:
            # Update the document with the vector AND the new flag status
            update_body = {
                "doc": {
                    "content_vector": vector,
                    "embedding_processed": True
                }
            }
            client.update(
                index=POSTS_INDEX_NAME,
                id=post_id,
                body=update_body
            )
            print(f"✅ Successfully updated post {post_id} with new embedding.")
        except Exception as e:
            print(f"❌ Failed to update post {post_id}. Error: {e}")
    
    print("Batch embedding job finished.")
    
if __name__ == "__main__":
    generate_and_update_embeddings()