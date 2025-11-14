from sqlalchemy.orm import Session
from ..models.notificacion import Notificacion
import httpx
import logging
import time
from ..config import settings
from typing import Dict, Any

logger = logging.getLogger("notification_service")


def emit_webhook(event: str, data: Dict[str, Any], max_retries: int = 3, timeout: float = 2.0):
    """Emitir webhook con reintentos y logging.

    - `event`: nombre lógico del evento
    - `data`: payload JSON
    - `max_retries`: intentos en caso de error (incluye el intento inicial)
    - `timeout`: timeout por petición en segundos
    """
    base = (settings.WEBSOCKET_SERVICE_URL or "").rstrip('/')
    endpoint_map = {
        'reserva_creada': '/api/webhooks/reserva-creada',
        'reserva_actualizada': '/api/webhooks/reserva-actualizada',
        'reserva_cancelada': '/api/webhooks/reserva-cancelada',
        'notificacion': '/api/webhooks/notificacion',
        'stats_update': '/api/webhooks/stats-update',
        'disponibilidad_actualizada': '/api/webhooks/disponibilidad-actualizada',
        'recordatorio': '/api/webhooks/recordatorio-evento',
    }
    path = endpoint_map.get(event, '/api/webhooks/notificacion')
    url = f"{base}{path}"

    if not base:
        logger.debug("WEBSOCKET_SERVICE_URL not configured; skipping webhook emit")
        return

    attempt = 0
    backoff = 0.5
    while attempt < max_retries:
        try:
            attempt += 1
            resp = httpx.post(url, json=data, timeout=timeout)
            if resp.status_code >= 200 and resp.status_code < 300:
                logger.debug(f"Webhook emitted to {url} (event={event}) status={resp.status_code}")
                return
            else:
                logger.warning(f"Webhook to {url} returned status {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.warning(f"Attempt {attempt} failed to emit webhook to {url}: {e}")

        # backoff before retrying
        time.sleep(backoff)
        backoff *= 2

    logger.error(f"Failed to emit webhook to {url} after {max_retries} attempts")


def schedule_emit_webhook(background_tasks, event: str, data: Dict[str, Any]):
    """Schedule emit_webhook to run in FastAPI BackgroundTasks."""
    if background_tasks is not None:
        background_tasks.add_task(emit_webhook, event, data)
    else:
        # fallback to synchronous call
        emit_webhook(event, data)


def create_notification(db: Session, payload: Dict[str, Any]) -> Notificacion:
    n = Notificacion(
        usuario_id=payload.get('usuario_id'),
        titulo=payload.get('titulo'),
        mensaje=payload.get('mensaje'),
        leida=payload.get('leida', False),
        reserva_id=payload.get('reserva_id'),
        espacio_id=payload.get('espacio_id'),
        metadata_info=payload.get('metadata', {}),
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    return n
