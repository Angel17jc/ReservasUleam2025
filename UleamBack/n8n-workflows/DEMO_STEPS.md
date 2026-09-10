# Demo Steps - Pilar 4: n8n Event Bus

## 🎯 Objetivo

Demostrar el flujo completo end-to-end del Event Bus n8n:
1. Webhook de pago entra a n8n
2. n8n valida, activa reserva, notifica WebSocket
3. n8n dispara webhook a partner
4. Partner responde con ACK

---

## 📋 Requisitos Previos

- [ ] n8n ejecutando en `http://localhost:5678`
- [ ] REST API ejecutando en `http://localhost:8000`
- [ ] GraphQL ejecutando en `http://localhost:8080`
- [ ] WebSocket ejecutando en `http://localhost:3001`
- [ ] Payment Service ejecutando (o MockAdapter disponible)
- [ ] Base de datos con tablas de partners y pagos
- [ ] JWT_TOKEN válido (obtenido de login)
- [ ] Partner registrado en BD con secret compartido

---

## 🚀 Demo 1: Payment Handler Flow

### Paso 1: Obtener JWT Token

```powershell
# Login en el sistema
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" `
  -Method POST `
  -Headers @{"Content-Type" = "application/json"} `
  -Body (@{
    email = "admin@uleam.com"
    password = "admin123"
  } | ConvertTo-Json)

$jwt = $response.access_token
Write-Host "JWT Token: $jwt" -ForegroundColor Green
```

### Paso 2: Crear una Reserva (preparación)

```powershell
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/reservas" `
  -Method POST `
  -Headers @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $jwt"
  } `
  -Body (@{
    customer_id = 1
    espacio_id = 1
    fecha_inicio = "2026-02-01"
    fecha_fin = "2026-02-05"
    numero_huespedes = 2
    estado_reserva = 1
  } | ConvertTo-Json)

$booking_id = $response.id
Write-Host "Booking ID: $booking_id" -ForegroundColor Green
```

### Paso 3: Abrir n8n y Crear el Payment Handler Workflow

1. Ir a `http://localhost:5678`
2. Crear nuevo workflow
3. Agregar nodo **Webhook** (trigger)
   - HTTP method: POST
   - Path: `/webhook/payment-handler`
4. Agregar nodo **Code** (validación) con el código del contrato
5. Agregar nodos **HTTP Request** para:
   - Activar reserva
   - Notificar WebSocket
6. Guardar y activar el workflow

### Paso 4: Simular Webhook de Pago

```powershell
# Obtener la URL del webhook de n8n
$webhookUrl = "http://localhost:5678/webhook/payment-handler"

# Crear payload de pago
$payload = @{
  event = "payment.success"
  source = "mock"
  timestamp = (Get-Date -AsUTC).ToString("yyyy-MM-ddTHH:mm:ssZ")
  trace_id = "pay-demo-001"
  payload = @{
    payment_id = "pm_demo_123"
    amount = 150.00
    currency = "USD"
    booking_id = $booking_id
    customer_id = 1
    customer_email = "cliente@uleam.com"
  }
} | ConvertTo-Json

# Enviar webhook a n8n
Invoke-RestMethod -Uri $webhookUrl `
  -Method POST `
  -Headers @{"Content-Type" = "application/json"} `
  -Body $payload

Write-Host "✅ Webhook enviado a n8n" -ForegroundColor Green
```

### Paso 5: Verificar Ejecución

1. En n8n, ver el ejecutions log
2. Verificar que cada nodo ejecutó correctamente
3. Revisar en REST que la reserva está confirmada:

```powershell
$reserva = Invoke-RestMethod -Uri "http://localhost:8000/api/reservas/$booking_id" `
  -Headers @{"Authorization" = "Bearer $jwt"}

Write-Host "Estado de reserva: $($reserva.estado_reserva)" -ForegroundColor Green
```

---

## 🎯 Demo 2: Partner Handler Flow

### Paso 1: Registrar un Partner

```powershell
# Registrar partner en BD
$partnerPayload = @{
  nombre = "TourCompany Ltd"
  webhook_url = "http://localhost:5678/webhook/partner-response"  # URL para recibir respuesta
  eventos_suscritos = @("booking.confirmed", "payment.success")
  descripcion = "Tours y excursiones"
} | ConvertTo-Json

$partner = Invoke-RestMethod -Uri "http://localhost:8000/api/partners/register" `
  -Method POST `
  -Headers @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $jwt"
  } `
  -Body $partnerPayload

$partner_id = $partner.id
$partner_secret = $partner.shared_secret

Write-Host "Partner registrado: $partner_id" -ForegroundColor Green
Write-Host "Secret: $partner_secret" -ForegroundColor Yellow
```

### Paso 2: Crear Partner Handler Workflow en n8n

1. Crear nuevo workflow
2. Agregar nodo **Webhook** con path: `/webhook/partner-handler`
3. Agregar nodo **Code** para verificar HMAC
4. Agregar nodo **Code** para normalizar evento
5. Agregar nodo **HTTP Request** para ejecutar acción
6. Guardar y activar

### Paso 3: Simular Webhook desde Partner

```powershell
# Generar HMAC-SHA256
$secret = $partner_secret
$eventPayload = @{
  order_id = "order_001"
  booking_reference = "bk_001"
  tour_package = "island_tour"
  participants = 4
  price = 50.00
}

$jsonBody = $eventPayload | ConvertTo-Json -Compress
$bytes = [System.Text.Encoding]::UTF8.GetBytes($jsonBody)

# Usar .NET para HMAC (PowerShell 7+)
$hmac = [System.Security.Cryptography.HMACSHA256]::new([System.Text.Encoding]::UTF8.GetBytes($secret))
$hash = $hmac.ComputeHash($bytes)
$signature = "sha256:" + [System.BitConverter]::ToString($hash).Replace("-", "").ToLower()

# Envelope del webhook
$envelope = @{
  event = "tour.purchased"
  source = "partner_hotel_group"
  timestamp = (Get-Date -AsUTC).ToString("yyyy-MM-ddTHH:mm:ssZ")
  partner_id = $partner_id
  hmac_signature = $signature
  trace_id = "tour-demo-001"
  payload = $eventPayload
} | ConvertTo-Json

# Enviar a n8n
Invoke-RestMethod -Uri "http://localhost:5678/webhook/partner-handler" `
  -Method POST `
  -Headers @{
    "Content-Type" = "application/json"
    "X-Hub-Signature" = $signature
  } `
  -Body $envelope

Write-Host "✅ Webhook desde partner enviado a n8n" -ForegroundColor Green
```

### Paso 4: Verificar ACK y Acción

1. Ver en n8n que la ejecución fue exitosa
2. Verificar en REST que la acción se ejecutó (orden creada, etc.)

---

## 🔧 Demo 3: Scheduled Tasks

### Paso 1: Crear Workflow de Scheduled Tasks

1. Crear nuevo workflow
2. Agregar 2 nodos **Cron**:
   - Cron 1: Cada día a las 23:59 (reporte diario)
   - Cron 2: Cada 6 horas (health check)
3. Agregar nodos **Code** para generar tareas
4. Agregar nodos **HTTP Request** para ejecutar
5. Guardar y activar

### Paso 2: Probar Manualmente (sin esperar al Cron)

1. En n8n, hacer click en "Execute Workflow"
2. Verificar en logs que los health checks se ejecutaron
3. Revisar que el reporte se generó:

```powershell
# Ver reporte del día
$report = Invoke-RestMethod -Uri "http://localhost:8000/api/reports/daily" `
  -Headers @{"Authorization" = "Bearer $jwt"}

Write-Host "Reporte generado: $report" -ForegroundColor Green
```

---

## ✅ Checklist de Demo Completa

- [ ] **Payment Handler**:
  - [ ] Webhook de pago entra correctamente
  - [ ] Validación pasa
  - [ ] Reserva se activa (estado = confirmed)
  - [ ] WebSocket notifica
  - [ ] Logs registran trace_id

- [ ] **Partner Handler**:
  - [ ] Webhook desde partner llega
  - [ ] HMAC se verifica correctamente
  - [ ] Evento se normaliza
  - [ ] Acción de negocio se ejecuta
  - [ ] ACK se responde

- [ ] **Scheduled Tasks**:
  - [ ] Reporte diario se genera
  - [ ] Health checks pasan
  - [ ] Emails se envían (o logs muestran intento)

- [ ] **Integración General**:
  - [ ] Flujo end-to-end funciona
  - [ ] No hay errores 500
  - [ ] Trace IDs aparecen en todas partes
  - [ ] Base de datos se actualiza correctamente

---

## 📸 Screenshots Esperados

### n8n Payment Handler Ejecución
- ✅ Webhook recibido
- ✅ Validación pasó
- ✅ HTTP calls ejecutados
- ✅ Status: success

### REST API Reserva Actualizada
```json
{
  "id": 1,
  "booking_id": "bk_001",
  "status": "confirmed",
  "payment_id": "pm_demo_123",
  "confirmed_at": "2026-01-23T14:30:00Z"
}
```

### WebSocket Notificación
Canal: `reservas:actualizar`
Evento: `reserva-actualizada`
Datos: booking_id, status, timestamp

---

## 🐛 Troubleshooting

| Problema | Solución |
|----------|----------|
| Webhook no llega a n8n | Verificar que n8n está corriendo; revisar firewall; probar URL con `curl` |
| HMAC signature inválido | Asegurar secret es correcto; usar `JSON.stringify()` sin espacios |
| HTTP Request falla | Verificar que REST/WS está disponible; revisar JWT token |
| Reporte no se genera | Verificar endpoint `/api/reports/daily` existe; revisar permisos |
| Partner webhook no se dispara | Verificar URL del partner es correcta; revisar timeout |

---

## 📝 Logs a Revisar

```powershell
# n8n logs (si estuviera en Docker)
# docker logs n8n_uleam

# REST API logs (si lo especifican)
# tail -f UleamBack/rest-service/logs/app.log

# Verificar event_logs en BD
Invoke-RestMethod -Uri "http://localhost:8000/api/admin/event-logs" `
  -Headers @{"Authorization" = "Bearer $jwt"}
```

---

## 🎁 Entregables Finales

1. ✅ 4 Workflows en JSON (payment, partner, mcp, scheduled)
2. ✅ Contrato de eventos (CONTRACT_EVENTS.md)
3. ✅ Utilidades HMAC (HMAC_UTILS.md)
4. ✅ Configuración de endpoints (README.md)
5. ✅ Este documento (DEMO_STEPS.md)
6. ✅ README con instrucciones de setup local
