from pydantic import BaseModel, Field, HttpUrl, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- AgentBase: Common attributes (WITHOUT config_data as a required field here)
class AgentBase(BaseModel):
    agent_name: str = Field(..., min_length=3, max_length=100)
    status: str = "active" # Default status

# --- AgentCreate: Explicitly defines all fields received from frontend
class AgentCreate(AgentBase): # Inherits agent_name, status
    email: str # User's email (for registration/linking)
    password: str # User's password (for registration/login)
    plan: str # 'subscribe' or 'byok'
    linkedin_urls: List[str] = Field(..., min_length=1, max_length=20)
    digest_tone: str
    post_tone: str
    apify_token: Optional[str] = None
    openai_token: Optional[str] = None

# --- AgentStatusUpdate (remains same)
class AgentStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|paused|error)$")

# --- AgentResponse: Includes config_data as this is part of BFF's internal model
class AgentResponse(AgentBase): # Inherits agent_name, status
    id: int # BFF's internal ID
    user_id: int
    pulse_agent_manager_id: str # ID from the external manager
    config_data: Dict[str, Any] # This is now part of the response model, populated by BFF
    apify_token: Optional[str] = None # Include if BYOK
    openai_token: Optional[str] = None # Include if BYOK
    is_deleted: bool = False # Soft delete flag
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
    generated_digest_url: Optional[str] = None
    generated_post_url: Optional[str] = None

    class ConfigDict:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class AgentUpdate(BaseModel):
    agent_name: Optional[str] = Field(None, min_length=3, max_length=100)
    status: Optional[str] = Field(None, pattern="^(active|paused|error)$")
    linkedin_urls: Optional[List[str]] = Field(None, min_length=1, max_length=20)
    digest_tone: Optional[str] = None
    post_tone: Optional[str] = None
    apify_token: Optional[str] = None
    openai_token: Optional[str] = None
    is_deleted: Optional[bool] = None