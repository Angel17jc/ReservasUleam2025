"""
Ver Reservas Tool (CONSULTA)

Permite consultar reservas existentes en el sistema.
"""
import logging
from typing import List
from datetime import datetime
from ..base_tool import BaseTool, ToolParameter, ToolResult, ToolCategory, ParameterType
from ..tool_registry import register_tool
from ..tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


@register_tool
class VerReservasTool(BaseTool):
    """
    Tool para consultar reservas.
    
    Permite filtrar por:
    - Usuario ID
    - Espacio ID
    - Estado de la reserva
    - Fecha
    """
    
    def _get_category(self) -> ToolCategory:
        return ToolCategory.CONSULTA
    
    def _get_description(self) -> str:
        return """Consulta reservas existentes en el sistema de reservas ULEAM.

Puedes filtrar por:
- usuario_id: ID del usuario que hizo la reserva
- espacio_id: ID del espacio reservado
- estado_id: Estado de la reserva (1=pendiente, 2=confirmada, 3=cancelada, 4=completada)

Retorna una lista de reservas con información completa: usuario, espacio, fecha, horario, estado, propósito."""
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="usuario_id",
                type=ParameterType.INTEGER,
                description="ID del usuario para filtrar sus reservas",
                required=False
            ),
            ToolParameter(
                name="espacio_id",
                type=ParameterType.INTEGER,
                description="ID del espacio para ver sus reservas",
                required=False
            ),
            ToolParameter(
                name="estado_id",
                type=ParameterType.INTEGER,
                description="Estado de la reserva: 1=pendiente, 2=confirmada, 3=cancelada, 4=completada",
                required=False,
                enum=[1, 2, 3, 4]
            )
        ]
    
    async def _execute(self, **kwargs) -> ToolResult:
        """
        Ejecuta la consulta de reservas.
        
        Args:
            usuario_id: ID del usuario (opcional)
            espacio_id: ID del espacio (opcional)
            estado_id: Estado de reserva (opcional)
        
        Returns:
            ToolResult: Lista de reservas encontradas
        """
        executor = ToolExecutor()
        
        try:
            # Construir query parameters
            params = {}
            
            if "usuario_id" in kwargs:
                params["usuario_id"] = kwargs["usuario_id"]
            
            if "espacio_id" in kwargs:
                params["espacio_id"] = kwargs["espacio_id"]
            
            if "estado_id" in kwargs:
                params["estado_id"] = kwargs["estado_id"]
            
            # Llamar a REST service
            reservas = await executor.call_rest_service(
                method="GET",
                endpoint="/api/reservas",
                params=params
            )
            
            # Formatear respuesta
            if isinstance(reservas, list):
                total = len(reservas)
                
                # Mapeo de estados
                estados_map = {
                    1: "Pendiente",
                    2: "Confirmada",
                    3: "Cancelada",
                    4: "Completada"
                }
                
                # Crear resumen legible
                if total == 0:
                    summary = "No se encontraron reservas con los criterios especificados."
                else:
                    summary = f"Se encontraron {total} reserva(s):\n"
                    for reserva in reservas[:5]:  # Mostrar primeras 5
                        espacio_nombre = reserva.get('espacio', {}).get('nombre', 'Sin espacio')
                        fecha = reserva.get('fecha_reserva', 'Sin fecha')
                        hora_inicio = reserva.get('hora_inicio', 'N/A')
                        hora_fin = reserva.get('hora_fin', 'N/A')
                        estado_id = reserva.get('estado_id', 1)
                        estado = estados_map.get(estado_id, 'Desconocido')
                        
                        summary += f"- {espacio_nombre} el {fecha} "
                        summary += f"de {hora_inicio} a {hora_fin} "
                        summary += f"(Estado: {estado})\n"
                    
                    if total > 5:
                        summary += f"... y {total - 5} más."
                
                return ToolResult(
                    success=True,
                    data={
                        "total": total,
                        "reservas": reservas,
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
                    error="Respuesta inesperada del servicio de reservas"
                )
        
        except Exception as e:
            logger.error(f"Error in ver_reservas: {e}")
            return ToolResult(
                success=False,
                error=f"No se pudieron consultar las reservas: {str(e)}"
            )
        
        finally:
            await executor.close()
