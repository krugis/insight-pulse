from pydantic import BaseModel, HttpUrl, EmailStr, Field
from typing import List, Optional

class AgentCreate(BaseModel):
    # Python code uses snake_case for attributes
    email: EmailStr
    plan_type: str = Field(..., alias='plan')
    apify_token: Optional[str] = Field(None, alias='apifyToken')
    openai_token: Optional[str] = Field(None, alias='openaiToken')
    digest_tone: str = Field(..., alias='digestTone')
    post_tone: str = Field(..., alias='postTone')
    linkedin_urls: List[HttpUrl] = Field(..., alias='linkedinUrls')

    class Config:
        from_attributes = True
        # This tells Pydantic to read the JSON using the aliases
        populate_by_name = True

class AgentResponse(BaseModel):
    id: int
    email: EmailStr
    plan_type: str
    
    class Config:
        from_attributes = True