"""
Conversation Model

Representa una conversación entre un usuario y el chatbot AI.

Principios aplicados:
- Single Responsibility: Solo representa conversaciones
- Encapsulation: Propiedades calculadas encapsuladas
"""

from sqlalchemy import Column, Integer, String, TIMESTAMP, Index, text
from sqlalchemy.orm import relationship

from ..database import Base


class Conversation(Base):
    """
    Modelo de conversación del chatbot.
    
    Attributes:
        id: Primary key
        usuario_id: ID del usuario (FK a tabla usuario del sistema principal)
        title: Título de la conversación (opcional)
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
        messages: Relación con mensajes
    """
    
    __tablename__ = "conversation"
    
    # ===== Columns =====
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))
    
    # ===== Relationships =====
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # ===== Indexes =====
    __table_args__ = (
        Index('idx_conversation_usuario_id', 'usuario_id'),
        Index('idx_conversation_created_at', 'created_at'),
    )
    
    # ===== Methods =====
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, usuario_id={self.usuario_id}, title='{self.title}')>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "message_count": len(self.messages) if self.messages else 0
        }
