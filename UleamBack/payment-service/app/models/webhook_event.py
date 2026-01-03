"""
Webhook Event model - Normalized event storage.

Stores all webhook events from providers and partners in a normalized format.
Enables event replay, debugging, and audit trails.

Business Rules:
- All webhooks are stored before processing
- Failed processing can be retried
- Events are immutable after creation
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, TIMESTAMP,
    func, Text, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from ..database import Base


class WebhookEvent(Base):
    """
    Webhook event entity for normalized storage.
    
    Stores all webhook events from any source (Stripe, MercadoPago, Mock, Partners)
    in a normalized format for processing and audit.
    
    Attributes:
        id: Primary key
        event_type: Normalized event type (payment.success, booking.confirmed, etc.)
        source: Event source (stripe, mercadopago, mock, partner)
        payload_json: Normalized event payload
        processed: Processing status
        error_message: Processing error details
        created_at: Event receipt timestamp
        updated_at: Last processing attempt timestamp
    
    Processing Flow:
        1. Webhook received
        2. Create WebhookEvent (processed=False)
        3. Process event asynchronously
        4. Update processed=True or record error
    """
    
    __tablename__ = "webhook_event"
    
    # ===== Primary Key =====
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        comment="Internal event ID"
    )
    
    # ===== Event Classification =====
    event_type = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Normalized event type: payment.success, payment.failed, booking.confirmed, etc."
    )
    
    source = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Event source: stripe, mercadopago, mock, partner:{partner_id}"
    )
    
    # ===== Event Data =====
    payload_json = Column(
        JSONB,
        nullable=False,
        comment="Normalized event payload with all relevant data"
    )
    
    # ===== Processing Status =====
    processed = Column(
        Boolean,
        default=False,
        index=True,
        comment="Processing status (True = successfully processed)"
    )
    
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if processing failed"
    )
    
    # ===== Audit Fields =====
    creado_en = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
        comment="Event receipt timestamp (UTC)"
    )
    
    actualizado_en = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
        comment="Last processing attempt timestamp (UTC)"
    )
    
    # ===== Constraints =====
    __table_args__ = (
        Index("ix_webhook_event_type_processed", "event_type", "processed"),
        Index("ix_webhook_event_source_created", "source", "creado_en"),
        Index("ix_webhook_event_processed_created", "processed", "creado_en"),
        {"comment": "Normalized webhook events from all sources"}
    )
    
    def __repr__(self) -> str:
        return (
            f"<WebhookEvent(id={self.id}, "
            f"type={self.event_type}, "
            f"source={self.source}, "
            f"processed={self.processed})>"
        )
    
    @property
    def is_from_provider(self) -> bool:
        """Check if event is from a payment provider"""
        return self.source in ["stripe", "mercadopago", "mock"]
    
    @property
    def is_from_partner(self) -> bool:
        """Check if event is from a partner"""
        return self.source.startswith("partner:")
    
    @property
    def partner_id(self) -> int:
        """Extract partner ID from source if applicable"""
        if self.is_from_partner:
            try:
                return int(self.source.split(":")[1])
            except (IndexError, ValueError):
                return None
        return None
    
    @property
    def needs_retry(self) -> bool:
        """Check if event processing should be retried"""
        return not self.processed and self.error_message is not None
    
    def mark_as_processed(self):
        """Mark event as successfully processed"""
        self.processed = True
        self.error_message = None
    
    def mark_as_failed(self, error: str):
        """
        Mark event processing as failed.
        
        Args:
            error: Error message
        """
        self.processed = False
        self.error_message = error
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "source": self.source,
            "payload": self.payload_json,
            "processed": self.processed,
            "error_message": self.error_message,
            "created_at": self.creado_en.isoformat() if self.creado_en else None,
            "updated_at": self.actualizado_en.isoformat() if self.actualizado_en else None
        }
    
    @staticmethod
    def get_event_types() -> list:
        """
        Get list of supported event types.
        
        Returns:
            list: Event types
        """
        return [
            # Payment events
            "payment.success",
            "payment.failed",
            "payment.refunded",
            "payment.cancelled",
            
            # Booking events (for partners)
            "booking.confirmed",
            "booking.cancelled",
            "booking.updated",
            
            # Partner-specific events (examples)
            "service.activated",
            "tour.purchased",
            "order.created",
            "order.completed"
        ]
