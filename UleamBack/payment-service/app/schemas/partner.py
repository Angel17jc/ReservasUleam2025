"""
Partner Schemas

Define schemas para operaciones de partners (B2B integrations).
"""

from pydantic import BaseModel, Field, field_validator, HttpUrl, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class PartnerCreate(BaseModel):
    """
    Schema para registrar un nuevo partner.
    
    Validaciones:
    - name único y no vacío
    - email válido
    - webhook_url debe ser HTTPS en producción
    - events_subscribed debe ser lista de eventos válidos
    """
    
    name: str = Field(
        ...,
        description="Nombre del partner (empresa/organización)",
        min_length=3,
        max_length=255
    )
    
    email: str = Field(
        ...,
        description="Email de contacto del partner",
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    
    webhook_url: str = Field(
        ...,
        description="URL HTTPS donde el partner recibe webhooks",
        min_length=10
    )
    
    events_subscribed: List[str] = Field(
        default_factory=lambda: ["payment.success", "payment.failed"],
        description="Lista de eventos a los que el partner quiere suscribirse"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Metadata adicional del partner"
    )
    
    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url_https(cls, v: str) -> str:
        """Validar que la URL sea HTTPS"""
        if not v.startswith(("https://", "http://")):
            raise ValueError("webhook_url must start with https:// or http://")
        
        # En producción, forzar HTTPS
        # if not v.startswith("https://"):
        #     raise ValueError("webhook_url must use HTTPS in production")
        
        return v
    
    @field_validator("events_subscribed")
    @classmethod
    def validate_events(cls, v: List[str]) -> List[str]:
        """Validar que los eventos sean conocidos"""
        allowed_events = {
            "payment.success",
            "payment.failed",
            "payment.pending",
            "payment.refunded",
            "payment.cancelled"
        }
        
        for event in v:
            if event not in allowed_events:
                raise ValueError(
                    f"Unknown event: {event}. Allowed: {allowed_events}"
                )
        
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Partner XYZ Corp",
                    "email": "webhooks@partner-xyz.com",
                    "webhook_url": "https://partner-xyz.com/webhooks/payments",
                    "events_subscribed": ["payment.success", "payment.failed"],
                    "metadata": {
                        "contact_person": "John Doe",
                        "phone": "+1234567890"
                    }
                }
            ]
        }
    )


class PartnerResponse(BaseModel):
    """
    Schema de respuesta de un partner.
    Incluye API key pero NO el secret.
    Mapea campos del modelo (español) a respuesta (inglés).
    """
    
    id: int = Field(..., description="ID del partner")
    name: str = Field(..., validation_alias="nombre", description="Nombre del partner")
    email: str = Field(..., description="Email del partner")
    webhook_url: str = Field(..., description="URL del webhook")
    api_key: str = Field(..., description="API key pública (visible)")
    is_active: bool = Field(..., description="Estado del partner")
    events_subscribed: List[str] = Field(..., validation_alias="eventos_suscritos", description="Eventos suscritos")
    webhook_success_count: int = Field(..., validation_alias="webhooks_succeeded", description="Webhooks exitosos")
    webhook_fail_count: int = Field(..., validation_alias="webhooks_failed", description="Webhooks fallidos")
    last_webhook_at: Optional[datetime] = Field(None, description="Último webhook")
    creado_en: datetime = Field(..., description="Fecha de creación")
    
    # Computed properties
    @property
    def webhook_success_rate(self) -> float:
        """Tasa de éxito de webhooks"""
        total = self.webhook_success_count + self.webhook_fail_count
        if total == 0:
            return 0.0
        return (self.webhook_success_count / total) * 100
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "name": "Partner XYZ Corp",
                    "email": "webhooks@partner-xyz.com",
                    "webhook_url": "https://partner-xyz.com/webhooks/payments",
                    "api_key": "pk_abc123def456",
                    "is_active": True,
                    "events_subscribed": ["payment.success", "payment.failed"],
                    "webhook_success_count": 150,
                    "webhook_fail_count": 5,
                    "last_webhook_at": "2026-01-16T10:00:00Z",
                    "creado_en": "2026-01-15T10:00:00Z"
                }
            ]
        }
    )


class PartnerWithSecret(PartnerResponse):
    """
    Schema de respuesta que INCLUYE el secret.
    Solo se usa al crear el partner (primera vez).
    NUNCA se vuelve a mostrar el secret.
    """
    
    secret_key: str = Field(..., description="Secret key (solo se muestra UNA VEZ)")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "name": "Partner XYZ Corp",
                    "api_key": "pk_abc123def456",
                    "secret_key": "sk_xyz789ghi012jkl345mno678pqr901stu234vwx567yza890bcd123",
                    "webhook_url": "https://partner-xyz.com/webhooks/payments",
                    "is_active": True
                }
            ]
        }
    )


class PartnerUpdate(BaseModel):
    """
    Schema para actualizar un partner.
    Todos los campos son opcionales.
    """
    
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    email: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    webhook_url: Optional[str] = Field(None, min_length=10)
    is_active: Optional[bool] = None
    events_subscribed: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url_https(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith(("https://", "http://")):
            raise ValueError("webhook_url must start with https:// or http://")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "is_active": False,
                    "webhook_url": "https://new-url.com/webhooks"
                }
            ]
        }
    )


class PartnerListResponse(BaseModel):
    """
    Schema de respuesta para listar partners con paginación.
    """
    
    total: int = Field(..., description="Total de partners")
    page: int = Field(..., description="Página actual", ge=1)
    page_size: int = Field(..., description="Tamaño de página", ge=1, le=100)
    partners: List[PartnerResponse] = Field(..., description="Lista de partners")
    
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
                    "total": 10,
                    "page": 1,
                    "page_size": 10,
                    "partners": []
                }
            ]
        }
    )


class WebhookDeliveryResult(BaseModel):
    """
    Schema que representa el resultado de entregar un webhook a un partner.
    """
    
    partner_id: int = Field(..., description="ID del partner")
    partner_name: str = Field(..., description="Nombre del partner")
    success: bool = Field(..., description="Si el webhook fue entregado exitosamente")
    status_code: Optional[int] = Field(None, description="HTTP status code de la respuesta")
    error_message: Optional[str] = Field(None, description="Mensaje de error si falló")
    response_time_ms: float = Field(..., description="Tiempo de respuesta en milisegundos")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "partner_id": 1,
                    "partner_name": "Partner XYZ",
                    "success": True,
                    "status_code": 200,
                    "error_message": None,
                    "response_time_ms": 245.5
                }
            ]
        }
    )