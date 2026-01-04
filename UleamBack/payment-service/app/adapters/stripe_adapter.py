"""
Stripe Payment Adapter

Implementación real del PaymentProvider para Stripe.
Integra con la API de Stripe para procesar pagos reales.

Documentación oficial: https://stripe.com/docs/api
SDK Python: https://github.com/stripe/stripe-python

Requisitos:
- stripe SDK instalado (pip install stripe==7.0.0)
- STRIPE_API_KEY configurado en .env
- STRIPE_WEBHOOK_SECRET configurado para validar webhooks
"""

import stripe
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .base import PaymentProvider
from ..schemas.webhook import NormalizedWebhookEvent
from ..config import settings

logger = logging.getLogger(__name__)


class StripeAdapter(PaymentProvider):
    """
    Adapter para procesar pagos con Stripe.
    
    Stripe utiliza PaymentIntents para manejar el flujo de pago.
    Este adapter abstrae la complejidad de Stripe y expone una interface simple.
    
    Flow de pago:
    1. create_payment() crea un PaymentIntent en Stripe
    2. El cliente usa el client_secret para completar el pago
    3. Stripe envía webhook cuando el pago se completa
    4. normalize_webhook() procesa el webhook
    
    Características de Stripe:
    - Maneja montos en centavos (ej: $50.00 = 5000 centavos)
    - Soporta múltiples métodos de pago automáticamente
    - Excelente documentación y sandbox
    - Strong Customer Authentication (SCA) para Europa
    """
    
    def __init__(self):
        """
        Inicializa el StripeAdapter con credenciales del settings.
        
        Raises:
            ValueError: Si STRIPE_API_KEY no está configurado
        """
        if not settings.STRIPE_API_KEY:
            raise ValueError(
                "STRIPE_API_KEY not configured. "
                "Set it in .env or environment variables."
            )
        
        # Configurar API key de Stripe
        stripe.api_key = settings.STRIPE_API_KEY
        
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        
        # Verificar que la API key es válida
        try:
            # Test API call
            stripe.Account.retrieve()
            logger.info("StripeAdapter initialized successfully")
        except stripe.error.AuthenticationError:
            logger.error("Invalid Stripe API key")
            raise ValueError("Invalid STRIPE_API_KEY")
        except Exception as e:
            logger.warning(f"Could not verify Stripe credentials: {e}")
    
    def create_payment(
        self,
        amount: float,
        currency: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crea un PaymentIntent en Stripe.
        
        PaymentIntent representa la intención de cobrar dinero al cliente.
        El cliente debe usar el client_secret para completar el pago.
        
        Args:
            amount: Monto en unidades (ej: 50.00 para $50)
            currency: Código de moneda (usd, eur, mxn, etc.)
            metadata: Datos adicionales (max 50 keys, 500 chars cada uno)
        
        Returns:
            Dict con:
                - payment_id: ID del PaymentIntent
                - status: "pending" (requires_payment_method)
                - amount: Monto confirmado
                - currency: Moneda confirmada
                - client_secret: Para completar el pago
                - created_at: Timestamp de creación
        
        Raises:
            Exception: Si falla la creación en Stripe
        
        Docs: https://stripe.com/docs/api/payment_intents/create
        """
        try:
            # Stripe maneja montos en centavos
            amount_cents = int(amount * 100)
            
            # Crear PaymentIntent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                metadata=metadata,
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "never"  # Solo métodos directos
                },
                description=metadata.get("descripcion", "Payment for ULEAM reservation")
            )
            
            logger.info(
                f"Stripe PaymentIntent created: {payment_intent.id} "
                f"(amount={amount} {currency})"
            )
            
            return {
                "payment_id": payment_intent.id,
                "status": "pending",  # Stripe inicia como pending
                "amount": amount,
                "currency": currency.upper(),
                "metadata": metadata,
                "client_secret": payment_intent.client_secret,
                "created_at": datetime.fromtimestamp(payment_intent.created)
            }
        
        except stripe.error.CardError as e:
            # Errores de tarjeta (saldo insuficiente, tarjeta rechazada, etc.)
            logger.error(f"Stripe CardError: {e.user_message}")
            raise Exception(f"Card error: {e.user_message}")
        
        except stripe.error.RateLimitError as e:
            logger.error("Stripe rate limit exceeded")
            raise Exception("Too many requests to payment provider")
        
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Stripe InvalidRequest: {e.user_message}")
            raise Exception(f"Invalid request: {e.user_message}")
        
        except stripe.error.AuthenticationError as e:
            logger.error("Stripe authentication failed")
            raise Exception("Payment provider authentication failed")
        
        except stripe.error.APIConnectionError as e:
            logger.error("Stripe network error")
            raise Exception("Could not connect to payment provider")
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise Exception(f"Payment provider error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error creating Stripe payment: {str(e)}")
            raise Exception(f"Unexpected error: {str(e)}")
    
    def get_payment_status(self, payment_id: str) -> str:
        """
        Consulta el estado de un PaymentIntent en Stripe.
        
        Args:
            payment_id: ID del PaymentIntent
        
        Returns:
            str: Estado normalizado del pago
        
        Raises:
            ValueError: Si el payment_id no existe
            Exception: Si falla la consulta
        
        Docs: https://stripe.com/docs/api/payment_intents/retrieve
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_id)
            
            # Mapear estados de Stripe a nuestros estados normalizados
            status = self._map_stripe_status(payment_intent.status)
            
            logger.debug(f"Stripe payment status: {payment_id} -> {status}")
            
            return status
        
        except stripe.error.InvalidRequestError:
            logger.warning(f"Stripe payment not found: {payment_id}")
            raise ValueError(f"Payment {payment_id} not found")
        
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving Stripe payment: {str(e)}")
            raise Exception(f"Error retrieving payment: {str(e)}")
    
    def refund_payment(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa un reembolso en Stripe.
        
        Args:
            payment_id: ID del PaymentIntent
            amount: Monto a reembolsar (None = reembolso total)
            reason: Motivo del reembolso (duplicate, fraudulent, requested_by_customer)
        
        Returns:
            Dict con datos del reembolso
        
        Raises:
            ValueError: Si el pago no puede ser reembolsado
            Exception: Si falla el reembolso
        
        Docs: https://stripe.com/docs/api/refunds/create
        """
        try:
            # Preparar parámetros del reembolso
            refund_params = {"payment_intent": payment_id}
            
            if amount is not None:
                refund_params["amount"] = int(amount * 100)
            
            # Stripe acepta: duplicate, fraudulent, requested_by_customer
            if reason:
                stripe_reason = "requested_by_customer"  # Default seguro
                if reason.lower() in ["duplicate", "fraudulent", "requested_by_customer"]:
                    stripe_reason = reason.lower()
                refund_params["reason"] = stripe_reason
            
            # Crear reembolso
            refund = stripe.Refund.create(**refund_params)
            
            logger.info(
                f"Stripe refund created: {refund.id} "
                f"(payment={payment_id}, amount={refund.amount/100})"
            )
            
            return {
                "refund_id": refund.id,
                "payment_id": payment_id,
                "amount": refund.amount / 100,
                "status": refund.status,  # pending, succeeded, failed, canceled
                "reason": refund.reason,
                "created_at": datetime.fromtimestamp(refund.created)
            }
        
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Stripe refund error: {e.user_message}")
            raise ValueError(f"Cannot refund payment: {e.user_message}")
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error processing refund: {str(e)}")
            raise Exception(f"Refund error: {str(e)}")
    
    def normalize_webhook(self, raw_data: Dict[str, Any]) -> NormalizedWebhookEvent:
        """
        Normaliza webhooks de Stripe al formato común.
        
        Stripe envía eventos como:
        - payment_intent.succeeded
        - payment_intent.payment_failed
        - payment_intent.canceled
        - charge.refunded
        
        Args:
            raw_data: Evento de Stripe (event.to_dict())
        
        Returns:
            NormalizedWebhookEvent con estructura común
        
        Docs: https://stripe.com/docs/api/events/types
        """
        # Mapeo de eventos de Stripe a eventos normalizados
        event_type_map = {
            "payment_intent.succeeded": "payment.success",
            "payment_intent.payment_failed": "payment.failed",
            "payment_intent.canceled": "payment.cancelled",
            "payment_intent.processing": "payment.pending",
            "charge.refunded": "payment.refunded"
        }
        
        stripe_event_type = raw_data.get("type", "")
        normalized_type = event_type_map.get(
            stripe_event_type,
            "payment.pending"  # Default para eventos desconocidos
        )
        
        # Extraer datos del PaymentIntent
        payment_intent = raw_data.get("data", {}).get("object", {})
        
        # Extraer error si existe
        error_message = None
        if payment_intent.get("last_payment_error"):
            error_message = payment_intent["last_payment_error"].get("message")
        
        return NormalizedWebhookEvent(
            event_type=normalized_type,
            payment_id=payment_intent.get("id", ""),
            status=self._map_stripe_status(payment_intent.get("status", "pending")),
            amount=payment_intent.get("amount", 0) / 100,  # Centavos a unidades
            currency=payment_intent.get("currency", "usd").upper(),
            metadata=payment_intent.get("metadata", {}),
            error_message=error_message,
            timestamp=datetime.utcnow(),
            raw_event=raw_data  # Guardar evento raw para debugging
        )
    
    def validate_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Valida la firma del webhook de Stripe usando HMAC.
        
        Stripe firma los webhooks con tu webhook secret para garantizar
        que provienen de Stripe y no han sido modificados.
        
        Args:
            payload: Payload raw del webhook en bytes
            signature: Valor del header "Stripe-Signature"
            timestamp: No usado (Stripe incluye timestamp en la firma)
        
        Returns:
            bool: True si la firma es válida
        
        Security:
        - Siempre validar firma antes de procesar webhook
        - Stripe incluye timestamp para prevenir replay attacks
        - Si falla validación, registrar el intento (posible ataque)
        
        Docs: https://stripe.com/docs/webhooks/signatures
        """
        if not self.webhook_secret:
            logger.warning(
                "STRIPE_WEBHOOK_SECRET not configured. "
                "Webhook signature validation skipped (INSECURE)"
            )
            return True  # En dev, permitir sin validación
        
        try:
            # Stripe SDK valida automáticamente timestamp y firma
            stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret
            )
            logger.debug("Stripe webhook signature validated successfully")
            return True
        
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Stripe webhook signature verification failed: {str(e)}")
            return False
        
        except Exception as e:
            logger.error(f"Error validating Stripe webhook signature: {str(e)}")
            return False
    
    def _map_stripe_status(self, stripe_status: str) -> str:
        """
        Mapea estados de Stripe a nuestros estados normalizados.
        
        Stripe PaymentIntent statuses:
        - requires_payment_method: Esperando método de pago
        - requires_confirmation: Esperando confirmación
        - requires_action: Requiere acción del cliente (3D Secure)
        - processing: Procesando
        - requires_capture: Esperando captura (para pagos manuales)
        - canceled: Cancelado
        - succeeded: Exitoso
        
        Args:
            stripe_status: Estado de Stripe
        
        Returns:
            str: Estado normalizado
        """
        status_map = {
            "succeeded": "completed",
            "processing": "pending",
            "requires_payment_method": "pending",
            "requires_confirmation": "pending",
            "requires_action": "pending",
            "requires_capture": "pending",
            "canceled": "cancelled",
            "canceledfailed": "failed"  # No es estándar, pero por si acaso
        }
        
        return status_map.get(stripe_status, "pending")
    
    def supports_refunds(self) -> bool:
        """Stripe soporta reembolsos completos"""
        return True
    
    def get_webhook_events(self) -> list[str]:
        """Eventos de webhook soportados por StripeAdapter"""
        return [
            "payment.success",
            "payment.failed",
            "payment.cancelled",
            "payment.refunded",
            "payment.pending"
        ]
