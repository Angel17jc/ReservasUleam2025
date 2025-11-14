from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..models import reserva as reserva_model, estado_reserva as estado_model, espacio as espacio_model, tipo_evento as tipo_evento_model
from typing import Optional
from datetime import time, datetime, date

def _blocking_state_ids(db: Session) -> set[int]:
    """
    Returns a set of estado_reserva IDs that deben bloquear conflictos cuando ya están aprobadas/bloqueos.
    Sólo consideramos estados aprobados (o bloqueos) para poder acumular solicitudes pendientes.
    """
    nombres_bloqueantes = ["Aprobada"]
    states = (
        db.query(estado_model.EstadoReserva.id)
        .filter(estado_model.EstadoReserva.nombre.in_(nombres_bloqueantes))
        .all()
    )
    return {row.id for row in states}

def has_conflict(db: Session, espacio_id: int, fecha, hora_inicio: time, hora_fin: time) -> bool:
    blocking_ids = _blocking_state_ids(db)
    if not blocking_ids:
        return False  # si no hay estados configurados, no bloqueamos

    q = (
        db.query(reserva_model.Reserva)
        .filter(
            reserva_model.Reserva.espacio_id == espacio_id,
            reserva_model.Reserva.fecha == fecha,
            reserva_model.Reserva.estado_id.in_(blocking_ids),
        )
    )
    existing = q.all()
    for r in existing:
        if (hora_inicio < r.hora_fin) and (hora_fin > r.hora_inicio):
            return True
    return False


def calc_availability(db: Session, espacio_id: int, fecha: date, incluir_pendientes: bool = True):
    """Calcula slots libres y ocupados entre 08:00-18:00 para un espacio/fecha."""
    jornada_ini = time(8, 0)
    jornada_fin = time(18, 0)

    estados_bloqueantes = db.query(estado_model.EstadoReserva).filter(
        estado_model.EstadoReserva.nombre.in_(
            ["Aprobada"] + (["Pendiente"] if incluir_pendientes else [])
        )
    ).all()
    blocking_ids = {e.id for e in estados_bloqueantes}

    reservas = (
        db.query(reserva_model.Reserva)
        .filter(
            reserva_model.Reserva.espacio_id == espacio_id,
            reserva_model.Reserva.fecha == fecha,
            reserva_model.Reserva.estado_id.in_(blocking_ids) if blocking_ids else True,
        )
        .order_by(reserva_model.Reserva.hora_inicio.asc())
        .all()
    )

    ocupados = []
    intervals = []
    for r in reservas:
        ocupados.append(
            {
                "id": r.id,
                "estado": getattr(r.estado, "nombre", None),
                "hora_inicio": r.hora_inicio.strftime("%H:%M"),
                "hora_fin": r.hora_fin.strftime("%H:%M"),
                "titulo": r.titulo,
                "usuario_id": r.usuario_id,
            }
        )
        intervals.append((r.hora_inicio, r.hora_fin))

    libres = []
    cursor = jornada_ini
    for ini, fin in intervals:
        if ini > cursor:
            libres.append({"hora_inicio": cursor.strftime("%H:%M"), "hora_fin": ini.strftime("%H:%M")})
        if fin > cursor:
            cursor = fin
    if cursor < jornada_fin:
        libres.append({"hora_inicio": cursor.strftime("%H:%M"), "hora_fin": jornada_fin.strftime("%H:%M")})

    espacio_obj = db.query(espacio_model.Espacio).filter(espacio_model.Espacio.id == espacio_id).first()
    nombre_espacio = espacio_obj.nombre if espacio_obj else None

    return {
        "espacio_id": espacio_id,
        "espacio_nombre": nombre_espacio,
        "fecha": fecha.isoformat(),
        "dia_semana": fecha.strftime("%A"),
        "ocupados": ocupados,
        "libres": libres,
    }


def create_reserva(db: Session, usuario_id: int, payload) -> reserva_model.Reserva:
    # ✅ NUEVO: Normalizar las horas para quitar timezone info
    hora_inicio = payload.hora_inicio
    hora_fin = payload.hora_fin
    
    # Si vienen como datetime, convertir a time
    if isinstance(hora_inicio, datetime):
        hora_inicio = hora_inicio.time()
    if isinstance(hora_fin, datetime):
        hora_fin = hora_fin.time()
    
    # Si tienen timezone info, quitarla
    if isinstance(hora_inicio, time) and hora_inicio.tzinfo is not None:
        hora_inicio = hora_inicio.replace(tzinfo=None)
    if isinstance(hora_fin, time) and hora_fin.tzinfo is not None:
        hora_fin = hora_fin.replace(tzinfo=None)
    
    # Validar ventana de tiempo
    if hora_inicio >= hora_fin:
        raise ValueError('hora_inicio must be before hora_fin')

    min_allowed = time(8, 0)
    max_allowed = time(18, 0)
    
    # ✅ Ahora la comparación funcionará
    if not (min_allowed <= hora_inicio < max_allowed and min_allowed < hora_fin <= max_allowed):
        raise ValueError('Reservations must be within 08:00 - 18:00')

    # Validación de capacidad
    espacio = db.query(espacio_model.Espacio).filter(espacio_model.Espacio.id == payload.espacio_id).first()
    if espacio is None:
        raise ValueError('Espacio not found')
    if payload.asistentes_estimada and espacio.capacidad_maxima and payload.asistentes_estimada > espacio.capacidad_maxima:
        raise ValueError('Estimated attendees exceed space capacity')

    # Verificar conflictos (a menos que sea un bloqueo)
    if not payload.es_bloqueo and has_conflict(db, payload.espacio_id, payload.fecha, hora_inicio, hora_fin):
        raise ValueError('Conflicting reservation exists')

    # Determinar estado inicial
    tipo_evento = None
    if payload.tipo_evento_id:
        tipo_evento = db.query(tipo_evento_model.TipoEvento).filter(tipo_evento_model.TipoEvento.id == payload.tipo_evento_id).first()

    # Estado inicial: siempre Pendiente (el admin decide aprobar/rechazar)
    estado = db.query(estado_model.EstadoReserva).filter(estado_model.EstadoReserva.nombre == 'Pendiente').first()

    codigo = f"R-{int(__import__('time').time())}-{__import__('random').randint(1000,9999)}"
    
    # ✅ Usar las horas normalizadas
    new_res = reserva_model.Reserva(
        codigo=codigo,
        usuario_id=usuario_id,
        espacio_id=payload.espacio_id,
        tipo_evento_id=payload.tipo_evento_id,
        estado_id=estado.id if estado else None,
        fecha=payload.fecha,
        hora_inicio=hora_inicio,  # ✅ Usar la hora normalizada
        hora_fin=hora_fin,        # ✅ Usar la hora normalizada
        titulo=payload.titulo,
        descripcion=payload.descripcion,
        es_bloqueo=payload.es_bloqueo,
        motivo_bloqueo=payload.motivo_bloqueo,
        asistentes_estimada=getattr(payload, 'asistentes_estimada', None)
    )
    db.add(new_res)
    db.commit()
    db.refresh(new_res)

    return new_res
