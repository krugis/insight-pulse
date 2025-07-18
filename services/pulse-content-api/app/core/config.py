from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:29092"
    KAFKA_POSTS_TOPIC: str = "new_posts"
    OPENSEARCH_HOST: str = "opensearch"
    OPENSEARCH_PORT: int = 9200
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
