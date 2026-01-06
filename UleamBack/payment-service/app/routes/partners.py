"""
Partner Routes

Endpoints para gestionar partners B2B.

Endpoints:
- POST /partners: Registrar nuevo partner
- GET /partners: Listar partners
- GET /partners/{id}: Obtener partner por ID
- PATCH /partners/{id}: Actualizar partner
- DELETE /partners/{id}: Eliminar partner
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..database import get_db
from ..schemas.partner import (
    PartnerCreate,
    PartnerResponse,
    PartnerWithSecret,
    PartnerUpdate,
    PartnerListResponse
)
from ..services.partner_service import PartnerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/partners", tags=["partners"])


@router.post(
    "",
    response_model=PartnerWithSecret,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo partner",
    description="Crea un nuevo partner B2B con API key y secret generados automáticamente"
)
def create_partner(
    partner_data: PartnerCreate,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo partner para recibir webhooks.
    
    **Flow**:
    1. Validar datos de entrada
    2. Generar API key y secret automáticamente
    3. Almacenar en BD
    4. Retornar partner con secret (SOLO UNA VEZ)
    
    **IMPORTANTE**:
    - El `secret_key` solo se muestra EN ESTA RESPUESTA
    - Guárdalo de forma segura
    - No se podrá recuperar después
    
    **Request Body**:
    ```json
    {
        "name": "Partner XYZ Corp",
        "email": "webhooks@partner-xyz.com",
        "webhook_url": "https://partner-xyz.com/webhooks/payments",
        "events_subscribed": ["payment.success", "payment.failed"]
    }
    ```
    
    **Response**: Partner con `api_key` y `secret_key`
    
    **Errors**:
    - 400: Datos inválidos
    - 422: Validación fallida
    - 500: Error interno
    """
    try:
        partner = PartnerService.create_partner(db=db, partner_data=partner_data)
        
        logger.info(f"Partner created via API: {partner.id}")
        
        return partner
    
    except Exception as e:
        logger.error(f"Error creating partner: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create partner: {str(e)}"
        )


@router.get(
    "",
    response_model=PartnerListResponse,
    summary="Listar partners",
    description="Lista todos los partners con filtros y paginación"
)
def list_partners(
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    db: Session = Depends(get_db)
):
    """
    Lista partners con filtros opcionales.
    
    **Query Parameters**:
    - `is_active`: Filtrar por activos (true) o inactivos (false)
    - `page`: Número de página (default: 1)
    - `page_size`: Resultados por página (default: 10, max: 100)
    
    **Response**: Lista paginada de partners
    
    **Example**:
    ```
    GET /partners?is_active=true&page=1&page_size=20
    ```
    """
    skip = (page - 1) * page_size
    
    partners, total = PartnerService.list_partners(
        db=db,
        is_active=is_active,
        skip=skip,
        limit=page_size
    )
    
    logger.info(f"Listed partners: total={total}, page={page}")
    
    return PartnerListResponse(
        total=total,
        page=page,
        page_size=page_size,
        partners=partners
    )


@router.get(
    "/{partner_id}",
    response_model=PartnerResponse,
    summary="Obtener partner por ID",
    description="Retorna los detalles de un partner específico"
)
def get_partner(
    partner_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene un partner por su ID.
    
    **Path Parameters**:
    - `partner_id`: ID del partner
    
    **Response**: Detalles del partner (SIN secret_key)
    
    **Errors**:
    - 404: Partner no encontrado
    """
    partner = PartnerService.get_partner(db=db, partner_id=partner_id)
    
    if not partner:
        logger.warning(f"Partner not found: {partner_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner {partner_id} not found"
        )
    
    return partner


@router.patch(
    "/{partner_id}",
    response_model=PartnerResponse,
    summary="Actualizar partner",
    description="Actualiza los datos de un partner existente"
)
def update_partner(
    partner_id: int,
    partner_update: PartnerUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza un partner.
    
    **Path Parameters**:
    - `partner_id`: ID del partner
    
    **Request Body** (todos los campos opcionales):
    ```json
    {
        "name": "New Name",
        "is_active": false,
        "webhook_url": "https://new-url.com/webhooks",
        "events_subscribed": ["payment.success"]
    }
    ```
    
    **Response**: Partner actualizado
    
    **Errors**:
    - 404: Partner no encontrado
    - 400: Datos inválidos
    """
    partner = PartnerService.update_partner(
        db=db,
        partner_id=partner_id,
        partner_update=partner_update
    )
    
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner {partner_id} not found"
        )
    
    logger.info(f"Partner updated: {partner_id}")
    
    return partner


@router.delete(
    "/{partner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar partner",
    description="Desactiva un partner (soft delete)"
)
def delete_partner(
    partner_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina (desactiva) un partner.
    
    **Nota**: Es un soft delete, el partner se marca como inactivo.
    
    **Path Parameters**:
    - `partner_id`: ID del partner
    
    **Response**: 204 No Content
    
    **Errors**:
    - 404: Partner no encontrado
    """
    deleted = PartnerService.delete_partner(db=db, partner_id=partner_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner {partner_id} not found"
        )
    
    logger.info(f"Partner deleted: {partner_id}")