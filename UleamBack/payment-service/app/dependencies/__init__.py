"""
Authentication Dependencies

FastAPI dependencies para obtener el usuario actual de los requests.
Usa la información almacenada por el JWTAuthMiddleware.
"""

from fastapi import Request, Depends, HTTPException, status
from typing import Dict, Any

from ..middleware import (
    get_current_user_from_request,
    get_current_user_id as _get_user_id,
    get_current_token as _get_token
)


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Dependency para obtener el usuario actual.
    
    Args:
        request: Request HTTP (con usuario en state)
    
    Returns:
        Dict con información del usuario
    
    Raises:
        HTTPException: Si no hay usuario autenticado
    
    Usage:
        @app.get("/protected")
        async def protected_endpoint(user: dict = Depends(get_current_user)):
            return {"user_id": user["id"]}
    """
    return get_current_user_from_request(request)


async def get_current_user_id(request: Request) -> int:
    """
    Dependency para obtener solo el ID del usuario actual.
    
    Args:
        request: Request HTTP
    
    Returns:
        ID del usuario
    
    Raises:
        HTTPException: Si no hay usuario autenticado
    
    Usage:
        @app.get("/my-payments")
        async def my_payments(user_id: int = Depends(get_current_user_id)):
            return {"user_id": user_id}
    """
    return _get_user_id(request)


async def get_current_token(request: Request) -> str:
    """
    Dependency para obtener el token JWT actual.
    
    Args:
        request: Request HTTP
    
    Returns:
        Token JWT
    
    Raises:
        HTTPException: Si no hay token
    
    Usage:
        @app.get("/forward-request")
        async def forward(token: str = Depends(get_current_token)):
            # Usar token para hacer requests a otros servicios
            pass
    """
    return _get_token(request)


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency para requerir rol de administrador.
    
    Args:
        user: Usuario actual (inyectado por get_current_user)
    
    Returns:
        Dict con información del usuario (si es admin)
    
    Raises:
        HTTPException: Si el usuario no es administrador
    
    Usage:
        @app.delete("/admin/payments/{id}")
        async def delete_payment(
            id: int,
            admin: dict = Depends(require_admin)
        ):
            # Solo admins pueden ejecutar esto
            pass
    """
    user_role = user.get("rol", "").lower()
    
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for this operation"
        )
    
    return user


# Alias para compatibilidad
CurrentUser = get_current_user
CurrentUserId = get_current_user_id
CurrentToken = get_current_token
RequireAdmin = require_admin
