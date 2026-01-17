"""
Tool Registry

Implementa el patrón Registry para registrar y descubrir tools disponibles.
Permite agregar nuevos tools dinámicamente sin modificar código existente.

Principios aplicados:
- Single Responsibility: Solo maneja registro de tools
- Open/Closed: Extensible sin modificación
"""

from typing import Dict, List, Optional
from .base_tool import BaseTool, ToolCategory
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry centralizado de todos los MCP tools disponibles.
    
    Usa el patrón Singleton para asegurar una única instancia.
    """
    
    _instance = None
    _tools: Dict[str, BaseTool] = {}
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance._tools = {}
        return cls._instance
    
    @classmethod
    def register(cls, tool: BaseTool) -> None:
        """
        Registra un tool en el registry.
        
        Args:
            tool: Instancia del tool a registrar
        """
        instance = cls()
        tool_name = tool.name
        
        if tool_name in instance._tools:
            logger.warning(f"Tool {tool_name} already registered, overwriting")
        
        instance._tools[tool_name] = tool
        logger.info(f"Registered tool: {tool_name} (category: {tool.category})")
    
    @classmethod
    def get(cls, tool_name: str) -> Optional[BaseTool]:
        """
        Obtiene un tool por nombre.
        
        Args:
            tool_name: Nombre del tool
        
        Returns:
            BaseTool: Instancia del tool o None si no existe
        """
        instance = cls()
        return instance._tools.get(tool_name)
    
    @classmethod
    def get_all(cls) -> Dict[str, BaseTool]:
        """
        Obtiene todos los tools registrados.
        
        Returns:
            Dict[str, BaseTool]: Diccionario de tools por nombre
        """
        instance = cls()
        return instance._tools.copy()
    
    @classmethod
    def get_by_category(cls, category: ToolCategory) -> Dict[str, BaseTool]:
        """
        Obtiene tools filtrados por categoría.
        
        Args:
            category: Categoría (CONSULTA, ACCION, REPORTE)
        
        Returns:
            Dict[str, BaseTool]: Tools de esa categoría
        """
        instance = cls()
        return {
            name: tool
            for name, tool in instance._tools.items()
            if tool.category == category
        }
    
    @classmethod
    def get_all_schemas(cls) -> List[Dict]:
        """
        Obtiene los schemas de todos los tools para function calling.
        
        Returns:
            List[Dict]: Lista de schemas compatibles con LLM
        """
        instance = cls()
        return [tool.get_schema() for tool in instance._tools.values()]
    
    @classmethod
    def list_tool_names(cls) -> List[str]:
        """
        Lista los nombres de todos los tools registrados.
        
        Returns:
            List[str]: Lista de nombres
        """
        instance = cls()
        return list(instance._tools.keys())
    
    @classmethod
    def count(cls) -> int:
        """
        Cuenta cuántos tools están registrados.
        
        Returns:
            int: Número de tools
        """
        instance = cls()
        return len(instance._tools)
    
    @classmethod
    def clear(cls) -> None:
        """
        Limpia todos los tools (útil para testing).
        """
        instance = cls()
        instance._tools.clear()
        logger.info("Tool registry cleared")


def register_tool(tool_class: type) -> type:
    """
    Decorador para auto-registrar tools.
    
    Usage:
        @register_tool
        class MyTool(BaseTool):
            ...
    
    Args:
        tool_class: Clase del tool
    
    Returns:
        type: Misma clase (para permitir instanciación normal)
    """
    tool_instance = tool_class()
    ToolRegistry.register(tool_instance)
    return tool_class
