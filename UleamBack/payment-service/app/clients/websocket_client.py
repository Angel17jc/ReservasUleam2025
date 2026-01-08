"""
WebSocket Service Client

Cliente HTTP para enviar notificaciones al websocket-service.
Permite enviar notificaciones en tiempo real a usuarios conectados.
"""

import httpx
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class WebSocketClient:
    """
    Cliente para comunicarse con el websocket-service.
    
    Responsabilidades:
    - Enviar notificaciones de pagos a usuarios conectados
    - Notificar eventos de reservas
    - Enviar mensajes broadcast
    """
    
    def __init__(self, base_url: str, timeout: float = 5.0):
        """
        Inicializar cliente WebSocket.
        
        Args:
            base_url: URL base del websocket-service (ej: http://localhost:3001)
            timeout: Timeout para requests HTTP en segundos
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        logger.info(f"WebSocketClient initialized: base_url={self.base_url}")
    
    async def close(self):
        """Cerrar el cliente HTTP"""
        await self.client.aclose()
        logger.debug("WebSocketClient closed")
    
    async def notify_payment_success(
        self,
        usuario_id: int,
        payment_data: Dict[str, Any]
    ) -> bool:
        """
        Notificar a un usuario que su pago fue exitoso.
        
        Args:
            usuario_id: ID del usuario a notificar
            payment_data: Datos del pago
        
        Returns:
            True si se envió la notificación, False en caso contrario
        """
        notification = {
            "type": "payment.success",
            "title": "¡Pago Exitoso!",
            "message": f"Tu pago de {payment_data.get('amount')} {payment_data.get('currency')} ha sido procesado correctamente.",
            "data": {
                "payment_id": payment_data.get("id"),
                "external_payment_id": payment_data.get("external_payment_id"),
                "reserva_id": payment_data.get("reserva_id"),
                "amount": payment_data.get("amount"),
                "currency": payment_data.get("currency"),
                "status": payment_data.get("status"),
                "provider": payment_data.get("provider_name")
            }
        }
        
        return await self._send_notification(usuario_id, notification)
    
    async def notify_payment_failed(
        self,
        usuario_id: int,
        payment_data: Dict[str, Any]
    ) -> bool:
        """
        Notificar a un usuario que su pago falló.
        
        Args:
            usuario_id: ID del usuario a notificar
            payment_data: Datos del pago
        
        Returns:
            True si se envió la notificación, False en caso contrario
        """
        notification = {
            "type": "payment.failed",
            "title": "Pago Fallido",
            "message": f"Tu pago no pudo ser procesado. {payment_data.get('error_message', '')}",
            "data": {
                "payment_id": payment_data.get("id"),
                "reserva_id": payment_data.get("reserva_id"),
                "amount": payment_data.get("amount"),
                "currency": payment_data.get("currency"),
                "error_message": payment_data.get("error_message")
            }
        }
        
        return await self._send_notification(usuario_id, notification)
    
    async def notify_payment_refunded(
        self,
        usuario_id: int,
        payment_data: Dict[str, Any]
    ) -> bool:
        """
        Notificar a un usuario que su pago fue reembolsado.
        
        Args:
            usuario_id: ID del usuario a notificar
            payment_data: Datos del pago
        
        Returns:
            True si se envió la notificación, False en caso contrario
        """
        notification = {
            "type": "payment.refunded",
            "title": "Reembolso Procesado",
            "message": f"Se ha procesado el reembolso de {payment_data.get('amount')} {payment_data.get('currency')}.",
            "data": {
                "payment_id": payment_data.get("id"),
                "external_payment_id": payment_data.get("external_payment_id"),
                "reserva_id": payment_data.get("reserva_id"),
                "amount": payment_data.get("amount"),
                "currency": payment_data.get("currency")
            }
        }
        
        return await self._send_notification(usuario_id, notification)
    
    async def notify_reserva_confirmed(
        self,
        usuario_id: int,
        reserva_id: int,
        payment_id: int
    ) -> bool:
        """
        Notificar a un usuario que su reserva fue confirmada.
        
        Args:
            usuario_id: ID del usuario a notificar
            reserva_id: ID de la reserva confirmada
            payment_id: ID del pago asociado
        
        Returns:
            True si se envió la notificación, False en caso contrario
        """
        notification = {
            "type": "reserva.confirmed",
            "title": "Reserva Confirmada",
            "message": f"Tu reserva #{reserva_id} ha sido confirmada. ¡Gracias por tu pago!",
            "data": {
                "reserva_id": reserva_id,
                "payment_id": payment_id
            }
        }
        
        return await self._send_notification(usuario_id, notification)
    
    async def _send_notification(
        self,
        usuario_id: int,
        notification: Dict[str, Any]
    ) -> bool:
        """
        Enviar una notificación a un usuario específico.
        
        Args:
            usuario_id: ID del usuario
            notification: Datos de la notificación
        
        Returns:
            True si se envió correctamente, False en caso contrario
        """
        try:
            # websocket-service expone POST /api/webhooks/notificacion para recibir notificaciones
            url = f"{self.base_url}/api/webhooks/notificacion"
            
            # Adaptar el formato al que espera websocket-service
            payload = {
                "usuario_id": usuario_id,
                "titulo": notification.get("title"),
                "mensaje": notification.get("message"),
                "tipo": notification.get("type"),
                "metadata": notification.get("data", {})
            }
            
            logger.debug(
                f"Sending notification to user: usuario_id={usuario_id}, "
                f"type={notification.get('type')}"
            )
            
            response = await self.client.post(url, json=payload)
            
            if response.status_code in (200, 201, 204):
                logger.info(
                    f"Notification sent successfully: usuario_id={usuario_id}, "
                    f"type={notification.get('type')}"
                )
                return True
            
            else:
                logger.warning(
                    f"Failed to send notification: status={response.status_code}, "
                    f"body={response.text[:200]}"
                )
                return False
        
        except httpx.TimeoutException:
            logger.warning(
                f"Timeout sending notification to websocket-service (timeout={self.timeout}s)"
            )
            return False
        
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error sending notification: {str(e)}")
            return False
        
        except Exception as e:
            logger.error(f"Unexpected error sending notification: {str(e)}", exc_info=True)
            return False
    
    async def broadcast_notification(
        self,
        notification: Dict[str, Any],
        user_ids: Optional[List[int]] = None
    ) -> bool:
        """
        Enviar notificación broadcast a múltiples usuarios.
        
        Args:
            notification: Datos de la notificación
            user_ids: Lista de IDs de usuarios (None = broadcast a todos)
        
        Returns:
            True si se envió correctamente, False en caso contrario
        """
        try:
            url = f"{self.base_url}/api/notifications/broadcast"
            payload = {
                "notification": notification,
                "user_ids": user_ids
            }
            
            logger.debug(f"Sending broadcast notification: type={notification.get('type')}")
            
            response = await self.client.post(url, json=payload)
            
            if response.status_code in (200, 201, 204):
                logger.info(f"Broadcast notification sent: type={notification.get('type')}")
                return True
            
            else:
                logger.warning(
                    f"Failed to send broadcast: status={response.status_code}, "
                    f"body={response.text[:200]}"
                )
                return False
        
        except Exception as e:
            logger.warning(f"Error sending broadcast notification: {str(e)}")
            return False
    
    async def health_check(self) -> bool:
        """
        Verificar que el websocket-service esté disponible.
        
        Returns:
            True si el servicio responde, False en caso contrario
        """
        try:
            url = f"{self.base_url}/health"
            response = await self.client.get(url)
            
            is_healthy = response.status_code == 200
            
            if is_healthy:
                logger.debug("WebSocket-service is healthy")
            else:
                logger.warning(f"WebSocket-service unhealthy: status={response.status_code}")
            
            return is_healthy
        
        except Exception as e:
            logger.error(f"WebSocket-service health check failed: {str(e)}")
            return False


# Singleton instance (inicializado en main.py)
websocket_client: Optional[WebSocketClient] = None


def get_websocket_client() -> WebSocketClient:
    """
    Obtener instancia singleton del WebSocketClient.
    
    Raises:
        RuntimeError: Si el cliente no ha sido inicializado
    """
    if websocket_client is None:
        raise RuntimeError(
            "WebSocketClient not initialized. Call init_websocket_client() first in main.py"
        )
    return websocket_client


def init_websocket_client(base_url: str, timeout: float = 5.0) -> WebSocketClient:
    """
    Inicializar el WebSocketClient singleton.
    
    Args:
        base_url: URL del websocket-service
        timeout: Timeout para requests
    
    Returns:
        Instancia del WebSocketClient
    """
    global websocket_client
    websocket_client = WebSocketClient(base_url, timeout)
    logger.info(f"WebSocketClient singleton initialized: {base_url}")
    return websocket_client
