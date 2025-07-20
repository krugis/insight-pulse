from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@postgres/mydatabase"
    # We will need a secret key to encrypt the API tokens
    ENCRYPTION_KEY: str = "a_very_secret_key_that_you_should_change"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()