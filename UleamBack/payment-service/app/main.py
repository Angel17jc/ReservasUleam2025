"""
FastAPI Application Entry Point - Payment Service

Implements:
- FastAPI application with OpenAPI documentation
- CORS middleware
- Global exception handling
- Health check endpoints
- Structured logging
- Startup/shutdown events

Author: Equipo ULEAM Reservas
Version: 1.0.0
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from .config import settings
from .database import check_database_connection, get_db_stats
from .routes import payments_router, webhooks_router, partners_router
from .clients.auth_client import init_auth_client
from .clients.rest_client import init_rest_client
from .clients.websocket_client import init_websocket_client
from .middleware import JWTAuthMiddleware

# ===== Logging Configuration =====
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if settings.LOG_FORMAT == "text" 
           else '{"time":"%(asctime)s", "name":"%(name)s", "level":"%(levelname)s", "message":"%(message)s"}'
)

logger = logging.getLogger(__name__)


# ===== Lifespan Events =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Startup:
        - Validate database connection
        - Log application configuration
        - Validate payment providers
    
    Shutdown:
        - Cleanup resources
        - Close connections
    """
    # Startup
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("=" * 60)
    
    # Database health check
    if check_database_connection():
        logger.info("✓ Database connection established")
    else:
        logger.error("✗ Database connection failed")
        raise RuntimeError("Cannot start service: Database connection failed")
    
    # Initialize microservice clients
    try:
        init_auth_client(str(settings.AUTH_SERVICE_URL), timeout=10.0)
        logger.info(f"✓ AuthClient initialized: {settings.AUTH_SERVICE_URL}")
        
        init_rest_client(str(settings.REST_SERVICE_URL), timeout=10.0)
        logger.info(f"✓ RestClient initialized: {settings.REST_SERVICE_URL}")
        
        init_websocket_client(str(settings.WEBSOCKET_SERVICE_URL), timeout=5.0)
        logger.info(f"✓ WebSocketClient initialized: {settings.WEBSOCKET_SERVICE_URL}")
    except Exception as e:
        logger.error(f"Failed to initialize service clients: {e}")
        raise
    
    # Validate payment providers
    try:
        providers = settings.validate_payment_providers()
        logger.info("Payment providers configured:")
        for provider, enabled in providers.items():
            status_icon = "✓" if enabled else "✗"
            logger.info(f"  {status_icon} {provider}: {'enabled' if enabled else 'disabled'}")
    except ValueError as e:
        logger.error(f"Payment provider validation failed: {e}")
        raise
    
    logger.info(f"Server starting on {settings.HOST}:{settings.PORT}")
    logger.info(f"API documentation: http://{settings.HOST}:{settings.PORT}/{settings.API_PREFIX}/docs")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Payment Service...")
    
    # Close service clients
    from .clients.auth_client import get_auth_client
    from .clients.rest_client import get_rest_client
    from .clients.websocket_client import get_websocket_client
    
    try:
        await get_auth_client().close()
        await get_rest_client().close()
        await get_websocket_client().close()
        logger.info("✓ Service clients closed")
    except Exception as e:
        logger.warning(f"Error closing service clients: {e}")
    
    logger.info("Cleanup completed")


# ===== FastAPI Application =====
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Microservicio de pagos con abstracción de pasarelas y webhooks B2B.\n\n"
        "**Características:**\n"
        "- Adapter Pattern para payment providers\n"
        "- Mock, Stripe, y MercadoPago adapters\n"
        "- Sistema de webhooks bidireccionales\n"
        "- Autenticación HMAC-SHA256\n"
        "- Registro de partners externos\n\n"
        "**Pilar 2 - Arquitectura de Microservicios**"
    ),
    version=settings.APP_VERSION,
    docs_url=f"/{settings.API_PREFIX}/docs",
    redoc_url=f"/{settings.API_PREFIX}/redoc",
    openapi_url=f"/{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan
)


# ===== CORS Middleware =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"]
)


# ===== Global Exception Handlers =====
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages"""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body,
            "message": "Request validation failed"
        }
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors"""
    logger.error(f"Database error on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Database error occurred",
            "message": "An error occurred while processing your request"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


# ===== API Routes =====
app.include_router(payments_router, prefix=f"/{settings.API_PREFIX}")
app.include_router(webhooks_router, prefix=f"/{settings.API_PREFIX}")
app.include_router(partners_router, prefix=f"/{settings.API_PREFIX}")


# ===== Root Endpoints =====
@app.get("/", tags=["Root"])
def root() -> Dict[str, Any]:
    """
    Root endpoint with service information.
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "pilar": 2,
        "status": "online",
        "documentation": f"/{settings.API_PREFIX}/docs"
    }


@app.get(f"/{settings.API_PREFIX}/health", tags=["Health"])
def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns service health status including:
    - Database connectivity
    - Connection pool statistics
    - Configuration status
    """
    db_healthy = check_database_connection()
    db_stats = get_db_stats() if db_healthy else {}
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": {
            "connected": db_healthy,
            "pool_stats": db_stats
        },
        "payment_providers": settings.validate_payment_providers()
    }


@app.get(f"/{settings.API_PREFIX}/info", tags=["Info"])
def service_info() -> Dict[str, Any]:
    """
    Service information endpoint.
    
    Returns detailed service configuration (non-sensitive).
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "configuration": {
            "api_prefix": settings.API_PREFIX,
            "cors_enabled": len(settings.CORS_ORIGINS) > 0,
            "log_level": settings.LOG_LEVEL,
            "mock_provider_enabled": settings.MOCK_PROVIDER_ENABLED,
            "webhook_timeout": settings.WEBHOOK_TIMEOUT_SECONDS,
            "webhook_max_retries": settings.WEBHOOK_MAX_RETRIES
        },
        "integrations": {
            "rest_service": str(settings.REST_SERVICE_URL),
            "websocket_service": str(settings.WEBSOCKET_SERVICE_URL),
            "auth_service": str(settings.AUTH_SERVICE_URL)
        }
    }


# ===== Request Logging Middleware =====
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all HTTP requests with timing information.
    """
    import time
    
    start_time = time.time()
    
    # Log request
    logger.info(f"→ {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log response
    logger.info(
        f"← {request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Duration: {duration:.3f}s"
    )
    
    # Add timing header
    response.headers["X-Process-Time"] = str(duration)
    
    return response


# ===== Future Router Registration =====
# Note: Routes will be added in subsequent commits
# app.include_router(payments_router, prefix=f"/{settings.API_PREFIX}")
# app.include_router(partners_router, prefix=f"/{settings.API_PREFIX}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower()
    )