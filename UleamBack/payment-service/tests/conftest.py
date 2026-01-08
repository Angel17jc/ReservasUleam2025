"""
Pytest Configuration

Configuración global de pytest para el payment-service.
Configura el PYTHONPATH y fixtures compartidos.
"""

import sys
import os
from pathlib import Path

# Añadir el directorio raíz del proyecto al PYTHONPATH
# Esto permite importar 'app' desde los tests
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importar después de añadir al path
from app.database import Base


@pytest.fixture(scope="session")
def test_database_url():
    """URL de base de datos de prueba"""
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine(test_database_url):
    """Engine de base de datos de prueba"""
    engine = create_engine(
        test_database_url,
        connect_args={"check_same_thread": False}  # Solo para SQLite
    )
    
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Limpiar
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_engine):
    """Sesión de base de datos para cada test"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def mock_auth_client():
    """Mock del AuthClient para tests"""
    from unittest.mock import AsyncMock
    
    mock = MagicMock()
    mock.validate_token = AsyncMock(return_value={
        "id": 1,
        "email": "test@example.com",
        "rol": "usuario",
        "nombre": "Test User"
    })
    mock.get_user_by_id = AsyncMock(return_value={
        "id": 1,
        "email": "test@example.com",
        "rol": "usuario"
    })
    mock.health_check = AsyncMock(return_value=True)
    mock.close = AsyncMock()
    
    return mock


@pytest.fixture
def mock_rest_client():
    """Mock del RestClient para tests"""
    from unittest.mock import AsyncMock
    
    mock = MagicMock()
    mock.validate_reserva = AsyncMock(return_value={
        "id": 123,
        "usuario_id": 1,
        "espacio_id": 456,
        "precio_total": 50.00
    })
    mock.get_reserva_by_id = AsyncMock(return_value={
        "id": 123,
        "usuario_id": 1
    })
    mock.update_reserva_status = AsyncMock(return_value=True)
    mock.health_check = AsyncMock(return_value=True)
    mock.close = AsyncMock()
    
    return mock


@pytest.fixture
def mock_websocket_client():
    """Mock del WebSocketClient para tests"""
    from unittest.mock import AsyncMock
    
    mock = MagicMock()
    mock.notify_payment_success = AsyncMock(return_value=True)
    mock.notify_payment_failed = AsyncMock(return_value=True)
    mock.notify_payment_refunded = AsyncMock(return_value=True)
    mock.notify_reserva_confirmed = AsyncMock(return_value=True)
    mock.broadcast_notification = AsyncMock(return_value=True)
    mock.health_check = AsyncMock(return_value=True)
    mock.close = AsyncMock()
    
    return mock


@pytest.fixture
def sample_payment_data():
    """Datos de pago de ejemplo para tests"""
    from decimal import Decimal
    
    return {
        "reserva_id": 123,
        "amount": Decimal("50.00"),
        "currency": "USD",
        "provider": "mock",
        "metadata": {
            "descripcion": "Test payment",
            "test": True
        }
    }


@pytest.fixture
def sample_user_data():
    """Datos de usuario de ejemplo para tests"""
    return {
        "id": 1,
        "email": "test@example.com",
        "rol": "usuario",
        "nombre": "Test User",
        "is_active": True
    }


@pytest.fixture
def auth_headers():
    """Headers con JWT de prueba"""
    return {
        "Authorization": "Bearer test_jwt_token_1234567890"
    }
