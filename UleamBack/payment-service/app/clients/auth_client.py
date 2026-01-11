"""
Auth Service Client

Cliente HTTP para validar tokens JWT con el auth-service.
Maneja autenticación y obtención de información de usuarios.
"""

import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AuthClient:
    """
    Cliente para comunicarse con el auth-service.
    
    Responsabilidades:
    - Validar tokens JWT
    - Obtener información del usuario actual
    - Verificar permisos y roles
    """
    
    def __init__(self, base_url: str, timeout: float = 10.0):
        """
        Inicializar cliente de autenticación (auth-service /api/v1/auth/validate).
        
        Args:
            base_url: URL base del auth-service (ej: http://localhost:9000)
            timeout: Timeout para requests HTTP en segundos
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        logger.info(f"AuthClient initialized: base_url={self.base_url}")
    
    async def close(self):
        """Cerrar el cliente HTTP"""
        await self.client.aclose()
        logger.debug("AuthClient closed")
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validar un token JWT contra auth-service (/api/v1/auth/validate).
        Compatible con tokens emitidos por auth-service y rest-service (mismo JWT_SECRET).
        """
        try:
            url = f"{self.base_url}/api/v1/auth/validate"
            response = await self.client.post(url, json={"token": token})

            if response.status_code != 200:
                logger.warning(
                    f"Auth validation non-200: status={response.status_code}, body={response.text[:200]}, token_prefix={token[:12]}..."
                )
                return None

            payload = response.json()
            if not payload.get("valid"):
                logger.warning(
                    f"Auth validation failed: error={payload.get('error')}, token_prefix={token[:12]}..."
                )
                return None

            user = payload.get("user") or {}
            if not user:
                logger.warning(
                    f"Auth validation missing user payload: body={response.text[:200]}, token_prefix={token[:12]}..."
                )
                return None

            logger.info(
                f"Token validated successfully: user_id={user.get('id')}, email={user.get('email')}"
            )
            return user

        except httpx.TimeoutException:
            logger.error(f"Timeout validating token with auth-service (timeout={self.timeout}s)")
            return None

        except httpx.HTTPError as e:
            logger.error(f"HTTP error validating token: {str(e)}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error validating token: {str(e)}", exc_info=True)
            return None
    
    async def health_check(self) -> bool:
        """
        Verificar que el auth-service esté disponible.
        
        Returns:
            True si el servicio responde, False en caso contrario
        """
        try:
            # auth-service expone endpoint raiz que retorna info
            url = f"{self.base_url}/"
            response = await self.client.get(url)
            
            is_healthy = response.status_code == 200
            
            if is_healthy:
                logger.debug("Auth-service is healthy")
            else:
                logger.warning(f"Auth-service unhealthy: status={response.status_code}")
            
            return is_healthy
        
        except Exception as e:
            logger.error(f"Auth-service health check failed: {str(e)}")
            return False


# Singleton instance (inicializado en main.py)
auth_client: Optional[AuthClient] = None


def get_auth_client() -> AuthClient:
    """
    Obtener instancia singleton del AuthClient.
    
    Raises:
        RuntimeError: Si el cliente no ha sido inicializado
    """
    if auth_client is None:
        raise RuntimeError(
            "AuthClient not initialized. Call init_auth_client() first in main.py"
        )
    return auth_client


def init_auth_client(base_url: str, timeout: float = 10.0) -> AuthClient:
    """
    Inicializar el AuthClient singleton.
    
    Args:
        base_url: URL del auth-service
        timeout: Timeout para requests
    
    Returns:
        Instancia del AuthClient
    """
    global auth_client
    auth_client = AuthClient(base_url, timeout)
    logger.info(f"AuthClient singleton initialized: {base_url}")
    return auth_client
