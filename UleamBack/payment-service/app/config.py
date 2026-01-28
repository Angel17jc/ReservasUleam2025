"""
Configuration module for Payment Service.

Implements Pydantic Settings for environment variable management with:
- Type validation
- Default values
- Environment variable loading
- Multiple environment support (dev, prod)

Best Practices:
- All secrets from environment variables
- Validation at startup
- Immutable after initialization
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, HttpUrl


class Settings(BaseSettings):
    """
    Application settings with validation and type safety.
    
    Environment variables are automatically loaded from .env file
    and validated according to type hints.
    """
    
    # ===== Database Configuration =====
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/payment_service_db",
        description="PostgreSQL connection URL (using psycopg v3 driver)"
    )
    
    # ===== JWT Configuration (shared with auth-service) =====
    SECRET_KEY: str = Field(
        ...,  # Required
        min_length=32,
        description="JWT secret key (must match auth-service)"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=1, le=1440)
    
    # ===== Payment Providers Configuration =====
    STRIPE_API_KEY: Optional[str] = Field(
        default=None,
        description="Stripe API key (sk_test_... or sk_live_...)"
    )
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(
        default=None,
        description="Stripe webhook signing secret"
    )
    MERCADOPAGO_ACCESS_TOKEN: Optional[str] = Field(
        default=None,
        description="MercadoPago access token"
    )
    MOCK_PROVIDER_ENABLED: bool = Field(
        default=True,
        description="Enable mock provider for development/testing"
    )
    
    # ===== Service Integration URLs =====
    REST_SERVICE_URL: HttpUrl = Field(
        default="http://localhost:8000",
        description="REST service base URL"
    )
    RESERVAS_INTERNAL_TOKEN: Optional[str] = Field(
        default=None,
        description="Shared secret to call rest-service internal endpoints"
    )
    WEBSOCKET_SERVICE_URL: HttpUrl = Field(
        default="http://localhost:3001",
        description="WebSocket service base URL"
    )
    AUTH_SERVICE_URL: HttpUrl = Field(
        default="http://localhost:9000",
        description="Auth service base URL"
    )
    
    # ===== Server Configuration =====
    PORT: int = Field(default=8001, ge=1024, le=65535)
    API_PREFIX: str = Field(default="api/v1", pattern="^[a-z0-9/]+$")
    HOST: str = Field(default="0.0.0.0")
    
    # ===== CORS Configuration =====
    CORS_ORIGINS: str | List[str] = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Allowed CORS origins (comma-separated string or list)"
    )
    
    # ===== Logging Configuration =====
    LOG_LEVEL: str = Field(
        default="INFO",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )
    LOG_FORMAT: str = Field(
        default="json",
        pattern="^(json|text)$"
    )
    
    # ===== Webhook Configuration =====
    WEBHOOK_TIMEOUT_SECONDS: int = Field(default=30, ge=5, le=120)
    WEBHOOK_MAX_RETRIES: int = Field(default=3, ge=0, le=10)
    WEBHOOK_RETRY_DELAY_SECONDS: int = Field(default=60, ge=10, le=600)
    
    # ===== Security Configuration =====
    HMAC_SECRET_LENGTH: int = Field(default=64, ge=32, le=128)
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, ge=10, le=1000)
    
    # ===== Application Metadata =====
    APP_NAME: str = Field(default="ULEAM Payment Service")
    APP_VERSION: str = Field(default="1.0.0")
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra environment variables
    )
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        """Ensure environment is lowercase"""
        return v.lower()
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT == "development"
    
    @property
    def database_pool_size(self) -> int:
        """Calculate optimal database pool size based on environment"""
        return 5 if self.is_development else 20
    
    @property
    def database_max_overflow(self) -> int:
        """Calculate max overflow for database connections"""
        return 5 if self.is_development else 10
    
    def validate_payment_providers(self) -> dict:
        """
        Validate that at least one payment provider is configured.
        
        Returns:
            dict: Status of each provider
        """
        providers_status = {
            "mock": self.MOCK_PROVIDER_ENABLED,
            "stripe": bool(self.STRIPE_API_KEY and self.STRIPE_WEBHOOK_SECRET),
            "mercadopago": bool(self.MERCADOPAGO_ACCESS_TOKEN)
        }
        
        if not any(providers_status.values()):
            raise ValueError("At least one payment provider must be configured")
        
        return providers_status


# Global settings instance
settings = Settings()

# Validate on import
if not settings.is_development:
    # In production, require explicit provider configuration
    if settings.MOCK_PROVIDER_ENABLED:
        raise ValueError("Mock provider should be disabled in production")
