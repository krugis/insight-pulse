from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.adapters.adapter_factory import get_adapter
from app.core.message_bus import publish_post

app = FastAPI(
    title="Pulse Ingest Service",
    description="Fetches content from social media platforms and publishes it for processing."
)

class IngestRequest(BaseModel):
    user_id: str

@app.post("/ingest/{platform}")
async def ingest_posts(platform: str, request: IngestRequest):
    """
    Ingests posts from a specified platform for a given user ID.
    """
    try:
        adapter = get_adapter(platform)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    print(f"🚀 Starting ingestion for platform '{platform}' and user '{request.user_id}'...")
    
    # 1. Fetch posts using the correct adapter
    posts = await adapter.fetch_posts(request.user_id)
    
    # 2. Publish each post to the message bus
    for post in posts:
        await publish_post(post)
        
    print(f"🎉 Ingestion complete. {len(posts)} posts published.")
    
    return {
        "status": "success",
        "platform": platform,
        "ingested_posts_count": len(posts)
    }
