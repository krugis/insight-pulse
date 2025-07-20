from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Example: When you use a real service like SendGrid, you would add:
    # SENDGRID_API_KEY: str
    # SENDER_EMAIL: str = "noreply@aigora.com"
    
    # For now, it can be empty
    pass

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()