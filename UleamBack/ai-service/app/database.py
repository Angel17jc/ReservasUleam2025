"""
Database Module

Gestiona la conexión a PostgreSQL y las sesiones de SQLAlchemy.

Principios aplicados:
- Single Responsibility: Solo maneja conexión a BD
- Dependency Injection: Provee sesiones via dependency
- Resource Management: Context managers para sesiones
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import OperationalError
from typing import Generator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# ===== SQLAlchemy Setup =====

# Engine configuration
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,  # Sin pool para evitar problemas con PostgreSQL
    echo=False,  # No logging de SQL queries (cambiar a True para debug)
    future=True  # Use SQLAlchemy 2.0 style
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)

# Base class for all models
Base = declarative_base()


# ===== Database Events =====

@event.listens_for(engine, "connect")
def set_connection_pragmas(_dbapi_conn, _connection_record):
    """
    Event listener para configurar conexiones.
    Útil para setear timezone, encoding, etc.
    """
    # PostgreSQL puede usar este handler para configuraciones específicas
    # Por ejemplo: SET timezone='UTC'


# ===== Dependency Injection =====

def get_db() -> Generator[Session, None, None]:
    """
    Dependency para FastAPI que provee una sesión de BD.
    
    Usage:
        @router.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db here
            pass
    
    La sesión se cierra automáticamente al terminar el request.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database error: %s", e)
        db.rollback()
        raise
    finally:
        db.close()


# ===== Database Utilities =====

def init_db():
    """
    Inicializa la base de datos creando todas las tablas.
    
    NOTA: En producción se debe usar Alembic para migraciones.
    Esta función es útil para desarrollo y testing.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Error creating database tables: %s", e)
        raise


def check_db_connection() -> bool:
    """
    Verifica si la conexión a la base de datos funciona.
    
    Returns:
        bool: True si la conexión es exitosa, False en caso contrario
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except OperationalError as e:
        logger.error("Database connection failed: %s", e)
        return False


def close_db():
    """
    Cierra todas las conexiones a la base de datos.
    Útil para cleanup en shutdown de la aplicación.
    """
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except OperationalError as e:
        logger.error("Error closing database connections: %s", e)
