"""
REST API Routes

Define los endpoints HTTP del Payment Service.
"""

from .payments import router as payments_router

__all__ = ["payments_router"]
