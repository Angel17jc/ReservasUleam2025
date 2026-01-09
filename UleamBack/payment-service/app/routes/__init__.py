"""
REST API Routes

Define los endpoints HTTP del Payment Service.
"""

from .payments import router as payments_router
from .webhooks import router as webhooks_router
from .partners import router as partners_router
from .partners_webhook import router as partners_webhook_router

__all__ = [
    "payments_router",
    "webhooks_router",
    "partners_router",
    "partners_webhook_router"
]