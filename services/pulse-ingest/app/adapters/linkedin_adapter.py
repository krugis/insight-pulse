import asyncio
from typing import List, Dict, Any
import httpx

from app.core.models import StandardPost, AuthorDetails, EngagementMetrics
from app.core.config import settings
from .base import SocialMediaAdapter

# Define constants for the Apify API
APIFY_BASE_URL = "https://api.apify.com/v2"
ACTOR_ID = "harvestapi~linkedin-post-search"

class LinkedInAdapter(SocialMediaAdapter):
    """Adapter for fetching posts from LinkedIn via the Apify API."""

    async def fetch_posts(self, author_url: str) -> List[StandardPost]:
        """
        Triggers an Apify actor run, waits for it to complete, and fetches the results.
        """
        print(f"INFO: Starting Apify actor run for LinkedIn URL: {author_url}")
        
        async with httpx.AsyncClient() as client:
            # Step 1: Start the Apify actor run
            run_input = { "authorUrls": [author_url], "maxPosts": 5 }
            start_url = f"{APIFY_BASE_URL}/acts/{ACTOR_ID}/runs?token={settings.APIFY_API_TOKEN}"
            
            response = await client.post(start_url, json=run_input)
            response.raise_for_status() # Raise an exception for bad status codes
            run_details = response.json().get("data", {})
            run_id = run_details.get("id")
            dataset_id = run_details.get("defaultDatasetId")

            if not run_id or not dataset_id:
                raise Exception("Failed to start Apify actor run or get IDs.")

            # Step 2: Poll for the actor run to complete
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
                
                await asyncio.sleep(5) # Wait for 5 seconds before checking again

            # Step 3: Fetch results from the dataset
            items_url = f"{APIFY_BASE_URL}/datasets/{dataset_id}/items?token={settings.APIFY_API_TOKEN}"
            items_response = await client.get(items_url)
            items_response.raise_for_status()
            api_posts = items_response.json()

            # Step 4: Map the API response to our standard format
            return [self._map_to_standard_post(post) for post in api_posts]

    def _map_to_standard_post(self, post: Dict[str, Any]) -> StandardPost:
        """Maps a single post from the Apify format to our internal StandardPost model."""
        # Safely access nested dictionaries
        author_data = post.get("author", {})
        engagement_data = post.get("engagement", {})
        
        # Create the nested models from the models.py file
        author_details = AuthorDetails(
            id=author_data.get("publicIdentifier")or "unknown",
            name=author_data.get("name", "Unknown Author"),
            info=author_data.get("info"),
            url=author_data.get("linkedinUrl")
        )
        
        engagement_metrics = EngagementMetrics(
            likes=engagement_data.get("likes", 0),
            comments=engagement_data.get("comments", 0),
            shares=engagement_data.get("shares", 0)
        )
        
        # Create the main StandardPost object, now including the required fields
        return StandardPost(
            source="linkedin",
            post_id=post.get("id"),
            post_url=post.get("linkedinUrl"),
            content=post.get("content", ""),
            published_at=post.get("postedAt", {}).get("date"),
            author=author_details,          # <-- This was the missing piece
            engagement=engagement_metrics   # <-- This was the missing piece
        )
