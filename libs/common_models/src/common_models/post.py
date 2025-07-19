from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional

class AuthorDetails(BaseModel):
    """Represents the author of a post. All fields are optional."""
    id: Optional[str] = Field(None, description="The unique public identifier of the author")
    name: Optional[str] = Field(None, description="The full name of the author")
    info: Optional[str] = Field(None, description="The author's title or headline")
    url: Optional[HttpUrl] = Field(None, description="A direct URL to the author's profile")

class EngagementMetrics(BaseModel):
    """Represents the engagement statistics of a post. Defaults to 0 if not present."""
    likes: int = Field(0, description="Total number of likes on the post")
    comments: int = Field(0, description="Total number of comments on the post")
    shares: int = Field(0, description="Total number of shares or reposts")

class StandardPost(BaseModel):
    """
    The standardized internal data model for a social media post.
    Only post_id is mandatory.
    """
    post_id: str = Field(..., description="The unique ID of the post on the platform")
    source: Optional[str] = Field(None, description="The platform the post came from, e.g., 'linkedin'")
    post_url: Optional[HttpUrl] = Field(None, description="A direct URL to the original post")
    content: Optional[str] = Field(None, description="The text content of the post")
    published_at: Optional[datetime] = Field(None, description="The timestamp when the post was published")
    author: Optional[AuthorDetails] = Field(None, description="Details of the post's author")
    engagement: Optional[EngagementMetrics] = Field(None, description="Engagement metrics for the post")