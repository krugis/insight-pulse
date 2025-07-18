from .base import SocialMediaAdapter
from .linkedin_adapter import LinkedInAdapter
# from .twitter_adapter import TwitterAdapter # You would add more here

def get_adapter(platform: str) -> SocialMediaAdapter:
    """Factory function to get the correct platform adapter."""
    if platform == "linkedin":
        return LinkedInAdapter()
    # elif platform == "twitter":
    #     return TwitterAdapter()
    else:
        raise ValueError(f"No adapter available for platform: {platform}")
