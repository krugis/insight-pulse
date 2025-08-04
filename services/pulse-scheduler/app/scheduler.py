import httpx
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import create_engine, text
from .core.config import settings

# --- Configuration ---
INGEST_API_URL = "http://pulse-ingest:8000/ingest/linkedin"
EMBEDDING_API_URL = "http://pulse-embedding-service:8005/run-batch"
AI_CORE_API_URL = "http://pulse-ai-core:8002/generate-newspaper" # <-- UPDATED

engine = create_engine(settings.DATABASE_URL)

async def run_daily_pipeline():
    """Orchestrates the entire daily workflow."""
    print("--- 🚀 Starting Daily Pipeline ---")
    
    # 1. Get all unique profile URLs from the database
    print("Fetching unique profiles...")
    all_urls = set()
    with engine.connect() as conn:
        profiles_result = conn.execute(text("SELECT DISTINCT url FROM profiles"))
        for row in profiles_result:
            all_urls.add(row.url)

    if not all_urls:
        print("No profiles found to scrape. Skipping pipeline.")
        return

    # 2. Trigger ingestion for all unique URLs
    print(f"Triggering ingestion for {len(all_urls)} unique profiles...")
    async with httpx.AsyncClient() as client:
        await client.post(INGEST_API_URL, json={"author_urls": list(all_urls)}, timeout=300.0)

    # 3. Trigger the embedding job
    print("Triggering embedding job...")
    async with httpx.AsyncClient() as client:
        await client.post(EMBEDDING_API_URL, timeout=30.0)

    # 4. Trigger AI core to generate the newspaper
    print("Triggering newspaper generation...")
    async with httpx.AsyncClient() as client:
        await client.post(AI_CORE_API_URL, timeout=600.0) # 10 min timeout for LLM

    print("--- ✅ Daily Pipeline Complete ---")

async def main():
    scheduler = AsyncIOScheduler()
    cron_parts = settings.SCHEDULE_CRON.split()
    scheduler.add_job(
        run_daily_pipeline, 'cron', 
        minute=cron_parts[0], hour=cron_parts[1], day=cron_parts[2], 
        month=cron_parts[3], day_of_week=cron_parts[4]
    )
    
    print(f"Scheduler started. Daily job scheduled for: {settings.SCHEDULE_CRON} (UTC)")
    scheduler.start()
    
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    asyncio.run(main())