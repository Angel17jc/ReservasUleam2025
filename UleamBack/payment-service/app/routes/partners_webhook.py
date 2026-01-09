"""
Partner Webhook Routes (INBOUND)

Endpoints para recibir webhooks de partners externos.

Este módulo implementa la comunicación INBOUND del flujo bidireccional B2B.
Los partners externos pueden notificarnos eventos mediante webhooks firmados con HMAC.

Endpoints:
- POST /partners/webhook: Recibir webhook de partner externo
- GET /partners/webhook/events: Listar tipos de eventos soportados

Seguridad:
- Autenticación por API Key
- Verificación de firma HMAC-SHA256
- Validación de timestamp (anti-replay)
- Rate limiting por partner
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
import json
import logging
from typing import Optional, Dict, Any

from ..database import get_db
from ..services.partner_service import PartnerService
from ..services.hmac_service import HmacService
from ..services.partner_webhook_processor import PartnerWebhookProcessor
from ..schemas.partner_event import (
    PartnerEventResponse,
    get_event_schema,
    EVENT_TYPE_MAPPING
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/partners/webhook", tags=["partners-webhook"])


@router.post(
    "",
    response_model=PartnerEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Recibir webhook de partner externo",
    description="Endpoint para que otros grupos/partners nos notifiquen eventos mediante webhooks"
)
async def receive_partner_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_api_key: str = Header(..., alias="X-Api-Key", description="API key del partner"),
    x_webhook_signature: str = Header(..., alias="X-Webhook-Signature", description="Firma HMAC del payload"),
    x_webhook_timestamp: str = Header(..., alias="X-Webhook-Timestamp", description="Timestamp Unix del evento")
):
    """
    Recibe y procesa webhooks de partners externos (comunicación INBOUND).
    
    **Security Flow**:
    1. Validar API key del partner
    2. Verificar que partner esté activo
    3. Validar firma HMAC del payload
    4. Verificar timestamp (anti-replay attack)
    5. Procesar evento según tipo
    
    **Headers Requeridos**:
    - `X-Api-Key`: API key del partner (obtenida al registrarse)
    - `X-Webhook-Signature`: Firma HMAC-SHA256 del payload
    - `X-Webhook-Timestamp`: Timestamp Unix (segundos)
    
    **Ejemplo de Request**:
    ```bash
    curl -X POST https://api.payments.com/api/v1/partners/webhook \\
      -H "X-Api-Key: pk_partner123..." \\
      -H "X-Webhook-Signature: abc123..." \\
      -H "X-Webhook-Timestamp: 1737336000" \\
      -H "Content-Type: application/json" \\
      -d '{
        "event_type": "booking.confirmed",
        "event_id": "evt_abc123",
        "timestamp": 1737336000,
        "booking_id": "book_123",
        "amount": 150.00,
        "currency": "USD",
        "metadata": {
          "room_type": "suite",
          "check_in": "2026-02-01"
        }
      }'
    ```
    
    **Eventos Soportados**:
    - `booking.confirmed`: Hotel confirmó reserva
    - `tour.purchased`: Tour fue comprado
    - `service.activated`: Servicio adicional activado
    - `booking.cancelled`: Reserva cancelada
    
    **Response Codes**:
    - 200: Evento procesado exitosamente
    - 401: API key inválida o firma HMAC incorrecta
    - 400: Payload inválido
    - 500: Error interno al procesar evento
    
    **Idempotencia**:
    - Si el evento incluye `event_id`, procesamos solo una vez
    - Webhooks duplicados retornan 200 sin reprocesar
    """
    try:
        # 1. Validar partner por API key
        partner = PartnerService.get_partner_by_api_key(db, x_api_key)
        
        if not partner:
            logger.warning(f"Invalid API key: {x_api_key[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        if not partner.is_active:
            logger.warning(f"Inactive partner: {partner.nombre}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Partner is inactive"
            )
        
        logger.info(
            f"Webhook received from partner: {partner.nombre} (id={partner.id})"
        )
        
        # 2. Obtener payload
        payload_bytes = await request.body()
        payload_str = payload_bytes.decode('utf-8')
        
        # 3. Verificar firma HMAC
        is_valid_signature = HmacService.verify_signature(
            payload=payload_str,
            signature=x_webhook_signature,
            secret_key=partner.secret_key,
            timestamp=x_webhook_timestamp,
            tolerance_seconds=300  # 5 minutos
        )
        
        if not is_valid_signature:
            logger.warning(
                f"Invalid webhook signature from partner: {partner.nombre}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        logger.debug(f"Webhook signature verified for partner: {partner.nombre}")
        
        # 4. Parsear payload
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        
        # 5. Validar event_type
        event_type = payload.get("event_type", "").lower()
        
        if not event_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing event_type"
            )
        
        # 6. Validar schema según event_type
        event_schema = get_event_schema(event_type)
        
        if not event_schema:
            logger.warning(f"Unsupported event type: {event_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported event type: {event_type}"
            )
        
        try:
            validated_event = event_schema(**payload)
        except Exception as e:
            logger.error(f"Event validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event data: {str(e)}"
            )
        
        # 7. Procesar evento
        result = await PartnerWebhookProcessor.process_event(
            db=db,
            partner=partner,
            event_data=payload
        )
        
        # 8. Actualizar estadísticas del partner
        partner.webhooks_received += 1
        db.commit()
        
        logger.info(
            f"Webhook processed successfully: "
            f"partner={partner.nombre}, "
            f"event_type={event_type}, "
            f"event_id={payload.get('event_id')}"
        )
        
        # 9. Retornar respuesta
        return PartnerEventResponse(
            status="processed",
            event_id=payload.get("event_id"),
            message=f"Event {event_type} processed successfully"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(
            f"Unexpected error processing partner webhook: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}"
        )


@router.get(
    "/events",
    summary="Listar eventos soportados",
    description="Retorna la lista de event_types que este servicio puede procesar"
)
def list_supported_events() -> Dict[str, Any]:
    """
    Lista todos los tipos de eventos que el servicio puede procesar.
    
    Útil para que partners sepan qué eventos pueden enviarnos.
    
    **Response**:
    ```json
    {
        "supported_events": [
            {
                "event_type": "booking.confirmed",
                "description": "Hotel confirmó una reserva",
                "required_fields": ["booking_id", "amount", "currency"],
                "example": {...}
            },
            ...
        ]
    }
    ```
    """
    events = []
    
    for event_type, schema_class in EVENT_TYPE_MAPPING.items():
        # Obtener ejemplo del schema
        example = schema_class.model_config.get("json_schema_extra", {}).get("example", {})
        
        # Obtener campos requeridos
        required_fields = []
        for field_name, field_info in schema_class.model_fields.items():
            if field_info.is_required():
                required_fields.append(field_name)
        
        events.append({
            "event_type": event_type,
            "description": schema_class.__doc__.strip() if schema_class.__doc__ else "",
            "required_fields": required_fields,
            "example": example
        })
    
    return {
        "supported_events": events,
        "count": len(events),
        "documentation": "https://docs.payments.com/webhooks/partner-events"
    }


@router.get(
    "/health",
    summary="Health check del endpoint de webhooks",
    description="Verifica que el endpoint de webhooks esté operativo"
)
def webhook_health_check() -> Dict[str, str]:
    """
    Health check para verificar disponibilidad del servicio.
    
    Partners pueden usar este endpoint para monitorear nuestra disponibilidad.
    """
    return {
        "status": "healthy",
        "service": "partner-webhook-receiver",
        "version": "1.0.0"
    }
