"""
Health Check Routes

Endpoints simples para verificar el estado del servicio.
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict

from ..database import get_db, check_db_connection
from ..adapters.adapter_factory import AdapterFactory
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=Dict)
async def health_check():
    """
    Health check básico del servicio.
    
    Returns:
        dict: Estado del servicio
    """
    return {
        "status": "healthy",
        "service": "ai-service",
        "version": "1.0.0"
    }


@router.get("/health/detailed", response_model=Dict)
async def detailed_health_check(_db: Session = Depends(get_db)):
    """
    Health check detallado incluyendo dependencias.
    
    Returns:
        dict: Estado detallado del servicio y sus dependencias
    """
    # Check database
    db_status = "healthy" if check_db_connection() else "unhealthy"
    
    # Check LLM providers
    providers_status = {}
    for provider_name in AdapterFactory.get_available_providers():
        is_configured = AdapterFactory.is_provider_configured(provider_name)
        providers_status[provider_name] = "configured" if is_configured else "not_configured"
    
    # Default provider
    default_provider = settings.DEFAULT_LLM_PROVIDER
    default_configured = AdapterFactory.is_provider_configured(default_provider)
    
    overall_status = "healthy" if (db_status == "healthy" and default_configured) else "degraded"
    
    # Extraer solo la parte después del @ de DATABASE_URL
    db_url = str(settings.DATABASE_URL).split("@")[-1] if settings.DATABASE_URL else "not_configured"
    
    return {
        "status": overall_status,
        "service": "ai-service",
        "version": "1.0.0",
        "database": {
            "status": db_status,
            "url": db_url
        },
        "llm_providers": providers_status,
        "default_provider": default_provider,
        "config": {
            "port": settings.PORT,
            "api_prefix": settings.API_PREFIX
        }
    }
