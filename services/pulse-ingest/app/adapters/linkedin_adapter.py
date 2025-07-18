import uuid
from datetime import datetime
from typing import List
from app.core.models import StandardPost
from .base import SocialMediaAdapter

class LinkedInAdapter(SocialMediaAdapter):
    """Mock adapter for fetching posts from LinkedIn."""
    
    async def fetch_posts(self, user_id: str) -> List[StandardPost]:
        print(f"MOCK: Fetching LinkedIn posts for user: {user_id}")
        # In a real app, you would make an API call to the commercial LinkedIn API here.
        return [
            StandardPost(
                source="linkedin",
                post_id=str(uuid.uuid4()),
                author_id=user_id,
                content="Excited to announce our new partnership with a leading tech company! #AI #Partnership",
                post_url=f"https://linkedin.com/posts/{user_id}/12345",
                published_at=datetime.utcnow()
            )
        ]
