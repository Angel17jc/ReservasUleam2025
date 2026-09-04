"""
Configuration Module

Gestiona todas las variables de entorno y configuraciones del AI Service.
Implementa el patrón Settings con Pydantic para validación y type safety.

Principios aplicados:
- Single Responsibility: Solo maneja configuración
- Open/Closed: Extensible sin modificar código existente
- Dependency Inversion: Inyección de configuración
"""
import logging
from pydantic import Field, field_validator, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Union


class Settings(BaseSettings):
    """
    Configuración global del AI Service.
    
    Todas las variables se cargan desde el archivo .env o variables de entorno.
    Pydantic valida automáticamente los tipos y valores requeridos.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ===== Database Configuration =====
    DATABASE_URL: str = Field(
        ...,  # obligatoria: se inyecta por entorno, sin credenciales por defecto
        description="PostgreSQL connection string"
    )
    
    # ===== JWT Configuration =====
    SECRET_KEY: str = Field(
        ...,  # obligatoria: debe coincidir con auth-service
        min_length=32,
        description="JWT secret key (shared with all services)"
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15,
        description="JWT token expiration in minutes"
    )
    
    # ===== LLM Providers Configuration =====
    DEFAULT_LLM_PROVIDER: str = Field(
        default="gemini",
        description="Default LLM provider (gemini | groq)"
    )
    GEMINI_API_KEY: Optional[str] = Field(
        default=None,
        description="Google Gemini API key"
    )
    GROQ_API_KEY: Optional[str] = Field(
        default=None,
        description="Groq API key"
    )
    
    # ===== Service Integration URLs =====
    REST_SERVICE_URL: str = Field(
        default="http://localhost:8000",
        description="REST Service base URL"
    )
    PAYMENT_SERVICE_URL: str = Field(
        default="http://localhost:8001",
        description="Payment Service base URL"
    )
    AUTH_SERVICE_URL: str = Field(
        default="http://localhost:9000",
        description="Auth Service base URL"
    )
    WEBSOCKET_SERVICE_URL: str = Field(
        default="http://localhost:3001",
        description="WebSocket Service base URL"
    )
    WEBSOCKET_SERVICE_URL: HttpUrl = Field(
        default="http://localhost:3001",
        description="WebSocket Service base URL"
    )
    
    # ===== Server Configuration =====
    PORT: int = Field(
        default=5000,
        ge=1024,
        le=65535,
        description="Server port"
    )
    HOST: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment (development, production)"
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    API_PREFIX: str = Field(
        default="api/v1",
        description="API prefix for all endpoints"
    )
    
    # ===== CORS Configuration =====
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default=["http://localhost:8084"],
        description="Allowed CORS origins (lista o cadena separada por comas)"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Acepta 'a,b' desde el entorno ademas de una lista JSON."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # ===== Storage Configuration =====
    UPLOAD_DIR: str = Field(
        default="../attached_assets/ai_uploads",
        description="Directory for uploaded files"
    )
    MAX_FILE_SIZE_MB: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum file size in MB"
    )
    ALLOWED_IMAGE_FORMATS: List[str] = Field(
        default=["jpg", "jpeg", "png", "webp"],
        description="Allowed image formats"
    )
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    # ===== Logging Configuration =====
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    LOG_FORMAT: str = Field(
        default="json",
        description="Logging format (json | text)"
    )
    
    # ===== Rate Limiting =====
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=30,
        ge=1,
        description="Rate limit per minute per user"
    )
    
    # ===== Validators =====
    @field_validator("DEFAULT_LLM_PROVIDER")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Validate LLM provider choice."""
        allowed = ["gemini", "groq"]
        if v.lower() not in allowed:
            raise ValueError(f"DEFAULT_LLM_PROVIDER must be one of {allowed}")
        return v.lower()
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()
    
    def get_log_level(self) -> int:
        """Convert log level string to logging constant."""
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return levels[self.LOG_LEVEL]


# Singleton instance
settings = Settings()


# Logging configuration
def configure_logging():
    """Configure global logging based on settings."""
    logging.basicConfig(
        level=settings.get_log_level(),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


# Initialize logging
configure_logging()
