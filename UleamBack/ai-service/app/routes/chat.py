"""
Chat Routes

Endpoints principales para interactuar con el chatbot AI.

Endpoints:
- POST /chat/message - Enviar mensaje
- GET /chat/conversations/{usuario_id} - Listar conversaciones
- GET /chat/conversations/{id}/messages - Ver mensajes
- GET /chat/providers - Listar providers disponibles
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.chat import (
    ChatMessageRequest,
    ChatResponse,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ProvidersResponse,
    ProviderInfo,
    MessageResponse
)
from ..services.orchestrator import AIOrchestrator
from ..services.conversation_service import ConversationService
from ..adapters.adapter_factory import AdapterFactory
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def send_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Envía un mensaje al chatbot y obtiene respuesta.
    
    Este es el endpoint principal del sistema de chat.
    
    Args:
        request: Request con el mensaje y parámetros
        db: Sesión de BD (inyectada)
    
    Returns:
        ChatResponse: Mensaje del usuario y respuesta del assistant
    
    Raises:
        HTTPException: Si falla el procesamiento
    
    Example:
        ```json
        {
          "content": "Hola, quiero reservar un espacio",
          "usuario_id": 1,
          "conversation_id": null,
          "provider": "gemini",
          "temperature": 0.7
        }
        ```
    """
    try:
        logger.info(
            "Processing chat message: usuario_id=%s, conversation_id=%s, provider=%s",
            request.usuario_id,
            request.conversation_id,
            request.provider
        )
        
        # Crear orchestrator con el provider solicitado
        orchestrator = AIOrchestrator(
            db=db,
            provider_name=request.provider
        )
        
        # Procesar mensaje
        result = await orchestrator.process_message(
            user_message=request.content,
            usuario_id=request.usuario_id,
            conversation_id=request.conversation_id,
            temperature=request.temperature
        )
        
        logger.info(
            "Message processed: conversation_id=%s, tokens=%s",
            result['conversation_id'],
            result['tokens_used']
        )
        
        # Convertir a response schema
        return ChatResponse(
            conversation_id=result["conversation_id"],
            user_message=MessageResponse(**result["user_message"]),
            assistant_message=MessageResponse(**result["assistant_message"]),
            model=result["model"],
            provider=result["provider"],
            tokens_used=result.get("tokens_used"),
            tools_executed=result.get("tools_executed")
        )
    
    except ValueError as e:
        logger.warning("Validation error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    
    except Exception as e:
        logger.error("Error processing message: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        ) from e


@router.get("/conversations/{usuario_id}", response_model=ConversationListResponse)
async def get_user_conversations(
    usuario_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Obtiene las conversaciones de un usuario.
    
    Args:
        usuario_id: ID del usuario
        limit: Límite de resultados (default: 50)
        offset: Offset para paginación (default: 0)
        db: Sesión de BD (inyectada)
    
    Returns:
        ConversationListResponse: Lista de conversaciones
    
    Example Response:
        ```json
        {
          "conversations": [...],
          "total": 10
        }
        ```
    """
    try:
        logger.debug("Fetching conversations for usuario_id=%s", usuario_id)
        
        conversations = ConversationService.get_user_conversations(
            db=db,
            usuario_id=usuario_id,
            limit=limit,
            offset=offset
        )
        
        # Convertir a response models
        conversation_responses = [
            ConversationResponse(
                id=conv.id,
                usuario_id=conv.usuario_id,
                title=conv.title,
                message_count=len(conv.messages) if conv.messages else 0,
                created_at=conv.created_at,
                updated_at=conv.updated_at
            )
            for conv in conversations
        ]
        
        return ConversationListResponse(
            conversations=conversation_responses,
            total=len(conversation_responses)
        )
    
    except Exception as e:
        logger.error("Error fetching conversations: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.get("/conversations/{conversation_id}/messages", response_model=ConversationDetailResponse)
async def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los mensajes de una conversación.
    
    Args:
        conversation_id: ID de la conversación
        db: Sesión de BD (inyectada)
    
    Returns:
        ConversationDetailResponse: Conversación con mensajes
    
    Raises:
        HTTPException: Si la conversación no existe
    """
    try:
        logger.debug("Fetching messages for conversation_id=%s", conversation_id)
        
        # Obtener conversación
        conversation = ConversationService.get_conversation(
            db=db,
            conversation_id=conversation_id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Obtener mensajes
        messages = ConversationService.get_conversation_messages(
            db=db,
            conversation_id=conversation_id
        )
        
        # Convertir a response
        return ConversationDetailResponse(
            id=conversation.id,
            usuario_id=conversation.usuario_id,
            title=conversation.title,
            message_count=len(messages),
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=[MessageResponse.model_validate(msg) for msg in messages]
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error("Error fetching conversation messages: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina una conversación.
    
    Args:
        conversation_id: ID de la conversación
        db: Sesión de BD (inyectada)
    
    Raises:
        HTTPException: Si la conversación no existe
    """
    try:
        logger.info("Deleting conversation: id=%s", conversation_id)
        
        deleted = ConversationService.delete_conversation(
            db=db,
            conversation_id=conversation_id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        return None
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error("Error deleting conversation: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.get("/providers", response_model=ProvidersResponse)
async def get_providers():
    """
    Lista los providers LLM disponibles y su estado.
    
    Returns:
        ProvidersResponse: Lista de providers con su configuración
    
    Example Response:
        ```json
        {
          "providers": [
            {
              "name": "gemini",
              "is_configured": true,
              "is_default": true,
              "models": ["gemini-2.5-flash"]
            },
            {
              "name": "groq",
              "is_configured": true,
              "is_default": false,
              "models": ["llama3-70b-8192", "mixtral-8x7b-32768"]
            }
          ],
          "default_provider": "gemini"
        }
        ```
    """
    try:
        providers_info = []
        default_provider = settings.DEFAULT_LLM_PROVIDER
        
        for provider_name in AdapterFactory.get_available_providers():
            is_configured = AdapterFactory.is_provider_configured(provider_name)
            
            # Obtener modelos disponibles
            models = []
            if is_configured:
                try:
                    adapter = AdapterFactory.create(provider_name)
                    models = adapter.get_available_models()
                except (ValueError, RuntimeError):
                    pass
            
            providers_info.append(ProviderInfo(
                name=provider_name,
                is_configured=is_configured,
                is_default=(provider_name == default_provider),
                models=models
            ))
        
        return ProvidersResponse(
            providers=providers_info,
            default_provider=default_provider
        )
    
    except Exception as e:
        logger.error("Error fetching providers: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e
