"""
Tool Execution Model

Representa la ejecución de un MCP Tool por el LLM.

Principios aplicados:
- Single Responsibility: Solo representa ejecuciones de tools
- Observability: Métricas de tiempo de ejecución
"""

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from ..database import Base


class ToolExecution(Base):
    """
    Modelo de ejecución de MCP Tool.
    
    Attributes:
        id: Primary key
        message_id: ID del mensaje que trigger el tool (FK)
        tool_name: Nombre del tool ejecutado
        parameters: JSON con los parámetros enviados al tool
        result: JSON con el resultado del tool
        status: Estado de la ejecución ('pending', 'success', 'failed')
        error_message: Mensaje de error (si failed)
        execution_time_ms: Tiempo de ejecución en milisegundos
        created_at: Fecha de creación
        message: Relación con mensaje
    """
    
    __tablename__ = "tool_execution"
    
    # ===== Columns =====
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(
        Integer,
        ForeignKey("message.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tool_name = Column(String(100), nullable=False, index=True)
    parameters = Column(JSONB, nullable=False)
    result = Column(JSONB, nullable=True)
    status = Column(String(20), nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default="NOW()")
    
    # ===== Relationships =====
    message = relationship(
        "Message",
        back_populates="tool_executions"
    )
    
    # ===== Constraints =====
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'success', 'failed')", name="check_tool_execution_status"),
        Index('idx_tool_execution_message_id', 'message_id'),
        Index('idx_tool_execution_tool_name', 'tool_name'),
        Index('idx_tool_execution_status', 'status'),
        Index('idx_tool_execution_created_at', 'created_at'),
        Index('idx_tool_execution_parameters', 'parameters', postgresql_using='gin'),
        Index('idx_tool_execution_result', 'result', postgresql_using='gin'),
    )
    
    # ===== Methods =====
    def __repr__(self) -> str:
        return f"<ToolExecution(id={self.id}, tool_name='{self.tool_name}', status='{self.status}')>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "message_id": self.message_id,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "result": self.result,
            "status": self.status,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @property
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self.status == "success"
    
    @property
    def is_failed(self) -> bool:
        """Check if execution failed."""
        return self.status == "failed"
    
    @property
    def is_pending(self) -> bool:
        """Check if execution is pending."""
        return self.status == "pending"
