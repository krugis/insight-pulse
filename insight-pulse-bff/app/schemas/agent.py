from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime 

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

class AgentRun(BaseModel):
    run_id: str = Field(..., description="Unique identifier for this specific agent run")
    agent_id: int = Field(..., description="Internal BFF Agent ID")
    timestamp: datetime = Field(..., description="Time of the agent run")
    status: str = Field(..., pattern="^(completed|failed|running)$", description="Status of the run")
    output_summary: Optional[str] = Field(None, description="Brief summary of the run's output")
    # In a real system, you might have links to full logs or generated content here
    generated_digest_url: Optional[str] = None
    generated_post_url: Optional[str] = None

    class ConfigDict:
        from_attributes = True
        # This is crucial for Pydantic to correctly serialize datetime objects to ISO format
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }