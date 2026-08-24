import json
from typing import List, Union, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CV RAG System API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    RUNNING_IN_DOCKER: bool = False

    # Database Settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "cv_rag"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/cv_rag"

    # CORS Configuration
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:5173", "http://localhost:3000"]

    # GPU Endpoint configuration
    GPU_ENDPOINT_URL: str = "https://router.huggingface.co/v1"
    GPU_API_KEY: str = ""
    GPU_MODEL_NAME: str = "google/gemma-3-4b-it"

    # Cloud Embedding configuration
    CLOUD_EMBEDDING_URL: str = "https://router.huggingface.co/v1"
    CLOUD_EMBEDDING_KEY: str = ""
    CLOUD_EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    # OpenAI-compatible library fallback
    OPENAI_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Parse CORS_ORIGINS if passed as a JSON string
        if isinstance(self.CORS_ORIGINS, str):
            try:
                self.CORS_ORIGINS = json.loads(self.CORS_ORIGINS)
            except json.JSONDecodeError:
                self.CORS_ORIGINS = [
                    origin.strip() 
                    for origin in self.CORS_ORIGINS.split(",") 
                    if origin.strip()
                ]
        
        # Automatically point to localhost if running outside Docker and URL points to 'db'
        if not self.RUNNING_IN_DOCKER and "@db:" in self.DATABASE_URL:
            self.DATABASE_URL = self.DATABASE_URL.replace("@db:", "@localhost:")

settings = Settings()
# Reload trigger comment.
