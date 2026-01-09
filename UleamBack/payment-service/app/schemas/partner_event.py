"""
Partner Event Schemas

Schemas para eventos recibidos de partners externos.
Define el contrato de comunicación B2B bidireccional.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime


class PartnerEventBase(BaseModel):
    """
    Schema base para eventos de partners.
    
    Todos los eventos de partners deben incluir estos campos.
    """
    event_type: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Tipo de evento (ej: booking.confirmed, tour.purchased)"
    )
    event_id: Optional[str] = Field(
        None,
        description="ID único del evento (para idempotencia)"
    )
    timestamp: int = Field(
        ...,
        description="Timestamp Unix del evento"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata adicional del evento"
    )
    
    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Validar formato de event_type (formato: resource.action)"""
        if "." not in v:
            raise ValueError("event_type must be in format 'resource.action'")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "booking.confirmed",
                "event_id": "evt_abc123xyz",
                "timestamp": 1737336000,
                "metadata": {
                    "booking_id": "book_123",
                    "user_id": 42
                }
            }
        }


class BookingConfirmedEvent(PartnerEventBase):
    """
    Evento: Hotel confirmó una reserva.
    
    Este evento indica que un partner (hotel) ha confirmado una reserva
    y espera que se procese el pago.
    """
    event_type: str = Field(default="booking.confirmed")
    booking_id: str = Field(..., description="ID de la reserva en el sistema del partner")
    payment_id: Optional[str] = Field(None, description="ID del pago relacionado (si existe)")
    amount: float = Field(..., gt=0, description="Monto de la reserva")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    customer_email: Optional[str] = Field(None, description="Email del cliente")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "booking.confirmed",
                "event_id": "evt_book_123",
                "timestamp": 1737336000,
                "booking_id": "book_123",
                "payment_id": "pay_456",
                "amount": 150.00,
                "currency": "USD",
                "customer_email": "usuario@example.com",
                "metadata": {
                    "room_type": "suite",
                    "check_in": "2026-02-01",
                    "check_out": "2026-02-05"
                }
            }
        }


class TourPurchasedEvent(PartnerEventBase):
    """
    Evento: Tour fue comprado por un cliente.
    
    Este evento indica que un partner (agencia de tours) vendió un paquete
    relacionado con nuestra reserva.
    """
    event_type: str = Field(default="tour.purchased")
    tour_id: str = Field(..., description="ID del tour")
    booking_id: Optional[str] = Field(None, description="ID de reserva relacionada")
    payment_id: Optional[str] = Field(None, description="ID del pago relacionado")
    amount: float = Field(..., gt=0, description="Monto del tour")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "tour.purchased",
                "event_id": "evt_tour_789",
                "timestamp": 1737336000,
                "tour_id": "tour_xyz",
                "booking_id": "book_123",
                "payment_id": "pay_456",
                "amount": 75.00,
                "currency": "USD",
                "metadata": {
                    "tour_name": "City Historical Tour",
                    "date": "2026-02-03",
                    "participants": 2
                }
            }
        }


class ServiceActivatedEvent(PartnerEventBase):
    """
    Evento: Servicio adicional fue activado.
    
    Este evento indica que un partner activó un servicio adicional
    relacionado con el pago/reserva.
    """
    event_type: str = Field(default="service.activated")
    service_id: str = Field(..., description="ID del servicio")
    service_type: str = Field(..., description="Tipo de servicio (ej: spa, restaurant)")
    payment_id: Optional[str] = Field(None, description="ID del pago relacionado")
    amount: Optional[float] = Field(None, gt=0, description="Monto del servicio")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "service.activated",
                "event_id": "evt_svc_999",
                "timestamp": 1737336000,
                "service_id": "svc_spa_01",
                "service_type": "spa",
                "payment_id": "pay_456",
                "amount": 50.00,
                "currency": "USD",
                "metadata": {
                    "service_name": "Full Body Massage",
                    "date": "2026-02-02",
                    "duration_minutes": 60
                }
            }
        }


class BookingCancelledEvent(PartnerEventBase):
    """
    Evento: Reserva fue cancelada por el partner.
    
    Este evento indica que un partner canceló una reserva,
    lo que podría requerir un reembolso.
    """
    event_type: str = Field(default="booking.cancelled")
    booking_id: str = Field(..., description="ID de la reserva cancelada")
    payment_id: Optional[str] = Field(None, description="ID del pago a reembolsar")
    reason: Optional[str] = Field(None, description="Razón de la cancelación")
    refund_amount: Optional[float] = Field(None, description="Monto a reembolsar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "booking.cancelled",
                "event_id": "evt_cancel_555",
                "timestamp": 1737336000,
                "booking_id": "book_123",
                "payment_id": "pay_456",
                "reason": "Customer request",
                "refund_amount": 150.00,
                "metadata": {
                    "cancelled_by": "customer",
                    "cancellation_fee": 0.00
                }
            }
        }


class PartnerEventResponse(BaseModel):
    """Response cuando se procesa un evento de partner exitosamente"""
    status: str = Field(default="processed", description="Estado del procesamiento")
    event_id: Optional[str] = Field(None, description="ID del evento procesado")
    message: Optional[str] = Field(None, description="Mensaje descriptivo")
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "processed",
                "event_id": "evt_abc123",
                "message": "Event booking.confirmed processed successfully",
                "processed_at": "2026-01-19T10:30:00Z"
            }
        }


# Mapeo de event_type a schema
EVENT_TYPE_MAPPING = {
    "booking.confirmed": BookingConfirmedEvent,
    "tour.purchased": TourPurchasedEvent,
    "service.activated": ServiceActivatedEvent,
    "booking.cancelled": BookingCancelledEvent,
}


def get_event_schema(event_type: str) -> Optional[type[PartnerEventBase]]:
    """
    Obtiene el schema apropiado para un event_type.
    
    Args:
        event_type: Tipo de evento
    
    Returns:
        Schema class o None si no existe
    """
    return EVENT_TYPE_MAPPING.get(event_type)
