"""
LLM Provider Base Interface

Define el contrato que todos los LLM adapters deben implementar.
Implementa el patrón Strategy para permitir intercambiar providers sin modificar lógica de negocio.

Principios SOLID aplicados:
- Interface Segregation: Interface mínima y específica
- Open/Closed: Extensible sin modificar código existente
- Dependency Inversion: Clientes dependen de abstracción, no de implementaciones concretas
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class LLMRole(str, Enum):
    """Roles válidos para mensajes del LLM."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"  # Para resultados de herramientas


@dataclass
class LLMMessage:
    """
    Estructura de un mensaje para el LLM.
    
    Attributes:
        role: Rol del mensaje (user, assistant, system)
        content: Contenido del mensaje
    """
    role: str
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {"role": self.role, "content": self.content}


@dataclass
class LLMResponse:
    """
    Respuesta normalizada de un LLM.
    
    Attributes:
        content: Contenido de la respuesta
        model: Nombre del modelo usado
        provider: Nombre del provider (gemini, groq, etc)
        tokens_used: Tokens consumidos (si disponible)
        finish_reason: Razón de finalización (stop, length, tool_calls, etc)
        tool_calls: Lista de llamadas a tools (si las hay)
    """
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    def has_tool_calls(self) -> bool:
        """Check if response has tool calls."""
        return self.tool_calls is not None and len(self.tool_calls) > 0


class LLMProvider(ABC):
    """
    Abstract base class para todos los LLM providers.
    
    Cada provider (Gemini, Groq, OpenAI, etc) debe implementar esta interface.
    Esto permite intercambiar providers sin cambiar la lógica de negocio del orchestrator.
    
    Methods:
        generate_response: Genera una respuesta de texto
        generate_with_vision: Genera respuesta analizando una imagen (para Commit 2)
        get_available_models: Lista los modelos disponibles del provider
        is_available: Verifica si el provider está configurado y disponible
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize provider with API key.
        
        Args:
            api_key: API key del provider (opcional si se usa variable de entorno)
        """
        self.api_key = api_key
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        """
        Genera una respuesta del LLM basada en el historial de mensajes.
        
        Args:
            messages: Lista de mensajes (historial de conversación)
            temperature: Temperatura (0.0 = determinístico, 1.0 = creativo)
            max_tokens: Máximo de tokens en la respuesta (None = sin límite)
            tools: Lista de tools disponibles para que el LLM llame (MCP - Commit 2)
        
        Returns:
            LLMResponse: Respuesta normalizada del LLM
        
        Raises:
            Exception: Si falla la generación
        """
        raise NotImplementedError("generate_response must be implemented by subclass")
    
    @abstractmethod
    async def generate_with_vision(
        self,
        image_bytes: bytes,
        prompt: str,
        image_format: str = "jpeg"
    ) -> str:
        """
        Genera respuesta analizando una imagen (Commit 2 - Multimodal).
        
        Args:
            image_bytes: Bytes de la imagen
            prompt: Prompt para analizar la imagen
            image_format: Formato de la imagen (jpeg, png, webp)
        
        Returns:
            str: Respuesta del análisis de la imagen
        
        Raises:
            NotImplementedError: Si el provider no soporta vision
            Exception: Si falla el análisis
        """
        raise NotImplementedError("generate_with_vision must be implemented by subclass")
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Lista los modelos disponibles del provider.
        
        Returns:
            List[str]: Lista de nombres de modelos disponibles
        """
        raise NotImplementedError("get_available_models must be implemented by subclass")
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Verifica si el provider está configurado y disponible.
        
        Returns:
            bool: True si está disponible, False en caso contrario
        """
        raise NotImplementedError("is_available must be implemented by subclass")
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Nombre del provider.
        
        Returns:
            str: Nombre del provider (ej: 'gemini', 'groq', 'openai')
        """
        raise NotImplementedError("provider_name must be implemented by subclass")
    
    def _validate_messages(self, messages: List[LLMMessage]) -> None:
        """
        Valida que la lista de mensajes sea correcta.
        
        Args:
            messages: Lista de mensajes a validar
        
        Raises:
            ValueError: Si la validación falla
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        for msg in messages:
            if not isinstance(msg, LLMMessage):
                raise ValueError(f"All messages must be LLMMessage instances, got {type(msg)}")
            
            if msg.role not in [role.value for role in LLMRole]:
                raise ValueError(f"Invalid role: {msg.role}")
            
            if not msg.content or not msg.content.strip():
                raise ValueError("Message content cannot be empty")
    
    def _validate_temperature(self, temperature: float) -> None:
        """
        Valida que la temperatura esté en rango válido.
        
        Args:
            temperature: Valor de temperatura
        
        Raises:
            ValueError: Si está fuera de rango
        """
        if not 0.0 <= temperature <= 2.0:
            raise ValueError(f"Temperature must be between 0.0 and 2.0, got {temperature}")
