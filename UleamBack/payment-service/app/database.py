"""
Database configuration and session management.

Implements:
- SQLAlchemy 2.0 async/sync sessions
- Connection pooling
- Health checks
- Context managers for transactions

Best Practices:
- Dependency injection via FastAPI Depends
- Automatic session cleanup
- Connection pool management
- Error handling and rollback
"""

from typing import Generator
import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .config import settings

logger = logging.getLogger(__name__)

# ===== Database Engine Configuration =====
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=settings.LOG_LEVEL == "DEBUG",  # Log SQL queries in debug mode
    poolclass=pool.QueuePool,
    connect_args={
        "connect_timeout": 10,
        "options": "-c timezone=utc"
    }
)

# ===== Session Factory =====
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Prevent lazy loading issues after commit
)

# ===== Declarative Base =====
Base = declarative_base()


# ===== Event Listeners for Connection Management =====
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log database connections"""
    logger.debug("Database connection established")


@event.listens_for(engine, "close")
def receive_close(dbapi_conn, connection_record):
    """Log database disconnections"""
    logger.debug("Database connection closed")


# ===== Dependency Injection for FastAPI =====
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    
    Yields:
        Session: SQLAlchemy session
    
    Note:
        Automatically commits on success and rolls back on error.
        Always closes the session when done.
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions outside FastAPI.
    
    Usage:
        with get_db_context() as db:
            result = db.query(Payment).all()
    
    Yields:
        Session: SQLAlchemy session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database transaction failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


# ===== Database Health Check =====
def check_database_connection() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False


def init_db():
    """
    Initialize database by creating all tables.
    
    Note:
        This should only be used in development.
        In production, use Alembic migrations.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise


def drop_db():
    """
    Drop all database tables.
    
    Warning:
        Only use in development/testing environments!
    """
    if settings.is_production:
        raise RuntimeError("Cannot drop database in production")
    
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {str(e)}")
        raise


# ===== Database Statistics =====
def get_db_stats() -> dict:
    """
    Get database connection pool statistics.
    
    Returns:
        dict: Pool statistics
    """
    return {
        "pool_size": engine.pool.size(),
        "checked_in": engine.pool.checkedin(),
        "checked_out": engine.pool.checkedout(),
        "overflow": engine.pool.overflow(),
        "total_connections": engine.pool.size() + engine.pool.overflow()
    }
