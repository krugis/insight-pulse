from abc import ABC, abstractmethod
from typing import List
from common_models.post import StandardPost

class SocialMediaAdapter(ABC):
    """Abstract base class for all social media adapters."""
    
    @abstractmethod
    async def fetch_posts(self, author_urls: List[str]) -> List[StandardPost]:
        """Fetches posts for a given list of user URLs and returns them in a standardized format."""
        pass