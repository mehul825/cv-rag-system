import json
from typing import List, Union
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

    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_CHAT_MODEL: str = "llama3.2"

    # Hugging Face Configuration
    HF_TOKEN: str = ""
    HF_MODEL: str = "google/gemma-3-4b-it"
    HF_API_URL: str = "https://router.huggingface.co/v1"

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

        # Automatically swap localhost for host.docker.internal when inside Docker container
        if self.RUNNING_IN_DOCKER and "localhost" in self.OLLAMA_BASE_URL:
            self.OLLAMA_BASE_URL = self.OLLAMA_BASE_URL.replace("localhost", "host.docker.internal")

settings = Settings()
# Reload trigger comment.
