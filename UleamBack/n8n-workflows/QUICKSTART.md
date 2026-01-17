# 🚀 n8n Pilar 4 - Quickstart Guide

## ¿Qué es esto?

Esta carpeta contiene la configuración completa del **Pilar 4: Event Bus n8n** para el proyecto ReservasULEAM.

Se incluyen:
- 4 workflows listos para importar a n8n
- Documentación técnica completa
- Guías de demo step-by-step
- Utilidades HMAC para seguridad

---

## ⚡ Inicio Rápido (5 minutos)

### 1️⃣ Asegurate que n8n está instalado

```powershell
# Verificar
node --version
npm list -g n8n
```

Si no está instalado:
```powershell
npm install -g n8n
```

### 2️⃣ Inicia n8n localmente

Desde la carpeta `UleamBack/`:

```powershell
.\run-n8n.ps1
```

O comando directo:
```powershell
$env:N8N_USER_FOLDER = ".\n8n-data"
n8n start
```

### 3️⃣ Abre n8n en el navegador

```
http://localhost:5678
```

Primera vez: crea usuario/contraseña

### 4️⃣ Importa los workflows

1. En el dashboard de n8n → **Import**
2. Selecciona cada archivo JSON:
   - `payment_handler.json`
   - `partner_handler.json`
   - `mcp_input_handler.json`
   - `scheduled_tasks.json`
3. Activa los workflows que necesites

### 5️⃣ Configura variables de entorno

En PowerShell, antes de iniciar n8n:

```powershell
$env:REST_JWT_TOKEN = "tu_jwt_token_aqui"
$env:PARTNER_SECRET = "shared_secret_del_partner"
$env:SMTP_HOST = "smtp.gmail.com"
$env:SMTP_USER = "noreply@uleam.com"
```

### 6️⃣ Prueba un webhook

```powershell
# Simular pago
curl -X POST http://localhost:5678/webhook/payment-handler `
  -H "Content-Type: application/json" `
  -d '{
    "event": "payment.success",
    "source": "mock",
    "timestamp": "2026-01-23T14:30:00Z",
    "trace_id": "test-001",
    "payload": {
      "payment_id": "pm_test",
      "booking_id": 1,
      "amount": 100
    }
  }'
```

✅ **¡Listo! n8n ya está recibiendo webhooks**

---

## 📂 Estructura de Archivos

```
n8n-workflows/
├── README.md                    ← Esta guía (pero más detallada)
├── QUICKSTART.md               ← Este archivo
├── CONTRACT_EVENTS.md          ← Contrato normalizado de eventos
├── ENDPOINTS_CONFIG.md         ← URLs y headers de los servicios
├── HMAC_UTILS.md               ← Utilidades de criptografía
├── DEMO_STEPS.md               ← Pasos completos de demostración
│
├── payment_handler.json        ← Workflow 1: Procesar pagos
├── partner_handler.json        ← Workflow 2: Webhooks de partners
├── mcp_input_handler.json      ← Workflow 3: Telegram/Email → AI
├── scheduled_tasks.json        ← Workflow 4: Tareas programadas
│
└── n8n-data/                   ← (Generado por n8n, ignorar)
```

---

## 🎯 Los 4 Workflows Explicados

### 1. Payment Handler
**¿Qué hace?**
Recibe webhook de pago → valida → activa reserva → notifica WebSocket → dispara webhook a partner

**Cuándo se dispara:** Al completar un pago en MockAdapter/Stripe

**URL:** `http://localhost:5678/webhook/payment-handler`

---

### 2. Partner Handler
**¿Qué hace?**
Recibe webhook de un partner → verifica HMAC → ejecuta acción de negocio → responde ACK

**Cuándo se dispara:** Cuando otro grupo envía un evento (ej: tour comprado)

**URL:** `http://localhost:5678/webhook/partner-handler`

---

### 3. MCP Input Handler (Opcional)
**¿Qué hace?**
Recibe mensaje Telegram/Email → extrae contenido → envía a AI Orchestrator → responde por el mismo canal

**Cuándo se dispara:** Usuario envía mensaje a bot Telegram

**URL:** Configurado en Telegram Bot settings

**Estado:** Desactivado por defecto (activar si usas Telegram)

---

### 4. Scheduled Tasks
**¿Qué hace?**
Tareas programadas: reporte diario, limpieza, health checks

**Cuándo se dispara:** 
- Reporte: Diariamente a las 23:59
- Health check: Cada 6 horas

**No necesita webhook**

---

## 🔐 Seguridad: HMAC-SHA256

Los webhooks entre partners se firman con **HMAC-SHA256** para verificar integridad.

### Generar Firma (Python)

```python
import hmac
import hashlib

secret = "partner_shared_secret"
payload = {"order_id": "order_001"}
body = str(payload)

signature = hmac.new(
    secret.encode(),
    body.encode(),
    hashlib.sha256
).hexdigest()

print(f"sha256:{signature}")
```

### Verificar Firma (n8n - JavaScript)

```javascript
const crypto = require('crypto');

const signature = "sha256:abcd1234...";
const secret = process.env.PARTNER_SECRET;
const body = JSON.stringify(payload);

const expected = crypto
  .createHmac('sha256', secret)
  .update(body)
  .digest('hex');

const isValid = expected === signature.split(':')[1];
```

---

## 🔗 Endpoints Críticos

| Servicio | URL | Método | Descripción |
|----------|-----|--------|-------------|
| REST | http://localhost:8000/api | GET/POST | CRUD reservas, pagos |
| GraphQL | http://localhost:8080/graphql | POST | Reportes y analytics |
| WebSocket | http://localhost:3001 | WS/HTTP | Notificaciones en tiempo real |
| n8n | http://localhost:5678 | - | Event Bus y workflows |

---

## 📝 Flujo Completo (End-to-End)

```
1. Cliente paga en frontend
   ↓
2. Payment Service envía webhook a n8n (payment_handler)
   ↓
3. n8n valida pago
   ↓
4. n8n activa reserva en REST API
   ↓
5. n8n notifica WebSocket
   ↓
6. WebSocket emite a clientes conectados
   ↓
7. n8n envía webhook firmado a partner
   ↓
8. Partner recibe en su webhook y responde ACK
   ↓
9. n8n registra resultado
   ↓
✅ Cliente ve confirmación en tiempo real
```

---

## 🧪 Comandos de Prueba Útiles

### Test 1: ¿Está n8n corriendo?

```powershell
curl http://localhost:5678
```

### Test 2: Enviar webhook de pago

```powershell
$payload = @{
    event = "payment.success"
    source = "mock"
    timestamp = (Get-Date -AsUTC).ToString("yyyy-MM-ddTHH:mm:ssZ")
    trace_id = "test-" + (Get-Random)
    payload = @{
        payment_id = "pm_test"
        booking_id = 1
        amount = 100
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5678/webhook/payment-handler" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body $payload
```

### Test 3: Verificar REST está disponible

```powershell
curl http://localhost:8000/api/health
```

### Test 4: Ver workflows en n8n

```powershell
curl http://localhost:5678/api/workflows
```

---

## ❌ Problemas Comunes

### ❓ "n8n no inicia"

```powershell
# Limpiar caché
Remove-Item -Path "$env:USERPROFILE\.n8n" -Recurse -Force

# Reintentar
n8n start
```

### ❓ "Puerto 5678 en uso"

```powershell
# Cambiar puerto
$env:N8N_PORT = "5679"
n8n start
```

### ❓ "Webhook no llega a n8n"

1. Verificar que n8n está corriendo: `curl http://localhost:5678`
2. Verificar firewall de Windows
3. Revisar URL exacta del webhook en n8n (tab Webhook)

### ❓ "HMAC signature inválido"

1. Asegurar que el secret es correcto (sin espacios)
2. Usar `JSON.stringify()` sin espacios en el body
3. Algoritmo debe ser SHA256 (no SHA1 u otro)

---

## 📚 Documentación Completa

- **`README.md`**: Guía detallada de instalación y uso
- **`CONTRACT_EVENTS.md`**: Definición del formato de eventos normalizados
- **`ENDPOINTS_CONFIG.md`**: URLs exactas y payloads de ejemplo
- **`HMAC_UTILS.md`**: Código de cifrado en Python, TypeScript, JavaScript
- **`DEMO_STEPS.md`**: Pasos paso-a-paso para demostración en vivo

---

## 🎁 Checklist Pre-Demo

- [ ] n8n corriendo en `http://localhost:5678`
- [ ] REST API corriendo en `http://localhost:8000`
- [ ] GraphQL corriendo en `http://localhost:8080`
- [ ] WebSocket corriendo en `http://localhost:3001`
- [ ] 4 workflows importados en n8n
- [ ] Variables de entorno configuradas
- [ ] Partners registrados en BD
- [ ] JWT token obtenido

---

## 🚀 Próximos Pasos

1. **Leer `README.md`** para entender arquitectura completa
2. **Abrir `DEMO_STEPS.md`** para hacer demo en vivo
3. **Revisar `CONTRACT_EVENTS.md`** para entender payloads
4. **Copiar código de `HMAC_UTILS.md`** a tus servicios (REST, Payment)
5. **Activar workflows** en n8n y probar

---

## 📞 Soporte

Si algo no funciona:

1. Revisar logs en n8n (tab "Execution")
2. Verificar que todos los servicios están corriendo
3. Revisar firewall de Windows
4. Comprobar que los JWTs no han expirado
5. Consultar `DEMO_STEPS.md` para troubleshooting específico

---

## ✅ Completado en Pilar 4

- ✅ n8n instalado localmente
- ✅ 4 workflows definidos en JSON
- ✅ Contrato de eventos normalizado
- ✅ Utilidades HMAC documentadas
- ✅ Endpoints configurados
- ✅ Pasos de demo completos
- ✅ Documentación lista

**¡Listo para empezar! 🎉**
