"""
Payment Provider Configuration model.

Stores configuration for different payment providers (Stripe, MercadoPago, Mock).
Allows dynamic configuration without code changes.

Business Rules:
- One configuration per provider name
- Sensitive data encrypted in config_json
- Only one provider can be default at a time
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, TIMESTAMP,
    func, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from ..database import Base


class PaymentProviderConfig(Base):
    """
    Payment provider configuration entity.
    
    Stores API credentials and settings for payment providers.
    Allows runtime configuration without code deployment.
    
    Attributes:
        id: Primary key
        name: Provider identifier (stripe, mercadopago, mock)
        is_active: Provider status
        config_json: Provider-specific configuration (API keys, etc.)
        created_at: Configuration creation timestamp
        updated_at: Last update timestamp
    
    Note:
        config_json should store encrypted credentials in production.
    """
    
    __tablename__ = "payment_provider_config"
    
    # ===== Primary Key =====
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        comment="Internal config ID"
    )
    
    # ===== Provider Identification =====
    name = Column(
        String(50),
        unique=True,
        nullable=False,
        comment="Provider identifier: stripe, mercadopago, mock"
    )
    
    # ===== Status =====
    is_active = Column(
        Boolean,
        default=True,
        index=True,
        comment="Provider active status"
    )
    
    # ===== Configuration =====
    config_json = Column(
        JSONB,
        default={},
        nullable=False,
        comment="Provider-specific configuration (API keys, webhook secrets, etc.)"
    )
    
    # ===== Audit Fields =====
    creado_en = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
        comment="Configuration creation timestamp (UTC)"
    )
    
    actualizado_en = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
        comment="Last update timestamp (UTC)"
    )
    
    # ===== Constraints =====
    __table_args__ = (
        CheckConstraint(
            "name IN ('stripe', 'mercadopago', 'mock')",
            name="chk_provider_name_valid"
        ),
        Index("ix_provider_name_active", "name", "is_active"),
        {"comment": "Payment provider configurations"}
    )
    
    def __repr__(self) -> str:
        return (
            f"<PaymentProviderConfig(id={self.id}, "
            f"name={self.name}, "
            f"active={self.is_active})>"
        )
    
    @property
    def is_stripe(self) -> bool:
        """Check if this is Stripe configuration"""
        return self.name == "stripe"
    
    @property
    def is_mercadopago(self) -> bool:
        """Check if this is MercadoPago configuration"""
        return self.name == "mercadopago"
    
    @property
    def is_mock(self) -> bool:
        """Check if this is Mock configuration"""
        return self.name == "mock"
    
    def get_config_value(self, key: str, default=None):
        """
        Get configuration value from config_json.
        
        Args:
            key: Configuration key
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        return self.config_json.get(key, default)
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert to dictionary for serialization.
        
        Args:
            include_sensitive: Include sensitive data from config_json
        
        Returns:
            dict: Provider configuration
        """
        data = {
            "id": self.id,
            "name": self.name,
            "is_active": self.is_active,
            "created_at": self.creado_en.isoformat() if self.creado_en else None,
            "updated_at": self.actualizado_en.isoformat() if self.actualizado_en else None
        }
        
        if include_sensitive:
            data["config"] = self.config_json
        else:
            # Return sanitized config (hide API keys)
            sanitized_config = {}
            for key, value in self.config_json.items():
                if any(sensitive in key.lower() for sensitive in ['key', 'secret', 'token', 'password']):
                    sanitized_config[key] = "***HIDDEN***"
                else:
                    sanitized_config[key] = value
            data["config"] = sanitized_config
        
        return data
