"""Application configuration."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "AI Agent App"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])

    # Environment
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    # Redis Cache
    REDIS_URL: str | None = None  # 例: "redis://localhost:6379/0"
    CACHE_TTL: int = 300  # デフォルトキャッシュTTL（秒）

    # Storage
    STORAGE_BACKEND: Literal["local", "azure"] = "local"
    LOCAL_STORAGE_PATH: str = "./uploads"

    # Azure Storage (for staging/production)
    AZURE_STORAGE_CONNECTION_STRING: str | None = None
    AZURE_STORAGE_CONTAINER_NAME: str = "uploads"

    # LLM Configuration
    # Anthropic
    ANTHROPIC_API_KEY: str | None = None

    # OpenAI / Azure OpenAI
    OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_OPENAI_DEPLOYMENT_NAME: str | None = None

    # LangSmith (optional for tracing)
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str | None = None
    LANGCHAIN_PROJECT: str = "ai-agent-app"

    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB default

    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


settings = Settings()
