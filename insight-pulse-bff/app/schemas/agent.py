from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AgentBase(BaseModel):
    agent_name: str = Field(..., min_length=3, max_length=100)
    status: str = "active"
    config_data: Dict[str, Any]

class AgentCreate(AgentBase):
    email: str # Not stored directly in Agent model, used for context or validation
    plan: str # 'subscribe' or 'byok'
    linkedin_urls: List[str] = Field(..., min_length=1, max_length=20)
    digest_tone: str
    post_tone: str
    apify_token: Optional[str] = None
    openai_token: Optional[str] = None

class AgentStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|paused|error)$")

class AgentResponse(AgentBase):
    id: int # BFF's internal ID
    user_id: int
    pulse_agent_manager_id: str # ID from the external manager
    apify_token: Optional[str] = None
    openai_token: Optional[str] = None

    class ConfigDict:
        from_attributes = True

class AgentDetailsResponse(AgentResponse):
    pass