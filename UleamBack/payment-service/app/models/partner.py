"""
Partner model - External B2B integrations.

Manages partnerships with external systems for webhook communications.
Implements secure HMAC-based authentication for webhook exchanges.

Business Rules:
- Unique partner names
- Active webhooks must have valid URLs
- Shared secrets are cryptographically secure
- Event subscriptions are validated
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, TIMESTAMP,
    func, Text, CheckConstraint, Index, ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import secrets

from ..database import Base


class Partner(Base):
    """
    Partner entity for B2B webhook integrations.
    
    Represents an external system (otro grupo) that can:
    - Receive webhooks from our system
    - Send webhooks to our system
    
    Attributes:
        id: Primary key
        nombre: Partner display name (unique)
        webhook_url: Partner's webhook endpoint
        shared_secret: HMAC secret for signature validation
        eventos_suscritos: Array of event types partner wants to receive
        is_active: Partner status
        descripcion: Partner description
        created_at: Registration timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "partner"
    
    # ===== Primary Key =====
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        comment="Internal partner ID"
    )
    
    # ===== Partner Identification =====
    nombre = Column(
        String(200),
        nullable=False,
        unique=True,
        comment="Partner name (must be unique)"
    )
    
    descripcion = Column(
        Text,
        nullable=True,
        comment="Partner description or notes"
    )
    
    # ===== Webhook Configuration =====
    webhook_url = Column(
        String(500),
        nullable=False,
        comment="Partner's webhook endpoint URL (HTTPS recommended)"
    )
    
    shared_secret = Column(
        String(128),
        nullable=False,
        comment="HMAC-SHA256 secret for webhook signature validation"
    )
    
    eventos_suscritos = Column(
        JSONB,
        default=[],
        nullable=False,
        comment="Array of event types: ['booking.confirmed', 'payment.success']"
    )
    
    # ===== Status =====
    is_active = Column(
        Boolean,
        default=True,
        index=True,
        comment="Partner active status (inactive partners don't receive webhooks)"
    )
    
    # ===== Audit Fields =====
    creado_en = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
        comment="Partner registration timestamp (UTC)"
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
            "length(shared_secret) >= 32",
            name="chk_partner_secret_length"
        ),
        Index("ix_partner_active_created", "is_active", "creado_en"),
        {"comment": "External partners for B2B webhook integrations"}
    )
    
    def __repr__(self) -> str:
        return (
            f"<Partner(id={self.id}, "
            f"nombre={self.nombre}, "
            f"active={self.is_active})>"
        )
    
    @staticmethod
    def generate_secret(length: int = 64) -> str:
        """
        Generate cryptographically secure random secret.
        
        Args:
            length: Secret length in characters
        
        Returns:
            str: Hex-encoded random secret
        """
        return secrets.token_hex(length // 2)
    
    def is_subscribed_to(self, event_type: str) -> bool:
        """
        Check if partner is subscribed to a specific event type.
        
        Args:
            event_type: Event type to check
        
        Returns:
            bool: True if subscribed and active
        """
        return self.is_active and event_type in (self.eventos_suscritos or [])
    
    def to_dict(self, include_secret: bool = False) -> dict:
        """
        Convert to dictionary for serialization.
        
        Args:
            include_secret: Include shared_secret in output (use with caution)
        
        Returns:
            dict: Partner data
        """
        data = {
            "id": self.id,
            "nombre": self.nombre,
            "webhook_url": self.webhook_url,
            "eventos_suscritos": self.eventos_suscritos,
            "is_active": self.is_active,
            "descripcion": self.descripcion,
            "created_at": self.creado_en.isoformat() if self.creado_en else None,
            "updated_at": self.actualizado_en.isoformat() if self.actualizado_en else None
        }
        
        if include_secret:
            data["shared_secret"] = self.shared_secret
        
        return data


class PartnerWebhookLog(Base):
    """
    Audit log for webhook communications with partners.
    
    Records every webhook sent to or received from partners for:
    - Debugging failed deliveries
    - Security audit trail
    - Performance monitoring
    
    Attributes:
        id: Primary key
        partner_id: Reference to partner
        event_type: Type of event
        payload_json: Webhook payload
        response_status: HTTP response code
        response_body: Partner's response
        signature_valid: Signature validation result
        error_message: Error details if failed
        direction: 'outgoing' or 'incoming'
        created_at: Log timestamp
    """
    
    __tablename__ = "partner_webhook_log"
    
    # ===== Primary Key =====
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        comment="Log entry ID"
    )
    
    # ===== Partner Reference =====
    partner_id = Column(
        Integer,
        nullable=False,
        index=True,
        comment="FK to partner.id"
    )
    
    # ===== Webhook Details =====
    event_type = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Event type (booking.confirmed, payment.success, etc.)"
    )
    
    payload_json = Column(
        JSONB,
        nullable=False,
        comment="Complete webhook payload"
    )
    
    # ===== Response Details =====
    response_status = Column(
        Integer,
        nullable=True,
        comment="HTTP status code from partner (200, 404, 500, etc.)"
    )
    
    response_body = Column(
        Text,
        nullable=True,
        comment="Response body from partner"
    )
    
    # ===== Security =====
    signature_valid = Column(
        Boolean,
        nullable=True,
        comment="HMAC signature validation result (for incoming webhooks)"
    )
    
    # ===== Error Tracking =====
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if webhook delivery failed"
    )
    
    # ===== Direction =====
    direction = Column(
        String(10),
        nullable=False,
        default="outgoing",
        comment="Webhook direction: 'outgoing' (sent to partner) or 'incoming' (received from partner)"
    )
    
    # ===== Timestamp =====
    creado_en = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
        comment="Log entry timestamp (UTC)"
    )
    
    # ===== Constraints =====
    __table_args__ = (
        CheckConstraint(
            "direction IN ('outgoing', 'incoming')",
            name="chk_webhook_direction"
        ),
        Index("ix_webhook_log_partner_created", "partner_id", "creado_en"),
        Index("ix_webhook_log_event_status", "event_type", "response_status"),
        {"comment": "Audit log for partner webhook communications"}
    )
    
    def __repr__(self) -> str:
        return (
            f"<PartnerWebhookLog(id={self.id}, "
            f"partner_id={self.partner_id}, "
            f"event={self.event_type}, "
            f"status={self.response_status})>"
        )
    
    @property
    def is_success(self) -> bool:
        """Check if webhook was successfully delivered"""
        return self.response_status is not None and 200 <= self.response_status < 300
    
    @property
    def is_outgoing(self) -> bool:
        """Check if webhook was sent to partner"""
        return self.direction == "outgoing"
    
    @property
    def is_incoming(self) -> bool:
        """Check if webhook was received from partner"""
        return self.direction == "incoming"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "partner_id": self.partner_id,
            "event_type": self.event_type,
            "payload": self.payload_json,
            "response_status": self.response_status,
            "response_body": self.response_body,
            "signature_valid": self.signature_valid,
            "error_message": self.error_message,
            "direction": self.direction,
            "created_at": self.creado_en.isoformat() if self.creado_en else None
        }
