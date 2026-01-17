"""
MCP (Model Context Protocol) Tools Module

Este módulo implementa las herramientas (tools) que el LLM puede invocar
para ejecutar acciones en el sistema de reservas.

Estructura:
- base_tool.py: Clase abstracta base para todos los tools
- tool_registry.py: Registry pattern para registrar y descubrir tools
- tool_executor.py: Ejecutor que maneja llamadas HTTP a servicios externos
- consulta/: Tools de consulta (read-only)
- accion/: Tools de acción (write operations)
- reporte/: Tools de reporte (agregaciones y análisis)

Principios aplicados:
- Single Responsibility: Cada tool hace una cosa específica
- Open/Closed: Extensible para nuevos tools sin modificar existentes
- Dependency Inversion: Tools dependen de abstracciones, no de implementaciones
"""

from .base_tool import BaseTool, ToolParameter, ToolResult
from .tool_registry import ToolRegistry
from .tool_executor import ToolExecutor

# Import all tools to auto-register them
from .consulta.buscar_espacios import BuscarEspaciosTool
from .consulta.ver_reservas import VerReservasTool
from .accion.crear_reserva import CrearReservaTool
from .accion.registrar_usuario import RegistrarUsuarioTool
from .reporte.estadisticas_reservas import EstadisticasReservasTool

__all__ = [
    'BaseTool',
    'ToolParameter',
    'ToolResult',
    'ToolRegistry',
    'ToolExecutor',
    'BuscarEspaciosTool',
    'VerReservasTool',
    'CrearReservaTool',
    'RegistrarUsuarioTool',
    'EstadisticasReservasTool',
]
