"""
Buscar Espacios Tool (CONSULTA)

Permite buscar espacios disponibles en el sistema de reservas ULEAM.
"""

from typing import List
from datetime import datetime
from ..base_tool import BaseTool, ToolParameter, ToolResult, ToolCategory, ParameterType
from ..tool_registry import register_tool
from ..tool_executor import ToolExecutor
import logging

logger = logging.getLogger(__name__)


@register_tool
class BuscarEspaciosTool(BaseTool):
    """
    Tool para buscar espacios disponibles.
    
    Permite filtrar por:
    - Capacidad mínima
    - Tipo de espacio
    - Disponibilidad
    - Nombre del espacio
    """
    
    def _get_category(self) -> ToolCategory:
        return ToolCategory.CONSULTA
    
    def _get_description(self) -> str:
        return """Busca espacios disponibles en el sistema de reservas ULEAM. 
        
Puedes filtrar por:
- capacidad_min: Capacidad mínima requerida (número de personas)
- tipo_espacio: Tipo de espacio (aula, laboratorio, auditorio, sala_reuniones, etc.)
- disponible: Si debe estar disponible (true/false)
- nombre: Buscar por nombre del espacio

Retorna una lista de espacios con su información completa: ID, nombre, capacidad, tipo, estado."""
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="capacidad_min",
                type=ParameterType.INTEGER,
                description="Capacidad mínima de personas que debe tener el espacio",
                required=False
            ),
            ToolParameter(
                name="tipo_espacio",
                type=ParameterType.STRING,
                description="Tipo de espacio a buscar",
                required=False,
                enum=["aula", "laboratorio", "auditorio", "sala_reuniones", "espacio_deportivo"]
            ),
            ToolParameter(
                name="disponible",
                type=ParameterType.BOOLEAN,
                description="Si debe estar disponible para reservas",
                required=False,
                default=True
            ),
            ToolParameter(
                name="nombre",
                type=ParameterType.STRING,
                description="Buscar por nombre del espacio (búsqueda parcial)",
                required=False
            )
        ]
    
    async def _execute(self, **kwargs) -> ToolResult:
        """
        Ejecuta la búsqueda de espacios.
        
        Args:
            capacidad_min: Capacidad mínima (opcional)
            tipo_espacio: Tipo de espacio (opcional)
            disponible: Filtrar por disponibilidad (opcional)
            nombre: Nombre del espacio (opcional)
        
        Returns:
            ToolResult: Lista de espacios encontrados
        """
        executor = ToolExecutor()
        
        try:
            # Construir query parameters
            params = {}
            
            if "capacidad_min" in kwargs:
                params["capacidad_min"] = kwargs["capacidad_min"]
            
            if "tipo_espacio" in kwargs:
                params["tipo_espacio"] = kwargs["tipo_espacio"]
            
            if "disponible" in kwargs:
                params["disponible"] = kwargs["disponible"]
            
            if "nombre" in kwargs:
                params["nombre"] = kwargs["nombre"]
            
            # Llamar a REST service
            espacios = await executor.call_rest_service(
                method="GET",
                endpoint="/api/espacios",
                params=params
            )
            
            # Formatear respuesta
            if isinstance(espacios, list):
                total = len(espacios)
                
                # Crear resumen legible
                if total == 0:
                    summary = "No se encontraron espacios con los criterios especificados."
                else:
                    summary = f"Se encontraron {total} espacio(s):\n"
                    for espacio in espacios[:5]:  # Mostrar primeros 5
                        summary += f"- {espacio.get('nombre', 'Sin nombre')} "
                        summary += f"(Capacidad: {espacio.get('capacidad', 'N/A')}, "
                        summary += f"Tipo: {espacio.get('tipo_espacio', {}).get('nombre', 'N/A')})\n"
                    
                    if total > 5:
                        summary += f"... y {total - 5} más."
                
                return ToolResult(
                    success=True,
                    data={
                        "total": total,
                        "espacios": espacios,
                        "summary": summary
                    },
                    metadata={
                        "filters_applied": params,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    error="Respuesta inesperada del servicio de espacios"
                )
        
        except Exception as e:
            logger.error(f"Error in buscar_espacios: {e}")
            return ToolResult(
                success=False,
                error=f"No se pudieron buscar espacios: {str(e)}"
            )
        
        finally:
            await executor.close()
