"""
Pydantic Schemas

Define los schemas de validación y serialización para el Payment Service.
Usa Pydantic v2 para validación de datos con type hints.
"""

from .payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentStatusUpdate,
    PaymentListResponse
)
from .webhook import (
    NormalizedWebhookEvent,
    WebhookEventResponse
)
from .partner import (
    PartnerCreate,
    PartnerResponse,
    PartnerWithSecret,
    PartnerUpdate,
    PartnerListResponse,
    WebhookDeliveryResult
)

__all__ = [
    # Payment schemas
    "PaymentCreate",
    "PaymentResponse",
    "PaymentStatusUpdate",
    "PaymentListResponse",
    
    # Webhook schemas
    "NormalizedWebhookEvent",
    "WebhookEventResponse",
    
    # Partner schemas
    "PartnerCreate",
    "PartnerResponse",
    "PartnerWithSecret",
    "PartnerUpdate",
    "PartnerListResponse",
    "WebhookDeliveryResult"
]