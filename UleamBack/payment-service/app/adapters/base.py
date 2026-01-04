"""
Base PaymentProvider Interface

Define el contrato que todos los payment adapters deben implementar.
Implementa el Adapter Pattern para abstraer diferentes pasarelas de pago.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class PaymentProvider(ABC):
    """
    Abstract Base Class que define el contrato para todos los payment providers.
    
    Esta interface permite intercambiar providers sin modificar el código cliente,
    aplicando el principio Open/Closed y Dependency Inversion de SOLID.
    
    Métodos que deben implementar los adapters:
    - create_payment: Crea un pago en el provider externo
    - get_payment_status: Consulta el estado de un pago
    - refund_payment: Procesa un reembolso (opcional)
    - normalize_webhook: Convierte webhook del provider a formato común
    - validate_webhook_signature: Valida la autenticidad del webhook
    """
    
    @abstractmethod
    def create_payment(
        self,
        amount: float,
        currency: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crea un pago en el provider externo.
        
        Args:
            amount: Monto del pago (en unidades, no centavos)
            currency: Código de moneda ISO 4217 (USD, EUR, MXN, etc.)
            metadata: Datos adicionales (reserva_id, usuario_id, descripción, etc.)
        
        Returns:
            Dict con la estructura:
            {
                "payment_id": str,        # ID único del pago en el provider
                "status": str,            # pending, completed, failed
                "amount": float,          # Monto confirmado
                "currency": str,          # Moneda confirmada
                "metadata": dict,         # Metadata almacenado
                "client_secret": str,     # Secret para completar pago (opcional)
                "created_at": datetime    # Timestamp de creación
            }
        
        Raises:
            Exception: Si falla la creación del pago
        """
        pass
    
    @abstractmethod
    def get_payment_status(self, payment_id: str) -> str:
        """
        Consulta el estado actual de un pago en el provider.
        
        Args:
            payment_id: ID del pago en el provider externo
        
        Returns:
            str: Estado normalizado del pago
                - "pending": Pago iniciado pero no completado
                - "completed": Pago exitoso y confirmado
                - "failed": Pago fallido
                - "cancelled": Pago cancelado
                - "refunded": Pago reembolsado
        
        Raises:
            ValueError: Si el payment_id no existe
            Exception: Si falla la consulta
        """
        pass
    
    @abstractmethod
    def refund_payment(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa un reembolso parcial o total de un pago.
        
        Args:
            payment_id: ID del pago a reembolsar
            amount: Monto a reembolsar (None = reembolso total)
            reason: Motivo del reembolso
        
        Returns:
            Dict con información del reembolso:
            {
                "refund_id": str,
                "payment_id": str,
                "amount": float,
                "status": str,
                "created_at": datetime
            }
        
        Raises:
            ValueError: Si el pago no puede ser reembolsado
            Exception: Si falla el reembolso
        """
        pass
    
    @abstractmethod
    def normalize_webhook(self, raw_data: Dict[str, Any]) -> "NormalizedWebhookEvent":
        """
        Normaliza el webhook del provider a un formato común.
        
        Esta es la clave del patrón Adapter: cada provider tiene su propio
        formato de webhook, pero todos se convierten a NormalizedWebhookEvent.
        
        Args:
            raw_data: Payload raw del webhook del provider
        
        Returns:
            NormalizedWebhookEvent: Evento normalizado con estructura común
        
        Ejemplo de transformación:
            Stripe: "payment_intent.succeeded" -> "payment.success"
            MercadoPago: "payment.approved" -> "payment.success"
        """
        pass
    
    @abstractmethod
    def validate_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Valida la firma criptográfica del webhook del provider.
        
        Implementa verificación HMAC o la firma específica del provider
        para garantizar que el webhook proviene del proveedor legítimo.
        
        Args:
            payload: Payload en bytes del webhook
            signature: Firma recibida en el header (ej: "Stripe-Signature")
            timestamp: Timestamp del webhook (para prevenir replay attacks)
        
        Returns:
            bool: True si la firma es válida, False en caso contrario
        
        Security notes:
        - Siempre validar firma antes de procesar webhook
        - Considerar tolerancia de timestamp (ej: 5 minutos)
        - Registrar intentos de firma inválida para auditoría
        """
        pass
    
    def get_provider_name(self) -> str:
        """
        Retorna el nombre del provider (para logging/debugging).
        
        Returns:
            str: Nombre del provider (stripe, mercadopago, mock, etc.)
        """
        return self.__class__.__name__.replace("Adapter", "").lower()
    
    def supports_refunds(self) -> bool:
        """
        Indica si el provider soporta reembolsos.
        
        Algunos providers de prueba pueden no implementar refunds.
        
        Returns:
            bool: True si soporta reembolsos
        """
        return True
    
    def get_webhook_events(self) -> list[str]:
        """
        Lista de eventos de webhook soportados por el provider.
        
        Útil para documentación y validación.
        
        Returns:
            list[str]: Lista de tipos de eventos
        """
        return [
            "payment.success",
            "payment.failed",
            "payment.cancelled",
            "payment.refunded"
        ]


# Type hint para el schema (se importa en tiempo de ejecución para evitar circular import)
if False:
    from ..schemas.webhook import NormalizedWebhookEvent
