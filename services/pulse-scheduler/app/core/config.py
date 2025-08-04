from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    # Default to 1:00 AM UTC daily, but can be overridden in .env
    SCHEDULE_CRON: str = "0 1 * * *" 
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()