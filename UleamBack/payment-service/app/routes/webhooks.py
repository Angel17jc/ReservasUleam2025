"""
Webhook Routes

Endpoints para recibir webhooks de payment providers.

Endpoints:
- POST /webhooks/providers/{provider}: Recibir webhooks de Stripe, MercadoPago, etc.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..database import get_db
from ..schemas.webhook import NormalizedWebhookEvent
from ..schemas.payment import PaymentStatusUpdate
from ..services.payment_service import PaymentService
from ..models.payment import PaymentStatus
from ..clients.rest_client import get_rest_client
from ..services.partner_service import PartnerService
from ..adapters.adapter_factory import AdapterFactory
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "/providers/{provider}",
    status_code=status.HTTP_200_OK,
    summary="Recibir webhook de payment provider",
    description="Endpoint para recibir notificaciones de pago de Stripe, MercadoPago, etc."
)
async def receive_provider_webhook(
    provider: str,
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db)
):
    """
    Recibe y procesa webhooks de payment providers.
    
    **Flow**:
    1. Obtener adapter del provider
    2. Validar firma HMAC del webhook
    3. Normalizar evento al formato común
    4. Actualizar estado del pago en BD
    5. Notificar a partners externos
    6. Retornar 200 OK
    
    **Security**:
    - Valida firma HMAC para autenticidad
    - Rechaza webhooks con firma inválida (401)
    - Previene replay attacks
    
    **Providers soportados**:
    - `stripe`: Webhooks de Stripe (firma en Stripe-Signature)
    - `mercadopago`: Webhooks de MercadoPago (firma en X-Signature)
    - `mock`: Webhooks de MockAdapter (testing)
    
    **Headers requeridos**:
    - Stripe: `Stripe-Signature`
    - MercadoPago: `X-Signature`
    - Mock: No requiere firma
    
    **Response**: `{"status": "processed"}`
    
    **Errors**:
    - 400: Provider no soportado
    - 401: Firma inválida
    - 404: Pago no encontrado
    - 500: Error interno
    """
    try:
        # 1. Obtener adapter del provider
        try:
            adapter = AdapterFactory.get_adapter(provider)
        except ValueError as e:
            logger.warning(f"Unsupported provider: {provider}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider}"
            )
        
        # 2. Leer payload raw
        payload_bytes = await request.body()
        payload_str = payload_bytes.decode('utf-8')
        
        # 3. Validar firma según provider
        signature = stripe_signature if provider == "stripe" else x_signature
        
        if provider != "mock":  # Mock no requiere validación
            if not signature:
                logger.warning(f"Missing signature header for provider: {provider}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing webhook signature"
                )
            
            # Obtener secret según provider
            webhook_secret = None
            if provider == "stripe":
                webhook_secret = settings.STRIPE_WEBHOOK_SECRET
            elif provider == "mercadopago":
                webhook_secret = settings.MERCADOPAGO_WEBHOOK_SECRET
            
            if not webhook_secret:
                logger.error(f"Webhook secret not configured for provider: {provider}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Webhook secret not configured"
                )
            
            # Validar firma usando el adapter (el adapter gestiona su secret internamente)
            is_valid = adapter.validate_webhook_signature(
                payload=payload_bytes,
                signature=signature
            )
            
            if not is_valid:
                logger.warning(f"Invalid webhook signature from {provider}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
        
        # 4. Parsear payload
        import json
        payload_json = json.loads(payload_str)
        
        # 5. Normalizar evento
        normalized_event = adapter.normalize_webhook(payload_json)
        
        logger.info(
            f"Webhook received: provider={provider}, "
            f"event={normalized_event.event_type}, "
            f"payment_id={normalized_event.payment_id}"
        )
        
        # 6. Buscar pago en BD
        payment = PaymentService.get_payment_by_external_id(
            db=db,
            external_payment_id=normalized_event.payment_id
        )
        
        if not payment:
            logger.warning(
                f"Payment not found for webhook: "
                f"provider={provider}, "
                f"external_id={normalized_event.payment_id}"
            )
            # Retornar 200 para que el provider no reintente
            return {"status": "ignored", "reason": "payment_not_found"}
        
        # 7. Actualizar estado del pago
        status_update = PaymentStatusUpdate(
            status=normalized_event.status,
            error_message=normalized_event.error_message
        )
        
        updated_payment = PaymentService.update_payment_status(
            db=db,
            external_payment_id=normalized_event.payment_id,
            status_update=status_update
        )
        
        if updated_payment:
            logger.info(
                f"Payment status updated: id={updated_payment.id}, "
                f"status={updated_payment.status}"
            )

            if (
                updated_payment.status == PaymentStatus.COMPLETED
                and settings.RESERVAS_INTERNAL_TOKEN
            ):
                try:
                    rest_client = get_rest_client()
                    await rest_client.update_reserva_status_internal(
                        reserva_id=updated_payment.reserva_id,
                        estado_nombre="Pagada",
                        internal_token=settings.RESERVAS_INTERNAL_TOKEN,
                        payment_code=updated_payment.external_payment_id,
                    )
                except Exception as e:
                    logger.error(
                        f"No se pudo marcar la reserva como pagada via webhook: {e}",
                        exc_info=True,
                    )
        
        # 8. Registrar evento en BD
        PaymentService.record_webhook_event(
            db=db,
            event_type=normalized_event.event_type,
            source=provider,
            payload=payload_json,
            payment_id=normalized_event.payment_id
        )
        
        # 9. Notificar a partners externos
        try:
            delivery_results = await PartnerService.notify_partners_of_payment_event(
                db=db,
                event=normalized_event
            )
            
            logger.info(
                f"Partners notified: "
                f"total={len(delivery_results)}, "
                f"successful={sum(1 for r in delivery_results if r.success)}"
            )
        except Exception as e:
            # No fallar el webhook si la notificación a partners falla
            logger.error(f"Error notifying partners: {e}", exc_info=True)
        
        return {
            "status": "processed",
            "event_type": normalized_event.event_type,
            "payment_id": normalized_event.payment_id
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}"
        )