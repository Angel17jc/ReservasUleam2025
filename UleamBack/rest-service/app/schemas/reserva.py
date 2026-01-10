from pydantic import BaseModel, field_validator
from datetime import date, time, datetime
from typing import Optional, Union

class ReservaCreate(BaseModel):
    espacio_id: int
    tipo_evento_id: Optional[int] = None
    fecha: date
    hora_inicio: time
    hora_fin: time
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    es_bloqueo: bool = False
    motivo_bloqueo: Optional[str] = None
    asistentes_estimada: Optional[int] = None
    
    @field_validator('hora_inicio', 'hora_fin', mode='before')
    @classmethod
    def parse_time(cls, v):
        """Convert string time to time object"""
        if isinstance(v, time):
            return v
        if isinstance(v, str):
            try:
                # Parse HH:MM format (most common)
                parts = v.split(':')
                if len(parts) >= 2:
                    hour = int(parts[0])
                    minute = int(parts[1])
                    second = int(parts[2]) if len(parts) > 2 else 0
                    return time(hour, minute, second)
            except (ValueError, IndexError):
                pass
        return v

class ReservaResponse(BaseModel):
    id: int
    codigo: str
    usuario_id: int
    espacio_id: int
    tipo_evento_id: Optional[int]
    estado_id: Optional[int]
    fecha: date
    hora_inicio: time
    hora_fin: time
    titulo: Optional[str]
    descripcion: Optional[str]
    es_bloqueo: bool

class ReservaEstadoUpdate(BaseModel):
    estado_id: int
