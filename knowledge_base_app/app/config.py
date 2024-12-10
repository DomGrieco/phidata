from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # OpenAI Configuration
    openai_api_key: str
    
    # Database Configuration
    db_host: str = "localhost"
    db_port: int = 5532
    db_name: str = "ai"
    db_user: str = "ai"
    db_password: str = "ai"
    db_url: str = "postgresql+psycopg://ai:ai@localhost:5532/ai"
    
    # Application Configuration
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # Vector Database Configuration
    vector_db_table: str = "knowledge_base"
    embeddings_model: str = "text-embedding-3-small"
    embeddings_dimensions: int = 1536
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings"""
    return Settings() 