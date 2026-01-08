"""
REST Service Client

Cliente HTTP para validar reservas con el rest-service.
Verifica que las reservas existan antes de procesar pagos.
"""

import httpx
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class RestClient:
    """
    Cliente para comunicarse con el rest-service.
    
    Responsabilidades:
    - Validar que una reserva existe
    - Obtener detalles de reservas
    - Verificar ownership de reservas
    """
    
    def __init__(self, base_url: str, timeout: float = 10.0):
        """
        Inicializar cliente REST.
        
        Args:
            base_url: URL base del rest-service (ej: http://localhost:8000)
            timeout: Timeout para requests HTTP en segundos
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        logger.info(f"RestClient initialized: base_url={self.base_url}")
    
    async def close(self):
        """Cerrar el cliente HTTP"""
        await self.client.aclose()
        logger.debug("RestClient closed")
    
    async def validate_reserva(
        self,
        reserva_id: int,
        usuario_id: int,
        token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Validar que una reserva existe y pertenece al usuario.
        
        Args:
            reserva_id: ID de la reserva
            usuario_id: ID del usuario que hace el pago
            token: JWT token del usuario
        
        Returns:
            Dict con datos de la reserva si existe y pertenece al usuario, None en caso contrario
            
        Example response:
            {
                "id": 123,
                "usuario_id": 456,
                "espacio_id": 789,
                "fecha_inicio": "2026-01-20T10:00:00Z",
                "fecha_fin": "2026-01-20T12:00:00Z",
                "estado": "pendiente",
                "precio_total": 50.00
            }
        """
        try:
            headers = {"Authorization": f"Bearer {token}"}
            url = f"{self.base_url}/api/v1/reservas/{reserva_id}"
            
            logger.debug(f"Validating reserva: reserva_id={reserva_id}, usuario_id={usuario_id}")
            
            response = await self.client.get(url, headers=headers)
            
            if response.status_code == 200:
                reserva_data = response.json()
                
                # Verificar ownership
                reserva_usuario_id = reserva_data.get("usuario_id")
                
                if reserva_usuario_id != usuario_id:
                    logger.warning(
                        f"Reserva ownership mismatch: reserva_id={reserva_id}, "
                        f"expected_user={usuario_id}, actual_user={reserva_usuario_id}"
                    )
                    return None
                
                logger.info(
                    f"Reserva validated successfully: reserva_id={reserva_id}, "
                    f"usuario_id={usuario_id}"
                )
                return reserva_data
            
            elif response.status_code == 404:
                logger.warning(f"Reserva not found: reserva_id={reserva_id}")
                return None
            
            elif response.status_code == 403:
                logger.warning(
                    f"Access denied to reserva: reserva_id={reserva_id}, "
                    f"usuario_id={usuario_id}"
                )
                return None
            
            else:
                logger.error(
                    f"Unexpected response from rest-service: "
                    f"status={response.status_code}, body={response.text[:200]}"
                )
                return None
        
        except httpx.TimeoutException:
            logger.error(
                f"Timeout validating reserva with rest-service (timeout={self.timeout}s)"
            )
            return None
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error validating reserva: {str(e)}")
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error validating reserva: {str(e)}", exc_info=True)
            return None
    
    async def get_reserva_by_id(self, reserva_id: int, token: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información de una reserva por ID.
        
        Args:
            reserva_id: ID de la reserva
            token: JWT token para autenticación
        
        Returns:
            Dict con información de la reserva o None si no existe
        """
        try:
            headers = {"Authorization": f"Bearer {token}"}
            url = f"{self.base_url}/api/v1/reservas/{reserva_id}"
            
            logger.debug(f"Getting reserva info: reserva_id={reserva_id}")
            
            response = await self.client.get(url, headers=headers)
            
            if response.status_code == 200:
                reserva_data = response.json()
                logger.debug(f"Reserva info retrieved: reserva_id={reserva_id}")
                return reserva_data
            
            elif response.status_code == 404:
                logger.warning(f"Reserva not found: reserva_id={reserva_id}")
                return None
            
            else:
                logger.error(
                    f"Error getting reserva info: status={response.status_code}, "
                    f"body={response.text[:200]}"
                )
                return None
        
        except Exception as e:
            logger.error(f"Error getting reserva by ID: {str(e)}", exc_info=True)
            return None
    
    async def update_reserva_status(
        self,
        reserva_id: int,
        estado: str,
        token: str
    ) -> bool:
        """
        Actualizar el estado de una reserva (llamado después de pago exitoso).
        
        Args:
            reserva_id: ID de la reserva
            estado: Nuevo estado ("confirmada", "cancelada", etc.)
            token: JWT token para autenticación
        
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            url = f"{self.base_url}/api/reservas/{reserva_id}/estado"
            payload = {"estado": estado}
            
            logger.debug(f"Updating reserva status: reserva_id={reserva_id}, estado={estado}")
            
            response = await self.client.patch(url, headers=headers, json=payload)
            
            if response.status_code in (200, 204):
                logger.info(f"Reserva status updated: reserva_id={reserva_id}, estado={estado}")
                return True
            
            else:
                logger.error(
                    f"Failed to update reserva status: status={response.status_code}, "
                    f"body={response.text[:200]}"
                )
                return False
        
        except Exception as e:
            logger.error(f"Error updating reserva status: {str(e)}", exc_info=True)
            return False
    
    async def health_check(self) -> bool:
        """
        Verificar que el rest-service esté disponible.
        
        Returns:
            True si el servicio responde, False en caso contrario
        """
        try:
            # rest-service expone endpoint raiz que retorna info
            url = f"{self.base_url}/"
            response = await self.client.get(url)
            
            is_healthy = response.status_code == 200
            
            if is_healthy:
                logger.debug("Rest-service is healthy")
            else:
                logger.warning(f"Rest-service unhealthy: status={response.status_code}")
            
            return is_healthy
        
        except Exception as e:
            logger.error(f"Rest-service health check failed: {str(e)}")
            return False


# Singleton instance (inicializado en main.py)
rest_client: Optional[RestClient] = None


def get_rest_client() -> RestClient:
    """
    Obtener instancia singleton del RestClient.
    
    Raises:
        RuntimeError: Si el cliente no ha sido inicializado
    """
    if rest_client is None:
        raise RuntimeError(
            "RestClient not initialized. Call init_rest_client() first in main.py"
        )
    return rest_client


def init_rest_client(base_url: str, timeout: float = 10.0) -> RestClient:
    """
    Inicializar el RestClient singleton.
    
    Args:
        base_url: URL del rest-service
        timeout: Timeout para requests
    
    Returns:
        Instancia del RestClient
    """
    global rest_client
    rest_client = RestClient(base_url, timeout)
    logger.info(f"RestClient singleton initialized: {base_url}")
    return rest_client
