# 🤝 INTEGRACIÓN B2B CORRECTA - Pilar 2 Payment Service

**Estado**: En Configuración  
**Servicio**: payment-service (Puerto 8001)

---

## ✅ ACLARACIÓN IMPORTANTE

La integración B2B **DEBE estar en payment-service** (Pilar 2), NO en rest-service.

### Por qué payment-service:
- ✅ Ya tiene infraestructura completa de webhooks bidireccionales
- ✅ Ya implementa HMAC-SHA256 para seguridad
- ✅ Ya tiene registro de partners con API keys
- ✅ Ya tiene endpoints `/partners` y `/partners/webhook`
- ✅ Ya cumple con todos los requisitos del Pilar 2

### Arquitectura Correcta:

```
┌─────────────────────────────────────────────────────────────────┐
│  EQUIPO A: Recomendaciones Turísticas                           │
│  URL: https://unfulminated-charley-airtightly.ngrok-free.dev   │
│                                                                  │
│  Envía eventos:                                                  │
│  - tour.purchased                                                │
│  - booking.confirmed                                             │
│  - recommendation.created                                        │
└───────────────────────────┬──────────────────────────────────────┘
                            │ HTTP + HMAC-SHA256
                            │
┌───────────────────────────┴──────────────────────────────────────┐
│  PAYMENT-SERVICE (NOSOTROS) - Puerto 8001                       │
│                                                                  │
│  INBOUND:  POST /api/v1/partners/webhook                        │
│  ├─ Recibe eventos del Equipo A                                 │
│  ├─ Valida X-Api-Key + X-Webhook-Signature (HMAC)              │
│  └─ Procesa: tour.purchased, booking.confirmed, etc.            │
│                                                                  │
│  OUTBOUND: Envía a Equipo A cuando:                             │
│  ├─ payment.success (pago exitoso)                              │
│  ├─ payment.failed (pago fallido)                               │
│  ├─ booking.confirmed (reserva confirmada)                      │
│  └─ service.activated (servicio activado)                       │
│                                                                  │
│  Registro: POST /api/v1/partners                                │
│  └─ Genera API key + secret para Equipo A                       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📋 Checklist de Configuración

### 1. Pre-requisitos
- [ ] payment-service corriendo en puerto 8001
- [ ] Base de datos payment_db activa
- [ ] Tabla `partner` creada (migrations aplicadas)
- [ ] ngrok exponiendo payment-service (si es necesario)

### 2. Registrar Equipo A como Partner
- [ ] Ejecutar script `register_equipo_a.py`
- [ ] Guardar API key y secret generados
- [ ] Compartir credenciales con Equipo A
- [ ] Recibir credenciales del Equipo A

### 3. Configurar Webhooks OUTBOUND
- [ ] Configurar URL del Equipo A en BD
- [ ] Configurar eventos a enviar
- [ ] Probar envío de webhook de prueba

### 4. Probar Webhooks INBOUND
- [ ] Equipo A envía webhook de prueba
- [ ] Validar firma HMAC
- [ ] Verificar procesamiento correcto

---

## 🚀 Pasos para Iniciar

### Paso 1: Iniciar payment-service

```powershell
cd C:\ReservasUleam2025\UleamBack\payment-service

# Verificar que esté el .env con DATABASE_URL
# DATABASE_URL=postgresql://user:pass@localhost:5432/payment_db

# Activar entorno virtual
C:\ReservasUleam2025\.venv-1\Scripts\Activate.ps1

# Aplicar migraciones (si es necesario)
alembic upgrade head

# Iniciar servicio
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Verificar que funciona**:
```powershell
curl http://localhost:8001/health
# Esperado: {"status": "healthy"}

curl http://localhost:8001/docs
# Abre Swagger UI
```

---

### Paso 2: Registrar Equipo A

```powershell
cd C:\ReservasUleam2025\UleamBack\payment-service
python register_equipo_a.py
```

**Esto genera**:
- API Key para el Equipo A
- Secret Key para firmar webhooks
- Registro en tabla `partner`

**Output esperado**:
```
[EXITO] Partner registrado correctamente

Partner ID: 1
API Key: pk_partner_abc123xyz...
Secret Key: sk_secret_def456uvw...

Webhook URL: https://unfulminated-charley-airtightly.ngrok-free.dev/api/reservas
```

---

### Paso 3: Compartir con Equipo A

**Enviar este mensaje al Equipo A**:

```
Hola Equipo A,

Ya registramos su sistema como partner en nuestro payment-service.

Para enviarnos webhooks, usar:

Endpoint: https://TU_NGROK_PAYMENT/api/v1/partners/webhook

Headers requeridos:
  X-Api-Key: [API_KEY_GENERADA]
  X-Webhook-Signature: [HMAC-SHA256 del payload usando SECRET]
  X-Webhook-Timestamp: [Unix timestamp]

Secret para generar HMAC: [SECRET_KEY_GENERADA]

Eventos que pueden enviarnos:
  - tour.purchased
  - booking.confirmed
  - service.activated
  - booking.cancelled

Formato del payload:
{
  "event_type": "tour.purchased",
  "event_id": "evt_unique_id",
  "timestamp": 1737336000,
  "booking_id": "tour_123",
  "amount": 120.00,
  "currency": "USD",
  "metadata": {
    "user_email": "user@example.com",
    "tour_name": "Tour Manta City"
  }
}

¿Pueden compartirnos sus credenciales también?

Saludos,
Equipo B - ULEAM Payment Service
```

---

### Paso 4: Recibir Credenciales del Equipo A

Cuando el Equipo A te envíe sus credenciales, configurar en payment-service:

1. **Actualizar el partner en BD**:
```sql
UPDATE partner
SET 
  equipo_a_api_key = '[SU_API_KEY]',
  equipo_a_secret = '[SU_SECRET]'
WHERE id = 1;
```

2. **O usar el endpoint de actualización**:
```powershell
curl -X PATCH http://localhost:8001/api/v1/partners/1 \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://unfulminated-charley-airtightly.ngrok-free.dev/api/reservas",
    "metadata": {
      "equipo_a_api_key": "[SU_API_KEY]",
      "equipo_a_secret": "[SU_SECRET]"
    }
  }'
```

---

## 🧪 Testing de Integración

### Test 1: Health Check

```powershell
# Payment service local
curl http://localhost:8001/health

# Payment service público (si tienes ngrok)
curl https://tu-ngrok-payment.ngrok-free.dev/health
```

---

### Test 2: Listar Partners

```powershell
curl http://localhost:8001/api/v1/partners
```

Debe mostrar al Equipo A registrado.

---

### Test 3: Webhook INBOUND (A → B)

**Crear script de prueba** `test_inbound_from_equipo_a.py`:

```python
import requests
import hmac
import hashlib
import json
import time

PAYMENT_SERVICE_URL = "http://localhost:8001"
API_KEY = "[API_KEY_DEL_EQUIPO_A]"  # La que generaste
SECRET = "[SECRET_DEL_EQUIPO_A]"    # La que generaste

payload = {
    "event_type": "tour.purchased",
    "event_id": "evt_test_001",
    "timestamp": int(time.time()),
    "booking_id": "tour_123",
    "amount": 120.00,
    "currency": "USD",
    "metadata": {
        "user_email": "test@uleam.edu.ec",
        "tour_name": "Tour Manta City - Test"
    }
}

# Generar firma HMAC
payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
signature = hmac.new(
    SECRET.encode(),
    payload_str.encode(),
    hashlib.sha256
).hexdigest()

# Enviar webhook
response = requests.post(
    f"{PAYMENT_SERVICE_URL}/api/v1/partners/webhook",
    json=payload,
    headers={
        "X-Api-Key": API_KEY,
        "X-Webhook-Signature": signature,
        "X-Webhook-Timestamp": str(payload["timestamp"])
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

**Ejecutar**:
```powershell
python test_inbound_from_equipo_a.py
```

**Esperado**:
```
Status: 200
Response: {"status": "success", "event_id": "evt_test_001"}
```

---

### Test 4: Webhook OUTBOUND (B → A)

**Usar endpoint de test del payment-service**:

```powershell
curl -X POST http://localhost:8001/api/v1/webhooks/test/partner/1
```

Esto envía un webhook de prueba al Equipo A.

**Verificar en logs del Equipo A** que recibieron el webhook.

---

## 📊 Endpoints del Payment Service

### Gestión de Partners

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/partners` | Registrar nuevo partner |
| GET | `/api/v1/partners` | Listar partners |
| GET | `/api/v1/partners/{id}` | Obtener partner |
| PATCH | `/api/v1/partners/{id}` | Actualizar partner |
| DELETE | `/api/v1/partners/{id}` | Eliminar partner |

### Webhooks INBOUND

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/partners/webhook` | Recibir webhook de partner |
| GET | `/api/v1/partners/webhook/events` | Eventos soportados |

### Webhooks OUTBOUND

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/webhooks/test/partner/{id}` | Enviar webhook de prueba |

---

## 🔐 Seguridad HMAC

### Generar Firma (Para enviar a partner):

```python
import hmac
import hashlib
import json

def generate_hmac(payload_dict, secret):
    # Serializar payload consistentemente
    payload_str = json.dumps(payload_dict, sort_keys=True, separators=(',', ':'))
    
    # Generar HMAC-SHA256
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature

# Uso
payload = {"event_type": "payment.success", "amount": 100}
secret = "sk_secret_xyz"
signature = generate_hmac(payload, secret)
```

### Verificar Firma (Al recibir de partner):

```python
def verify_hmac(payload_dict, signature_received, secret):
    expected = generate_hmac(payload_dict, secret)
    
    # Comparación timing-safe
    return hmac.compare_digest(expected, signature_received)
```

---

## 📞 Troubleshooting

### Error: "Partner not found"
**Causa**: El partner no está registrado  
**Solución**: Ejecutar `register_equipo_a.py`

### Error: "Invalid signature"
**Causa**: La firma HMAC no coincide  
**Solución**:
- Verificar que usen el mismo secret
- Verificar que la serialización del payload sea idéntica
- Usar `sort_keys=True` y `separators=(',', ':')`

### Error: "Timestamp too old/new"
**Causa**: El timestamp está fuera del rango permitido (±5 min)  
**Solución**: Sincronizar relojes del sistema

### Error: "Connection refused"
**Causa**: payment-service no está corriendo  
**Solución**: `uvicorn app.main:app --port 8001 --reload`

---

## ✅ Resumen

1. **payment-service** es el servicio correcto para B2B (Pilar 2)
2. Ya tiene toda la infraestructura implementada
3. Solo falta:
   - Iniciar payment-service
   - Registrar Equipo A
   - Intercambiar credenciales
   - Probar webhooks bidireccionales

---

## 📄 Archivos Importantes

- `app/routes/partners.py` - Gestión de partners
- `app/routes/partners_webhook.py` - Webhooks INBOUND
- `app/services/partner_service.py` - Lógica de negocio
- `app/services/hmac_service.py` - Seguridad HMAC
- `B2B_INTEGRATION_GUIDE.md` - Guía completa
- `register_equipo_a.py` - Script de registro

---

🚀 **SIGUIENTE ACCIÓN**: Iniciar payment-service en puerto 8001 y ejecutar `register_equipo_a.py`
