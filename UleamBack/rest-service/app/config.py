import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database configuration - same as auth-service
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USERNAME: str = "Reservas_ULEAM"
    DB_PASSWORD: str = "123456"
    DB_NAME: str = "reservasuleam"
    
    # JWT configuration - MUST match auth-service exactly
    SECRET_KEY: str = "mi-secreto-auth-service-super-seguro-2025"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # WebSocket service
    WEBSOCKET_SERVICE_URL: str = "http://localhost:3001"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
