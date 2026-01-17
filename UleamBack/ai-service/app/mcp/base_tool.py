"""
Base Tool Abstract Class

Define la interface que todos los MCP tools deben implementar.
Usa el patrón Template Method para estandarizar la ejecución de tools.

Principios SOLID aplicados:
- Single Responsibility: Solo define el contrato de un tool
- Open/Closed: Extensible sin modificar esta clase
- Liskov Substitution: Cualquier tool puede ser usado de forma intercambiable
- Interface Segregation: Interface mínima y específica
- Dependency Inversion: Clientes dependen de abstracción, no de implementaciones
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """Categorías de tools según su función."""
    CONSULTA = "consulta"  # Read-only queries
    ACCION = "accion"      # Write operations
    REPORTE = "reporte"    # Analytics and reports


class ParameterType(str, Enum):
    """Tipos de datos para parámetros de tools."""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ToolParameter:
    """
    Definición de un parámetro de tool.
    
    Attributes:
        name: Nombre del parámetro
        type: Tipo de dato (string, integer, etc)
        description: Descripción para el LLM
        required: Si es obligatorio
        default: Valor por defecto (si no es required)
        enum: Valores permitidos (opcional)
    """
    name: str
    type: ParameterType
    description: str
    required: bool = False
    default: Any = None
    enum: Optional[List[Any]] = None
    
    def to_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema format for LLM."""
        schema = {
            "type": self.type.value,
            "description": self.description
        }
        
        if self.enum:
            schema["enum"] = self.enum
        
        return schema


@dataclass
class ToolResult:
    """
    Resultado de la ejecución de un tool.
    
    Attributes:
        success: Si la ejecución fue exitosa
        data: Datos resultantes (si success=True)
        error: Mensaje de error (si success=False)
        metadata: Información adicional (tiempo de ejecución, etc)
    """
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "success": self.success
        }
        
        if self.success:
            result["data"] = self.data
        else:
            result["error"] = self.error
        
        if self.metadata:
            result["metadata"] = self.metadata
        
        return result


class BaseTool(ABC):
    """
    Clase abstracta base para todos los MCP tools.
    
    Cada tool debe implementar:
    - _execute(): Lógica específica del tool
    - get_parameters(): Definición de parámetros
    
    Esta clase provee:
    - execute(): Template method que maneja logging y errores
    - get_schema(): Genera schema para function calling del LLM
    - validate_parameters(): Validación básica de parámetros
    """
    
    def __init__(self):
        """Initialize tool."""
        self.name = self.__class__.__name__.replace('Tool', '').lower()
        self.category = self._get_category()
        self.description = self._get_description()
        self.parameters = self.get_parameters()
    
    @abstractmethod
    def _get_category(self) -> ToolCategory:
        """
        Retorna la categoría del tool.
        
        Returns:
            ToolCategory: CONSULTA, ACCION o REPORTE
        """
        pass
    
    @abstractmethod
    def _get_description(self) -> str:
        """
        Retorna descripción del tool para el LLM.
        
        La descripción debe ser clara y concisa, explicando:
        - Qué hace el tool
        - Cuándo usarlo
        - Qué retorna
        
        Returns:
            str: Descripción del tool
        """
        pass
    
    @abstractmethod
    def get_parameters(self) -> List[ToolParameter]:
        """
        Define los parámetros que acepta el tool.
        
        Returns:
            List[ToolParameter]: Lista de parámetros
        """
        pass
    
    @abstractmethod
    async def _execute(self, **kwargs) -> ToolResult:
        """
        Implementación específica del tool.
        
        Este método debe ser implementado por cada tool concreto.
        Contiene la lógica de negocio específica.
        
        Args:
            **kwargs: Parámetros del tool
        
        Returns:
            ToolResult: Resultado de la ejecución
        """
        pass
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        Template method que ejecuta el tool con logging y manejo de errores.
        
        Este método NO debe ser sobrescrito. Usa _execute() para lógica específica.
        
        Args:
            **kwargs: Parámetros del tool
        
        Returns:
            ToolResult: Resultado de la ejecución
        """
        logger.info(f"Executing tool: {self.name} with params: {kwargs}")
        
        try:
            # Validar parámetros
            validation_error = self.validate_parameters(kwargs)
            if validation_error:
                return ToolResult(
                    success=False,
                    error=validation_error
                )
            
            # Ejecutar lógica específica
            result = await self._execute(**kwargs)
            
            logger.info(f"Tool {self.name} executed successfully")
            return result
        
        except Exception as e:
            logger.error(f"Error executing tool {self.name}: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Error al ejecutar {self.name}: {str(e)}"
            )
    
    def validate_parameters(self, params: Dict[str, Any]) -> Optional[str]:
        """
        Valida que los parámetros requeridos estén presentes.
        
        Args:
            params: Parámetros recibidos
        
        Returns:
            str: Mensaje de error si hay problemas, None si todo OK
        """
        for param in self.parameters:
            if param.required and param.name not in params:
                return f"Parámetro requerido faltante: {param.name}"
        
        return None
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Genera el schema del tool para function calling del LLM.
        
        Compatible con OpenAI Function Calling y Google Gemini Function Calling.
        
        Returns:
            Dict: Schema en formato JSON Schema
        """
        # Construir propiedades de parámetros
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = param.to_schema()
            if param.required:
                required.append(param.name)
        
        schema = {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties
            }
        }
        
        if required:
            schema["parameters"]["required"] = required
        
        return schema
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', category='{self.category}')>"
