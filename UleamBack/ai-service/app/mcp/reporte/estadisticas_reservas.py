"""
Estadísticas de Reservas Tool (REPORTE)

Genera reportes y estadísticas sobre el uso de espacios.
"""

from typing import List
from datetime import datetime, timedelta
from collections import Counter
from ..base_tool import BaseTool, ToolParameter, ToolResult, ToolCategory, ParameterType
from ..tool_registry import register_tool
from ..tool_executor import ToolExecutor
import logging

logger = logging.getLogger(__name__)


@register_tool
class EstadisticasReservasTool(BaseTool):
    """
    Tool para generar estadísticas de reservas.
    
    Genera reportes sobre:
    - Total de reservas en un período
    - Espacios más utilizados
    - Distribución por estado
    - Horarios pico
    """
    
    def _get_category(self) -> ToolCategory:
        return ToolCategory.REPORTE
    
    def _get_description(self) -> str:
        return """Genera estadísticas y reportes sobre el uso de espacios en ULEAM.

Parámetros opcionales:
- espacio_id: ID del espacio para estadísticas específicas
- dias: Número de días hacia atrás para el reporte (default: 30 días)
- incluir_canceladas: Si incluir reservas canceladas (default: false)

Retorna:
- Total de reservas en el período
- Espacios más utilizados
- Distribución por estado (pendientes, confirmadas, canceladas, completadas)
- Promedio de reservas por día
- Horarios más populares

Útil para análisis de ocupación y toma de decisiones."""
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="espacio_id",
                type=ParameterType.INTEGER,
                description="ID del espacio para estadísticas específicas (opcional)",
                required=False
            ),
            ToolParameter(
                name="dias",
                type=ParameterType.INTEGER,
                description="Número de días hacia atrás para el reporte",
                required=False,
                default=30
            ),
            ToolParameter(
                name="incluir_canceladas",
                type=ParameterType.BOOLEAN,
                description="Si incluir reservas canceladas en las estadísticas",
                required=False,
                default=False
            )
        ]
    
    async def _execute(self, **kwargs) -> ToolResult:
        """
        Ejecuta la generación de estadísticas.
        
        Args:
            espacio_id: ID del espacio (opcional)
            dias: Días hacia atrás (default: 30)
            incluir_canceladas: Incluir canceladas (default: False)
        
        Returns:
            ToolResult: Estadísticas y reporte generado
        """
        executor = ToolExecutor()
        
        try:
            # Obtener todas las reservas (filtrar por espacio si se especifica)
            params = {}
            if "espacio_id" in kwargs:
                params["espacio_id"] = kwargs["espacio_id"]
            
            reservas = await executor.call_rest_service(
                method="GET",
                endpoint="/api/reservas",
                params=params
            )
            
            if not isinstance(reservas, list):
                return ToolResult(
                    success=False,
                    error="No se pudieron obtener las reservas para generar estadísticas"
                )
            
            # Filtrar por período de días
            dias = kwargs.get("dias", 30)
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            reservas_filtradas = []
            for r in reservas:
                try:
                    fecha_reserva = datetime.fromisoformat(r.get('fecha_reserva', '').split('T')[0])
                    if fecha_reserva >= fecha_limite:
                        reservas_filtradas.append(r)
                except:
                    continue
            
            # Filtrar canceladas si corresponde
            incluir_canceladas = kwargs.get("incluir_canceladas", False)
            if not incluir_canceladas:
                reservas_filtradas = [r for r in reservas_filtradas if r.get('estado_id') != 3]
            
            # Calcular estadísticas
            total_reservas = len(reservas_filtradas)
            
            if total_reservas == 0:
                return ToolResult(
                    success=True,
                    data={
                        "total": 0,
                        "summary": f"No hay reservas en los últimos {dias} días."
                    }
                )
            
            # Distribución por estado
            estados_count = Counter(r.get('estado_id') for r in reservas_filtradas)
            estados_map = {
                1: "Pendiente",
                2: "Confirmada",
                3: "Cancelada",
                4: "Completada"
            }
            
            # Espacios más utilizados
            espacios_count = Counter(
                r.get('espacio', {}).get('nombre', 'Sin nombre')
                for r in reservas_filtradas
            )
            top_espacios = espacios_count.most_common(5)
            
            # Horarios más populares (agrupados por hora de inicio)
            horarios_count = Counter(
                r.get('hora_inicio', 'N/A').split(':')[0] if ':' in r.get('hora_inicio', '') else 'N/A'
                for r in reservas_filtradas
            )
            top_horarios = horarios_count.most_common(3)
            
            # Promedio de reservas por día
            promedio_dia = round(total_reservas / dias, 2)
            
            # Crear reporte legible
            summary = f"📊 REPORTE DE ESTADÍSTICAS - Últimos {dias} días\n\n"
            
            summary += f"📈 RESUMEN GENERAL:\n"
            summary += f"   • Total de reservas: {total_reservas}\n"
            summary += f"   • Promedio por día: {promedio_dia}\n\n"
            
            summary += f"📊 DISTRIBUCIÓN POR ESTADO:\n"
            for estado_id, count in estados_count.items():
                estado_nombre = estados_map.get(estado_id, 'Desconocido')
                porcentaje = round((count / total_reservas) * 100, 1)
                summary += f"   • {estado_nombre}: {count} ({porcentaje}%)\n"
            
            if top_espacios:
                summary += f"\n🏆 TOP 5 ESPACIOS MÁS UTILIZADOS:\n"
                for i, (espacio, count) in enumerate(top_espacios, 1):
                    porcentaje = round((count / total_reservas) * 100, 1)
                    summary += f"   {i}. {espacio}: {count} reservas ({porcentaje}%)\n"
            
            if top_horarios:
                summary += f"\n🕐 HORARIOS MÁS POPULARES:\n"
                for hora, count in top_horarios:
                    if hora != 'N/A':
                        porcentaje = round((count / total_reservas) * 100, 1)
                        summary += f"   • {hora}:00 hrs: {count} reservas ({porcentaje}%)\n"
            
            return ToolResult(
                success=True,
                data={
                    "total_reservas": total_reservas,
                    "promedio_por_dia": promedio_dia,
                    "distribucion_estados": dict(estados_count),
                    "top_espacios": top_espacios,
                    "top_horarios": top_horarios,
                    "periodo_dias": dias,
                    "summary": summary
                },
                metadata={
                    "fecha_inicio": fecha_limite.isoformat(),
                    "fecha_fin": datetime.now().isoformat(),
                    "incluye_canceladas": incluir_canceladas,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        except Exception as e:
            logger.error(f"Error in estadisticas_reservas: {e}")
            return ToolResult(
                success=False,
                error=f"No se pudieron generar las estadísticas: {str(e)}"
            )
        
        finally:
            await executor.close()
