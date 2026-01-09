"""
Partner Webhook Processor

Procesa eventos recibidos de partners externos (webhooks INBOUND).

Responsabilidades:
- Procesar eventos de partners (booking.confirmed, tour.purchased, etc.)
- Actualizar estado de pagos según eventos externos
- Coordinar respuestas automáticas a partners
- Logging y auditoría de eventos recibidos

Integración:
- Se integra con PaymentService para actualizar pagos
- Se integra con PartnerService para enviar respuestas
- Se integra con RestClient para actualizar reservas
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.payment import Payment
from ..models.partner import Partner
from ..models.webhook_event import WebhookEvent
from ..schemas.partner_event import (
    BookingConfirmedEvent,
    TourPurchasedEvent,
    ServiceActivatedEvent,
    BookingCancelledEvent
)
from ..services.payment_service import PaymentService
from ..services.partner_service import PartnerService
from ..schemas.webhook import NormalizedWebhookEvent

logger = logging.getLogger(__name__)


class PartnerWebhookProcessor:
    """
    Procesador de webhooks recibidos de partners externos.
    
    Implementa lógica de negocio para cada tipo de evento B2B.
    """
    
    @staticmethod
    async def process_event(
        db: Session,
        partner: Partner,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Procesa un evento de partner y ejecuta acciones correspondientes.
        
        Args:
            db: Sesión de BD
            partner: Partner que envió el evento
            event_data: Datos del evento
        
        Returns:
            Dict con resultado del procesamiento
        
        Raises:
            ValueError: Si el event_type no es soportado
        """
        event_type = event_data.get("event_type", "").lower()
        
        logger.info(
            f"Processing partner event: type={event_type}, "
            f"partner={partner.nombre}, "
            f"event_id={event_data.get('event_id')}"
        )
        
        # Registrar evento en BD para auditoría
        webhook_event = WebhookEvent(
            event_type=event_type,
            source=f"partner:{partner.id}",
            payload_json=event_data,  # Campo correcto según modelo
            processed=False
        )
        db.add(webhook_event)
        db.commit()
        db.refresh(webhook_event)
        
        try:
            # Dispatch según tipo de evento
            if event_type == "booking.confirmed":
                result = await PartnerWebhookProcessor._handle_booking_confirmed(
                    db, partner, BookingConfirmedEvent(**event_data)
                )
            
            elif event_type == "tour.purchased":
                result = await PartnerWebhookProcessor._handle_tour_purchased(
                    db, partner, TourPurchasedEvent(**event_data)
                )
            
            elif event_type == "service.activated":
                result = await PartnerWebhookProcessor._handle_service_activated(
                    db, partner, ServiceActivatedEvent(**event_data)
                )
            
            elif event_type == "booking.cancelled":
                result = await PartnerWebhookProcessor._handle_booking_cancelled(
                    db, partner, BookingCancelledEvent(**event_data)
                )
            
            else:
                logger.warning(f"Unknown event type: {event_type}")
                result = {
                    "status": "ignored",
                    "reason": f"Event type '{event_type}' not supported"
                }
            
            # Actualizar estado del evento
            webhook_event.processed = True
            db.commit()
            
            logger.info(f"Event processed successfully: event_id={event_data.get('event_id')}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error processing partner event: {e}", exc_info=True)
            webhook_event.processed = False
            webhook_event.error_message = str(e)
            db.commit()
            raise
    
    @staticmethod
    async def _handle_booking_confirmed(
        db: Session,
        partner: Partner,
        event: BookingConfirmedEvent
    ) -> Dict[str, Any]:
        """
        Maneja evento: Partner confirmó una reserva.
        
        Flujo:
        1. Si existe payment_id, actualizar metadata del pago
        2. Si no existe pago, crear uno nuevo automáticamente
        3. Notificar al partner con payment.success
        
        Business Logic:
        - Una confirmación de reserva debe tener un pago asociado
        - Si el pago no existe, lo creamos en estado "pending"
        - Actualizamos metadata con info de la reserva
        """
        logger.info(
            f"Handling booking.confirmed: booking_id={event.booking_id}, "
            f"payment_id={event.payment_id}, amount={event.amount}"
        )
        
        payment = None
        
        # 1. Buscar pago existente
        if event.payment_id:
            payment = db.query(Payment).filter(
                Payment.external_payment_id == event.payment_id
            ).first()
        
        # 2. Si no existe pago, crear uno nuevo
        if not payment:
            logger.info(f"Creating new payment for booking: {event.booking_id}")
            
            # Crear pago en estado pending (el partner confirmó pero esperamos el pago)
            payment = Payment(
                external_payment_id=f"partner_{partner.id}_{event.booking_id}",
                provider_name="partner",
                amount=event.amount,
                currency=event.currency,
                status="pending",
                metadata={
                    "booking_id": event.booking_id,
                    "partner_id": partner.id,
                    "partner_name": partner.nombre,
                    "event_type": "booking.confirmed",
                    "customer_email": event.customer_email,
                    **event.metadata
                }
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)
            
            logger.info(f"Payment created: id={payment.id}, external_id={payment.external_payment_id}")
        
        # 3. Actualizar metadata del pago con info de la reserva
        else:
            logger.info(f"Updating existing payment: id={payment.id}")
            
            if not payment.metadata:
                payment.metadata = {}
            
            payment.metadata.update({
                "booking_confirmed": True,
                "booking_confirmed_at": event.timestamp,
                "partner_booking_id": event.booking_id,
                **event.metadata
            })
            
            db.commit()
        
        # 4. Notificar al partner (respuesta bidireccional)
        # Si el pago está completado, notificamos payment.success
        if payment.status == "completed":
            await PartnerWebhookProcessor._notify_partner_payment_success(
                db, partner, payment
            )
        
        return {
            "status": "processed",
            "action": "payment_created" if event.payment_id is None else "payment_updated",
            "payment_id": payment.id,
            "external_payment_id": payment.external_payment_id
        }
    
    @staticmethod
    async def _handle_tour_purchased(
        db: Session,
        partner: Partner,
        event: TourPurchasedEvent
    ) -> Dict[str, Any]:
        """
        Maneja evento: Partner vendió un tour relacionado.
        
        Flujo:
        1. Buscar pago asociado
        2. Actualizar metadata con info del tour
        3. Agregar tour a servicios adicionales
        """
        logger.info(
            f"Handling tour.purchased: tour_id={event.tour_id}, "
            f"payment_id={event.payment_id}, amount={event.amount}"
        )
        
        # 1. Buscar pago asociado
        payment = None
        if event.payment_id:
            payment = db.query(Payment).filter(
                Payment.external_payment_id == event.payment_id
            ).first()
        
        if not payment and event.booking_id:
            # Buscar por booking_id en metadata
            payment = db.query(Payment).filter(
                Payment.metadata["booking_id"].astext == event.booking_id
            ).first()
        
        if not payment:
            logger.warning(f"Payment not found for tour: tour_id={event.tour_id}")
            return {
                "status": "ignored",
                "reason": "payment_not_found",
                "tour_id": event.tour_id
            }
        
        # 2. Actualizar metadata con info del tour
        if not payment.metadata:
            payment.metadata = {}
        
        # Agregar tour a lista de servicios adicionales
        additional_services = payment.metadata.get("additional_services", [])
        additional_services.append({
            "type": "tour",
            "tour_id": event.tour_id,
            "amount": event.amount,
            "currency": event.currency,
            "purchased_at": event.timestamp,
            **event.metadata
        })
        
        payment.metadata["additional_services"] = additional_services
        payment.metadata["total_additional_amount"] = sum(
            s.get("amount", 0) for s in additional_services
        )
        
        db.commit()
        
        logger.info(f"Tour added to payment: payment_id={payment.id}, tour_id={event.tour_id}")
        
        return {
            "status": "processed",
            "action": "tour_added",
            "payment_id": payment.id,
            "tour_id": event.tour_id
        }
    
    @staticmethod
    async def _handle_service_activated(
        db: Session,
        partner: Partner,
        event: ServiceActivatedEvent
    ) -> Dict[str, Any]:
        """
        Maneja evento: Partner activó un servicio adicional.
        
        Similar a tour.purchased pero para servicios generales.
        """
        logger.info(
            f"Handling service.activated: service_id={event.service_id}, "
            f"type={event.service_type}, payment_id={event.payment_id}"
        )
        
        # Buscar pago asociado
        payment = None
        if event.payment_id:
            payment = db.query(Payment).filter(
                Payment.external_payment_id == event.payment_id
            ).first()
        
        if not payment:
            logger.warning(f"Payment not found for service: service_id={event.service_id}")
            return {
                "status": "ignored",
                "reason": "payment_not_found",
                "service_id": event.service_id
            }
        
        # Actualizar metadata con servicio activado
        if not payment.metadata:
            payment.metadata = {}
        
        activated_services = payment.metadata.get("activated_services", [])
        activated_services.append({
            "service_id": event.service_id,
            "service_type": event.service_type,
            "amount": event.amount,
            "currency": event.currency,
            "activated_at": event.timestamp,
            **event.metadata
        })
        
        payment.metadata["activated_services"] = activated_services
        db.commit()
        
        logger.info(f"Service activated for payment: payment_id={payment.id}, service_id={event.service_id}")
        
        return {
            "status": "processed",
            "action": "service_activated",
            "payment_id": payment.id,
            "service_id": event.service_id
        }
    
    @staticmethod
    async def _handle_booking_cancelled(
        db: Session,
        partner: Partner,
        event: BookingCancelledEvent
    ) -> Dict[str, Any]:
        """
        Maneja evento: Partner canceló una reserva.
        
        Flujo:
        1. Buscar pago asociado
        2. Marcar pago como "refunded" o crear reembolso
        3. Notificar al partner del reembolso procesado
        """
        logger.info(
            f"Handling booking.cancelled: booking_id={event.booking_id}, "
            f"payment_id={event.payment_id}, refund_amount={event.refund_amount}"
        )
        
        # Buscar pago asociado
        payment = None
        if event.payment_id:
            payment = db.query(Payment).filter(
                Payment.external_payment_id == event.payment_id
            ).first()
        
        if not payment:
            # Buscar por booking_id en metadata
            payments = db.query(Payment).filter(
                Payment.metadata["booking_id"].astext == event.booking_id
            ).all()
            
            if payments:
                payment = payments[0]
        
        if not payment:
            logger.warning(f"Payment not found for cancelled booking: {event.booking_id}")
            return {
                "status": "ignored",
                "reason": "payment_not_found",
                "booking_id": event.booking_id
            }
        
        # Actualizar estado del pago
        if payment.status != "refunded":
            logger.info(f"Marking payment as refunded: payment_id={payment.id}")
            
            # En producción, aquí llamaríamos al adapter para procesar reembolso real
            payment.status = "refunded"
            
            if not payment.metadata:
                payment.metadata = {}
            
            payment.metadata.update({
                "cancelled": True,
                "cancelled_at": event.timestamp,
                "cancellation_reason": event.reason,
                "refund_amount": event.refund_amount or payment.amount,
                "cancelled_by_partner": partner.nombre
            })
            
            db.commit()
            
            # Notificar al partner que el reembolso fue procesado
            await PartnerWebhookProcessor._notify_partner_payment_refunded(
                db, partner, payment
            )
        
        return {
            "status": "processed",
            "action": "payment_refunded",
            "payment_id": payment.id,
            "booking_id": event.booking_id
        }
    
    @staticmethod
    async def _notify_partner_payment_success(
        db: Session,
        partner: Partner,
        payment: Payment
    ):
        """
        Notifica al partner que el pago fue exitoso (respuesta bidireccional).
        """
        try:
            event = NormalizedWebhookEvent(
                event_type="payment.success",
                payment_id=payment.external_payment_id,
                status="completed",
                amount=payment.amount,
                currency=payment.currency,
                metadata=payment.metadata or {},
                raw_payload={}
            )
            
            await PartnerService.deliver_webhook_to_partner(partner, event)
            
            logger.info(f"Partner notified of payment success: payment_id={payment.id}")
        
        except Exception as e:
            logger.error(f"Failed to notify partner: {e}", exc_info=True)
    
    @staticmethod
    async def _notify_partner_payment_refunded(
        db: Session,
        partner: Partner,
        payment: Payment
    ):
        """
        Notifica al partner que el pago fue reembolsado.
        """
        try:
            event = NormalizedWebhookEvent(
                event_type="payment.refunded",
                payment_id=payment.external_payment_id,
                status="refunded",
                amount=payment.amount,
                currency=payment.currency,
                metadata=payment.metadata or {},
                raw_payload={}
            )
            
            await PartnerService.deliver_webhook_to_partner(partner, event)
            
            logger.info(f"Partner notified of refund: payment_id={payment.id}")
        
        except Exception as e:
            logger.error(f"Failed to notify partner of refund: {e}", exc_info=True)
