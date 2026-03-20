from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Postgres
    POSTGRES_URL: str

    # Qdrant
    QDRANT_URL: str
    QDRANT_COLLECTION_NAME: str

    # OpenAlex
    OPEN_ALEX_API_KEY: str

    # Groq
    GROQ_API_KEY: str
    
    # Hugging Face
    HF_HUB_OFFLINE: int

    class Config:
        env_file=".env"

settings= Settings()