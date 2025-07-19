import asyncio
from typing import List, Dict, Any
import httpx

from common_models.post import StandardPost, AuthorDetails, EngagementMetrics
from app.core.config import settings
from .base import SocialMediaAdapter

APIFY_BASE_URL = "https://api.apify.com/v2"
ACTOR_ID = "harvestapi~linkedin-post-search"

class LinkedInAdapter(SocialMediaAdapter):
    """Adapter for fetching posts from LinkedIn via the Apify API."""

    async def fetch_posts(self, author_urls: List[str]) -> List[StandardPost]:
        """
        Triggers one Apify actor run for a list of authors, waits for it to complete, 
        and fetches all results.
        """
        print(f"INFO: Starting Apify actor run for {len(author_urls)} LinkedIn URLs")
        
        async with httpx.AsyncClient() as client:
            run_input = { "authorUrls": author_urls, "maxPosts": 5 }
            start_url = f"{APIFY_BASE_URL}/acts/{ACTOR_ID}/runs?token={settings.APIFY_API_TOKEN}"
            
            response = await client.post(start_url, json=run_input, timeout=30.0)
            response.raise_for_status()
            run_details = response.json().get("data", {})
            run_id = run_details.get("id")
            dataset_id = run_details.get("defaultDatasetId")

            if not run_id or not dataset_id:
                raise Exception("Failed to start Apify actor run or get IDs.")

            status_url = f"{APIFY_BASE_URL}/actor-runs/{run_id}?token={settings.APIFY_API_TOKEN}"
            while True:
                run_status_response = await client.get(status_url)
                run_status_response.raise_for_status()
                status = run_status_response.json().get("data", {}).get("status")
                print(f"INFO: Apify run {run_id} status: {status}")

                if status == "SUCCEEDED":
                    break
                if status in ["FAILED", "ABORTED", "TIMED_OUT"]:
                    raise Exception(f"Apify run {run_id} failed with status: {status}")
                
                await asyncio.sleep(5)

            items_url = f"{APIFY_BASE_URL}/datasets/{dataset_id}/items?token={settings.APIFY_API_TOKEN}"
            items_response = await client.get(items_url)
            items_response.raise_for_status()
            api_posts = items_response.json()

            return [self._map_to_standard_post(post) for post in api_posts if post]

    def _map_to_standard_post(self, post: Dict[str, Any]) -> StandardPost:
        """Maps a single post from the Apify format to our internal StandardPost model."""
        # Safely handle potential null values for nested objects
        author_data = post.get("author") or {}
        engagement_data = post.get("engagement") or {}
        posted_at_data = post.get("postedAt") or {}

        author_details = AuthorDetails(
            id=author_data.get("publicIdentifier") or "unknown",
            name=author_data.get("name"),
            info=author_data.get("info"),
            url=author_data.get("linkedinUrl")
        )
        
        engagement_metrics = EngagementMetrics(
            likes=engagement_data.get("likes", 0),
            comments=engagement_data.get("comments", 0),
            shares=engagement_data.get("shares", 0)
        )
        
        return StandardPost(
            post_id=post.get("id"),
            source="linkedin",
            post_url=post.get("linkedinUrl"),
            content=post.get("content"),
            published_at=posted_at_data.get("date"),
            author=author_details,
            engagement=engagement_metrics
        )