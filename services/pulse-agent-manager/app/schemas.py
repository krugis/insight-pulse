from pydantic import BaseModel, HttpUrl, EmailStr
from typing import List, Optional

class ProfileBase(BaseModel):
    url: HttpUrl

class AgentBase(BaseModel):
    email: EmailStr
    plan_type: str
    apify_token: Optional[str] = None
    openai_token: Optional[str] = None
    digest_tone: str
    post_tone: str
    linkedin_urls: List[HttpUrl]

class AgentCreate(AgentBase):
    pass

class Agent(AgentBase):
    id: int

    class Config:
        orm_mode = True