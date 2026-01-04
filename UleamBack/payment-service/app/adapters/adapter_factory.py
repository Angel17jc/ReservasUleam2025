"""
Adapter Factory

Implementa el Factory Pattern para crear instancias de payment adapters.
Proporciona un punto centralizado para obtener el adapter correcto según el provider.

Patrones aplicados:
- Factory Method: Método estático para crear adapters
- Singleton: Reutiliza instancias de adapters (cache)
- Strategy: Los adapters son estrategias intercambiables

Benefits:
- Desacoplamiento: El código cliente no conoce las clases concretas
- Configuración centralizada: Validación de credenciales en un solo lugar
- Performance: Cache de instancias reduce overhead
- Extensibilidad: Agregar nuevos providers sin modificar código existente
"""

import logging
from typing import Dict

from .base import PaymentProvider
from .mock_adapter import MockAdapter
from .stripe_adapter import StripeAdapter
from ..config import settings

logger = logging.getLogger(__name__)


class AdapterFactory:
    """
    Factory para crear y gestionar instancias de payment adapters.
    
    Implementa el patrón Singleton para los adapters, reutilizando
    instancias para mejorar performance y mantener estado si es necesario.
    
    Usage:
        adapter = AdapterFactory.get_adapter("stripe")
        payment = adapter.create_payment(50.0, "USD", {...})
    
    Supported providers:
        - "mock": MockAdapter (development/testing)
        - "stripe": StripeAdapter (production)
        - "mercadopago": MercadoPagoAdapter (TODO)
    """
    
    # Cache de adapters instanciados (Singleton pattern)
    _adapters: Dict[str, PaymentProvider] = {}
    
    # Lock para thread-safety (si usamos threads en el futuro)
    _lock = None  # threading.Lock() si se necesita
    
    @classmethod
    def get_adapter(cls, provider_name: str) -> PaymentProvider:
        """
        Obtiene o crea una instancia del adapter solicitado.
        
        Utiliza cache para reutilizar instancias (Singleton pattern por provider).
        
        Args:
            provider_name: Nombre del provider ("mock", "stripe", "mercadopago")
        
        Returns:
            PaymentProvider: Instancia del adapter correspondiente
        
        Raises:
            ValueError: Si el provider no es soportado o está mal configurado
        
        Examples:
            >>> adapter = AdapterFactory.get_adapter("mock")
            >>> payment = adapter.create_payment(50.0, "USD", {})
            
            >>> adapter = AdapterFactory.get_adapter("stripe")
            >>> # Usa credenciales de STRIPE_API_KEY del settings
        """
        # Normalizar nombre del provider
        provider_name = provider_name.lower().strip()
        
        # Verificar si ya existe en cache
        if provider_name in cls._adapters:
            logger.debug(f"Using cached adapter for provider: {provider_name}")
            return cls._adapters[provider_name]
        
        # Crear nueva instancia según el provider
        adapter = cls._create_adapter(provider_name)
        
        # Almacenar en cache
        cls._adapters[provider_name] = adapter
        
        logger.info(f"Adapter created and cached: {provider_name}")
        
        return adapter
    
    @classmethod
    def _create_adapter(cls, provider_name: str) -> PaymentProvider:
        """
        Crea una nueva instancia del adapter (método privado).
        
        Args:
            provider_name: Nombre del provider
        
        Returns:
            PaymentProvider: Nueva instancia del adapter
        
        Raises:
            ValueError: Si el provider no es válido o no está configurado
        """
        if provider_name == "mock":
            return cls._create_mock_adapter()
        
        elif provider_name == "stripe":
            return cls._create_stripe_adapter()
        
        elif provider_name == "mercadopago":
            return cls._create_mercadopago_adapter()
        
        else:
            logger.error(f"Unsupported payment provider requested: {provider_name}")
            raise ValueError(
                f"Unsupported payment provider: {provider_name}. "
                f"Supported providers: mock, stripe, mercadopago"
            )
    
    @classmethod
    def _create_mock_adapter(cls) -> MockAdapter:
        """
        Crea instancia de MockAdapter.
        
        Returns:
            MockAdapter: Adapter de prueba
        
        Raises:
            ValueError: Si MockAdapter está deshabilitado en producción
        """
        # Verificar si mock está habilitado
        if not settings.MOCK_PROVIDER_ENABLED:
            logger.error("Attempted to use MockAdapter in production")
            raise ValueError(
                "Mock provider is disabled in production. "
                "Set MOCK_PROVIDER_ENABLED=true in .env to enable (only for development)"
            )
        
        logger.info("Creating MockAdapter (development/testing mode)")
        return MockAdapter()
    
    @classmethod
    def _create_stripe_adapter(cls) -> StripeAdapter:
        """
        Crea instancia de StripeAdapter.
        
        Returns:
            StripeAdapter: Adapter de Stripe
        
        Raises:
            ValueError: Si las credenciales de Stripe no están configuradas
        """
        # Verificar que las credenciales estén configuradas
        if not settings.STRIPE_API_KEY:
            logger.error("Stripe API key not configured")
            raise ValueError(
                "Stripe provider requires STRIPE_API_KEY. "
                "Set it in .env or environment variables."
            )
        
        # Advertir si webhook secret no está configurado
        if not settings.STRIPE_WEBHOOK_SECRET:
            logger.warning(
                "STRIPE_WEBHOOK_SECRET not configured. "
                "Webhook signature validation will be skipped (INSECURE)"
            )
        
        logger.info("Creating StripeAdapter with configured credentials")
        return StripeAdapter()
    
    @classmethod
    def _create_mercadopago_adapter(cls):
        """
        Crea instancia de MercadoPagoAdapter.
        
        TODO: Implementar MercadoPagoAdapter en el futuro.
        
        Returns:
            MercadoPagoAdapter: Adapter de MercadoPago
        
        Raises:
            NotImplementedError: MercadoPago aún no está implementado
        """
        logger.error("MercadoPago adapter not implemented yet")
        raise NotImplementedError(
            "MercadoPago adapter is not implemented yet. "
            "Coming in a future version. Use 'mock' or 'stripe' for now."
        )
    
    @classmethod
    def clear_cache(cls) -> None:
        """
        Limpia el cache de adapters.
        
        Útil para testing o cuando se necesita recrear adapters
        (ej: después de cambiar credenciales).
        
        Warning:
            Esto no afecta adapters ya obtenidos por el código cliente.
            Solo afecta futuras llamadas a get_adapter().
        """
        count = len(cls._adapters)
        cls._adapters.clear()
        logger.info(f"Adapter cache cleared ({count} adapters removed)")
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """
        Retorna la lista de providers disponibles según la configuración.
        
        Verifica qué providers tienen las credenciales necesarias configuradas.
        
        Returns:
            list[str]: Lista de providers disponibles
        
        Example:
            >>> AdapterFactory.get_available_providers()
            ['mock', 'stripe']
        """
        available = []
        
        # Mock siempre disponible si está habilitado
        if settings.MOCK_PROVIDER_ENABLED:
            available.append("mock")
        
        # Stripe disponible si hay API key
        if settings.STRIPE_API_KEY:
            available.append("stripe")
        
        # MercadoPago disponible si hay access token
        if settings.MERCADOPAGO_ACCESS_TOKEN:
            available.append("mercadopago")  # Cuando se implemente
        
        return available
    
    @classmethod
    def is_provider_available(cls, provider_name: str) -> bool:
        """
        Verifica si un provider está disponible.
        
        Args:
            provider_name: Nombre del provider
        
        Returns:
            bool: True si el provider está disponible
        
        Example:
            >>> if AdapterFactory.is_provider_available("stripe"):
            ...     adapter = AdapterFactory.get_adapter("stripe")
        """
        return provider_name.lower() in cls.get_available_providers()
    
    @classmethod
    def validate_provider_config(cls, provider_name: str) -> Dict[str, any]:
        """
        Valida la configuración de un provider sin crear instancia.
        
        Útil para health checks y verificación de configuración.
        
        Args:
            provider_name: Nombre del provider
        
        Returns:
            Dict con estado de validación:
            {
                "provider": str,
                "available": bool,
                "configured": bool,
                "issues": list[str]
            }
        
        Example:
            >>> status = AdapterFactory.validate_provider_config("stripe")
            >>> if not status["configured"]:
            ...     print(f"Issues: {status['issues']}")
        """
        provider_name = provider_name.lower()
        issues = []
        configured = True
        
        if provider_name == "mock":
            if not settings.MOCK_PROVIDER_ENABLED:
                configured = False
                issues.append("MOCK_PROVIDER_ENABLED is false")
        
        elif provider_name == "stripe":
            if not settings.STRIPE_API_KEY:
                configured = False
                issues.append("STRIPE_API_KEY not configured")
            if not settings.STRIPE_WEBHOOK_SECRET:
                issues.append("STRIPE_WEBHOOK_SECRET not configured (webhooks insecure)")
        
        elif provider_name == "mercadopago":
            if not settings.MERCADOPAGO_ACCESS_TOKEN:
                configured = False
                issues.append("MERCADOPAGO_ACCESS_TOKEN not configured")
            issues.append("MercadoPago adapter not implemented yet")
        
        else:
            configured = False
            issues.append(f"Unknown provider: {provider_name}")
        
        return {
            "provider": provider_name,
            "available": cls.is_provider_available(provider_name),
            "configured": configured and len(issues) == 0,
            "issues": issues
        }
    
    @classmethod
    def get_cached_providers(cls) -> list[str]:
        """
        Retorna la lista de providers actualmente en cache.
        
        Returns:
            list[str]: Nombres de providers con instancias cacheadas
        """
        return list(cls._adapters.keys())
