"""
Payment Schemas

Define los schemas de validación para operaciones de pago.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal


class PaymentCreate(BaseModel):
    """
    Schema para crear un nuevo pago.
    
    Simplificado para reservas aprobadas con monto fijo:
    - amount: fijo 20.00 (USD)
    - currency: USD
    - provider: stripe
    - reserva_id: obligatorio
    - description: opcional (se guarda en metadata)
    """
    
    reserva_id: int = Field(
        ...,
        description="ID de la reserva en el REST service",
        gt=0
    )
    amount: Decimal = Field(
        default=Decimal("20.00"),
        description="Monto fijo de la reserva (USD 20.00 / 2h)",
        gt=0,
        decimal_places=2
    )
    currency: str = Field(
        default="USD",
        description="Código de moneda ISO 4217",
        max_length=3,
        pattern="^[A-Z]{3}$"
    )
    provider: str = Field(
        default="stripe",
        description="Proveedor de pago a utilizar",
        pattern="^stripe$"
    )
    description: Optional[str] = Field(
        default=None,
        description="Descripción opcional que verá el usuario en el pago"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Datos adicionales del pago"
    )
    
    @field_validator("currency", mode="before")
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        """Convertir moneda a mayúsculas"""
        return v.upper() if isinstance(v, str) else v
    
    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validar que la moneda esté soportada"""
        allowed_currencies = {"USD"}
        if v not in allowed_currencies:
            raise ValueError(f"Currency must be one of {allowed_currencies}")
        return v
    
    @field_validator("provider", mode="before")
    @classmethod
    def lowercase_provider(cls, v: str) -> str:
        """Convertir provider a minúsculas"""
        return v.lower() if isinstance(v, str) else v
    
    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validar que el provider sea stripe (o mock/mercadopago si se habilitan)"""
        allowed_providers = {"stripe"}
        if v not in allowed_providers:
            raise ValueError("Solo se soporta stripe en este flujo")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "reserva_id": 123,
                    "description": "Pago de reserva aprobada",
                    "amount": 20.00,
                    "currency": "USD",
                    "provider": "stripe"
                }
            ]
        }
    )


class PaymentResponse(BaseModel):
    """
    Schema de respuesta de un pago.
    Incluye todos los datos del pago almacenado en BD.
    """
    
    id: int = Field(..., description="ID interno del pago")
    external_payment_id: str = Field(..., description="ID del pago en el provider")
    reserva_id: int = Field(..., description="ID de la reserva")
    usuario_id: int = Field(..., description="ID del usuario que creó el pago")
    provider_name: str = Field(..., description="Proveedor de pago utilizado")
    amount: Decimal = Field(..., description="Monto del pago")
    currency: str = Field(..., description="Moneda del pago")
    status: str = Field(..., description="Estado del pago")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    error_message: Optional[str] = Field(None, description="Mensaje de error si aplica")
    creado_en: datetime = Field(..., description="Fecha de creación")
    actualizado_en: Optional[datetime] = Field(None, description="Última actualización")
    
    # Propiedades computadas
    @property
    def is_completed(self) -> bool:
        """Indica si el pago está completado"""
        return self.status == "completed"
    
    @property
    def is_pending(self) -> bool:
        """Indica si el pago está pendiente"""
        return self.status == "pending"
    
    @property
    def can_be_refunded(self) -> bool:
        """Indica si el pago puede ser reembolsado"""
        return self.status == "completed"
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "external_payment_id": "mock_abc123xyz",
                    "reserva_id": 123,
                    "usuario_id": 5,
                    "provider_name": "mock",
                    "amount": 50.00,
                    "currency": "USD",
                    "status": "completed",
                    "metadata_json": {
                        "descripcion": "Reserva de Sala A"
                    },
                    "error_message": None,
                    "creado_en": "2026-01-15T10:00:00Z",
                    "actualizado_en": "2026-01-15T10:00:05Z"
                }
            ]
        }
    )


class PaymentStatusUpdate(BaseModel):
    """
    Schema para actualizar el estado de un pago.
    Usado internamente por webhooks.
    """
    
    status: str = Field(
        ...,
        description="Nuevo estado del pago",
        pattern="^(pending|completed|failed|refunded|cancelled)$"
    )
    error_message: Optional[str] = Field(
        None,
        description="Mensaje de error si el estado es 'failed'"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "completed",
                    "error_message": None
                },
                {
                    "status": "failed",
                    "error_message": "Tarjeta rechazada"
                }
            ]
        }
    )


class PaymentListResponse(BaseModel):
    """
    Schema de respuesta para listar pagos con paginación.
    """
    
    total: int = Field(..., description="Total de pagos")
    page: int = Field(..., description="Página actual", ge=1)
    page_size: int = Field(..., description="Tamaño de página", ge=1, le=100)
    payments: List[PaymentResponse] = Field(..., description="Lista de pagos")
    
    @property
    def total_pages(self) -> int:
        """Calcula el número total de páginas"""
        return (self.total + self.page_size - 1) // self.page_size
    
    @property
    def has_next(self) -> bool:
        """Indica si hay página siguiente"""
        return self.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        """Indica si hay página anterior"""
        return self.page > 1
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total": 25,
                    "page": 1,
                    "page_size": 10,
                    "payments": []
                }
            ]
        }
    )
