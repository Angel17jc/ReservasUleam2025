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

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


# TODO: Implementar en Commit 4 - Middleware de autenticación JWT
# Por ahora, usamos usuario_id hardcodeado para pruebas
MOCK_USER_ID = 1  # Simula usuario autenticado


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo pago",
    description="Crea un nuevo pago utilizando el provider especificado"
)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo pago.
    
    **Flow**:
    1. Validar datos de entrada
    2. Crear pago en el provider externo (Stripe, Mock, etc.)
    3. Almacenar registro en BD
    4. Retornar Payment creado
    
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
    - 400: Datos inválidos
    - 422: Validación fallida (Pydantic)
    - 500: Error del provider o interno
    """
    try:
        # TODO Commit 4: Obtener usuario_id del JWT
        usuario_id = MOCK_USER_ID
        
        payment = PaymentService.create_payment(
            db=db,
            usuario_id=usuario_id,
            payment_data=payment_data
        )
        
        logger.info(f"Payment created via API: {payment.id}")
        
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
    description="Retorna los detalles de un pago específico"
)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene un pago por su ID.
    
    **Path Parameters**:
    - `payment_id`: ID del pago
    
    **Response**: Detalles completos del pago
    
    **Errors**:
    - 404: Pago no encontrado
    
    **Security**: 
    TODO Commit 4 - Validar que el usuario solo acceda a sus propios pagos
    """
    # TODO Commit 4: Obtener usuario_id del JWT y validar ownership
    usuario_id = MOCK_USER_ID
    
    payment = PaymentService.get_payment(
        db=db,
        payment_id=payment_id,
        usuario_id=None  # Por ahora sin validación
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
    description="Lista pagos con filtros y paginación"
)
def list_payments(
    reserva_id: Optional[int] = Query(None, description="Filtrar por ID de reserva"),
    status: Optional[str] = Query(None, description="Filtrar por estado", pattern="^(pending|completed|failed|refunded|cancelled)$"),
    provider: Optional[str] = Query(None, description="Filtrar por provider", pattern="^(mock|stripe|mercadopago)$"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    db: Session = Depends(get_db)
):
    """
    Lista pagos con filtros opcionales y paginación.
    
    **Query Parameters**:
    - `reserva_id`: Filtrar por reserva
    - `status`: Filtrar por estado (pending, completed, failed, etc.)
    - `provider`: Filtrar por provider (mock, stripe, mercadopago)
    - `page`: Número de página (default: 1)
    - `page_size`: Resultados por página (default: 10, max: 100)
    
    **Response**: Lista paginada de pagos con metadata
    
    **Example**:
    ```
    GET /payments?status=completed&page=1&page_size=20
    ```
    """
    # TODO Commit 4: Filtrar por usuario_id del JWT
    usuario_id = None  # Por ahora lista todos
    
    skip = (page - 1) * page_size
    
    payments, total = PaymentService.list_payments(
        db=db,
        usuario_id=usuario_id,
        reserva_id=reserva_id,
        status=status,
        provider=provider,
        skip=skip,
        limit=page_size
    )
    
    logger.info(f"Listed payments: total={total}, page={page}")
    
    return PaymentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        payments=payments
    )


@router.get(
    "/stats/summary",
    summary="Estadísticas de pagos",
    description="Retorna estadísticas agregadas de pagos"
)
def get_payment_stats(
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas de pagos.
    
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
    
    TODO Commit 4: Filtrar por usuario_id del JWT
    """
    # TODO Commit 4: usuario_id = get_current_user_id()
    usuario_id = None  # Por ahora stats globales
    
    stats = PaymentService.get_payment_statistics(db=db, usuario_id=usuario_id)
    
    logger.info("Payment statistics retrieved")
    
    return stats
