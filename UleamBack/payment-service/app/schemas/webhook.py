"""
Webhook Schemas

Define el formato normalizado de webhooks y sus schemas de validación.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime


class NormalizedWebhookEvent(BaseModel):
    """
    Evento de webhook normalizado.
    
    Todos los adapters deben convertir sus webhooks específicos a este formato común.
    Esto permite procesar webhooks de manera uniforme sin importar el provider.
    
    Ejemplo de normalización:
        Stripe "payment_intent.succeeded" -> event_type="payment.success"
        MercadoPago "payment.approved" -> event_type="payment.success"
    """
    
    event_type: str = Field(
        ...,
        description="Tipo de evento normalizado",
        examples=["payment.success", "payment.failed", "payment.refunded"]
    )
    payment_id: str = Field(
        ...,
        description="ID del pago en el provider externo",
        min_length=1
    )
    status: str = Field(
        ...,
        description="Estado del pago",
        pattern="^(pending|completed|failed|refunded|cancelled)$"
    )
    amount: float = Field(
        ...,
        description="Monto del pago en unidades (no centavos)",
        gt=0
    )
    currency: str = Field(
        ...,
        description="Código de moneda ISO 4217",
        min_length=3,
        max_length=3,
        pattern="^[A-Z]{3}$"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Datos adicionales del pago (reserva_id, usuario_id, etc.)"
    )
    error_message: Optional[str] = Field(
        None,
        description="Mensaje de error si el pago falló"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp del evento"
    )
    raw_event: Optional[Dict[str, Any]] = Field(
        None,
        description="Evento raw del provider (para debugging)",
        exclude=True  # No se serializa en respuestas
    )
    
    @field_validator("currency", mode="before")
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        """Convertir moneda a mayúsculas"""
        return v.upper() if isinstance(v, str) else v
    
    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Validar que el tipo de evento sea conocido"""
        allowed_events = {
            "payment.success",
            "payment.failed",
            "payment.cancelled",
            "payment.refunded",
            "payment.pending",
            "payment.processing"
        }
        if v not in allowed_events:
            raise ValueError(f"Unknown event type: {v}. Allowed: {allowed_events}")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "event_type": "payment.success",
                    "payment_id": "pay_abc123xyz",
                    "status": "completed",
                    "amount": 50.00,
                    "currency": "USD",
                    "metadata": {
                        "reserva_id": 123,
                        "usuario_id": 5,
                        "descripcion": "Reserva de sala A"
                    },
                    "error_message": None,
                    "timestamp": "2026-01-15T10:30:00Z"
                }
            ]
        }
    }
    
    def is_success(self) -> bool:
        """Verifica si el evento representa un pago exitoso"""
        return self.event_type == "payment.success" and self.status == "completed"
    
    def is_failure(self) -> bool:
        """Verifica si el evento representa un pago fallido"""
        return self.event_type == "payment.failed" or self.status == "failed"
    
    def get_reserva_id(self) -> Optional[int]:
        """Extrae el reserva_id del metadata"""
        return self.metadata.get("reserva_id")
    
    def get_usuario_id(self) -> Optional[int]:
        """Extrae el usuario_id del metadata"""
        return self.metadata.get("usuario_id")


class WebhookEventResponse(BaseModel):
    """
    Schema de respuesta para eventos de webhook almacenados.
    """
    
    id: int = Field(..., description="ID del registro del webhook")
    event_type: str = Field(..., description="Tipo de evento")
    source: str = Field(..., description="Fuente del webhook (stripe, mercadopago, etc.)")
    payment_id: Optional[str] = Field(None, description="ID del pago relacionado")
    processed: bool = Field(..., description="Si el webhook fue procesado")
    error_message: Optional[str] = Field(None, description="Error al procesar")
    created_at: datetime = Field(..., description="Fecha de recepción")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "event_type": "payment.success",
                    "source": "stripe",
                    "payment_id": "pay_abc123",
                    "processed": True,
                    "error_message": None,
                    "created_at": "2026-01-15T10:30:00Z"
                }
            ]
        }
    }
