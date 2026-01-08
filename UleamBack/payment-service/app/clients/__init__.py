"""
HTTP Clients for Microservices Integration

Clients para comunicación con otros servicios del sistema.
Usa httpx para requests HTTP asíncronos.
"""

from .auth_client import AuthClient
from .rest_client import RestClient
from .websocket_client import WebSocketClient

__all__ = [
    "AuthClient",
    "RestClient",
    "WebSocketClient"
]
