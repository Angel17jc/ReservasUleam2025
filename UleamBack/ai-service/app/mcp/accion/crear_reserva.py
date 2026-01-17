"""
Crear Reserva Tool (ACCIÓN)

Permite crear una nueva reserva de espacio en el sistema.
"""

from typing import List
from datetime import datetime
from ..base_tool import BaseTool, ToolParameter, ToolResult, ToolCategory, ParameterType
from ..tool_registry import register_tool
from ..tool_executor import ToolExecutor
import logging

logger = logging.getLogger(__name__)


@register_tool
class CrearReservaTool(BaseTool):
    """
    Tool para crear una nueva reserva.
    
    Requiere:
    - Usuario ID
    - Espacio ID
    - Fecha de reserva
    - Hora inicio y fin
    - Propósito de la reserva
    """
    
    def _get_category(self) -> ToolCategory:
        return ToolCategory.ACCION
    
    def _get_description(self) -> str:
        return """Crea una nueva reserva de espacio en el sistema ULEAM.

Parámetros requeridos:
- usuario_id: ID del usuario que hace la reserva
- espacio_id: ID del espacio a reservar
- fecha_reserva: Fecha en formato YYYY-MM-DD (ej: 2026-01-26)
- hora_inicio: Hora de inicio en formato HH:MM (ej: 14:00)
- hora_fin: Hora de finalización en formato HH:MM (ej: 16:00)
- proposito: Motivo o descripción de la reserva

Crea la reserva y retorna la información completa de la reserva creada, incluyendo su ID único."""
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="usuario_id",
                type=ParameterType.INTEGER,
                description="ID del usuario que realiza la reserva",
                required=True
            ),
            ToolParameter(
                name="espacio_id",
                type=ParameterType.INTEGER,
                description="ID del espacio a reservar",
                required=True
            ),
            ToolParameter(
                name="fecha_reserva",
                type=ParameterType.STRING,
                description="Fecha de la reserva en formato YYYY-MM-DD (ej: 2026-01-26)",
                required=True
            ),
            ToolParameter(
                name="hora_inicio",
                type=ParameterType.STRING,
                description="Hora de inicio en formato HH:MM (ej: 14:00)",
                required=True
            ),
            ToolParameter(
                name="hora_fin",
                type=ParameterType.STRING,
                description="Hora de finalización en formato HH:MM (ej: 16:00)",
                required=True
            ),
            ToolParameter(
                name="proposito",
                type=ParameterType.STRING,
                description="Propósito o descripción de la reserva",
                required=True
            )
        ]
    
    async def _execute(self, **kwargs) -> ToolResult:
        """
        Ejecuta la creación de la reserva.
        
        Args:
            usuario_id: ID del usuario
            espacio_id: ID del espacio
            fecha_reserva: Fecha (YYYY-MM-DD)
            hora_inicio: Hora inicio (HH:MM)
            hora_fin: Hora fin (HH:MM)
            proposito: Propósito de la reserva
        
        Returns:
            ToolResult: Información de la reserva creada
        """
        executor = ToolExecutor()
        
        try:
            # Preparar datos de la reserva
            reserva_data = {
                "usuario_id": kwargs["usuario_id"],
                "espacio_id": kwargs["espacio_id"],
                "fecha_reserva": kwargs["fecha_reserva"],
                "hora_inicio": kwargs["hora_inicio"],
                "hora_fin": kwargs["hora_fin"],
                "proposito": kwargs["proposito"],
                "estado_id": 1  # 1 = Pendiente por defecto
            }
            
            # Llamar a REST service para crear reserva
            nueva_reserva = await executor.call_rest_service(
                method="POST",
                endpoint="/api/reservas",
                json_data=reserva_data
            )
            
            # Crear mensaje de éxito
            espacio_nombre = nueva_reserva.get('espacio', {}).get('nombre', 'el espacio')
            fecha = nueva_reserva.get('fecha_reserva', 'la fecha indicada')
            hora_inicio = nueva_reserva.get('hora_inicio', '')
            hora_fin = nueva_reserva.get('hora_fin', '')
            
            summary = f"✅ Reserva creada exitosamente!\n\n"
            summary += f"📍 Espacio: {espacio_nombre}\n"
            summary += f"📅 Fecha: {fecha}\n"
            summary += f"🕐 Horario: {hora_inicio} - {hora_fin}\n"
            summary += f"📝 Propósito: {kwargs['proposito']}\n"
            summary += f"🆔 ID de reserva: {nueva_reserva.get('id', 'N/A')}\n"
            summary += f"⏳ Estado: Pendiente de confirmación"
            
            return ToolResult(
                success=True,
                data={
                    "reserva": nueva_reserva,
                    "summary": summary
                },
                metadata={
                    "action": "create_reserva",
                    "reserva_id": nueva_reserva.get('id'),
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        except Exception as e:
            logger.error(f"Error in crear_reserva: {e}")
            
            # Mensajes de error más amigables
            error_msg = str(e).lower()
            if "already exists" in error_msg or "conflict" in error_msg:
                user_error = "Ya existe una reserva para ese espacio en ese horario. Por favor elige otro horario."
            elif "not found" in error_msg:
                user_error = "El espacio o usuario especificado no existe. Verifica los IDs."
            elif "invalid" in error_msg:
                user_error = "Los datos proporcionados son inválidos. Verifica el formato de fecha y horarios."
            else:
                user_error = f"No se pudo crear la reserva: {str(e)}"
            
            return ToolResult(
                success=False,
                error=user_error
            )
        
        finally:
            await executor.close()
