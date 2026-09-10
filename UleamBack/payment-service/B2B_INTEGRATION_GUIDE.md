# 🤝 Guía de Integración B2B - Webhooks Bidireccionales

**Para**: Grupos externos (Hotel, Tours, Servicios)  
**Propósito**: Integración de webhooks con payment-service

---

## 📋 Resumen

El **payment-service** soporta webhooks **bidireccionales**:

- **OUTBOUND**: Nosotros te notificamos cuando hay pagos (payment.success, payment.failed, etc.)
- **INBOUND**: Tú nos notificas eventos de tu sistema (booking.confirmed, tour.purchased, etc.)

---

## 🚀 Inicio Rápido

### 1. Intercambio de Credenciales

**Necesitamos de ti**:
```json
{
  "partner_name": "Hotel Paradise",
  "partner_type": "hotel | tour | service",
  "webhook_url": "https://tu-sistema.com/webhooks/payment",
  "contact_email": "dev@hotel-paradise.com"
}
```

**Te damos**:
```json
{
  "api_key": "partner_key_abc123",
  "shared_secret": "partner_secret_xyz789",
  "webhook_endpoint": "http://localhost:8024/api/v1/partners/webhook",
  "documentation": "http://localhost:8024/api/v1/docs"
}
```

### 2. Registrar Partner en BD

```sql
INSERT INTO partner (
  nombre, 
  tipo_partner, 
  api_key, 
  secret_key, 
  webhook_url, 
  is_active
)
VALUES (
  'Hotel Paradise',
  'hotel',
  'partner_key_abc123',
  'partner_secret_xyz789',
  'https://hotel-paradise.com/webhooks/payment',
  true
);
```

---

## 📤 OUTBOUND: Recibir Webhooks de Nosotros

### Eventos que Enviamos

| Evento | Descripción | Cuándo se envía |
|--------|-------------|-----------------|
| `payment.success` | Pago completado | Usuario paga reserva |
| `payment.failed` | Pago rechazado | Tarjeta rechazada |
| `payment.refunded` | Reembolso procesado | Cancelación con reembolso |
| `payment.cancelled` | Pago cancelado | Cancelación sin reembolso |

### Payload Enviado

```json
{
  "event_type": "payment.success",
  "event_id": "evt_abc123",
  "timestamp": 1737324000,
  "payment_id": 456,
  "reserva_id": 789,
  "amount": 150.00,
  "currency": "USD",
  "status": "completed",
  "provider": "stripe",
  "customer_email": "user@example.com",
  "metadata": {
    "room_type": "deluxe",
    "check_in": "2026-02-01",
    "check_out": "2026-02-04"
  }
}
```

### Headers Enviados

```http
POST https://hotel-paradise.com/webhooks/payment
Content-Type: application/json
X-Signature: abc123def456...
X-Webhook-Timestamp: 1737324000
User-Agent: ULEAM-Payment-Service/1.0
```

### Verificar Firma HMAC (Python)

```python
import hmac
import hashlib
import json

def verify_webhook_signature(payload_str, signature, secret):
    """Verifica firma HMAC de webhook"""
    # Generar firma esperada
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Comparación timing-safe
    return hmac.compare_digest(signature, expected_signature)

# Uso
@app.post("/webhooks/payment")
async def receive_payment_webhook(request: Request):
    # 1. Obtener headers
    signature = request.headers.get("X-Signature")
    timestamp = request.headers.get("X-Webhook-Timestamp")
    
    # 2. Leer body
    payload_bytes = await request.body()
    payload_str = payload_bytes.decode('utf-8')
    
    # 3. Verificar firma
    if not verify_webhook_signature(payload_str, signature, SECRET):
        raise HTTPException(401, "Invalid signature")
    
    # 4. Verificar timestamp (anti-replay)
    if abs(int(time.time()) - int(timestamp)) > 300:  # 5 min
        raise HTTPException(401, "Timestamp expired")
    
    # 5. Procesar evento
    payload = json.loads(payload_str)
    if payload["event_type"] == "payment.success":
        # Confirmar reserva en tu sistema
        confirm_booking(payload["reserva_id"])
    
    return {"status": "received"}
```

### Verificar Firma HMAC (Node.js)

```javascript
const crypto = require('crypto');

function verifyWebhookSignature(payloadStr, signature, secret) {
    const expectedSignature = crypto
        .createHmac('sha256', secret)
        .update(payloadStr)
        .digest('hex');
    
    return crypto.timingSafeEqual(
        Buffer.from(signature),
        Buffer.from(expectedSignature)
    );
}

// Uso con Express
app.post('/webhooks/payment', express.raw({type: 'application/json'}), (req, res) => {
    const signature = req.headers['x-signature'];
    const timestamp = req.headers['x-webhook-timestamp'];
    const payloadStr = req.body.toString('utf8');
    
    // Verificar firma
    if (!verifyWebhookSignature(payloadStr, signature, SECRET)) {
        return res.status(401).json({error: 'Invalid signature'});
    }
    
    // Verificar timestamp
    if (Math.abs(Date.now() / 1000 - parseInt(timestamp)) > 300) {
        return res.status(401).json({error: 'Timestamp expired'});
    }
    
    // Procesar evento
    const payload = JSON.parse(payloadStr);
    if (payload.event_type === 'payment.success') {
        confirmBooking(payload.reserva_id);
    }
    
    res.json({status: 'received'});
});
```

---

## 📥 INBOUND: Enviar Webhooks a Nosotros

### Eventos que Aceptamos

| Evento | Descripción | Acción |
|--------|-------------|--------|
| `booking.confirmed` | Hotel confirma reserva | Crea Payment |
| `tour.purchased` | Tour comprado | Actualiza metadata |
| `service.activated` | Servicio activado | Registra en metadata |
| `booking.cancelled` | Cancelación | Procesa reembolso |

### Endpoint

```
POST http://localhost:8024/api/v1/partners/webhook
```

### Generar Firma HMAC (Python)

```python
import hmac
import hashlib
import json
import time
import requests

def generate_hmac_signature(payload, secret):
    """Genera firma HMAC para webhook"""
    # Serializar payload (orden consistente)
    payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    
    # Generar firma
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature

# Ejemplo: Enviar booking.confirmed
def send_booking_confirmed(booking_id, reserva_id, amount):
    payload = {
        "event_type": "booking.confirmed",
        "event_id": f"booking_{booking_id}",
        "timestamp": int(time.time()),
        "booking_id": booking_id,
        "reserva_id": reserva_id,
        "amount": amount,
        "currency": "USD",
        "customer_email": "user@example.com",
        "metadata": {
            "room_type": "deluxe",
            "nights": 3
        }
    }
    
    # Generar firma
    signature = generate_hmac_signature(payload, SHARED_SECRET)
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": API_KEY,
        "X-Webhook-Signature": signature,
        "X-Webhook-Timestamp": str(payload["timestamp"])
    }
    
    # Enviar
    response = requests.post(
        "http://localhost:8024/api/v1/partners/webhook",
        json=payload,
        headers=headers
    )
    
    return response.json()
```

### Generar Firma HMAC (Node.js)

```javascript
const crypto = require('crypto');
const axios = require('axios');

function generateHmacSignature(payload, secret) {
    // Serializar payload (orden consistente)
    const payloadStr = JSON.stringify(payload, Object.keys(payload).sort());
    
    // Generar firma
    return crypto
        .createHmac('sha256', secret)
        .update(payloadStr)
        .digest('hex');
}

// Ejemplo: Enviar booking.confirmed
async function sendBookingConfirmed(bookingId, reservaId, amount) {
    const payload = {
        event_type: 'booking.confirmed',
        event_id: `booking_${bookingId}`,
        timestamp: Math.floor(Date.now() / 1000),
        booking_id: bookingId,
        reserva_id: reservaId,
        amount: amount,
        currency: 'USD',
        customer_email: 'user@example.com',
        metadata: {
            room_type: 'deluxe',
            nights: 3
        }
    };
    
    // Generar firma
    const signature = generateHmacSignature(payload, SHARED_SECRET);
    
    // Headers
    const headers = {
        'Content-Type': 'application/json',
        'X-Api-Key': API_KEY,
        'X-Webhook-Signature': signature,
        'X-Webhook-Timestamp': payload.timestamp.toString()
    };
    
    // Enviar
    const response = await axios.post(
        'http://localhost:8024/api/v1/partners/webhook',
        payload,
        { headers }
    );
    
    return response.data;
}
```

### Schemas de Eventos

#### 1. booking.confirmed

```json
{
  "event_type": "booking.confirmed",
  "event_id": "booking_456",
  "timestamp": 1737324000,
  "booking_id": "booking_456",
  "reserva_id": 789,
  "amount": 150.00,
  "currency": "USD",
  "customer_email": "user@example.com",
  "metadata": {
    "room_type": "deluxe",
    "check_in": "2026-02-01",
    "check_out": "2026-02-04",
    "nights": 3
  }
}
```

**Acción**: Crea nuevo Payment si no existe

#### 2. tour.purchased

```json
{
  "event_type": "tour.purchased",
  "event_id": "tour_789",
  "timestamp": 1737324000,
  "payment_id": 456,
  "tour_id": "tour_789",
  "tour_name": "City Historical Tour",
  "tour_date": "2026-02-02",
  "participants": 4,
  "amount": 80.00,
  "currency": "USD",
  "metadata": {
    "guide": "John Doe",
    "language": "Spanish"
  }
}
```

**Acción**: Actualiza metadata del Payment con info del tour

#### 3. service.activated

```json
{
  "event_type": "service.activated",
  "event_id": "service_123",
  "timestamp": 1737324000,
  "payment_id": 456,
  "service_id": "service_123",
  "service_name": "Airport Transfer",
  "amount": 30.00,
  "currency": "USD",
  "metadata": {
    "pickup_time": "2026-02-01T10:00:00Z",
    "vehicle_type": "sedan"
  }
}
```

**Acción**: Registra servicio en metadata del Payment

#### 4. booking.cancelled

```json
{
  "event_type": "booking.cancelled",
  "event_id": "cancel_456",
  "timestamp": 1737324000,
  "payment_id": 456,
  "booking_id": "booking_456",
  "refund_amount": 150.00,
  "reason": "Customer request",
  "cancellation_policy": "full_refund",
  "metadata": {
    "cancelled_by": "customer",
    "cancelled_at": "2026-01-25T15:00:00Z"
  }
}
```

**Acción**: Procesa reembolso y actualiza Payment

### Respuestas

**Éxito (200)**:
```json
{
  "status": "processed",
  "event_id": "booking_456",
  "message": "Event processed successfully",
  "timestamp": "2026-01-19T20:00:00Z"
}
```

**Error - API Key inválida (401)**:
```json
{
  "detail": "Invalid API key"
}
```

**Error - Firma inválida (401)**:
```json
{
  "detail": "Invalid webhook signature"
}
```

**Error - Timestamp expirado (401)**:
```json
{
  "detail": "Webhook timestamp expired (tolerance: 5 minutes)"
}
```

**Error - Evento no soportado (400)**:
```json
{
  "detail": "Unsupported event type: unknown.event"
}
```

---

## 🔍 Testing

### 1. Health Check

```bash
curl http://localhost:8024/api/v1/partners/webhook/health
```

**Respuesta**:
```json
{
  "status": "healthy",
  "service": "partners-webhook-endpoint",
  "timestamp": "2026-01-19T20:00:00Z"
}
```

### 2. Listar Eventos Soportados

```bash
curl http://localhost:8024/api/v1/partners/webhook/events
```

**Respuesta**:
```json
{
  "supported_events": [
    {
      "event_type": "booking.confirmed",
      "description": "Hotel confirms booking",
      "required_fields": ["booking_id", "reserva_id", "amount", "currency"],
      "example": {...}
    },
    ...
  ]
}
```

### 3. Enviar Webhook de Prueba

```bash
# Payload
PAYLOAD='{
  "event_type": "booking.confirmed",
  "event_id": "test_123",
  "timestamp": 1737324000,
  "booking_id": "test_123",
  "reserva_id": 1,
  "amount": 100.00,
  "currency": "USD",
  "customer_email": "test@example.com",
  "metadata": {}
}'

# Generar firma (ejemplo con Python)
SIGNATURE=$(python -c "
import hmac, hashlib, json
payload = $PAYLOAD
secret = 'partner_secret_xyz789'
payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
print(hmac.new(secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest())
")

# Enviar
curl -X POST http://localhost:8024/api/v1/partners/webhook \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: partner_key_abc123" \
  -H "X-Webhook-Signature: $SIGNATURE" \
  -H "X-Webhook-Timestamp: 1737324000" \
  -d "$PAYLOAD"
```

---

## 🛡️ Seguridad

### Mejores Prácticas

1. **Siempre verificar firma HMAC**
   - Usa `hmac.compare_digest()` (Python) o `crypto.timingSafeEqual()` (Node.js)
   - Previene timing attacks

2. **Validar timestamp**
   - Tolerancia: 5 minutos
   - Previene replay attacks

3. **Usar HTTPS en producción**
   - Nunca envíes credenciales sin TLS

4. **Rotar secrets periódicamente**
   - Cambiar shared_secret cada 6 meses

5. **Validar input**
   - Verificar event_type soportado
   - Validar campos requeridos
   - Sanitizar metadata

6. **Logging y auditoría**
   - Registrar todos los webhooks recibidos
   - Guardar payloads para debugging
   - Monitorear intentos fallidos

### Troubleshooting

**Error: "Invalid signature"**
- ✅ Verifica que estés usando el `shared_secret` correcto
- ✅ Asegúrate de serializar el JSON con el mismo orden (`sort_keys=True`)
- ✅ No modifiques el payload después de generar la firma

**Error: "Timestamp expired"**
- ✅ Verifica que tu reloj esté sincronizado (NTP)
- ✅ Genera el timestamp justo antes de enviar
- ✅ Tolerancia es 5 minutos (300 segundos)

**Error: "Invalid API key"**
- ✅ Verifica que estés usando el `api_key` correcto
- ✅ Header debe ser `X-Api-Key` (case-sensitive)

**Error: 500 Internal Server Error**
- ✅ Revisa logs del payment-service
- ✅ Verifica que el payload tenga todos los campos requeridos
- ✅ Contacta al equipo de payment-service

---

## 📞 Contacto

**Equipo Payment Service**:
- Email: dev@uleam-payment.com
- Slack: #payment-service-support
- Docs: http://localhost:8024/api/v1/docs

**Disponibilidad**: Lunes a Viernes, 9am - 6pm

---

## 📚 Referencias

- [OpenAPI Documentation](http://localhost:8024/api/v1/docs)
- [HMAC-SHA256 Specification](https://datatracker.ietf.org/doc/html/rfc2104)
- [Webhook Security Best Practices](https://webhooks.fyi/security/hmac)

---

**Versión**: 1.0  
