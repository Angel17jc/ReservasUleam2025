"""
Payment model - Core transaction entity.

Represents a payment transaction in the system with:
- External provider integration
- Status tracking
- Audit trail
- Metadata for business logic

Business Rules:
- One payment per reserva
- Immutable external_payment_id
- Status transitions must be valid
- Amount must be positive
"""

from sqlalchemy import (
    Column, Integer, String, Numeric, TIMESTAMP, 
    func, Text, Enum as SQLEnum, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from decimal import Decimal
import enum
from datetime import datetime

from ..database import Base


class PaymentStatus(str, enum.Enum):
    """
    Payment status enumeration.
    
    Status Flow:
        pending → completed (success)
        pending → failed (error)
        completed → refunded (refund requested)
        pending → cancelled (user cancelled)
    """
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    
    @classmethod
    def is_valid_transition(cls, from_status: str, to_status: str) -> bool:
        """
        Validate if status transition is allowed.
        
        Args:
            from_status: Current status
            to_status: Desired status
        
        Returns:
            bool: True if transition is valid
        """
        valid_transitions = {
            cls.PENDING: [cls.COMPLETED, cls.FAILED, cls.CANCELLED],
            cls.COMPLETED: [cls.REFUNDED],
            cls.FAILED: [cls.PENDING],  # Allow retry
            cls.REFUNDED: [],  # Final state
            cls.CANCELLED: []  # Final state
        }
        
        return to_status in valid_transitions.get(from_status, [])
    
    @classmethod
    def is_final_status(cls, status: str) -> bool:
        """Check if status is final (no more transitions allowed)"""
        return status in [cls.REFUNDED, cls.CANCELLED]


class Payment(Base):
    """
    Payment entity representing a transaction.
    
    Attributes:
        id: Primary key
        external_payment_id: Unique ID from payment provider
        reserva_id: Foreign key to reserva (rest-service)
        usuario_id: Foreign key to usuario (rest-service)
        provider_name: Payment provider identifier
        amount: Payment amount (always positive)
        currency: ISO 4217 currency code
        status: Current payment status
        metadata_json: Additional business data
        error_message: Error details if failed
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "payment"
    
    # ===== Primary Key =====
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        comment="Internal payment ID"
    )
    
    # ===== External References =====
    external_payment_id = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique ID from payment provider (Stripe, MercadoPago, Mock)"
    )
    
    # ===== Business References (Foreign Keys to rest-service) =====
    reserva_id = Column(
        Integer,
        nullable=False,
        index=True,
        comment="FK to rest-service.reserva.id"
    )
    
    usuario_id = Column(
        Integer,
        nullable=False,
        index=True,
        comment="FK to rest-service.usuario.id"
    )
    
    # ===== Provider Information =====
    provider_name = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Payment provider: stripe, mercadopago, mock"
    )
    
    # ===== Payment Details =====
    amount = Column(
        Numeric(10, 2),
        nullable=False,
        comment="Payment amount (positive decimal)"
    )
    
    currency = Column(
        String(3),
        nullable=False,
        default="USD",
        comment="ISO 4217 currency code (USD, EUR, MXN, etc.)"
    )
    
    # ===== Status Tracking =====
    status = Column(
        SQLEnum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True,
        comment="Current payment status"
    )
    
    # ===== Additional Data =====
    metadata_json = Column(
        JSONB,
        default={},
        nullable=False,
        comment="Additional payment metadata (client_secret, checkout_url, etc.)"
    )
    
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if payment failed"
    )
    
    # ===== Audit Fields =====
    creado_en = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
        comment="Creation timestamp (UTC)"
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
            "amount > 0",
            name="chk_payment_amount_positive"
        ),
        CheckConstraint(
            "length(currency) = 3",
            name="chk_payment_currency_length"
        ),
        Index("ix_payment_status_created", "status", "creado_en"),
        Index("ix_payment_reserva_usuario", "reserva_id", "usuario_id"),
        {"comment": "Payment transactions with provider integration"}
    )
    
    def __repr__(self) -> str:
        return (
            f"<Payment(id={self.id}, "
            f"external_id={self.external_payment_id}, "
            f"amount={self.amount} {self.currency}, "
            f"status={self.status})>"
        )
    
    @property
    def is_completed(self) -> bool:
        """Check if payment is successfully completed"""
        return self.status == PaymentStatus.COMPLETED
    
    @property
    def is_pending(self) -> bool:
        """Check if payment is pending"""
        return self.status == PaymentStatus.PENDING
    
    @property
    def can_be_refunded(self) -> bool:
        """Check if payment can be refunded"""
        return self.status == PaymentStatus.COMPLETED
    
    @property
    def is_final(self) -> bool:
        """Check if payment status is final"""
        return PaymentStatus.is_final_status(self.status)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "external_payment_id": self.external_payment_id,
            "reserva_id": self.reserva_id,
            "usuario_id": self.usuario_id,
            "provider_name": self.provider_name,
            "amount": float(self.amount),
            "currency": self.currency,
            "status": self.status.value,
            "metadata": self.metadata_json,
            "error_message": self.error_message,
            "created_at": self.creado_en.isoformat() if self.creado_en else None,
            "updated_at": self.actualizado_en.isoformat() if self.actualizado_en else None
        }
