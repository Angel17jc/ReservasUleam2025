"""
Payment Provider Adapters

Este módulo implementa el Adapter Pattern para abstraer diferentes
proveedores de pago (Stripe, MercadoPago, Mock).

Principios SOLID aplicados:
- Open/Closed: Abierto para extensión (nuevos adapters), cerrado para modificación
- Dependency Inversion: Dependencia de abstracción (PaymentProvider), no de implementaciones
- Interface Segregation: Interface mínima pero suficiente
"""

from .base import PaymentProvider
from .mock_adapter import MockAdapter
from .stripe_adapter import StripeAdapter
from .adapter_factory import AdapterFactory

__all__ = [
    "PaymentProvider",
    "MockAdapter",
    "StripeAdapter",
    "AdapterFactory"
]
