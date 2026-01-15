"""
Tool Execution Manager

Gestiona la ejecución de MCP Tools durante conversaciones con LLMs.

Responsabilidades:
- Ejecutar tools solicitadas por el LLM
- Validar parámetros de entrada
- Manejar errores y timeouts
- Formatear resultados para reinserción en el LLM
- Logging detallado de ejecuciones

Principios aplicados:
- Single Responsibility: Solo ejecuta tools
- Dependency Injection: Recibe ToolRegistry
- Error Handling: Manejo robusto de fallos
"""

from typing import Dict, Any, List, Optional
import logging
import json
import time
from datetime import datetime

from ..mcp.tool_registry import ToolRegistry
from ..mcp.base_tool import ToolResult

logger = logging.getLogger(__name__)


class ToolExecutionManager:
    """
    Gestiona la ejecución de MCP Tools solicitadas por LLMs.
    
    Proporciona una capa de abstracción entre el orchestrator y las tools,
    manejando validación, logging y formateo de resultados.
    """
    
    def __init__(self):
        """Initialize tool execution manager."""
        self.registry = ToolRegistry
        logger.info("ToolExecutionManager initialized")
    
    async def execute_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una tool específica con los parámetros dados.
        
        Args:
            tool_name: Nombre de la tool a ejecutar
            parameters: Parámetros de la tool
        
        Returns:
            Dict con resultado formateado para el LLM
        
        Raises:
            ValueError: Si la tool no existe o parámetros inválidos
            RuntimeError: Si falla la ejecución
        """
        start_time = time.time()
        
        try:
            # 1. Validar que la tool existe
            tool = self.registry.get(tool_name)
            if not tool:
                available_tools = self.registry.list_tool_names()
                error_msg = (
                    f"Tool '{tool_name}' not found. "
                    f"Available tools: {', '.join(available_tools)}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 2. Log inicio de ejecución
            logger.info(
                "Executing tool: name=%s, params=%s",
                tool_name,
                json.dumps(parameters, default=str)
            )
            
            # 3. Ejecutar la tool
            result: ToolResult = await tool.execute(**parameters)
            
            # 4. Calcular tiempo de ejecución
            execution_time = time.time() - start_time
            
            # 5. Log resultado
            if result.success:
                logger.info(
                    "Tool executed successfully: name=%s, time=%.2fs",
                    tool_name,
                    execution_time
                )
            else:
                logger.warning(
                    "Tool execution failed: name=%s, error=%s",
                    tool_name,
                    result.error
                )
            
            # 6. Formatear resultado para el LLM
            formatted_result = self._format_result_for_llm(
                tool_name=tool_name,
                result=result,
                execution_time=execution_time
            )
            
            return formatted_result
        
        except ValueError as e:
            # Error de validación (tool no existe, parámetros inválidos)
            logger.error("Validation error executing tool: %s", e)
            raise
        
        except Exception as e:
            # Error inesperado durante ejecución
            error_msg = f"Unexpected error executing tool '{tool_name}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
    
    async def execute_multiple_tools(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Ejecuta múltiples tool calls en secuencia.
        
        Útil cuando el LLM solicita ejecutar varias tools en una sola respuesta.
        
        Args:
            tool_calls: Lista de tool calls (cada uno con name y parameters)
        
        Returns:
            Lista de resultados formateados
        """
        results = []
        
        for i, tool_call in enumerate(tool_calls):
            try:
                tool_name = tool_call.get("name") or tool_call.get("function", {}).get("name")
                parameters = tool_call.get("parameters") or tool_call.get("arguments", {})
                
                # Si arguments es string (JSON), parsearlo
                if isinstance(parameters, str):
                    parameters = json.loads(parameters)
                
                logger.debug(
                    "Executing tool %d/%d: %s",
                    i + 1,
                    len(tool_calls),
                    tool_name
                )
                
                result = await self.execute_tool_call(tool_name, parameters)
                results.append(result)
            
            except Exception as e:
                # Continuar con las demás tools aunque una falle
                error_result = {
                    "tool_name": tool_call.get("name", "unknown"),
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                results.append(error_result)
                logger.error("Failed to execute tool in batch: %s", e)
        
        logger.info(
            "Executed %d tools: %d successful, %d failed",
            len(results),
            sum(1 for r in results if r.get("success")),
            sum(1 for r in results if not r.get("success"))
        )
        
        return results
    
    def _format_result_for_llm(
        self,
        tool_name: str,
        result: ToolResult,
        execution_time: float
    ) -> Dict[str, Any]:
        """
        Formatea el resultado de una tool para que el LLM lo pueda interpretar.
        
        Args:
            tool_name: Nombre de la tool ejecutada
            result: Resultado de la ejecución
            execution_time: Tiempo de ejecución en segundos
        
        Returns:
            Dict con formato compatible con LLMs
        """
        formatted = {
            "tool_name": tool_name,
            "success": result.success,
            "timestamp": datetime.now().isoformat(),
            "execution_time": round(execution_time, 2)
        }
        
        if result.success:
            # Resultado exitoso
            formatted["data"] = result.data
            
            # Incluir summary si existe (más fácil de interpretar para el LLM)
            if result.data and "summary" in result.data:
                formatted["summary"] = result.data["summary"]
        else:
            # Error
            formatted["error"] = result.error
            formatted["data"] = None
        
        return formatted
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Obtiene lista de tools disponibles con sus schemas.
        
        Returns:
            Lista de schemas de tools para el LLM
        """
        schemas = self.registry.get_all_schemas()
        
        logger.debug("Retrieved %d tool schemas", len(schemas))
        
        return schemas
    
    def get_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Obtiene tools filtradas por categoría.
        
        Args:
            category: Categoría de tools (CONSULTA, ACCION, REPORTE)
        
        Returns:
            Lista de schemas de tools de esa categoría
        """
        from ..mcp.base_tool import ToolCategory
        
        try:
            category_enum = ToolCategory[category.upper()]
            tools = self.registry.get_by_category(category_enum)
            schemas = [tool.get_schema() for tool in tools]
            
            logger.debug("Retrieved %d tools for category %s", len(schemas), category)
            
            return schemas
        except KeyError:
            logger.error("Invalid category: %s", category)
            return []
    
    def validate_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Optional[str]:
        """
        Valida una tool call antes de ejecutarla.
        
        Args:
            tool_name: Nombre de la tool
            parameters: Parámetros a validar
        
        Returns:
            None si es válido, mensaje de error si no
        """
        # Verificar que la tool existe
        tool = self.registry.get(tool_name)
        if not tool:
            return f"Tool '{tool_name}' does not exist"
        
        # Validar parámetros (la tool lo hace internamente)
        validation_error = tool.validate_parameters(parameters)
        
        return validation_error
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información detallada de una tool.
        
        Args:
            tool_name: Nombre de la tool
        
        Returns:
            Dict con información de la tool o None si no existe
        """
        tool = self.registry.get(tool_name)
        if not tool:
            return None
        
        return {
            "name": tool.name,
            "description": tool.description,
            "category": tool.category.value,
            "parameters": [
                {
                    "name": param.name,
                    "type": param.type.value,
                    "description": param.description,
                    "required": param.required
                }
                for param in tool.get_parameters()
            ],
            "schema": tool.get_schema()
        }
