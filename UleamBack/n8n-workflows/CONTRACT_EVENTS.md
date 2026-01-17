# Contrato Normalizado de Eventos para n8n

## Estructura Base del Evento

Todo evento que pase por n8n debe seguir esta estructura normalizada en JSON:

```json
{
  "event": "payment.success | booking.confirmed | partner.webhook.received",
  "source": "stripe | mercadopago | mock | partner_name",
  "timestamp": "2026-01-23T14:30:00Z",
  "payload": {
    // Datos específicos del evento
  },
  "partner_id": "uuid | null",
  "hmac_signature": "sha256_hash_if_required",
  "retry_count": 0,
  "trace_id": "unique_id_for_logging"
}
```

## Campos Obligatorios

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `event` | string | Nombre del evento (ej: `payment.success`, `booking.confirmed`) |
| `source` | string | Origen del evento (pasarela, partner, internal) |
| `timestamp` | ISO-8601 | Fecha/hora UTC del evento |
| `payload` | object | Datos específicos del evento |
| `trace_id` | string | UUID para rastrear el evento a través de todos los servicios |

## Campos Opcionales

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `partner_id` | uuid \| null | ID del partner si el evento viene de integración B2B |
| `hmac_signature` | string | HMAC-SHA256 para verificar integridad (si viene de partner) |
| `retry_count` | number | Contador de reintentos (n8n puede usar para backoff) |

---

## Eventos Específicos

### 1. Payment Success (desde pasarela)

**Trigger**: Webhook del MockAdapter / Stripe / MercadoPago

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
    "customer_id": "cust_123",
    "metadata": {
      "service": "hotel_reservation"
    }
  }
}
```

**Acciones en n8n**:
1. Validar HMAC (si aplica)
2. Verificar estructura payload
3. Activar reserva en REST → `POST /reservas/{booking_id}/confirm`
4. Notificar WebSocket → `POST /api/webhooks/reserva-actualizada`
5. Enviar email de confirmación
6. Disparar webhook a partner registrado

---

### 2. Booking Confirmed (evento de negocio)

**Trigger**: acción desde REST/GraphQL después de pago confirmado

```json
{
  "event": "booking.confirmed",
  "source": "internal",
  "timestamp": "2026-01-23T14:30:05Z",
  "trace_id": "bk-001-xyz",
  "payload": {
    "booking_id": "bk_001",
    "customer_id": "cust_123",
    "service_id": "svc_456",
    "check_in": "2026-02-01",
    "check_out": "2026-02-05",
    "total_amount": 150.00
  }
}
```

---

### 3. Partner Webhook Received (desde grupo partner)

**Trigger**: Webhook HTTP desde otro grupo

```json
{
  "event": "tour.purchased",
  "source": "partner_hotel_group",
  "timestamp": "2026-01-23T14:35:00Z",
  "partner_id": "partner_uuid_xyz",
  "hmac_signature": "sha256:abcd1234...xyz",
  "trace_id": "tour-999-partner",
  "payload": {
    "order_id": "order_001",
    "booking_reference": "bk_001",
    "tour_package": "island_tour",
    "participants": 4,
    "price": 50.00
  }
}
```

**Acciones en n8n**:
1. Verificar `hmac_signature` con secret del partner
2. Normalizar evento
3. Ejecutar acción de negocio (ej: crear orden, actualizar itinerario)
4. Responder ACK HTTP 200

---

### 4. Scheduled Task (cron)

**Trigger**: Cron job diario / semanal

```json
{
  "event": "scheduled.daily_report",
  "source": "n8n_scheduler",
  "timestamp": "2026-01-23T23:59:00Z",
  "trace_id": "cron-daily-2026-01-23",
  "payload": {
    "task": "generate_daily_report",
    "report_type": "bookings",
    "date": "2026-01-23"
  }
}
```

---

## Firma HMAC-SHA256

### Cálculo para Partner Webhooks

```
secret = "partner_shared_secret_from_db"
body_json = JSON.stringify(payload)
signature = HMAC-SHA256(secret, body_json)
header = `sha256:${signature}`
```

### Verificación en n8n

En el workflow, usar nodo **Function** o **JavaScript**:

```javascript
const crypto = require('crypto');
const secret = $env.PARTNER_SECRET; // obtenido del lookup del partner
const body = JSON.stringify($input.body);
const signature = crypto
  .createHmac('sha256', secret)
  .update(body)
  .digest('hex');

return signature === $input.body.hmac_signature.split(':')[1];
```

---

## Logging y Trazabilidad

Todo evento debe registrar:
- `trace_id`: para seguimiento end-to-end
- `created_at`: timestamp de ingreso
- `workflow_id`: qué workflow procesó
- `status`: success, failed, retry
- `error_message`: si aplica
- `duration_ms`: tiempo de procesamiento
