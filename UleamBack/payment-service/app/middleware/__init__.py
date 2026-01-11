"""
Middleware de Autenticación JWT

Middleware para validar tokens JWT en requests HTTP.
Se ejecuta antes de los endpoints protegidos.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from typing import Optional

from ..clients.auth_client import get_auth_client

logger = logging.getLogger(__name__)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware que valida tokens JWT en requests.
    
    Extrae el token del header Authorization, lo valida con auth-service,
    y almacena la información del usuario en request.state para uso posterior.
    
    Endpoints públicos (no requieren autenticación):
    - GET /
    - GET /docs
    - GET /openapi.json
    - GET /api/v1/health
    - GET /api/v1/info
    - POST /api/v1/webhooks/*  (webhooks de providers externos)
    
    Todos los demás endpoints requieren JWT válido.
    """
    
    def __init__(self, app, public_paths: Optional[list] = None):
        """
        Inicializar middleware.
        
        Args:
            app: Aplicación FastAPI
            public_paths: Lista de rutas públicas (sin autenticación)
        """
        super().__init__(app)
        
        # Rutas públicas por defecto
        self.public_paths = public_paths or [
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/health",
            "/api/v1/info",
        ]
        
        # Prefijos públicos (ej: /api/v1/webhooks/*)
        self.public_prefixes = [
            "/api/v1/webhooks/providers/",
        ]
        
        logger.info(
            f"JWTAuthMiddleware initialized: "
            f"public_paths={len(self.public_paths)}, "
            f"public_prefixes={len(self.public_prefixes)}"
        )
    
    def _is_public_path(self, path: str) -> bool:
        """
        Verificar si una ruta es pública (no requiere autenticación).
        
        Args:
            path: Path del request
        
        Returns:
            True si la ruta es pública, False en caso contrario
        """
        # Verificar rutas exactas
        if path in self.public_paths:
            return True
        
        # Verificar prefijos
        for prefix in self.public_prefixes:
            if path.startswith(prefix):
                return True
        
        return False
    
    async def dispatch(self, request: Request, call_next):
        """
        Procesar request y validar JWT si es necesario.
        
        Args:
            request: Request HTTP
            call_next: Siguiente middleware/endpoint
        
        Returns:
            Response del endpoint o error de autenticación
        """
        path = request.url.path
        
        # Permitir rutas públicas sin autenticación
        if self._is_public_path(path):
            logger.debug(f"Public path accessed: {path}")
            return await call_next(request)
        
        # Extraer token del header Authorization o cookies de sesión
        auth_header = request.headers.get("Authorization")
        cookie_token = None
        query_token = None
        if not auth_header:
            # tolerar flujos donde el token viene en cookie (p.ej. front que guarda en sessionStorage/cookie)
            cookie_token = (
                request.cookies.get("uleam_token")
                or request.cookies.get("access_token")
                or request.cookies.get("token")
            )
            # y también permitir query param ?token=... para debug/front con proxies
            query_token = request.query_params.get("token") if not cookie_token else None
            if not cookie_token and not query_token:
                logger.warning(f"Missing Authorization header and cookie/query token: path={path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "detail": "Missing Authorization header",
                        "error": "authentication_required"
                    }
                )
        
        # Verificar formato "Bearer <token>"
        token = None
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
            else:
                logger.warning(f"Invalid Authorization header format: path={path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "detail": "Invalid Authorization header format. Expected 'Bearer <token>'",
                        "error": "invalid_token_format"
                    }
                )
        else:
            token = cookie_token or query_token
        
        # Validar token con auth-service
        try:
            auth_client = get_auth_client()
            user_data = await auth_client.validate_token(token)
            
            if not user_data:
                logger.warning(f"Invalid or expired token: path={path}, token_prefix={token[:12]}...")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "detail": "Invalid or expired token",
                        "error": "invalid_token"
                    }
                )
            
            # Almacenar información del usuario en request.state
            request.state.user = user_data
            request.state.token = token
            
            logger.debug(
                f"Authenticated request: path={path}, user_id={user_data.get('id')}, "
                f"email={user_data.get('email')}"
            )
            
            # Continuar con el request
            return await call_next(request)
        
        except RuntimeError as e:
            # AuthClient no inicializado
            logger.error(f"AuthClient not initialized: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "detail": "Authentication service unavailable",
                    "error": "service_unavailable"
                }
            )
        
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal error during authentication",
                    "error": "internal_error"
                }
            )


def get_current_user_from_request(request: Request) -> dict:
    """
    Obtener información del usuario actual del request.
    
    Args:
        request: Request HTTP (debe haber pasado por JWTAuthMiddleware)
    
    Returns:
        Dict con información del usuario
    
    Raises:
        HTTPException: Si no hay usuario en el request
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    
    return request.state.user


def get_current_user_id(request: Request) -> int:
    """
    Obtener el ID del usuario actual del request.
    
    Args:
        request: Request HTTP
    
    Returns:
        ID del usuario
    
    Raises:
        HTTPException: Si no hay usuario en el request
    """
    user = get_current_user_from_request(request)
    return user.get("id")


def get_current_token(request: Request) -> str:
    """
    Obtener el token JWT del request actual.
    
    Args:
        request: Request HTTP
    
    Returns:
        Token JWT
    
    Raises:
        HTTPException: Si no hay token en el request
    """
    if not hasattr(request.state, "token"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not found"
        )
    
    return request.state.token
