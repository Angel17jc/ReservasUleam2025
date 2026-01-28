"""
Message Model

Representa un mensaje dentro de una conversación.

Principios aplicados:
- Single Responsibility: Solo representa mensajes
- Data Integrity: Validación de roles permitidos
"""

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from ..database import Base


class Message(Base):
    """
    Modelo de mensaje del chatbot.
    
    Attributes:
        id: Primary key
        conversation_id: ID de la conversación (FK)
        role: Rol del mensaje ('user', 'assistant', 'system')
        content: Contenido del mensaje
        tool_calls: JSON con las llamadas a tools MCP (si las hay)
        created_at: Fecha de creación
        conversation: Relación con conversación
        tool_executions: Relación con ejecuciones de tools
    """
    
    __tablename__ = "message"
    
    # ===== Columns =====
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversation.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role = Column(
        String(20),
        nullable=False,
        index=True
    )
    content = Column(Text, nullable=False)
    tool_calls = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default="NOW()")
    
    # ===== Relationships =====
    conversation = relationship(
        "Conversation",
        back_populates="messages"
    )
    
    tool_executions = relationship(
        "ToolExecution",
        back_populates="message",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # ===== Constraints =====
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system', 'tool')", name="check_message_role"),
        Index('idx_message_conversation_id', 'conversation_id'),
        Index('idx_message_created_at', 'created_at'),
        Index('idx_message_role', 'role'),
        Index('idx_message_tool_calls', 'tool_calls', postgresql_using='gin'),
    )
    
    # ===== Methods =====
    def __repr__(self) -> str:
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, role='{self.role}', content='{content_preview}')>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "tool_calls": self.tool_calls,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tool_executions": [te.to_dict() for te in self.tool_executions] if self.tool_executions else []
        }
    
    @property
    def is_from_user(self) -> bool:
        """Check if message is from user."""
        return self.role == "user"
    
    @property
    def is_from_assistant(self) -> bool:
        """Check if message is from assistant."""
        return self.role == "assistant"
    
    @property
    def has_tool_calls(self) -> bool:
        """Check if message has tool calls."""
        return self.tool_calls is not None and len(self.tool_calls) > 0
