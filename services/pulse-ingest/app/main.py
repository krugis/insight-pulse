from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from app.adapters.adapter_factory import get_adapter
from app.core.message_bus import publish_post

app = FastAPI(
    title="Pulse Ingest Service",
    description="Fetches content from social media platforms and publishes it for processing."
)

# Updated request model to accept a URL
class IngestRequest(BaseModel):
    author_url: HttpUrl

@app.post("/ingest/{platform}")
async def ingest_posts(platform: str, request: IngestRequest):
    """
    Ingests posts from a specified platform for a given author URL.
    """
    try:
        adapter = get_adapter(platform)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    print(f"🚀 Starting ingestion for platform '{platform}' and author '{request.author_url}'...")
    
    try:
        # 1. Fetch posts using the correct adapter
        posts = await adapter.fetch_posts(str(request.author_url))
        
        # 2. Publish each post to the message bus
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
