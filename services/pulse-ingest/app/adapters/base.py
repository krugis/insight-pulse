from abc import ABC, abstractmethod
from typing import List
from app.core.models import StandardPost

class SocialMediaAdapter(ABC):
    """Abstract base class for all social media adapters."""
    
    @abstractmethod
    async def fetch_posts(self, user_id: str) -> List[StandardPost]:
        """Fetches posts for a given user ID and returns them in a standardized format."""
        pass
