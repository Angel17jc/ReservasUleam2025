# Endpoints Requeridos para n8n Integration

## 📌 Endpoints que Necesitan Existir o Verificarse

Este documento lista todos los endpoints que n8n invocará y cómo implementarlos en los servicios backend.

---

## 🔴 REST Service (FastAPI) - Obligatorio

### 1. `POST /api/reservas/{id}/confirm`

Activa una reserva después de confirmar pago.

**Usar para:** Payment Handler - Activar Reserva

**Request:**
```json
{
  "payment_id": "pm_123abc",
  "status": "confirmed",
  "amount": 150.00
}
```

**Response (200):**
```json
{
  "id": 1,
  "booking_id": "bk_001",
  "status": "confirmed",
  "payment_id": "pm_123abc",
  "confirmed_at": "2026-01-23T14:30:00Z"
}
```

**Implementación (FastAPI):**

```python
# rest-service/app/routes/reservas.py

@router.post("/reservas/{reserva_id}/confirm")
async def confirm_reservation(
    reserva_id: int,
    data: ReservaConfirmRequest,  # payment_id, status, amount
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Confirmar reserva después de pago exitoso."""
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    # Actualizar estado
    reserva.estado_reserva = 2  # Aprobada
    reserva.payment_id = data.payment_id
    reserva.confirmed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(reserva)
    
    return reserva
```

---

### 2. `GET /api/health`

Health check simple (ya debe existir).

**Request:** GET

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-23T14:30:00Z",
  "version": "1.0.0"
}
```

---

### 3. `POST /api/webhooks/reserva-actualizada`

Notificar al WebSocket service que una reserva se actualizó.

**Usar para:** Payment Handler - Notificar WebSocket

**Request:**
```json
{
  "booking_id": "bk_001",
  "status": "confirmed",
  "timestamp": "2026-01-23T14:30:00Z",
  "user_id": 1,
  "event": "reserva-actualizada"
}
```

**Response (204 No Content o 200)**

**Implementación:**

```python
# rest-service/app/routes/webhooks.py

@router.post("/webhooks/reserva-actualizada")
async def notify_websocket_reserva_actualizada(
    data: WebhookReservaActualizada
):
    """Notificar a WebSocket que una reserva fue actualizada."""
    # Forwarding HTTP a WebSocket service
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://localhost:3001/api/webhooks/reserva-actualizada",
            json=data.dict()
        )
    return {"status": "notified"}
```

---

### 4. `GET /api/partners` y `GET /api/partners/{id}`

Obtener datos de partners registrados.

**Usar para:** Partner Handler - Validación y lookup de secret

**Response:**
```json
{
  "id": 1,
  "nombre": "TourCompany Ltd",
  "webhook_url": "https://api.tourcompany.com/webhooks",
  "shared_secret": "hidden",  // No exponer en respuesta
  "eventos_suscritos": ["booking.confirmed"],
  "is_active": true
}
```

**Implementación:**

```python
# rest-service/app/routes/partners.py

@router.get("/partners/{partner_id}")
async def get_partner(partner_id: int, db: Session = Depends(get_db)):
    """Obtener partner por ID (sin exponer secret)."""
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404)
    
    # No devolver el secret en la respuesta pública
    return PartnerPublicResponse.from_orm(partner)
```

---

### 5. `POST /api/partners/register`

Registrar un nuevo partner.

**Usar para:** Admin - Registrar partner para integraciones

**Request:**
```json
{
  "nombre": "TourCompany Ltd",
  "webhook_url": "https://api.tourcompany.com/webhooks",
  "eventos_suscritos": ["booking.confirmed", "payment.success"],
  "descripcion": "Tours y excursiones"
}
```

**Response (201):**
```json
{
  "id": 1,
  "nombre": "TourCompany Ltd",
  "webhook_url": "https://...",
  "shared_secret": "your_secret_key",  // Comunicar de forma segura
  "is_active": true
}
```

---

### 6. `POST /api/partner-webhooks/log`

Registrar intento de webhook enviado a partner (para auditoría).

**Usar para:** Payment Handler - Registrar que se envió webhook

**Request:**
```json
{
  "partner_id": 1,
  "event_type": "booking.confirmed",
  "payload": {...},
  "hmac_signature": "sha256:abc123...",
  "http_status": 200,
  "response_body": "ack",
  "error_message": null,
  "retry_count": 0
}
```

**Response (201):**
```json
{
  "id": 1,
  "partner_id": 1,
  "event_type": "booking.confirmed",
  "status": "success",
  "created_at": "2026-01-23T14:30:00Z"
}
```

---

### 7. `POST /api/orders` (o equivalente)

Crear una orden/servicio cuando un partner envía un webhook.

**Usar para:** Partner Handler - Ejecutar acción de negocio

**Request:**
```json
{
  "booking_reference": "bk_001",
  "service": "tour",
  "provider": "partner_name",
  "amount": 50.00
}
```

**Response (201):**
```json
{
  "id": 1,
  "booking_reference": "bk_001",
  "order_id": "order_001"
}
```

---

### 8. `POST /api/reports/daily`

Generar reporte diario.

**Usar para:** Scheduled Tasks - Reporte diario

**Request:**
```json
{
  "date": "2026-01-23",
  "report_type": "bookings"
}
```

**Response (200):**
```json
{
  "date": "2026-01-23",
  "total_bookings": 45,
  "total_revenue": 5000.00,
  "report_url": "http://localhost:8000/reports/2026-01-23.pdf"
}
```

---

## 🟠 WebSocket Service (NestJS) - Obligatorio

### 1. `POST /api/webhooks/reserva-actualizada`

Recibir notificación de actualización y emitir por Socket.IO.

**Ya debe existir según [ReservasUleam2025/explicacion.md](ReservasUleam2025/explicacion.md#L90-L97)**

---

## 🟡 Payment Service (Python, FastAPI) - Obligatorio si existe

### 1. `POST /api/payments/{id}/confirm`

Confirmar pago recibido.

**Request:**
```json
{
  "payment_id": "pm_123abc",
  "status": "confirmed",
  "timestamp": "2026-01-23T14:30:00Z"
}
```

**Response (200):**
```json
{
  "id": 1,
  "payment_id": "pm_123abc",
  "status": "confirmed"
}
```

---

## 🟢 Opcionales pero Recomendados

### 1. `POST /api/admin/cleanup`

Limpieza de datos antiguos (para Scheduled Tasks).

```python
@router.post("/admin/cleanup", dependencies=[Depends(require_admin)])
async def cleanup_old_data(db: Session = Depends(get_db)):
    """Limpiar registros antiguos."""
    # Eliminar logs de hace >90 días
    db.query(EventLog).filter(
        EventLog.created_at < datetime.utcnow() - timedelta(days=90)
    ).delete()
    
    db.commit()
    return {"cleaned": True}
```

### 2. `POST /api/internal/send-email`

Enviar email desde n8n.

**Request:**
```json
{
  "to": "cliente@uleam.com",
  "subject": "Confirmación de Reserva",
  "template": "booking_confirmation",
  "variables": {
    "booking_id": "bk_001",
    "amount": 150.00
  }
}
```

---

## 📋 Implementación Checklist

- [ ] `POST /api/reservas/{id}/confirm` - activar reserva
- [ ] `GET /api/health` - health check
- [ ] `POST /api/webhooks/reserva-actualizada` - notificar WS
- [ ] `GET /api/partners/{id}` - obtener partner
- [ ] `POST /api/partners/register` - registrar partner
- [ ] `POST /api/partner-webhooks/log` - auditoría de webhooks
- [ ] `POST /api/orders` - crear orden desde partner
- [ ] `POST /api/reports/daily` - generar reporte
- [ ] `POST /api/payments/{id}/confirm` - confirmar pago (Payment Service)
- [ ] `POST /api/admin/cleanup` - limpieza (opcional)
- [ ] `POST /api/internal/send-email` - envío de emails (opcional)

---

## 🔒 Security Headers (Todos los Endpoints)

Todos los endpoints deben incluir estos headers en las respuestas:

```python
# Middleware en FastAPI
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

---

## 🔑 Autenticación

Endpoints sensibles deben validar JWT:

```python
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

@router.post("/api/reservas/{id}/confirm")
async def confirm_reservation(
    reserva_id: int,
    credentials: HTTPAuthCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    # Validar JWT
    token = credentials.credentials
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    # ... resto del código
```

---

## 🧪 Verificación en n8n

Antes de activar workflows, verificar que cada endpoint:

1. **Existe**: `curl http://localhost:8000/api/health`
2. **Responde**: Status 200, no 404
3. **Acepta method**: POST/GET según n8n
4. **Devuelve JSON**: Si n8n espera JSON
5. **Autentica**: Si requiere Authorization header

---

## 📊 Flujo de Datos Ejemplo

```
n8n Payment Handler
  ↓
POST /api/reservas/1/confirm
  ↓
REST valida pago
  ↓
REST actualiza BD
  ↓
REST responde 200 + reserva confirmada
  ↓
n8n sigue al siguiente nodo
  ↓
POST /api/webhooks/reserva-actualizada
  ↓
WS recibe notificación
  ↓
WS emite por Socket.IO
  ↓
Clientes conectados reciben en tiempo real ✅
```

---

## 📝 Estado Actual (Verificado)

✅ `POST /api/webhooks/*` - Ya existen en WebSocket service (vía [explicacion.md](explicacion.md))
⚠️  `POST /api/reservas/{id}/confirm` - Posible que exista, verificar
⚠️  `POST /api/partners/register` - Modelo Partner existe, endpoint falta
❓ Otros endpoints - Verificar en repo

**Recomendación:** Revisar archivos existentes antes de crear nuevos endpoints.
