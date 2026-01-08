"""
Unit Tests for Payment Service

Tests de la lógica de negocio principal del PaymentService.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session

from app.services.payment_service import PaymentService
from app.schemas.payment import PaymentCreate
from app.models.payment import Payment, PaymentStatus


class TestPaymentService:
    """Tests para PaymentService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock de sesión de base de datos"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def payment_data(self):
        """Datos de pago de prueba"""
        return PaymentCreate(
            reserva_id=123,
            amount=Decimal("50.00"),
            currency="USD",
            provider="mock",
            metadata={"descripcion": "Test payment"}
        )
    
    @pytest.mark.asyncio
    async def test_create_payment_success(self, mock_db, payment_data):
        """Test crear pago exitoso"""
        # Arrange
        usuario_id = 1
        token = "fake_token"
        
        # Mock rest_client para validar reserva
        mock_reserva = {
            "id": 123,
            "usuario_id": 1,
            "espacio_id": 456,
            "precio_total": 50.00
        }
        
        with patch("app.clients.rest_client.get_rest_client") as mock_rest, \
             patch("app.clients.websocket_client.get_websocket_client") as mock_ws, \
             patch("app.adapters.adapter_factory.AdapterFactory.get_adapter") as mock_adapter:
            
            # Configure mocks
            mock_rest.return_value.validate_reserva = AsyncMock(return_value=mock_reserva)
            mock_rest.return_value.update_reserva_status = AsyncMock(return_value=True)
            mock_ws.return_value.notify_payment_success = AsyncMock(return_value=True)
            mock_ws.return_value.notify_reserva_confirmed = AsyncMock(return_value=True)
            
            mock_adapter.return_value.create_payment.return_value = {
                "payment_id": "mock_12345",
                "status": "completed"
            }
            
            # Act
            payment = await PaymentService.create_payment(
                db=mock_db,
                usuario_id=usuario_id,
                payment_data=payment_data,
                token=token
            )
            
            # Assert
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_rest.return_value.validate_reserva.assert_called_once()
            # No verificamos notify porque puede fallar sin afectar el pago
    
    @pytest.mark.asyncio
    async def test_create_payment_invalid_reserva(self, mock_db, payment_data):
        """Test crear pago con reserva inválida"""
        # Arrange
        usuario_id = 1
        token = "fake_token"
        
        with patch("app.clients.rest_client.get_rest_client") as mock_rest:
            mock_rest.return_value.validate_reserva = AsyncMock(return_value=None)
            
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                await PaymentService.create_payment(
                    db=mock_db,
                    usuario_id=usuario_id,
                    payment_data=payment_data,
                    token=token
                )
            
            assert "no encontrada" in str(exc_info.value)
            mock_db.rollback.assert_called_once()
    
    def test_get_payment_by_id(self, mock_db):
        """Test obtener pago por ID"""
        # Arrange
        payment_id = 1
        usuario_id = 1
        
        mock_payment = Payment(
            id=1,
            external_payment_id="mock_123",
            reserva_id=123,
            usuario_id=1,
            provider_name="mock",
            amount=Decimal("50.00"),
            currency="USD",
            status=PaymentStatus.COMPLETED
        )
        
        # Mock query encadenada correctamente
        mock_query = MagicMock()
        mock_filter1 = MagicMock()
        mock_filter2 = MagicMock()
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.first.return_value = mock_payment
        
        # Act
        result = PaymentService.get_payment(
            db=mock_db,
            payment_id=payment_id,
            usuario_id=usuario_id
        )
        
        # Assert
        assert result == mock_payment
        mock_db.query.assert_called_once()
    
    def test_list_payments_with_filters(self, mock_db):
        """Test listar pagos con filtros"""
        # Arrange
        usuario_id = 1
        
        mock_payments = [
            Payment(
                id=1,
                external_payment_id="mock_123",
                reserva_id=123,
                usuario_id=1,
                provider_name="mock",
                amount=Decimal("50.00"),
                currency="USD",
                status=PaymentStatus.COMPLETED
            )
        ]
        
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_payments
        
        # Act
        payments, total = PaymentService.list_payments(
            db=mock_db,
            usuario_id=usuario_id,
            skip=0,
            limit=10
        )
        
        # Assert
        assert len(payments) == 1
        assert total == 1
        assert payments[0].id == 1
