from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional

class AuthorDetails(BaseModel):
    """Represents the author of a post."""
    id: str = Field(..., description="The unique public identifier of the author, e.g., 'satyanadella'")
    name: str = Field(..., description="The full name of the author")
    info: Optional[str] = Field(None, description="The author's title or headline")
    url: Optional[HttpUrl] = Field(None, description="A direct URL to the author's profile")

class EngagementMetrics(BaseModel):
    """Represents the engagement statistics of a post."""
    likes: int = Field(0, description="Total number of likes on the post")
    comments: int = Field(0, description="Total number of comments on the post")
    shares: int = Field(0, description="Total number of shares or reposts")

class StandardPost(BaseModel):
    """
    The standardized internal data model for a social media post
    from any platform.
    """
    source: str = Field(..., description="The platform the post came from, e.g., 'linkedin'")
    post_id: str = Field(..., description="The unique ID of the post on the platform")
    post_url: HttpUrl = Field(..., description="A direct URL to the original post")
    content: str = Field(..., description="The text content of the post")
    published_at: datetime = Field(..., description="The timestamp when the post was published")
    author: AuthorDetails = Field(..., description="Details of the post's author")
    engagement: EngagementMetrics = Field(..., description="Engagement metrics for the post")
