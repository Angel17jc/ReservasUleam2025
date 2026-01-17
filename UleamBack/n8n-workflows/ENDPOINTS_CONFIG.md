# Configuración de Endpoints para n8n Workflows

## 🎯 Endpoints del Proyecto (Locales)

### REST Service (FastAPI)
- **URL Base**: `http://localhost:8000`
- **API Base**: `http://localhost:8000/api`
- **GraphQL Fallback**: `http://localhost:8000/graphql` (si aplica)

**Endpoints críticos para n8n**:
```
GET    /api/health                           # Health check
POST   /api/reservas/{id}/confirm            # Activar reserva (Payment Handler)
POST   /api/webhooks/reserva-actualizada    # Notificar actualización (WS)
GET    /api/partners                         # Listar partners
GET    /api/partners/{id}                    # Obtener secret del partner
POST   /api/partner-webhooks/log             # Registrar intento de webhook
POST   /internal/payments/confirm            # Procesar pago confirmado
```

### GraphQL Service (Go)
- **URL**: `http://localhost:8080/graphql`
- **Método**: POST (GraphQL queries/mutations)

**Queries/Mutations para n8n**:
```graphql
# Buscar reserva
query GetBooking($id: ID!) {
  booking(id: $id) {
    id
    customer_id
    total_amount
    status
  }
}

# Actualizar estado
mutation UpdateBookingStatus($id: ID!, $status: String!) {
  updateBookingStatus(id: $id, status: $status) {
    id
    status
  }
}
```

### WebSocket Service (NestJS)
- **URL**: `http://localhost:3001`
- **Port**: 3001
- **Socket.IO**: Cliente JavaScript

**Endpoints webhook (para notificaciones)**:
```
POST   /api/webhooks/reserva-creada          # Nueva reserva
POST   /api/webhooks/reserva-actualizada    # Actualización
POST   /api/webhooks/reserva-cancelada      # Cancelación
POST   /api/webhooks/notificacion           # Notificación genérica
POST   /api/webhooks/stats-update           # Estadísticas
```

### Payment Service (Python)
- **URL Base**: `http://localhost:8001` (puerto estimado)
- **API Base**: `http://localhost:8001/api`

**Endpoints**:
```
POST   /api/payments                        # Crear pago
GET    /api/payments/{id}                   # Obtener pago
POST   /api/payments/{id}/confirm           # Confirmar pago
GET    /api/providers/health                # Health check proveedor
```

---

## 🔐 Seguridad: HMAC y Secrets

### Headers Requeridos para n8n → REST API

```
Content-Type: application/json
Authorization: Bearer {JWT_TOKEN}
X-Request-ID: {TRACE_ID}
X-Hub-Signature: sha256={HMAC_SIGNATURE}
```

### Generación de HMAC en n8n

Usar nodo **Function** de n8n:

```javascript
const crypto = require('crypto');

// Para partner webhooks outbound
const secret = "partner_shared_secret";
const body = JSON.stringify({
  event: "payment.success",
  payload: { /* datos */ }
});

const signature = crypto
  .createHmac('sha256', secret)
  .update(body)
  .digest('hex');

return {
  "X-Hub-Signature": `sha256:${signature}`,
  "signature": signature
};
```

---

## 📦 Ejemplos de Payloads

### Payment Handler - Input (Webhook desde MockAdapter)

```json
{
  "event": "payment.success",
  "source": "mock",
  "timestamp": "2026-01-23T14:30:00Z",
  "trace_id": "pay-123-abc",
  "payload": {
    "payment_id": "pm_123abc",
    "amount": 150.00,
    "currency": "USD",
    "booking_id": "bk_001",
    "customer_id": "cust_123"
  }
}
```

### Activar Reserva - POST /api/reservas/{id}/confirm

```json
{
  "payment_id": "pm_123abc",
  "status": "confirmed",
  "confirmation_timestamp": "2026-01-23T14:30:00Z"
}
```

### Notificar WebSocket - POST /api/webhooks/reserva-actualizada

```json
{
  "booking_id": "bk_001",
  "status": "confirmed",
  "event": "reserva-actualizada",
  "timestamp": "2026-01-23T14:30:00Z",
  "user_id": "cust_123"
}
```

### Partner Webhook Outbound (con HMAC)

```json
{
  "event": "booking.confirmed",
  "source": "uleam_hotel_system",
  "timestamp": "2026-01-23T14:30:00Z",
  "trace_id": "bk-001-xyz",
  "payload": {
    "booking_id": "bk_001",
    "customer_id": "cust_123",
    "service_id": "svc_456"
  }
}
```

---

## 🌍 URLs de Partner (Ejemplo)

Cuando registres un partner en la BD, tendrás:

```json
{
  "partner_id": "partner_uuid_xyz",
  "name": "TourCompany Tours Ltd",
  "webhook_url": "https://api.tourcompany.com/webhooks/uleam",
  "secret": "shared_secret_key_123",
  "subscribed_events": ["booking.confirmed", "payment.success"],
  "is_active": true
}
```

---

## 🧪 Probar Endpoints desde n8n

### 1. Test HTTP Request (nodo HTTP Request)

```
Method: GET
URL: http://localhost:8000/api/health
Headers:
  - Content-Type: application/json
```

**Response esperado**:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-23T14:30:00Z"
}
```

### 2. Activar Reserva

```
Method: POST
URL: http://localhost:8000/api/reservas/bk_001/confirm
Headers:
  - Content-Type: application/json
  - Authorization: Bearer {JWT_TOKEN}
Body:
{
  "payment_id": "pm_123abc",
  "status": "confirmed"
}
```

---

## 📋 Checklist Antes de Iniciar Workflows

- [ ] REST API está corriendo en `localhost:8000`
- [ ] GraphQL está corriendo en `localhost:8080`
- [ ] WebSocket está corriendo en `localhost:3001`
- [ ] Base de datos está accesible
- [ ] n8n está corriendo en `localhost:5678`
- [ ] Partners están registrados en la BD
- [ ] Secrets de partners están guardados (para HMAC)
- [ ] SMTP/Email está configurado (si es necesario)

---

## 🚨 Troubleshooting

**n8n no puede conectar a REST API**:
- Verificar que REST está corriendo: `curl http://localhost:8000/api/health`
- Revisar firewall de Windows
- Considerar usar `host.docker.internal` si n8n estuviera en Docker

**HMAC signature inválido**:
- Verificar que el secret es correcto en n8n
- Usar `JSON.stringify()` sin espacios en el body
- Confirmar algoritmo: sha256

**Webhook al partner falla**:
- Verificar URL del partner es accesible
- Revisar timeout (por defecto 10s)
- Registrar intent en `PartnerWebhookLog` para auditoría
