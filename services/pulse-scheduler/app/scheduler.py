import httpx
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import create_engine, text
from .core.config import settings

# --- Configuration ---
INGEST_API_URL = "http://pulse-ingest:8000/ingest/linkedin"
EMBEDDING_API_URL = "http://pulse-embedding-service:8005/run-batch" # <-- UPDATED
AI_CORE_API_BASE_URL = "http://pulse-ai-core:8002"

# --- Database Connection ---
engine = create_engine(settings.DATABASE_URL)

async def trigger_embedding():
    """Triggers the embedding service via its API."""
    print("SCHEDULER: Triggering embedding job via API...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(EMBEDDING_API_URL, timeout=30.0)
            response.raise_for_status()
        print("SCHEDULER: Embedding job triggered successfully.")
    except Exception as e:
        print(f"SCHEDULER: Error triggering embedding job: {e}")

async def run_daily_pipeline():
    """The main function that orchestrates the entire daily workflow."""
    print("--- 🚀 Starting Daily Pipeline ---")
    
    # 1. Get all agents and their profiles from the database
    print("Fetching agent configurations...")
    all_urls = set()
    agents = []
    with engine.connect() as conn:
        agents_result = conn.execute(text("SELECT id, email FROM agents"))
        for agent_row in agents_result:
            agent = {"id": agent_row.id, "email": agent_row.email, "urls": []}
            profiles_result = conn.execute(text(f"SELECT url FROM profiles WHERE agent_id = {agent_row.id}"))
            for profile_row in profiles_result:
                agent["urls"].append(profile_row.url)
                all_urls.add(profile_row.url)
            agents.append(agent)

    if not agents:
        print("No agents found. Skipping pipeline.")
        return

    # 2. Trigger ingestion for all unique URLs
    print(f"Triggering ingestion for {len(all_urls)} unique profiles...")
    async with httpx.AsyncClient() as client:
        await client.post(INGEST_API_URL, json={"author_urls": list(all_urls)}, timeout=60.0)

    # 3. Trigger the embedding job via API
    await trigger_embedding()

    # 4. Trigger AI core for each agent
    for agent in agents:
        print(f"Triggering AI core for agent {agent['id']}...")
        async with httpx.AsyncClient() as client:
            await client.post(f"{AI_CORE_API_BASE_URL}/generate-for-agent/{agent['id']}")

    print("--- ✅ Daily Pipeline Complete ---")


async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_daily_pipeline, 'cron', hour=1, minute=0) # Run at 1:00 AM UTC
    
    print("Scheduler started. Waiting for scheduled jobs...")
    scheduler.start()
    
    try:
        while True:
            await asyncio.sleep(3600) # Sleep for an hour
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    asyncio.run(main())