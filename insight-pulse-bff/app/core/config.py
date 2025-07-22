from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Database settings
    # Default to a PostgreSQL URL format for Docker Compose
    DATABASE_URL: str = "postgresql://aigora_db_user:supersecretkey@db:5432/aigora_db"
    PULSE_AGENT_MANAGER_BASE_URL: str = "http://pulse-agent-manager:8003"
    # Security settings
    SECRET_KEY: str = "supersecretkey" # CHANGE THIS IN PRODUCTION TO A LONG, RANDOM STRING!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # External API keys
    APIFY_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()