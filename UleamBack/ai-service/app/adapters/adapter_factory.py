"""
Adapter Factory

Factory Pattern para crear instancias de LLM Providers.

Principios aplicados:
- Factory Pattern: Encapsula la creación de objetos
- Single Responsibility: Solo se encarga de instanciar adapters
- Open/Closed: Fácil agregar nuevos providers sin modificar código
"""

from typing import Optional
import logging

from .base import LLMProvider
from .gemini_adapter import GeminiAdapter
from .groq_adapter import GroqAdapter
from ..config import settings

logger = logging.getLogger(__name__)


class AdapterFactory:
    """
    Factory para crear instancias de LLM Providers.
    
    Centraliza la lógica de creación y configuración de adapters.
    """
    
    # Registry de providers disponibles
    _providers = {
        "gemini": GeminiAdapter,
        "groq": GroqAdapter,
    }
    
    @classmethod
    def create(
        cls,
        provider_name: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> LLMProvider:
        """
        Crea una instancia del provider especificado.
        
        Args:
            provider_name: Nombre del provider ('gemini' | 'groq')
                          Si es None, usa DEFAULT_LLM_PROVIDER de settings
            api_key: API key del provider (opcional, usa settings por defecto)
        
        Returns:
            LLMProvider: Instancia del provider
        
        Raises:
            ValueError: Si el provider no existe o no está configurado
        
        Example:
            # Usar provider por defecto
            adapter = AdapterFactory.create()
            
            # Usar provider específico
            adapter = AdapterFactory.create("groq")
            
            # Con API key custom
            adapter = AdapterFactory.create("gemini", api_key="custom_key")
        """
        # Determinar provider a usar
        if provider_name is None:
            provider_name = settings.DEFAULT_LLM_PROVIDER
        
        provider_name = provider_name.lower()
        
        # Validar que existe
        if provider_name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Unknown LLM provider: '{provider_name}'. "
                f"Available providers: {available}"
            )
        
        # Obtener API key
        if api_key is None:
            api_key = cls._get_api_key_for_provider(provider_name)
        
        # Validar que tiene API key
        if not api_key:
            raise ValueError(
                f"No API key found for provider '{provider_name}'. "
                f"Please set {provider_name.upper()}_API_KEY in .env"
            )
        
        # Crear instancia
        provider_class = cls._providers[provider_name]
        
        try:
            instance = provider_class(api_key=api_key)
            logger.info("Created LLM adapter: %s", provider_name)
            return instance
        
        except Exception as e:
            logger.error("Error creating adapter for %s: %s", provider_name, e)
            raise ValueError(f"Failed to initialize {provider_name} adapter: {str(e)}") from e
    
    @classmethod
    def create_default(cls) -> LLMProvider:
        """
        Crea una instancia del provider por defecto configurado en settings.
        
        Returns:
            LLMProvider: Instancia del provider por defecto
        
        Raises:
            ValueError: Si el provider por defecto no está configurado
        """
        return cls.create(provider_name=settings.DEFAULT_LLM_PROVIDER)
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """
        Lista todos los providers disponibles.
        
        Returns:
            list[str]: Nombres de providers disponibles
        """
        return list(cls._providers.keys())
    
    @classmethod
    def is_provider_configured(cls, provider_name: str) -> bool:
        """
        Verifica si un provider está configurado (tiene API key).
        
        Args:
            provider_name: Nombre del provider
        
        Returns:
            bool: True si está configurado
        """
        provider_name = provider_name.lower()
        
        if provider_name not in cls._providers:
            return False
        
        api_key = cls._get_api_key_for_provider(provider_name)
        return api_key is not None and len(api_key) > 0
    
    @classmethod
    def _get_api_key_for_provider(cls, provider_name: str) -> Optional[str]:
        """
        Obtiene la API key del provider desde settings.
        
        Args:
            provider_name: Nombre del provider
        
        Returns:
            Optional[str]: API key o None
        """
        if provider_name == "gemini":
            return settings.GEMINI_API_KEY
        elif provider_name == "groq":
            return settings.GROQ_API_KEY
        else:
            return None
    
    @classmethod
    def register_provider(
        cls,
        name: str,
        provider_class: type[LLMProvider]
    ) -> None:
        """
        Registra un nuevo provider (extensibilidad).
        
        Permite agregar providers custom sin modificar el código del factory.
        
        Args:
            name: Nombre del provider
            provider_class: Clase que implementa LLMProvider
        
        Raises:
            ValueError: Si el provider ya existe o la clase es inválida
        """
        name = name.lower()
        
        if name in cls._providers:
            raise ValueError(f"Provider '{name}' is already registered")
        
        if not issubclass(provider_class, LLMProvider):
            raise ValueError("Provider class must inherit from LLMProvider")
        
        cls._providers[name] = provider_class
        logger.info("Registered new LLM provider: %s", name)


# Helper function para uso directo
def get_llm_adapter(provider_name: Optional[str] = None) -> LLMProvider:
    """
    Helper function para obtener un adapter rápidamente.
    
    Args:
        provider_name: Nombre del provider (None = usar default)
    
    Returns:
        LLMProvider: Instancia del adapter
    """
    return AdapterFactory.create(provider_name)
