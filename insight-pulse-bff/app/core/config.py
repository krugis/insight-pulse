from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql://user:password@db:5432/aigora_db"

    # Security settings
    SECRET_KEY: str = "supersecretkey" # CHANGE THIS IN PRODUCTION!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # External API keys (for BYOK plans)
    APIFY_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Base URL for other internal microservices
    PULSE_AGENT_MANAGER_BASE_URL: str = "http://pulse-agent-manager:8003"
    #PULSE_INGEST_BASE_URL: Optional[str] = None # Placeholder
    #PULSE_AI_CORE_BASE_URL: Optional[str] = None # Placeholder
    #PULSE_SCHEDULER_BASE_URL: Optional[str] = None # Placeholder
    ^#PULSE_EMAIL_BASE_URL: Optional[str] = None # Placeholder

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()