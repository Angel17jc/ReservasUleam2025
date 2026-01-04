"""
Mock Payment Adapter

Implementación de prueba del PaymentProvider que simula un proveedor de pago
sin hacer llamadas a APIs externas.

Ideal para:
- Desarrollo local sin credenciales reales
- Testing automatizado
- Demos y pruebas de concepto

Características:
- Auto-completa pagos instantáneamente
- Soporta todos los métodos del PaymentProvider
- No requiere configuración externa
"""

import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .base import PaymentProvider
from ..schemas.webhook import NormalizedWebhookEvent

logger = logging.getLogger(__name__)


class MockAdapter(PaymentProvider):
    """
    Adapter de prueba que simula un payment provider sin APIs externas.
    
    Comportamiento:
    - create_payment: Auto-completa el pago instantáneamente
    - get_payment_status: Retorna siempre "completed"
    - refund_payment: Simula reembolso exitoso
    - validate_webhook_signature: Siempre retorna True (sin validación)
    
    IMPORTANTE: Solo usar en development/testing, NUNCA en producción.
    """
    
    def __init__(self):
        """Inicializa el MockAdapter con almacenamiento en memoria"""
        self.payments: Dict[str, Dict[str, Any]] = {}
        self.refunds: Dict[str, Dict[str, Any]] = {}
        logger.info("MockAdapter initialized (in-memory storage)")
    
    def create_payment(
        self,
        amount: float,
        currency: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simula la creación de un pago.
        
        El pago se completa instantáneamente para facilitar testing.
        En un provider real, el pago quedaría en estado "pending".
        
        Args:
            amount: Monto del pago
            currency: Moneda (USD, EUR, etc.)
            metadata: Datos adicionales
        
        Returns:
            Dict con los datos del pago simulado
        """
        # Generar ID único simulado
        payment_id = f"mock_{uuid.uuid4().hex[:12]}"
        
        # Simular datos del pago
        payment_data = {
            "payment_id": payment_id,
            "status": "completed",  # Mock auto-completa
            "amount": amount,
            "currency": currency.upper(),
            "metadata": metadata,
            "client_secret": f"mock_secret_{uuid.uuid4().hex[:8]}",
            "created_at": datetime.utcnow()
        }
        
        # Almacenar en memoria (simula BD del provider)
        self.payments[payment_id] = payment_data
        
        logger.info(
            f"Mock payment created: {payment_id} "
            f"(amount={amount} {currency}, auto-completed)"
        )
        
        return payment_data
    
    def get_payment_status(self, payment_id: str) -> str:
        """
        Consulta el estado de un pago simulado.
        
        Args:
            payment_id: ID del pago
        
        Returns:
            str: Estado del pago (siempre "completed" si existe)
        
        Raises:
            ValueError: Si el payment_id no existe
        """
        if payment_id not in self.payments:
            logger.warning(f"Payment not found in MockAdapter: {payment_id}")
            raise ValueError(f"Payment {payment_id} not found in mock storage")
        
        status = self.payments[payment_id]["status"]
        logger.debug(f"Mock payment status retrieved: {payment_id} -> {status}")
        
        return status
    
    def refund_payment(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simula un reembolso de pago.
        
        Args:
            payment_id: ID del pago a reembolsar
            amount: Monto a reembolsar (None = reembolso total)
            reason: Motivo del reembolso
        
        Returns:
            Dict con los datos del reembolso simulado
        
        Raises:
            ValueError: Si el pago no existe o no puede ser reembolsado
        """
        if payment_id not in self.payments:
            raise ValueError(f"Payment {payment_id} not found")
        
        payment = self.payments[payment_id]
        
        if payment["status"] != "completed":
            raise ValueError(
                f"Payment {payment_id} cannot be refunded (status: {payment['status']})"
            )
        
        # Calcular monto del reembolso
        refund_amount = amount if amount is not None else payment["amount"]
        
        if refund_amount > payment["amount"]:
            raise ValueError(
                f"Refund amount ({refund_amount}) exceeds payment amount ({payment['amount']})"
            )
        
        # Generar ID del reembolso
        refund_id = f"mock_refund_{uuid.uuid4().hex[:12]}"
        
        # Datos del reembolso
        refund_data = {
            "refund_id": refund_id,
            "payment_id": payment_id,
            "amount": refund_amount,
            "reason": reason or "No reason provided",
            "status": "succeeded",
            "created_at": datetime.utcnow()
        }
        
        # Almacenar reembolso
        self.refunds[refund_id] = refund_data
        
        # Actualizar estado del pago
        payment["status"] = "refunded"
        payment["refunded_amount"] = refund_amount
        
        logger.info(
            f"Mock refund created: {refund_id} "
            f"(payment={payment_id}, amount={refund_amount})"
        )
        
        return refund_data
    
    def normalize_webhook(self, raw_data: Dict[str, Any]) -> NormalizedWebhookEvent:
        """
        Normaliza un webhook simulado.
        
        MockAdapter recibe webhooks ya en formato normalizado,
        por lo que solo necesita construir el objeto NormalizedWebhookEvent.
        
        Args:
            raw_data: Datos del webhook
        
        Returns:
            NormalizedWebhookEvent con estructura normalizada
        """
        # Mock adapter espera datos ya normalizados
        return NormalizedWebhookEvent(
            event_type=raw_data.get("event_type", "payment.success"),
            payment_id=raw_data["payment_id"],
            status=raw_data.get("status", "completed"),
            amount=raw_data["amount"],
            currency=raw_data["currency"],
            metadata=raw_data.get("metadata", {}),
            error_message=raw_data.get("error_message"),
            timestamp=raw_data.get("timestamp", datetime.utcnow())
        )
    
    def validate_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Simula validación de firma de webhook.
        
        IMPORTANTE: MockAdapter acepta CUALQUIER firma para facilitar testing.
        En producción, NUNCA usar MockAdapter.
        
        Args:
            payload: Payload del webhook
            signature: Firma recibida
            timestamp: Timestamp del webhook
        
        Returns:
            bool: Siempre True (sin validación real)
        """
        logger.warning(
            "MockAdapter.validate_webhook_signature: "
            "No real validation (always returns True)"
        )
        return True
    
    def supports_refunds(self) -> bool:
        """MockAdapter soporta reembolsos simulados"""
        return True
    
    def get_webhook_events(self) -> list[str]:
        """Eventos de webhook soportados por MockAdapter"""
        return [
            "payment.success",
            "payment.failed",
            "payment.cancelled",
            "payment.refunded",
            "payment.pending"
        ]
    
    def get_payment_details(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """
        Método auxiliar para obtener detalles completos del pago.
        
        Útil para debugging y testing.
        
        Args:
            payment_id: ID del pago
        
        Returns:
            Dict con todos los datos del pago o None si no existe
        """
        return self.payments.get(payment_id)
    
    def clear_storage(self) -> None:
        """
        Limpia el almacenamiento en memoria.
        
        Útil para testing cuando necesitas resetear el estado.
        """
        self.payments.clear()
        self.refunds.clear()
        logger.info("MockAdapter storage cleared")
    
    def get_storage_stats(self) -> Dict[str, int]:
        """
        Retorna estadísticas del almacenamiento.
        
        Returns:
            Dict con contadores de pagos y reembolsos
        """
        return {
            "total_payments": len(self.payments),
            "total_refunds": len(self.refunds),
            "completed_payments": sum(
                1 for p in self.payments.values() if p["status"] == "completed"
            ),
            "refunded_payments": sum(
                1 for p in self.payments.values() if p["status"] == "refunded"
            )
        }
