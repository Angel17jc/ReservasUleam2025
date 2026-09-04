import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database configuration - same as auth-service
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USERNAME: str = "Reservas_ULEAM"
    DB_PASSWORD: str  # obligatoria: se inyecta por entorno
    DB_NAME: str = "reservasuleam"

    # Auth database (independent, owned by auth-service)
    AUTH_DB_HOST: str = "localhost"
    AUTH_DB_PORT: int = 5432
    AUTH_DB_USERNAME: str = "Reservas_ULEAM"
    AUTH_DB_PASSWORD: str  # obligatoria: se inyecta por entorno
    AUTH_DB_NAME: str = "auth_service_db"
    
    # JWT configuration - MUST match auth-service exactly
    SECRET_KEY: str  # obligatoria: debe coincidir con auth-service
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # WebSocket service
    WEBSOCKET_SERVICE_URL: str = "http://localhost:3001"

    # Internal provisioning secret (Auth -> REST sync de usuarios)
    INTERNAL_PROVISION_TOKEN: str  # obligatoria: secreto interno Auth -> REST
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
