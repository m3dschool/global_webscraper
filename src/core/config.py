from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "postgresql://user:password@localhost:5432/webscraper"
    redis_url: str = "redis://localhost:6379/0"
    
    gemini_api_key: str
    
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    max_concurrent_scrapes: int = 5
    default_request_timeout: int = 30
    retry_attempts: int = 3
    
    proxy_enabled: bool = False
    proxy_pool_size: int = 10
    
    prometheus_port: int = 8000
    log_level: str = "INFO"
    
    debug: bool = False

    class Config:
        env_file = ".env"


settings = Settings()