"""
Payment Routes

Endpoints REST para gestionar pagos.

Endpoints:
- POST /payments: Crear nuevo pago
- GET /payments/{id}: Obtener pago por ID
- GET /payments: Listar pagos con filtros
- GET /payments/stats: Estadísticas de pagos
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentListResponse
)
from ..services.payment_service import PaymentService
from ..models.payment import Payment
from ..dependencies import get_current_user_id, get_current_token, get_current_user

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo pago",
    description="Crea un nuevo pago utilizando el provider especificado (requiere autenticación JWT)"
)
async def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id),
    token: str = Depends(get_current_token)
):
    """
    Crea un nuevo pago (requiere autenticación JWT).
    
    **Flow**:
    1. Autenticar usuario (JWT)
    2. Validar que la reserva existe y pertenece al usuario
    3. Crear pago en el provider externo (Stripe, Mock, etc.)
    4. Almacenar registro en BD
    5. Actualizar estado de reserva (si pago exitoso)
    6. Enviar notificación en tiempo real al usuario
    7. Retornar Payment creado
    
    **Headers**:
    - Authorization: Bearer <token> (requerido)
    
    **Request Body**:
    ```json
    {
        "reserva_id": 123,
        "amount": 50.00,
        "currency": "USD",
        "provider": "mock",
        "metadata": {
            "descripcion": "Reserva de Sala A"
        }
    }
    ```
    
    **Response**: Payment creado con ID y external_payment_id
    
    **Errors**:
    - 400: Reserva no encontrada o no pertenece al usuario
    - 401: Token inválido o expirado
    - 422: Validación fallida (Pydantic)
    - 500: Error del provider o interno
    """
    try:
        payment = await PaymentService.create_payment(
            db=db,
            usuario_id=usuario_id,
            payment_data=payment_data,
            token=token
        )
        
        logger.info(f"Payment created via API: {payment.id}, user={usuario_id}")
        
        return payment
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error creating payment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment: {str(e)}"
        )


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Obtener pago por ID",
    description="Retorna los detalles de un pago específico (requiere autenticación JWT)"
)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id)
):
    """
    Obtiene un pago por su ID (requiere autenticación JWT).
    
    El usuario solo puede acceder a sus propios pagos.
    
    **Headers**:
    - Authorization: Bearer <token> (requerido)
    
    **Path Parameters**:
    - `payment_id`: ID del pago
    
    **Response**: Detalles completos del pago
    
    **Errors**:
    - 401: Token inválido o expirado
    - 403: El pago no pertenece al usuario
    - 404: Pago no encontrado
    """
    payment = PaymentService.get_payment(
        db=db,
        payment_id=payment_id,
        usuario_id=usuario_id  # Validar ownership
    )
    
    if not payment:
        logger.warning(f"Payment not found: {payment_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found"
        )
    
    return payment


@router.get(
    "",
    response_model=PaymentListResponse,
    summary="Listar pagos",
    description="Lista pagos del usuario autenticado con filtros y paginación"
)
def list_payments(
    reserva_id: Optional[int] = Query(None, description="Filtrar por ID de reserva"),
    provider: Optional[str] = Query(None, description="Filtrar por provider"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filtrar por status"),
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(10, ge=1, le=100, description="Elementos por página"),
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id)
):
    """
    Lista los pagos del usuario autenticado con filtros y paginación.
    
    **Headers**:
    - Authorization: Bearer <token> (requerido)
    
    **Query Parameters**:
    - `reserva_id`: Filtrar por reserva específica
    - `provider`: Filtrar por provider (mock, stripe, etc.)
    - `status`: Filtrar por estado (pending, completed, failed, refunded)
    - `page`: Página actual (default: 1)
    - `per_page`: Elementos por página (default: 10, max: 100)
    
    **Response**: Lista paginada de pagos del usuario
    
    **Errors**:
    - 401: Token inválido o expirado
    """
    payments, total = PaymentService.list_payments(
        db=db,
        usuario_id=usuario_id,  # Filtrar por usuario autenticado
        reserva_id=reserva_id,
        status=status_filter,
        provider=provider,
        skip=(page - 1) * per_page,
        limit=per_page
    )
    
    logger.info(f"Listed payments: total={total}, page={page}, user={usuario_id}")
    
    return PaymentListResponse(
        total=total,
        page=page,
        page_size=per_page,
        payments=payments
    )


@router.get(
    "/stats/summary",
    summary="Estadísticas de pagos",
    description="Retorna estadísticas agregadas de pagos del usuario autenticado"
)
def get_payment_stats(
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_current_user_id)
):
    """
    Obtiene estadísticas de pagos del usuario autenticado.
    
    **Headers**:
    - Authorization: Bearer <token> (requerido)
    
    **Response**:
    ```json
    {
        "total_payments": 42,
        "completed_payments": 35,
        "pending_payments": 5,
        "failed_payments": 2,
        "total_amount_completed": 1250.00,
        "providers": {
            "mock": {"total": 30, "completed": 25, ...},
            "stripe": {"total": 12, "completed": 10, ...}
        }
    }
    ```
    
    **Errors**:
    - 401: Token inválido o expirado
    """
    stats = PaymentService.get_payment_statistics(db=db, usuario_id=usuario_id)
    
    logger.info(f"Payment statistics retrieved for user={usuario_id}")
    
    return stats
