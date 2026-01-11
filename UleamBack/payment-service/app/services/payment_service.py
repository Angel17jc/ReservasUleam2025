"""
Payment Service

Orquesta la lógica de negocio de pagos.
Coordina entre adapters, base de datos y servicios externos.

Responsabilidades:
- Crear pagos usando el adapter apropiado
- Actualizar estados de pago
- Consultar historial de pagos
- Validar reglas de negocio
- Logging y auditoría

Principios SOLID aplicados:
- Single Responsibility: Solo maneja lógica de negocio de pagos
- Dependency Injection: Recibe Session como parámetro
- Open/Closed: Extensible sin modificar código existente
"""

import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
from decimal import Decimal

from ..models.payment import Payment, PaymentStatus
from ..models.webhook_event import WebhookEvent
from ..schemas.payment import PaymentCreate, PaymentStatusUpdate
from ..adapters.adapter_factory import AdapterFactory

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Servicio que orquesta la lógica de negocio de pagos.
    
    Este servicio es stateless y todas las operaciones requieren
    una sesión de BD activa (Dependency Injection).
    
    Usage:
        service = PaymentService()
        payment = service.create_payment(db, usuario_id=5, payment_data=data)
    """
    
    @staticmethod
    async def create_payment(
        db: Session,
        usuario_id: int,
        payment_data: PaymentCreate,
        token: str
    ) -> Payment:
        """
        Crea un nuevo pago utilizando el provider especificado.
        
        Flujo:
        1. Validar datos de entrada (Pydantic ya lo hace)
        2. Validar que la reserva existe y pertenece al usuario (rest-service)
        3. Obtener adapter del provider
        4. Crear pago en el provider externo
        5. Almacenar registro en BD local
        6. Enviar notificación al usuario (websocket-service)
        7. Retornar Payment creado
        
        Args:
            db: Sesión de BD
            usuario_id: ID del usuario que crea el pago
            payment_data: Datos del pago (validados por Pydantic)
            token: JWT token del usuario para validaciones
        
        Returns:
            Payment: Registro del pago creado
        
        Raises:
            ValueError: Si el provider no está disponible o la reserva no existe
            Exception: Si falla la creación en el provider
        
        Business Rules:
        - Solo usuarios autenticados pueden crear pagos
        - La reserva debe existir y pertenecer al usuario
        - El monto debe ser > 0 (validado por schema)
        - El provider debe estar configurado
        """
        try:
            # 1. Validar que la reserva existe y pertenece al usuario
            from ..clients.rest_client import get_rest_client
            from ..clients.websocket_client import get_websocket_client
            
            logger.info(
                f"Creating payment: usuario_id={usuario_id}, "
                f"reserva_id={payment_data.reserva_id}, "
                "provider=stripe"
            )
            
            rest_client = get_rest_client()
            reserva = await rest_client.validate_reserva(
                reserva_id=payment_data.reserva_id,
                usuario_id=usuario_id,
                token=token
            )
            
            if not reserva:
                logger.warning(
                    f"Reserva validation failed: reserva_id={payment_data.reserva_id}, "
                    f"usuario_id={usuario_id}"
                )
                raise ValueError(
                    f"Reserva {payment_data.reserva_id} no encontrada o no pertenece al usuario"
                )

            estado_reserva = (reserva.get("estado_nombre") or reserva.get("estado") or "").lower()
            if estado_reserva != "aprobada":
                raise ValueError("La reserva debe estar aprobada antes de pagar")

            # 1.b: evitar dobles pagos
            existing_payment = (
                db.query(Payment)
                .filter(Payment.reserva_id == payment_data.reserva_id)
                .order_by(desc(Payment.creado_en))
                .first()
            )

            if existing_payment and existing_payment.status == PaymentStatus.COMPLETED:
                raise ValueError(
                    f"Reserva ya pagada (payment={existing_payment.external_payment_id})"
                )

            # Reutilizar intent pendiente si sigue vigente (<15h)
            deadline = datetime.utcnow() + timedelta(hours=15)
            if existing_payment and existing_payment.status == PaymentStatus.PENDING:
                try:
                    expires_at = existing_payment.metadata_json.get("payment_deadline")
                    if expires_at:
                        expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                        if datetime.utcnow() <= expires_dt:
                            logger.info(
                                "Reutilizando PaymentIntent pendiente existente "
                                f"(payment_id={existing_payment.external_payment_id})"
                            )
                            return existing_payment
                except Exception:
                    logger.debug("No se pudo parsear payment_deadline existente; se generará uno nuevo")

            # 2. Obtener adapter del provider (fijado a stripe)
            provider = "stripe"
            adapter = AdapterFactory.get_adapter(provider)

            # 3. Preparar metadata
            description = payment_data.description or payment_data.metadata.get("descripcion") if payment_data.metadata else None
            metadata = payment_data.metadata or {}
            metadata.update({
                "descripcion": description or "Pago de reserva ULEAM",
                "reserva_id": payment_data.reserva_id,
                "usuario_id": usuario_id,
                "reserva_codigo": reserva.get("codigo"),
                "espacio_id": reserva.get("espacio_id") or reserva.get("espacio", {}).get("id"),
                "created_by_service": "payment-service",
                "payment_deadline": deadline.isoformat() + "Z",
                "created_at": datetime.utcnow().isoformat() + "Z"
            })
            
            # 4. Crear pago en el provider externo (monto fijo 20 USD)
            provider_response = adapter.create_payment(
                amount=float(Decimal("20.00")),
                currency="USD",
                metadata=metadata
            )
            
            # 4. Mapear status del provider al enum
            # MockAdapter retorna "completed" inmediatamente
            # Otros providers pueden retornar "pending"
            provider_status = provider_response.get("status", "pending")
            try:
                payment_status = PaymentStatus(provider_status)
            except ValueError:
                # Si el status del provider no es válido, usar PENDING por defecto
                logger.warning(f"Invalid status from provider: {provider_status}, using PENDING")
                payment_status = PaymentStatus.PENDING
            
            # 5. Almacenar en BD local
            payment = Payment(
                external_payment_id=provider_response["payment_id"],
                reserva_id=payment_data.reserva_id,
                usuario_id=usuario_id,
                provider_name=provider,
                amount=Decimal("20.00"),
                currency="USD",
                status=payment_status,  # Usa el status del provider
                metadata_json={
                    **metadata,
                    "client_secret": provider_response.get("client_secret"),
                    "provider_status": provider_status,
                }
            )
            
            db.add(payment)
            db.commit()
            db.refresh(payment)
            
            logger.info(
                f"Payment created successfully: id={payment.id}, "
                f"external_id={payment.external_payment_id}, "
                f"status={payment_status.value}"
            )
            
            # 6. Enviar notificación al usuario (no bloqueante)
            try:
                websocket_client = get_websocket_client()
                
                payment_dict = {
                    "id": payment.id,
                    "external_payment_id": payment.external_payment_id,
                    "reserva_id": payment.reserva_id,
                    "amount": float(payment.amount),
                    "currency": payment.currency,
                    "status": payment.status.value,
                    "provider_name": payment.provider_name
                }
                
                if payment.is_completed:
                    await websocket_client.notify_payment_success(usuario_id, payment_dict)
                    
                    # Actualizar estado de la reserva a "Pagada" (vía usuario JWT)
                    await rest_client.update_reserva_status(
                        reserva_id=payment_data.reserva_id,
                        estado="pagada",
                        estado_nombre="Pagada",
                        token=token
                    )
                    
                    # Notificar que la reserva fue confirmada/pagada
                    await websocket_client.notify_reserva_confirmed(
                        usuario_id=usuario_id,
                        reserva_id=payment_data.reserva_id,
                        payment_id=payment.id
                    )
                    
                    logger.info(f"Reserva pagada y notificada: reserva_id={payment_data.reserva_id}")
                
                elif payment.status == PaymentStatus.FAILED:
                    await websocket_client.notify_payment_failed(usuario_id, payment_dict)
                
            except Exception as e:
                # No fallar la creación del pago si falla la notificación
                logger.warning(f"Failed to send notification: {str(e)}")
            
            return payment
        
        except ValueError as e:
            # Error de validación o provider no disponible
            logger.error(f"Validation error creating payment: {str(e)}")
            db.rollback()
            raise
        
        except Exception as e:
            # Error inesperado
            logger.error(f"Error creating payment: {str(e)}", exc_info=True)
            db.rollback()
            raise Exception(f"Failed to create payment: {str(e)}")
    
    @staticmethod
    def get_payment(
        db: Session,
        payment_id: int,
        usuario_id: Optional[int] = None
    ) -> Optional[Payment]:
        """
        Obtiene un pago por ID.
        
        Args:
            db: Sesión de BD
            payment_id: ID del pago
            usuario_id: Si se proporciona, valida que el pago pertenezca al usuario
        
        Returns:
            Payment o None si no existe
        
        Security:
        - Si se proporciona usuario_id, solo retorna pagos del usuario
        - Previene acceso no autorizado a pagos de otros usuarios
        """
        query = db.query(Payment).filter(Payment.id == payment_id)
        
        if usuario_id is not None:
            query = query.filter(Payment.usuario_id == usuario_id)
        
        payment = query.first()
        
        if payment:
            logger.debug(f"Payment retrieved: id={payment_id}")
        else:
            logger.warning(
                f"Payment not found: id={payment_id}, "
                f"usuario_id={usuario_id}"
            )
        
        return payment
    
    @staticmethod
    def get_payment_by_external_id(
        db: Session,
        external_payment_id: str
    ) -> Optional[Payment]:
        """
        Busca un pago por su ID externo (del provider).
        
        Útil para procesar webhooks cuando solo tenemos el ID del provider.
        
        Args:
            db: Sesión de BD
            external_payment_id: ID del pago en el provider
        
        Returns:
            Payment o None si no existe
        """
        payment = db.query(Payment).filter(
            Payment.external_payment_id == external_payment_id
        ).first()
        
        if payment:
            logger.debug(f"Payment found by external_id: {external_payment_id}")
        else:
            logger.warning(f"Payment not found by external_id: {external_payment_id}")
        
        return payment
    
    @staticmethod
    def list_payments(
        db: Session,
        usuario_id: Optional[int] = None,
        reserva_id: Optional[int] = None,
        status: Optional[str] = None,
        provider: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Payment], int]:
        """
        Lista pagos con filtros y paginación.
        
        Args:
            db: Sesión de BD
            usuario_id: Filtrar por usuario
            reserva_id: Filtrar por reserva
            status: Filtrar por estado
            provider: Filtrar por provider
            skip: Offset para paginación
            limit: Cantidad de resultados (max 100)
        
        Returns:
            tuple: (lista_de_pagos, total_count)
        
        Example:
            payments, total = PaymentService.list_payments(
                db, usuario_id=5, status="completed", skip=0, limit=10
            )
        """
        # Limitar el límite máximo
        limit = min(limit, 100)
        
        # Construir query base
        query = db.query(Payment)
        
        # Aplicar filtros
        filters = []
        
        if usuario_id is not None:
            filters.append(Payment.usuario_id == usuario_id)
        
        if reserva_id is not None:
            filters.append(Payment.reserva_id == reserva_id)
        
        if status is not None:
            try:
                status_enum = PaymentStatus(status)
                filters.append(Payment.status == status_enum)
            except ValueError:
                logger.warning(f"Invalid status filter: {status}")
        
        if provider is not None:
            filters.append(Payment.provider_name == provider.lower())
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Contar total
        total = query.count()
        
        # Aplicar ordenamiento y paginación
        payments = query.order_by(desc(Payment.creado_en)).offset(skip).limit(limit).all()
        
        logger.debug(
            f"Listed payments: filters={len(filters)}, "
            f"total={total}, returned={len(payments)}"
        )
        
        return payments, total
    
    @staticmethod
    def update_payment_status(
        db: Session,
        external_payment_id: str,
        status_update: PaymentStatusUpdate
    ) -> Optional[Payment]:
        """
        Actualiza el estado de un pago.
        
        Usado principalmente por webhooks para actualizar el estado
        después de que el payment provider procesa el pago.
        
        Args:
            db: Sesión de BD
            external_payment_id: ID del pago en el provider
            status_update: Nuevo estado y mensaje de error (opcional)
        
        Returns:
            Payment actualizado o None si no existe
        
        Business Rules:
        - Solo se pueden actualizar estados válidos
        - El cambio de estado se registra con timestamp
        - Si hay error, se almacena el mensaje
        """
        payment = db.query(Payment).filter(
            Payment.external_payment_id == external_payment_id
        ).first()
        
        if not payment:
            logger.warning(
                f"Cannot update payment status: payment not found "
                f"(external_id={external_payment_id})"
            )
            return None
        
        # Guardar estado anterior para logging
        old_status = payment.status
        
        # Actualizar estado
        try:
            payment.status = PaymentStatus(status_update.status)
            
            if status_update.error_message:
                payment.error_message = status_update.error_message

            # Marcar metadata de pago exitoso
            if payment.status == PaymentStatus.COMPLETED:
                meta = payment.metadata_json or {}
                meta["paid_at"] = datetime.utcnow().isoformat() + "Z"
                payment.metadata_json = meta
            
            db.commit()
            db.refresh(payment)
            
            logger.info(
                f"Payment status updated: id={payment.id}, "
                f"external_id={external_payment_id}, "
                f"{old_status} -> {payment.status}"
            )
            
            return payment
        
        except ValueError as e:
            logger.error(f"Invalid status value: {status_update.status}")
            db.rollback()
            raise ValueError(f"Invalid status: {status_update.status}")
    
    @staticmethod
    def get_payment_statistics(
        db: Session,
        usuario_id: Optional[int] = None
    ) -> dict:
        """
        Obtiene estadísticas de pagos.
        
        Args:
            db: Sesión de BD
            usuario_id: Si se proporciona, estadísticas del usuario
        
        Returns:
            dict con estadísticas:
            {
                "total_payments": int,
                "completed_payments": int,
                "pending_payments": int,
                "failed_payments": int,
                "total_amount_completed": Decimal,
                "providers": dict
            }
        """
        query = db.query(Payment)
        
        if usuario_id is not None:
            query = query.filter(Payment.usuario_id == usuario_id)
        
        all_payments = query.all()
        
        # Calcular estadísticas
        stats = {
            "total_payments": len(all_payments),
            "completed_payments": sum(
                1 for p in all_payments if p.status == PaymentStatus.COMPLETED
            ),
            "pending_payments": sum(
                1 for p in all_payments if p.status == PaymentStatus.PENDING
            ),
            "failed_payments": sum(
                1 for p in all_payments if p.status == PaymentStatus.FAILED
            ),
            "refunded_payments": sum(
                1 for p in all_payments if p.status == PaymentStatus.REFUNDED
            ),
            "total_amount_completed": sum(
                p.amount for p in all_payments if p.status == PaymentStatus.COMPLETED
            ),
            "providers": {}
        }
        
        # Estadísticas por provider
        for payment in all_payments:
            provider = payment.provider_name
            if provider not in stats["providers"]:
                stats["providers"][provider] = {
                    "total": 0,
                    "completed": 0,
                    "pending": 0,
                    "failed": 0
                }
            
            stats["providers"][provider]["total"] += 1
            
            if payment.status == PaymentStatus.COMPLETED:
                stats["providers"][provider]["completed"] += 1
            elif payment.status == PaymentStatus.PENDING:
                stats["providers"][provider]["pending"] += 1
            elif payment.status == PaymentStatus.FAILED:
                stats["providers"][provider]["failed"] += 1
        
        logger.debug(f"Payment statistics calculated: {stats}")
        
        return stats
    
    @staticmethod
    def record_webhook_event(
        db: Session,
        event_type: str,
        source: str,
        payload: dict,
        payment_id: Optional[str] = None
    ) -> WebhookEvent:
        """
        Registra un evento de webhook en la BD.
        
        Args:
            db: Sesión de BD
            event_type: Tipo de evento (payment.success, etc.)
            source: Fuente del webhook (stripe, mercadopago, etc.)
            payload: Payload completo del webhook
            payment_id: ID del pago relacionado (opcional)
        
        Returns:
            WebhookEvent creado
        """
        webhook_event = WebhookEvent(
            event_type=event_type,
            source=source,
            payload_json=payload,
            processed=False
        )
        
        db.add(webhook_event)
        db.commit()
        db.refresh(webhook_event)
        
        logger.info(
            f"Webhook event recorded: id={webhook_event.id}, "
            f"type={event_type}, source={source}"
        )
        
        return webhook_event
