"""
Tool Executor

Ejecutor centralizado que maneja llamadas HTTP a servicios externos
(REST service, Auth service, Payment service).

Responsabilidades:
- Realizar llamadas HTTP con retry logic
- Manejar autenticación
- Normalizar respuestas
- Logging de llamadas

Principios aplicados:
- Single Responsibility: Solo ejecuta llamadas HTTP
- Dependency Injection: Recibe configuración
"""

import httpx
from typing import Dict, Any, Optional
import logging
from ..config import settings

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    Ejecutor de llamadas HTTP para MCP tools.
    
    Centraliza la lógica de comunicación con servicios externos.
    """
    
    def __init__(self):
        """Initialize executor with HTTP client."""
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.client = httpx.AsyncClient(timeout=self.timeout)
        
        # Service URLs
        self.rest_service_url = getattr(settings, 'REST_SERVICE_URL', 'http://localhost:8000')
        self.auth_service_url = getattr(settings, 'AUTH_SERVICE_URL', 'http://localhost:9000')
        self.payment_service_url = getattr(settings, 'PAYMENT_SERVICE_URL', 'http://localhost:8001')
    
    async def call_rest_service(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Llama al REST service (puerto 8000).
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: Endpoint path (ej: '/api/espacios')
            params: Query parameters
            json_data: JSON body
            headers: HTTP headers
        
        Returns:
            Dict: Response data
        
        Raises:
            Exception: Si la llamada falla
        """
        url = f"{self.rest_service_url}{endpoint}"
        
        logger.debug(f"Calling REST service: {method} {url}")
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers or {}
            )
            
            response.raise_for_status()
            
            # Try to parse as JSON
            try:
                data = response.json()
            except Exception:
                data = {"response": response.text}
            
            logger.info(f"REST service call successful: {method} {endpoint}")
            return data
        
        except httpx.HTTPStatusError as e:
            logger.error(f"REST service HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Error del servicio REST: {e.response.status_code}")
        
        except httpx.RequestError as e:
            logger.error(f"REST service request error: {e}")
            raise Exception(f"Error al conectar con REST service: {str(e)}")
    
    async def call_auth_service(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Llama al Auth service (puerto 9000).
        
        Args:
            method: HTTP method
            endpoint: Endpoint path (ej: '/api/v1/auth/register')
            params: Query parameters
            json_data: JSON body
            headers: HTTP headers
        
        Returns:
            Dict: Response data
        
        Raises:
            Exception: Si la llamada falla
        """
        url = f"{self.auth_service_url}{endpoint}"
        
        logger.debug(f"Calling Auth service: {method} {url}")
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers or {}
            )
            
            response.raise_for_status()
            
            try:
                data = response.json()
            except Exception:
                data = {"response": response.text}
            
            logger.info(f"Auth service call successful: {method} {endpoint}")
            return data
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Auth service HTTP error: {e.response.status_code} - {e.response.text}")
            
            # Try to get error message from response
            try:
                error_data = e.response.json()
                error_msg = error_data.get('message') or error_data.get('detail') or str(e.response.text)
            except:
                error_msg = str(e.response.text)
            
            raise Exception(f"Error del servicio de autenticación: {error_msg}")
        
        except httpx.RequestError as e:
            logger.error(f"Auth service request error: {e}")
            raise Exception(f"Error al conectar con Auth service: {str(e)}")
    
    async def call_payment_service(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Llama al Payment service (puerto 8001).
        
        Args:
            method: HTTP method
            endpoint: Endpoint path
            params: Query parameters
            json_data: JSON body
            headers: HTTP headers
        
        Returns:
            Dict: Response data
        
        Raises:
            Exception: Si la llamada falla
        """
        url = f"{self.payment_service_url}{endpoint}"
        
        logger.debug(f"Calling Payment service: {method} {url}")
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers or {}
            )
            
            response.raise_for_status()
            
            try:
                data = response.json()
            except Exception:
                data = {"response": response.text}
            
            logger.info(f"Payment service call successful: {method} {endpoint}")
            return data
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Payment service HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Error del servicio de pagos: {e.response.status_code}")
        
        except httpx.RequestError as e:
            logger.error(f"Payment service request error: {e}")
            raise Exception(f"Error al conectar con Payment service: {str(e)}")
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    def __del__(self):
        """Ensure client is closed."""
        try:
            import asyncio
            asyncio.create_task(self.close())
        except:
            pass
