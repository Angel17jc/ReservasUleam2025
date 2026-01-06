"""
Partner Service

Orquesta la lógica de negocio de partners y webhook delivery.

Responsabilidades:
- CRUD de partners
- Webhook delivery a partners externos
- Retry logic para webhooks fallidos
- Estadísticas de delivery

Principios SOLID:
- Single Responsibility: Solo maneja lógica de partners
- Dependency Injection: Recibe Session como parámetro
- Open/Closed: Extensible sin modificar código existente
"""

import logging
import httpx
import asyncio
import time
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime

from ..models.partner import Partner
from ..schemas.partner import PartnerCreate, PartnerUpdate, WebhookDeliveryResult
from ..schemas.webhook import NormalizedWebhookEvent
from .hmac_service import HmacService

logger = logging.getLogger(__name__)


class PartnerService:
    """
    Servicio stateless para gestión de partners y webhook delivery.
    
    Todos los métodos son estáticos y requieren una sesión de BD activa.
    """
    
    @staticmethod
    def create_partner(
        db: Session,
        partner_data: PartnerCreate
    ) -> Partner:
        """
        Crea un nuevo partner con API key y secret generados.
        
        Args:
            db: Sesión de BD
            partner_data: Datos del partner
        
        Returns:
            Partner: Partner creado con api_key y secret_key
        
        Business Rules:
            - API key y secret se generan automáticamente
            - Partner inicia activo por defecto
            - Webhook URL debe ser válida
        """
        try:
            # Generar credenciales
            api_key = Partner.generate_api_key()
            secret_key = Partner.generate_secret_key()
            
            # Crear partner (usando nombres de campos del modelo Commit 1)
            partner = Partner(
                nombre=partner_data.name,
                email=partner_data.email,
                webhook_url=partner_data.webhook_url,
                api_key=api_key,
                secret_key=secret_key,
                shared_secret=secret_key,  # Por compatibilidad con Commit 1
                is_active=True,
                eventos_suscritos=partner_data.events_subscribed,
                descripcion=partner_data.metadata.get("description") if partner_data.metadata else None
            )
            
            db.add(partner)
            db.commit()
            db.refresh(partner)
            
            logger.info(
                f"Partner created: id={partner.id}, nombre='{partner.nombre}', "
                f"api_key={partner.api_key[:8]}..."
            )
            
            return partner
        
        except Exception as e:
            logger.error(f"Error creating partner: {e}", exc_info=True)
            db.rollback()
            raise
    
    @staticmethod
    def get_partner(
        db: Session,
        partner_id: int
    ) -> Optional[Partner]:
        """
        Obtiene un partner por ID.
        
        Args:
            db: Sesión de BD
            partner_id: ID del partner
        
        Returns:
            Partner o None si no existe
        """
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        
        if partner:
            logger.debug(f"Partner retrieved: id={partner_id}")
        else:
            logger.warning(f"Partner not found: id={partner_id}")
        
        return partner
    
    @staticmethod
    def get_partner_by_api_key(
        db: Session,
        api_key: str
    ) -> Optional[Partner]:
        """
        Obtiene un partner por su API key.
        
        Args:
            db: Sesión de BD
            api_key: API key del partner
        
        Returns:
            Partner o None si no existe
        """
        return db.query(Partner).filter(Partner.api_key == api_key).first()
    
    @staticmethod
    def list_partners(
        db: Session,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Partner], int]:
        """
        Lista partners con filtros y paginación.
        
        Args:
            db: Sesión de BD
            is_active: Filtrar por estado activo/inactivo
            skip: Offset para paginación
            limit: Cantidad de resultados
        
        Returns:
            tuple: (lista_de_partners, total_count)
        """
        query = db.query(Partner)
        
        if is_active is not None:
            query = query.filter(Partner.is_active == is_active)
        
        total = query.count()
        partners = query.offset(skip).limit(limit).all()
        
        logger.debug(f"Listed partners: total={total}, returned={len(partners)}")
        
        return partners, total
    
    @staticmethod
    def update_partner(
        db: Session,
        partner_id: int,
        partner_update: PartnerUpdate
    ) -> Optional[Partner]:
        """
        Actualiza un partner.
        
        Args:
            db: Sesión de BD
            partner_id: ID del partner
            partner_update: Datos a actualizar
        
        Returns:
            Partner actualizado o None si no existe
        """
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        
        if not partner:
            logger.warning(f"Cannot update: partner not found (id={partner_id})")
            return None
        
        # Actualizar campos (mapeo inglés -> español para compatibilidad con modelo Commit 1)
        update_data = partner_update.model_dump(exclude_unset=True)
        
        # Mapeo de nombres de campos schema (inglés) -> modelo (español)
        field_mapping = {
            "name": "nombre",
            "events_subscribed": "eventos_suscritos",
        }
        
        for field, value in update_data.items():
            # Usar nombre mapeado si existe, sino usar el original
            model_field = field_mapping.get(field, field)
            
            # Manejar metadata especialmente (se guarda en descripcion)
            if field == "metadata" and value:
                partner.descripcion = value.get("description", partner.descripcion)
            else:
                setattr(partner, model_field, value)
        
        db.commit()
        db.refresh(partner)
        
        logger.info(f"Partner updated: id={partner_id}, fields={list(update_data.keys())}")
        
        return partner
    
    @staticmethod
    def delete_partner(
        db: Session,
        partner_id: int
    ) -> bool:
        """
        Elimina un partner (soft delete: marca como inactivo).
        
        Args:
            db: Sesión de BD
            partner_id: ID del partner
        
        Returns:
            bool: True si se eliminó, False si no existe
        """
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        
        if not partner:
            return False
        
        partner.is_active = False
        db.commit()
        
        logger.info(f"Partner deactivated: id={partner_id}")
        
        return True
    
    @staticmethod
    async def deliver_webhook_to_partner(
        partner: Partner,
        event: NormalizedWebhookEvent,
        timeout: int = 10,
        max_retries: int = 3
    ) -> WebhookDeliveryResult:
        """
        Entrega un webhook a un partner con retry logic.
        
        Args:
            partner: Partner destino
            event: Evento normalizado a enviar
            timeout: Timeout en segundos
            max_retries: Máximo número de reintentos
        
        Returns:
            WebhookDeliveryResult: Resultado de la entrega
        
        Security:
            - Firma el payload con HMAC-SHA256
            - Incluye timestamp para prevenir replay attacks
            - Usa HTTPS (validado en producción)
        
        Retry Logic:
            - Reintenta hasta max_retries veces
            - Exponential backoff: 1s, 2s, 4s...
            - Solo reintenta en errores de red o 5xx
        """
        start_time = time.time()
        
        try:
            # Preparar payload (mode='json' serializa datetime correctamente)
            payload = event.model_dump(mode='json', exclude={"raw_event"})
            
            # Generar headers con firma HMAC
            headers = HmacService.generate_webhook_headers(
                payload=payload,
                secret=partner.secret_key,
                additional_headers={
                    "X-Partner-ID": str(partner.id),
                    "X-Event-Type": event.event_type
                }
            )
            
            # Intentar delivery con retries
            last_error = None
            status_code = None
            
            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        response = await client.post(
                            partner.webhook_url,
                            json=payload,
                            headers=headers
                        )
                        
                        status_code = response.status_code
                        
                        # Success: 2xx status codes
                        if 200 <= status_code < 300:
                            response_time_ms = (time.time() - start_time) * 1000
                            
                            logger.info(
                                f"Webhook delivered successfully: "
                                f"partner={partner.nombre}, "
                                f"event={event.event_type}, "
                                f"status={status_code}, "
                                f"time={response_time_ms:.1f}ms"
                            )
                            
                            return WebhookDeliveryResult(
                                partner_id=partner.id,
                                partner_name=partner.nombre,
                                success=True,
                                status_code=status_code,
                                error_message=None,
                                response_time_ms=response_time_ms
                            )
                        
                        # Client error 4xx: no retry
                        elif 400 <= status_code < 500:
                            last_error = f"Client error: {status_code}"
                            break
                        
                        # Server error 5xx: retry
                        else:
                            last_error = f"Server error: {status_code}"
                            if attempt < max_retries - 1:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                continue
                
                except httpx.TimeoutException:
                    last_error = f"Timeout after {timeout}s"
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                
                except httpx.RequestError as e:
                    last_error = f"Request error: {str(e)}"
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
            
            # Failed after all retries
            response_time_ms = (time.time() - start_time) * 1000
            
            logger.error(
                f"Webhook delivery failed: "
                f"partner={partner.nombre}, "
                f"event={event.event_type}, "
                f"error={last_error}, "
                f"attempts={max_retries}"
            )
            
            return WebhookDeliveryResult(
                partner_id=partner.id,
                partner_name=partner.nombre,
                success=False,
                status_code=status_code,
                error_message=last_error,
                response_time_ms=response_time_ms
            )
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            logger.error(
                f"Unexpected error delivering webhook: "
                f"partner={partner.nombre}, error={str(e)}",
                exc_info=True
            )
            
            return WebhookDeliveryResult(
                partner_id=partner.id,
                partner_name=partner.nombre,
                success=False,
                status_code=None,
                error_message=f"Unexpected error: {str(e)}",
                response_time_ms=response_time_ms
            )
    
    @staticmethod
    async def notify_partners_of_payment_event(
        db: Session,
        event: NormalizedWebhookEvent
    ) -> List[WebhookDeliveryResult]:
        """
        Notifica a todos los partners activos de un evento de pago.
        
        Args:
            db: Sesión de BD
            event: Evento normalizado
        
        Returns:
            List[WebhookDeliveryResult]: Resultados de cada delivery
        
        Business Logic:
            - Solo notifica a partners activos
            - Solo notifica si el partner está suscrito al evento
            - Actualiza estadísticas de éxito/fallo
            - Delivery en paralelo (asyncio.gather)
        """
        import asyncio
        
        # Obtener partners activos suscritos al evento
        partners = db.query(Partner).filter(
            Partner.is_active == True
        ).all()
        
        # Filtrar por suscripción
        subscribed_partners = [
            p for p in partners if p.is_subscribed_to(event.event_type)
        ]
        
        if not subscribed_partners:
            logger.info(f"No partners subscribed to event: {event.event_type}")
            return []
        
        logger.info(
            f"Notifying {len(subscribed_partners)} partners of event: "
            f"{event.event_type}"
        )
        
        # Deliver webhooks en paralelo
        tasks = [
            PartnerService.deliver_webhook_to_partner(partner, event)
            for partner in subscribed_partners
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Actualizar estadísticas
        for partner, result in zip(subscribed_partners, results):
            if isinstance(result, WebhookDeliveryResult):
                partner.webhooks_sent += 1
                partner.last_webhook_at = datetime.utcnow()
                
                if result.success:
                    partner.webhooks_succeeded += 1
                else:
                    partner.webhooks_failed += 1
        
        db.commit()
        
        # Loggear resumen
        successful = sum(1 for r in results if isinstance(r, WebhookDeliveryResult) and r.success)
        failed = len(results) - successful
        
        logger.info(
            f"Partner notification complete: "
            f"successful={successful}, failed={failed}"
        )
        
        return [r for r in results if isinstance(r, WebhookDeliveryResult)]