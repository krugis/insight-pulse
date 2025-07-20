from pydantic import BaseModel, HttpUrl, EmailStr, Field
from typing import List, Optional

class AgentCreate(BaseModel):
    email: EmailStr
    plan: str = Field(..., alias='plan_type') # Accept 'plan' and map it to 'plan_type'
    apify_token: Optional[str] = Field(None, alias='apifyToken')
    openai_token: Optional[str] = Field(None, alias='openaiToken')
    digest_tone: str = Field(..., alias='digestTone')
    post_tone: str = Field(..., alias='postTone')
    linkedin_urls: List[HttpUrl] = Field(..., alias='linkedinUrls')

    class Config:
        from_attributes = True
        populate_by_name = True # Allow both alias and field name

class AgentResponse(BaseModel):
    id: int
    email: EmailStr
    plan_type: str

    class Config:
        from_attributes = True