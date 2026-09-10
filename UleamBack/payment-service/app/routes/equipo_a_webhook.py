"""
Equipo A Webhook Routes - Endpoint de Compatibilidad

Endpoints específicos para integración con Equipo A - Recomendaciones Turísticas ULEAM.
"""


from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import hmac
import hashlib

from ..config import settings
from ..database import get_db
from ..services.hmac_service import HmacService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/equipo-a", tags=["equipo-a-integration"])


# Configuracion de Equipo A: el secreto y las URLs se inyectan por entorno,
# nunca se versionan en el codigo.
EQUIPO_A_CONFIG = {
    "shared_secret": settings.EQUIPO_A_SHARED_SECRET,
    "webhook_url": settings.EQUIPO_A_WEBHOOK_URL,
    "health_url": settings.EQUIPO_A_HEALTH_URL,
    "status_url": settings.EQUIPO_A_STATUS_URL,
    "eventos_que_envian": ["tour.purchased", "booking.confirmed", "recommendation.created"],
    "eventos_que_reciben": ["booking.confirmed", "payment.success", "service.activated"]
}


def _require_shared_secret() -> str:
    """Devuelve el secreto compartido o corta la peticion si no esta configurado."""
    secret = EQUIPO_A_CONFIG["shared_secret"]
    if not secret:
        logger.error(
            "[Equipo A] EQUIPO_A_SHARED_SECRET no esta configurado: "
            "la integracion B2B esta deshabilitada."
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Equipo A integration is not configured"
        )
    return secret


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Recibir webhook de Equipo A",
    description="Endpoint compatible con formato de Equipo A - Recomendaciones Turísticas ULEAM"
)
async def receive_equipo_a_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_signature: str = Header(..., alias="X-Signature", description="Firma HMAC-SHA256 del payload")
):
  
    try:
        # 1. Leer body raw
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')
        
        # 2. Parsear JSON
        try:
            payload = json.loads(body_str)
        except json.JSONDecodeError:
            logger.error("[Equipo A Webhook] JSON inválido recibido")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        
        # 3. Verificar firma HMAC
        # IMPORTANTE: Pasar el dict para que se serialice consistentemente
        # con separators=(',', ':') y sort_keys=True
        is_valid = HmacService.validate_signature(
            payload=payload,  # Pasar dict, no string
            signature=x_signature,
            secret=_require_shared_secret()
        )
        
        # 4. Logging detallado para debugging HMAC
        if not is_valid:
            # Generar lo que esperábamos para comparar
            normalized_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            logger.error(
                f"[Equipo A Webhook] ❌ FIRMA INVÁLIDA - Debugging Info:\n"
                f"   📦 Payload recibido: {json.dumps(payload, indent=2)}\n"
                f"   📝 Payload normalizado: {normalized_payload}\n"
                f"   ✍️  Firma recibida: {x_signature}\n"
                f"   💡 Mensaje para Equipo B: Asegúrense de usar json.dumps(payload, sort_keys=True, separators=(',', ':'))"
            )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid HMAC signature"
            )
        
        # 5. Validar estructura del payload
        event_type = payload.get("event")
        timestamp_str = payload.get("timestamp")
        data = payload.get("data", {})
        source = payload.get("source")
        
        if not event_type or not timestamp_str or not data:
            logger.error("[Equipo A Webhook] Payload incompleto")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: event, timestamp, data"
            )
        
        # 6. Validar que sea de Equipo A
        if source != "equipo-a-recomendaciones":
            logger.warning(f"[Equipo A Webhook] Source inesperado: {source}")
        
        # 7. Validar que sea evento esperado
        if event_type not in EQUIPO_A_CONFIG["eventos_que_envian"]:
            logger.warning(
                f"[Equipo A Webhook] Evento no esperado: {event_type}\n"
                f"   Eventos esperados: {EQUIPO_A_CONFIG['eventos_que_envian']}"
            )
        
        # 8. Log del evento recibido
        logger.info(
            f"✅ [Equipo A Webhook] Evento recibido y firma válida\n"
            f"   Evento: {event_type}\n"
            f"   Timestamp: {timestamp_str}\n"
            f"   Data keys: {list(data.keys())}\n"
            f"   Source: {source}"
        )
        
        # 9. Procesar según tipo de evento
        result = await process_equipo_a_event(db, event_type, data, timestamp_str)
        
        return {
            "status": "ok",
            "message": "Webhook received and processed",
            "event": event_type,
            "processed_at": datetime.utcnow().isoformat() + "Z",
            "result": result
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(
            f"❌ [Equipo A Webhook] Error inesperado: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing webhook: {str(e)}"
        )


async def process_equipo_a_event(
    db: Session,
    event_type: str,
    data: Dict[str, Any],
    timestamp_str: str
) -> Dict[str, Any]:
    """
    Procesa eventos específicos de Equipo A.
    
    Args:
        db: Sesión de BD
        event_type: Tipo de evento (tour.purchased, booking.confirmed, etc.)
        data: Datos del evento
        timestamp_str: Timestamp ISO del evento
    
    Returns:
        dict: Resultado del procesamiento
    """
    try:
        if event_type == "tour.purchased":
            # Usuario confirmó compra de tour en Equipo A
            # Podemos crear una recomendación o registro en nuestro sistema
            
            booking_id = data.get("booking_id")
            user_email = data.get("user_email")
            tour_name = data.get("tour_name")
            amount = data.get("amount", 0.0)
            persons = data.get("persons", 1)
            
            logger.info(
                f"📦 [Equipo A] Tour purchased:\n"
                f"   Booking ID: {booking_id}\n"
                f"   User: {user_email}\n"
                f"   Tour: {tour_name}\n"
                f"   Amount: ${amount}\n"
                f"   Persons: {persons}"
            )
            
            # TODO: Crear notificación o registro en BD
            # from ..services.notification_service import create_notification
            # notification = create_notification(db, {
            #     "titulo": f"Tour confirmado: {tour_name}",
            #     "mensaje": f"El usuario {user_email} confirmó un tour por ${amount}",
            #     "metadata": data
            # })
            
            return {
                "action": "tour_registered",
                "booking_id": booking_id,
                "user_email": user_email,
                "tour_name": tour_name
            }
        
        elif event_type == "booking.confirmed":
            # Reserva confirmada en sistema de Equipo A
            
            booking_id = data.get("booking_id")
            user_email = data.get("user_email")
            
            logger.info(
                f"📦 [Equipo A] Booking confirmed:\n"
                f"   Booking ID: {booking_id}\n"
                f"   User: {user_email}"
            )
            
            # TODO: Sincronizar con nuestro sistema
            
            return {
                "action": "booking_synced",
                "booking_id": booking_id
            }
        
        elif event_type == "recommendation.created":
            # Nueva recomendación generada por Equipo A
            
            recommendation_id = data.get("recommendation_id", "unknown")
            user_email = data.get("user_email")
            tour_recommended = data.get("tour_recommended")
            
            logger.info(
                f"📦 [Equipo A] Recommendation created:\n"
                f"   Recommendation ID: {recommendation_id}\n"
                f"   User: {user_email}\n"
                f"   Tour: {tour_recommended}"
            )
            
            # TODO: Crear notificación para usuario
            
            return {
                "action": "recommendation_received",
                "recommendation_id": recommendation_id
            }
        
        else:
            logger.warning(f"[Equipo A] Evento no procesado: {event_type}")
            return {
                "action": "event_logged",
                "message": f"Event {event_type} logged but not processed"
            }
    
    except Exception as e:
        logger.error(f"Error procesando evento de Equipo A: {e}", exc_info=True)
        raise


@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="Estado de integración con Equipo A",
    description="Retorna el estado actual de la integración bidireccional con Equipo A"
)
async def get_equipo_a_integration_status(db: Session = Depends(get_db)):

    try:
        # Buscar si existe partner "Equipo A" registrado
        from ..models.partner import Partner
        equipo_a_partner = db.query(Partner).filter(
            Partner.nombre.ilike("%equipo a%")
        ).first()
        
        statistics = {}
        if equipo_a_partner:
            statistics = {
                "partner_id": equipo_a_partner.id,
                "partner_name": equipo_a_partner.nombre,
                "is_active": equipo_a_partner.is_active,
                "webhooks_sent": equipo_a_partner.webhooks_sent,
                "webhooks_succeeded": equipo_a_partner.webhooks_succeeded,
                "webhooks_failed": equipo_a_partner.webhooks_failed,
                "last_webhook_at": equipo_a_partner.last_webhook_at.isoformat() if equipo_a_partner.last_webhook_at else None
            }
        
        return {
            "status": "configured",
            "integration_name": "Equipo A - Recomendaciones Turísticas ULEAM",
            "equipo_a": {
                "webhook_url": EQUIPO_A_CONFIG["webhook_url"],
                "health_url": EQUIPO_A_CONFIG["health_url"],
                "status_url": EQUIPO_A_CONFIG["status_url"],
                "shared_secret_configured": bool(EQUIPO_A_CONFIG["shared_secret"])
            },
            "events": {
                "we_receive_from_equipo_a": EQUIPO_A_CONFIG["eventos_que_envian"],
                "we_send_to_equipo_a": EQUIPO_A_CONFIG["eventos_que_reciben"]
            },
            "endpoints": {
                "receive_from_equipo_a": "/api/v1/equipo-a/webhook",
                "send_to_equipo_a": EQUIPO_A_CONFIG["webhook_url"]
            },
            "statistics": statistics if statistics else {
                "message": "No partner registered yet. Run register_equipo_a.py to create partner."
            }
        }
    
    except Exception as e:
        logger.error(f"Error obteniendo estado de integración: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting integration status: {str(e)}"
        )


@router.post(
    "/test-send",
    status_code=status.HTTP_200_OK,
    summary="Enviar webhook de prueba a Equipo A",
    description="Envía un webhook de prueba a Equipo A para verificar conectividad"
)
async def test_send_to_equipo_a(db: Session = Depends(get_db)):
    """
    Envía un webhook de prueba a Equipo A.
    
    **Útil para:**
    - Verificar que Equipo A está recibiendo webhooks
    - Probar firma HMAC
    - Verificar formato de payload
    
    **Response:**
    - 200: Webhook enviado exitosamente
    - 500: Error al enviar
    """
    import httpx
    
    try:
        # Preparar payload de prueba (formato Equipo A)
        payload = {
            "event": "booking.confirmed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": {
                "booking_id": "test_booking_123",
                "user_email": "test@uleam.edu.ec",
                "user_id": "uleam_user_999",
                "tour_name": "Test - Verificación de Integración",
                "amount": 0.0,
                "persons": 1,
                "destination": "Test Destination",
                "description": "Webhook de prueba desde payment-service",
                "space": "Test Space",
                "date": datetime.utcnow().isoformat(),
                "time_start": "10:00",
                "time_end": "11:00"
            },
            "source": "equipo-b-uleam-reservas"
        }
        
        # Generar firma HMAC (sobre el string serializado)
        payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        signature = hmac.new(
            _require_shared_secret().encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        logger.info(
            f"📤 [Test] Enviando webhook a Equipo A\n"
            f"   URL: {EQUIPO_A_CONFIG['webhook_url']}\n"
            f"   Event: {payload['event']}\n"
            f"   Signature: {signature[:16]}...\n"
            f"   Payload serializado: {payload_str[:100]}..."
        )
        
        # ⚠️ CRÍTICO: Enviar el MISMO string usado para calcular la firma
        # Usar content= con el string serializado, NO json=
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                EQUIPO_A_CONFIG["webhook_url"],
                content=payload_str,  # ← Enviar string, no dict
                headers={
                    "Content-Type": "application/json",
                    "X-Signature": signature
                }
            )
        
        if response.status_code == 200:
            logger.info(
                f"✅ [Test] Webhook enviado exitosamente a Equipo A\n"
                f"   Status: {response.status_code}\n"
                f"   Response: {response.text}"
            )
            
            return {
                "status": "success",
                "message": "Test webhook sent successfully to Equipo A",
                "equipo_a_response": response.json() if response.text else None,
                "status_code": response.status_code
            }
        else:
            logger.error(
                f"❌ [Test] Error al enviar webhook a Equipo A\n"
                f"   Status: {response.status_code}\n"
                f"   Response: {response.text}"
            )
            
            return {
                "status": "error",
                "message": f"Equipo A returned status {response.status_code}",
                "equipo_a_response": response.text,
                "status_code": response.status_code
            }
    
    except httpx.TimeoutException:
        logger.error("[Test] Timeout al enviar webhook a Equipo A")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout connecting to Equipo A. Check if their ngrok is active."
        )
    
    except Exception as e:
        logger.error(f"[Test] Error enviando webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending test webhook: {str(e)}"
        )
