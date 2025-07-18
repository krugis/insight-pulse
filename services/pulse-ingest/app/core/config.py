import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # This will automatically load the APIFY_API_TOKEN from an environment variable.
    # The model_config line tells pydantic to look for a .env file if it exists.
    APIFY_API_TOKEN: str

    model_config = SettingsConfigDict(env_file=".env")

# Create a single instance to be used across the application
settings = Settings()
