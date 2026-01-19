"""
Conversation Service

Maneja la lógica de negocio de conversaciones y mensajes.

Principios aplicados:
- Single Responsibility: Solo maneja operaciones de BD de conversaciones
- Repository Pattern: Encapsula acceso a datos
- Separation of Concerns: Separado del orchestrator
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import logging

from ..models.conversation import Conversation
from ..models.message import Message


logger = logging.getLogger(__name__)


class ConversationService:
    """
    Servicio para gestionar conversaciones y mensajes.
    
    Maneja todas las operaciones CRUD relacionadas con conversaciones.
    """
    
    @staticmethod
    def create_conversation(
        db: Session,
        usuario_id: int,
        title: Optional[str] = None
    ) -> Conversation:
        """
        Crea una nueva conversación.
        
        Args:
            db: Sesión de BD
            usuario_id: ID del usuario
            title: Título opcional
        
        Returns:
            Conversation: Conversación creada
        """
        try:
            conversation = Conversation(
                usuario_id=usuario_id,
                title=title or f"Conversación {usuario_id}"
            )
            
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            
            logger.info("Created conversation: id=%s, usuario_id=%s", conversation.id, usuario_id)
            return conversation
        
        except Exception as e:
            logger.error("Error creating conversation: %s", e)
            db.rollback()
            raise
    
    @staticmethod
    def get_conversation(
        db: Session,
        conversation_id: int
    ) -> Optional[Conversation]:
        """
        Obtiene una conversación por ID.
        
        Args:
            db: Sesión de BD
            conversation_id: ID de la conversación
        
        Returns:
            Optional[Conversation]: Conversación o None
        """
        return db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
    
    @staticmethod
    def get_user_conversations(
        db: Session,
        usuario_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Conversation]:
        """
        Obtiene conversaciones de un usuario.
        
        Args:
            db: Sesión de BD
            usuario_id: ID del usuario
            limit: Límite de resultados
            offset: Offset para paginación
        
        Returns:
            List[Conversation]: Lista de conversaciones
        """
        return db.query(Conversation).filter(
            Conversation.usuario_id == usuario_id
        ).order_by(
            desc(Conversation.updated_at)
        ).limit(limit).offset(offset).all()
    
    @staticmethod
    def add_message(
        db: Session,
        conversation_id: int,
        role: str,
        content: str,
        tool_calls: Optional[dict] = None
    ) -> Message:
        """
        Añade un mensaje a una conversación.
        
        Args:
            db: Sesión de BD
            conversation_id: ID de la conversación
            role: Rol del mensaje ('user' | 'assistant' | 'system')
            content: Contenido del mensaje
            tool_calls: Llamadas a tools (opcional)
        
        Returns:
            Message: Mensaje creado
        
        Raises:
            ValueError: Si el rol es inválido
        """
        try:
            # Validar rol
            valid_roles = ['user', 'assistant', 'system', 'tool']
            if role not in valid_roles:
                raise ValueError(f"Invalid role: {role}. Must be one of {valid_roles}")
            
            # Crear mensaje
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                tool_calls=tool_calls
            )
            
            db.add(message)
            db.commit()
            db.refresh(message)
            
            logger.debug("Added message: id=%s, role=%s, conversation_id=%s", message.id, role, conversation_id)
            return message
        
        except Exception as e:
            logger.error("Error adding message: %s", e)
            db.rollback()
            raise
    
    @staticmethod
    def get_conversation_messages(
        db: Session,
        conversation_id: int,
        limit: Optional[int] = None
    ) -> List[Message]:
        """
        Obtiene mensajes de una conversación.
        
        Args:
            db: Sesión de BD
            conversation_id: ID de la conversación
            limit: Límite de mensajes (None = todos)
        
        Returns:
            List[Message]: Lista de mensajes ordenados por fecha
        """
        query = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def update_conversation_title(
        db: Session,
        conversation_id: int,
        title: str
    ) -> Optional[Conversation]:
        """
        Actualiza el título de una conversación.
        
        Args:
            db: Sesión de BD
            conversation_id: ID de la conversación
            title: Nuevo título
        
        Returns:
            Optional[Conversation]: Conversación actualizada o None
        """
        try:
            conversation = ConversationService.get_conversation(db, conversation_id)
            
            if not conversation:
                return None
            
            conversation.title = title
            db.commit()
            db.refresh(conversation)
            
            logger.info("Updated conversation title: id=%s, title='%s'", conversation_id, title)
            return conversation
        
        except Exception as e:
            logger.error("Error updating conversation title: %s", e)
            db.rollback()
            raise
    
    @staticmethod
    def delete_conversation(
        db: Session,
        conversation_id: int
    ) -> bool:
        """
        Elimina una conversación (y sus mensajes en cascada).
        
        Args:
            db: Sesión de BD
            conversation_id: ID de la conversación
        
        Returns:
            bool: True si se eliminó, False si no existía
        """
        try:
            conversation = ConversationService.get_conversation(db, conversation_id)
            
            if not conversation:
                return False
            
            db.delete(conversation)
            db.commit()
            
            logger.info("Deleted conversation: id=%s", conversation_id)
            return True
        
        except Exception as e:
            logger.error("Error deleting conversation: %s", e)
            db.rollback()
            raise
