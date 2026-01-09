"""
Tests para Webhooks Bidireccionales (INBOUND)

Valida el flujo completo de comunicación B2B:
- Recepción de webhooks de partners
- Validación de HMAC
- Procesamiento de eventos
- Respuestas automáticas

Author: Equipo ULEAM Reservas
"""

import pytest
import json
import time
import hmac
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.partner import Partner
from app.models.payment import Payment
from app.services.hmac_service import HmacService


class TestPartnerWebhookEndpoint:
    """Tests para el endpoint POST /partners/webhook"""
    
    @pytest.fixture
    def mock_partner(self):
        """Partner mock para testing"""
        partner = MagicMock(spec=Partner)
        partner.id = 1
        partner.nombre = "Test Hotel Partner"
        partner.email = "test@hotel.com"
        partner.api_key = "pk_test_123456"
        partner.secret_key = "sk_test_secret_key_xyz"
        partner.is_active = True
        partner.webhooks_received = 0
        return partner
    
    @pytest.fixture
    def valid_webhook_payload(self):
        """Payload válido de webhook"""
        return {
            "event_type": "booking.confirmed",
            "event_id": "evt_test_123",
            "timestamp": int(time.time()),
            "booking_id": "book_123",
            "payment_id": "pay_456",
            "amount": 150.00,
            "currency": "USD",
            "customer_email": "customer@example.com",
            "metadata": {
                "room_type": "suite",
                "check_in": "2026-02-01",
                "check_out": "2026-02-05"
            }
        }
    
    def generate_hmac_signature(self, payload: dict, secret_key: str) -> tuple[str, str]:
        """Genera firma HMAC para payload usando HmacService"""
        from app.services.hmac_service import HmacService
        
        timestamp = str(payload["timestamp"])
        
        # Usar HmacService para generar firma (solo payload, no timestamp)
        signature = HmacService.generate_signature(
            payload=payload,
            secret=secret_key
        )
        
        return signature, timestamp
    
    @patch("app.routes.partners_webhook.PartnerService.get_partner_by_api_key")
    @patch("app.routes.partners_webhook.PartnerWebhookProcessor.process_event")
    def test_receive_valid_webhook(
        self,
        mock_process_event,
        mock_get_partner,
        mock_partner,
        valid_webhook_payload
    ):
        """Test: Recibir webhook válido con HMAC correcto"""
        # Setup mocks
        mock_get_partner.return_value = mock_partner
        mock_process_event.return_value = {
            "status": "processed",
            "action": "payment_created"
        }
        
        # Generar firma HMAC (esto serializa el payload internamente)
        signature, timestamp = self.generate_hmac_signature(
            valid_webhook_payload,
            mock_partner.secret_key
        )
        
        # Serializar payload con el mismo método que HmacService usa
        payload_json = json.dumps(valid_webhook_payload, sort_keys=True, separators=(',', ':'))
        
        # Hacer request con content (raw bytes) en lugar de json
        client = TestClient(app)
        response = client.post(
            "/api/v1/partners/webhook",
            content=payload_json,
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": mock_partner.api_key,
                "X-Webhook-Signature": signature,
                "X-Webhook-Timestamp": timestamp
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        assert data["event_id"] == valid_webhook_payload["event_id"]
        
        # Verificar que se llamó al procesador
        mock_process_event.assert_called_once()
    
    @patch("app.routes.partners_webhook.PartnerService.get_partner_by_api_key")
    def test_receive_webhook_invalid_api_key(self, mock_get_partner, valid_webhook_payload):
        """Test: Webhook con API key inválida debe retornar 401"""
        # API key no existe
        mock_get_partner.return_value = None
        
        signature, timestamp = self.generate_hmac_signature(
            valid_webhook_payload,
            "sk_fake_key"
        )
        
        client = TestClient(app)
        response = client.post(
            "/api/v1/partners/webhook",
            json=valid_webhook_payload,
            headers={
                "X-Api-Key": "pk_invalid_key",
                "X-Webhook-Signature": signature,
                "X-Webhook-Timestamp": timestamp
            }
        )
        
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]
    
    @patch("app.routes.partners_webhook.PartnerService.get_partner_by_api_key")
    def test_receive_webhook_invalid_signature(
        self,
        mock_get_partner,
        mock_partner,
        valid_webhook_payload
    ):
        """Test: Webhook con firma HMAC inválida debe retornar 401"""
        mock_get_partner.return_value = mock_partner
        
        _, timestamp = self.generate_hmac_signature(
            valid_webhook_payload,
            mock_partner.secret_key
        )
        
        client = TestClient(app)
        response = client.post(
            "/api/v1/partners/webhook",
            json=valid_webhook_payload,
            headers={
                "X-Api-Key": mock_partner.api_key,
                "X-Webhook-Signature": "invalid_signature_xyz",
                "X-Webhook-Timestamp": timestamp
            }
        )
        
        assert response.status_code == 401
        assert "Invalid webhook signature" in response.json()["detail"]
    
    @patch("app.routes.partners_webhook.PartnerService.get_partner_by_api_key")
    def test_receive_webhook_inactive_partner(
        self,
        mock_get_partner,
        mock_partner,
        valid_webhook_payload
    ):
        """Test: Webhook de partner inactivo debe retornar 401"""
        mock_partner.is_active = False
        mock_get_partner.return_value = mock_partner
        
        signature, timestamp = self.generate_hmac_signature(
            valid_webhook_payload,
            mock_partner.secret_key
        )
        
        client = TestClient(app)
        response = client.post(
            "/api/v1/partners/webhook",
            json=valid_webhook_payload,
            headers={
                "X-Api-Key": mock_partner.api_key,
                "X-Webhook-Signature": signature,
                "X-Webhook-Timestamp": timestamp
            }
        )
        
        assert response.status_code == 401
        assert "Partner is inactive" in response.json()["detail"]
    
    @patch("app.routes.partners_webhook.PartnerService.get_partner_by_api_key")
    def test_receive_webhook_expired_timestamp(
        self,
        mock_get_partner,
        mock_partner,
        valid_webhook_payload
    ):
        """Test: Webhook con timestamp expirado debe retornar 401"""
        mock_get_partner.return_value = mock_partner
        
        # Timestamp de hace 10 minutos (> 5 min tolerance)
        old_timestamp = int(time.time()) - 600
        valid_webhook_payload["timestamp"] = old_timestamp
        
        signature, _ = self.generate_hmac_signature(
            valid_webhook_payload,
            mock_partner.secret_key
        )
        
        client = TestClient(app)
        response = client.post(
            "/api/v1/partners/webhook",
            json=valid_webhook_payload,
            headers={
                "X-Api-Key": mock_partner.api_key,
                "X-Webhook-Signature": signature,
                "X-Webhook-Timestamp": str(old_timestamp)
            }
        )
        
        assert response.status_code == 401
        assert "Invalid webhook signature" in response.json()["detail"]
    
    @patch("app.routes.partners_webhook.PartnerService.get_partner_by_api_key")
    def test_receive_webhook_unsupported_event_type(
        self,
        mock_get_partner,
        mock_partner,
        valid_webhook_payload
    ):
        """Test: Webhook con event_type no soportado debe retornar 400"""
        mock_get_partner.return_value = mock_partner
        
        # Event type no soportado
        valid_webhook_payload["event_type"] = "unknown.event"
        
        signature, timestamp = self.generate_hmac_signature(
            valid_webhook_payload,
            mock_partner.secret_key
        )
        
        # Serializar payload con el mismo método que HmacService
        payload_json = json.dumps(valid_webhook_payload, sort_keys=True, separators=(',', ':'))
        
        client = TestClient(app)
        response = client.post(
            "/api/v1/partners/webhook",
            content=payload_json,
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": mock_partner.api_key,
                "X-Webhook-Signature": signature,
                "X-Webhook-Timestamp": timestamp
            }
        )
        
        assert response.status_code == 400
        assert "Unsupported event type" in response.json()["detail"]
    
    def test_list_supported_events(self):
        """Test: GET /partners/webhook/events lista eventos soportados"""
        client = TestClient(app)
        response = client.get("/api/v1/partners/webhook/events")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "supported_events" in data
        assert len(data["supported_events"]) >= 4  # booking.confirmed, tour.purchased, etc.
        
        # Verificar estructura de eventos
        for event in data["supported_events"]:
            assert "event_type" in event
            assert "description" in event
            assert "required_fields" in event
            assert "example" in event
    
    def test_webhook_health_check(self):
        """Test: GET /partners/webhook/health verifica disponibilidad"""
        client = TestClient(app)
        response = client.get("/api/v1/partners/webhook/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "partner-webhook-receiver"


class TestPartnerWebhookProcessor:
    """Tests para PartnerWebhookProcessor"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock de sesión de BD"""
        db = MagicMock()
        db.commit = MagicMock()
        db.add = MagicMock()
        db.query = MagicMock()
        return db
    
    @pytest.fixture
    def mock_partner(self):
        """Partner mock"""
        partner = MagicMock(spec=Partner)
        partner.id = 1
        partner.nombre = "Test Partner"
        partner.secret_key = "sk_test_123"
        return partner
    
    @pytest.mark.asyncio
    async def test_process_booking_confirmed_create_payment(
        self,
        mock_db,
        mock_partner
    ):
        """Test: booking.confirmed crea nuevo pago si no existe"""
        from app.services.partner_webhook_processor import PartnerWebhookProcessor
        
        # Mock: No existe pago previo
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        event_data = {
            "event_type": "booking.confirmed",
            "event_id": "evt_123",
            "timestamp": int(time.time()),
            "booking_id": "book_456",
            "amount": 200.00,
            "currency": "USD",
            "metadata": {"room_type": "deluxe"}
        }
        
        with patch("app.services.partner_webhook_processor.PartnerService.deliver_webhook_to_partner"):
            result = await PartnerWebhookProcessor.process_event(
                db=mock_db,
                partner=mock_partner,
                event_data=event_data
            )
        
        # Verificar que se creó un pago
        assert result["status"] == "processed"
        assert result["action"] == "payment_created"
        assert "payment_id" in result
    
    @pytest.mark.asyncio
    async def test_process_tour_purchased_updates_payment(
        self,
        mock_db,
        mock_partner
    ):
        """Test: tour.purchased actualiza metadata de pago existente"""
        from app.services.partner_webhook_processor import PartnerWebhookProcessor
        
        # Mock: Existe pago previo
        mock_payment = MagicMock(spec=Payment)
        mock_payment.id = 1
        mock_payment.metadata = {}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_payment
        
        event_data = {
            "event_type": "tour.purchased",
            "event_id": "evt_tour_123",
            "timestamp": int(time.time()),
            "tour_id": "tour_xyz",
            "payment_id": "pay_456",
            "amount": 75.00,
            "currency": "USD",
            "metadata": {"tour_name": "City Tour"}
        }
        
        result = await PartnerWebhookProcessor.process_event(
            db=mock_db,
            partner=mock_partner,
            event_data=event_data
        )
        
        # Verificar que se agregó el tour a metadata
        assert result["status"] == "processed"
        assert result["action"] == "tour_added"
        assert "additional_services" in mock_payment.metadata


class TestHMACIntegration:
    """Tests de integración para firma HMAC"""
    
    def test_hmac_signature_generation_and_verification(self):
        """Test: Generar y verificar firma HMAC"""
        secret_key = "sk_test_secret_123"
        payload = '{"event_type":"test.event","data":"test"}'
        timestamp = str(int(time.time()))
        
        # Generar firma (usa 'secret' no 'secret_key')
        signature = HmacService.generate_signature(
            payload=payload,
            secret=secret_key
        )
        
        # Verificar firma (verify_signature combina validación + timestamp)
        is_valid = HmacService.verify_signature(
            payload=payload,
            signature=signature,
            secret_key=secret_key,
            timestamp=timestamp,
            tolerance_seconds=300
        )
        
        assert is_valid
    
    def test_hmac_signature_invalid_secret(self):
        """Test: Firma HMAC con secret incorrecto falla"""
        payload = '{"event_type":"test.event"}'
        timestamp = str(int(time.time()))
        
        # Generar con un secret (usa 'secret' no 'secret_key')
        signature = HmacService.generate_signature(
            payload=payload,
            secret="sk_secret_1"
        )
        
        # Verificar con otro secret
        is_valid = HmacService.verify_signature(
            payload=payload,
            signature=signature,
            secret_key="sk_secret_2",  # Secret diferente
            timestamp=timestamp
        )
        
        assert not is_valid
