"""
AI Service - FastAPI Application

Servicio de chat con IA multimodal (Pilar 3 - 20%)
Incluye integración con Gemini y Groq.

Author: Sistema de Reservas ULEAM
Version: 1.0.0
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.database import engine, Base
from app.routes import health, chat
# Import models to register them with SQLAlchemy
from app.models import Conversation, Message, ToolExecution  # noqa: F401

# ================================
# Logging Configuration
# ================================

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ai_service.log')
    ]
)

logger = logging.getLogger(__name__)


# ================================
# Lifespan Events
# ================================

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación.
    
    Startup:
    - Verificar conexión a BD
    - Crear tablas si no existen
    - Verificar configuración de LLM providers
    
    Shutdown:
    - Cerrar conexiones
    """
    # STARTUP
    logger.info("=" * 60)
    logger.info("AI Service Starting...")
    logger.info("=" * 60)
    
    try:
        # Verificar conexión a BD
        logger.info("Testing database connection...")
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Database connection successful")
        
        # Crear tablas si no existen
        logger.info("Creating database tables if not exist...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables ready")
        
        # Log de configuración
        logger.info("Environment: %s", settings.ENVIRONMENT)
        db_url_safe = str(settings.DATABASE_URL).split('@')[1] if '@' in str(settings.DATABASE_URL) else "not_configured"
        logger.info("Database: %s", db_url_safe)
        logger.info("Default LLM Provider: %s", settings.DEFAULT_LLM_PROVIDER)
        
        # Verificar providers configurados
        from app.adapters.adapter_factory import AdapterFactory
        available = AdapterFactory.get_available_providers()
        logger.info("Available LLM Providers: %s", ', '.join(available))
        
        for provider in available:
            is_configured = AdapterFactory.is_provider_configured(provider)
            status_icon = "✓" if is_configured else "✗"
            status_text = 'configured' if is_configured else 'not configured'
            logger.info("  %s %s: %s", status_icon, provider, status_text)
        
        logger.info("=" * 60)
        logger.info("AI Service Ready on port %s", settings.PORT)
        logger.info("=" * 60)
        
    except (OperationalError, RuntimeError) as e:
        logger.error("❌ Startup failed: %s", e, exc_info=True)
        raise
    
    yield  # App está corriendo
    
    # SHUTDOWN
    logger.info("AI Service shutting down...")
    engine.dispose()
    logger.info("✓ Database connections closed")


# ================================
# FastAPI Application
# ================================

app = FastAPI(
    title="AI Service - Sistema de Reservas ULEAM",
    description=(
        "Servicio de chat con IA multimodal (Texto + Imagen). "
        "Integra Google Gemini y Groq para proporcionar asistencia "
        "en la gestión de reservas de espacios."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
)


# ================================
# CORS Middleware
# ================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# ================================
# Request Logging Middleware
# ================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware para loggear todas las requests y calcular tiempo de respuesta.
    """
    start_time = time.time()
    
    # Log de request
    logger.info("→ %s %s", request.method, request.url.path)
    
    # Procesar request
    try:
        response = await call_next(request)
    except (ValueError, RuntimeError) as e:
        logger.error("Request failed: %s", e, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    # Calcular tiempo de respuesta
    process_time = (time.time() - start_time) * 1000  # en ms
    
    # Log de response
    logger.info(
        "← %s %s status=%d time=%.2fms",
        request.method,
        request.url.path,
        response.status_code,
        process_time
    )
    
    # Agregar header de tiempo
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    
    return response


# ================================
# Exception Handlers
# ================================

@app.exception_handler(404)
async def not_found_handler(request: Request, _exc):
    """Handler para 404 Not Found"""
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Endpoint not found",
            "path": str(request.url.path)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(_request: Request, exc):
    """Handler para 500 Internal Server Error"""
    logger.error("Internal error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.ENVIRONMENT == "development" else None
        }
    )


# ================================
# Routes Registration
# ================================

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint - Info del servicio.
    """
    return {
        "service": "AI Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Chat con IA multimodal para Sistema de Reservas ULEAM",
        "endpoints": {
            "health": "/api/v1/health",
            "chat": "/api/v1/chat/message",
            "docs": "/api/v1/docs"
        }
    }


# Incluir routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")


# ================================
# Entry Point
# ================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level=str(settings.LOG_LEVEL).lower()
    )
