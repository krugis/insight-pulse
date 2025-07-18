from pydantic import BaseModel, Field
from datetime import datetime

class StandardPost(BaseModel):
    source: str = Field(..., description="The platform the post came from, e.g., 'linkedin'")
    post_id: str = Field(..., description="The unique ID of the post on the platform")
    author_id: str = Field(..., description="The unique ID of the author on the platform")
    content: str = Field(..., description="The text content of the post")
    post_url: str = Field(..., description="A direct URL to the original post")
    published_at: datetime = Field(..., description="The timestamp when the post was published")
