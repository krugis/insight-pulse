from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from app.adapters.adapter_factory import get_adapter
from app.core.message_bus import publish_post
import json

app = FastAPI(
    title="Pulse Ingest Service",
    description="Fetches content from social media platforms and publishes it for processing."
)

# --- UPDATED ---
class IngestRequest(BaseModel):
    author_urls: List[HttpUrl]

@app.post("/ingest/{platform}")
async def ingest_posts(platform: str, request: IngestRequest):
    """
    Ingests posts from a specified platform for a given list of author URLs.
    """
    try:
        adapter = get_adapter(platform)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    print(f"🚀 Starting bulk ingestion for platform '{platform}'...")
    
    try:
        # Pass the entire list of URLs to the adapter
        # The adapter will now handle the bulk request efficiently
        author_urls_str = [str(url) for url in request.author_urls]
        posts = await adapter.fetch_posts(author_urls_str)
        
        for post in posts:
            await publish_post(post)
            
        print(f"🎉 Ingestion complete. {len(posts)} posts published.")
        
        return {
            "status": "success",
            "platform": platform,
            "ingested_posts_count": len(posts)
        }
    except Exception as e:
        print(f"ERROR: Ingestion failed. Reason: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during ingestion: {e}")
    
@app.post("/ingest/linkedin/test-local")
async def test_local_ingestion():
    """
    An endpoint to test the data mapping logic using a local file,
    bypassing the live Apify API call.
    """
    # The file path is now a local variable again
    local_file_path = "test_data/apify_output.json"
    
    print(f"--- 🚀 Starting LOCAL INGESTION TEST from file: {local_file_path} ---")
    
    try:
        with open(local_file_path, "r") as f:
            api_posts = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Test data file not found: {local_file_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load test data: {e}")

    adapter = get_adapter("linkedin")
    successful_posts = 0
    
    for post in api_posts:
        if not post:
            continue
        try:
            standard_post = adapter._map_to_standard_post(post)
            await publish_post(standard_post)
            successful_posts += 1
        except Exception as e:
            print(f"--- ❌ MAPPING FAILED ---")
            print(json.dumps(post, indent=2))
            raise HTTPException(
                status_code=500,
                detail=f"Mapping failed for post ID {post.get('id')}: {e}"
            )

    return {"status": "local test successful", "mapped_posts": successful_posts}