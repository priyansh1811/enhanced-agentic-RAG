"""Configuration settings for Archon."""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    google_api_key: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    tavily_api_key: Optional[str] = Field(None, env="TAVILY_API_KEY")
    langsmith_api_key: Optional[str] = Field(None, env="LANGSMITH_API_KEY")
    
    # Database Configuration
    qdrant_url: str = Field("http://localhost:6333", env="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(None, env="QDRANT_API_KEY")
    
    # Application Configuration
    company_ticker: str = Field("MSFT", env="COMPANY_TICKER")
    company_name: str = Field("Microsoft", env="COMPANY_NAME")
    company_email: str = Field("analyst@archon.ai", env="COMPANY_EMAIL")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("logs/archon.log", env="LOG_FILE")
    
    # Memory and Storage
    memory_store_path: str = Field("data/memory_store.json", env="MEMORY_STORE_PATH")
    vector_store_path: str = Field("data/vector_store", env="VECTOR_STORE_PATH")
    
    # Model Configuration
    embedding_model: str = Field("sentence-transformers/all-MiniLM-L6-v2")
    llm_model: str = Field("gpt-4")
    temperature: float = Field(0.1)
    max_tokens: int = Field(4000)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
