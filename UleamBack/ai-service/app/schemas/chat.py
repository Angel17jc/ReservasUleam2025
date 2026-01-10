"""
Chat Schemas

Pydantic schemas para validación de requests/responses de chat.

Principios aplicados:
- Input Validation: Valida todas las entradas del usuario
- Data Transfer Objects: DTOs para comunicación API
- Type Safety: Type hints completos
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Roles válidos para mensajes."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessageRequest(BaseModel):
    """
    Request para enviar un mensaje al chatbot.
    
    Attributes:
        content: Contenido del mensaje
        conversation_id: ID de conversación existente (None = nueva conversación)
        usuario_id: ID del usuario que envía el mensaje
        provider: Provider LLM a usar (None = usar default)
        temperature: Temperatura para generación (0.0-2.0)
    """
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Contenido del mensaje"
    )
    conversation_id: Optional[int] = Field(
        None,
        description="ID de conversación existente (None para nueva conversación)"
    )
    usuario_id: int = Field(
        ...,
        gt=0,
        description="ID del usuario"
    )
    provider: Optional[str] = Field(
        None,
        description="Provider LLM ('gemini' | 'groq')"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Creatividad del LLM (0.0=determinístico, 2.0=muy creativo)"
    )
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Valida que el contenido no esté vacío después de strip."""
        if not v.strip():
            raise ValueError("Message content cannot be empty or whitespace")
        return v.strip()
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: Optional[str]) -> Optional[str]:
        """Valida que el provider sea válido."""
        if v is not None:
            allowed = ["gemini", "groq"]
            if v.lower() not in allowed:
                raise ValueError(f"Provider must be one of {allowed}")
            return v.lower()
        return v


class MessageResponse(BaseModel):
    """
    Response de un mensaje.
    
    Attributes:
        id: ID del mensaje
        conversation_id: ID de la conversación
        role: Rol del mensaje
        content: Contenido
        tool_calls: Llamadas a tools (si las hay)
        created_at: Timestamp de creación
    """
    id: int
    conversation_id: int
    role: str
    content: str
    tool_calls: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """
    Response completa del chat incluyendo mensaje del usuario y del assistant.
    
    Attributes:
        conversation_id: ID de la conversación
        user_message: Mensaje del usuario
        assistant_message: Respuesta del assistant
        model: Modelo usado
        provider: Provider usado
        tokens_used: Tokens consumidos
    """
    conversation_id: int
    user_message: MessageResponse
    assistant_message: MessageResponse
    model: str
    provider: str
    tokens_used: Optional[int] = None


class ConversationResponse(BaseModel):
    """
    Response de una conversación.
    
    Attributes:
        id: ID de la conversación
        usuario_id: ID del usuario
        title: Título
        message_count: Cantidad de mensajes
        created_at: Timestamp de creación
        updated_at: Timestamp de última actualización
    """
    id: int
    usuario_id: int
    title: Optional[str] = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    """
    Response detallada de una conversación incluyendo mensajes.
    
    Attributes:
        messages: Lista de mensajes de la conversación
    """
    messages: List[MessageResponse] = []


class ConversationListResponse(BaseModel):
    """
    Response de lista de conversaciones.
    
    Attributes:
        conversations: Lista de conversaciones
        total: Total de conversaciones
    """
    conversations: List[ConversationResponse]
    total: int


class ProviderInfo(BaseModel):
    """
    Información de un provider LLM.
    
    Attributes:
        name: Nombre del provider
        is_configured: Si está configurado (tiene API key)
        is_default: Si es el provider por defecto
        models: Lista de modelos disponibles
    """
    name: str
    is_configured: bool
    is_default: bool
    models: List[str]


class ProvidersResponse(BaseModel):
    """
    Response con lista de providers disponibles.
    
    Attributes:
        providers: Lista de providers
        default_provider: Provider por defecto
    """
    providers: List[ProviderInfo]
    default_provider: str
