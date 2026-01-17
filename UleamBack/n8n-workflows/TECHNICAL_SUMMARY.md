# 📊 Pilar 4: Resumen Técnico y Referencias

## 🎯 Objetivo del Pilar 4

Implementar n8n como **Event Bus centralizado** que orqueste:
1. Webhooks de pagos (Payment Handler)
2. Webhooks de partners (Partner Handler)
3. Mensajes de IA (MCP Input Handler)
4. Tareas programadas (Scheduled Tasks)

**Principio fundamental:** "Todo evento externo pasa por n8n"

---

## 📦 Estructura Entregada

```
n8n-workflows/
├── 📄 README.md                    ← Guía completa de instalación
├── 📄 QUICKSTART.md                ← Inicio rápido (5 minutos)
├── 📄 CONTRACT_EVENTS.md           ← Formato normalizado de eventos
├── 📄 ENDPOINTS_CONFIG.md          ← URLs y payloads de servicios
├── 📄 HMAC_UTILS.md                ← Cifrado y seguridad
├── 📄 REQUIRED_ENDPOINTS.md        ← Endpoints necesarios en servicios
├── 📄 DEMO_STEPS.md                ← Pasos para demostración
│
├── 📋 payment_handler.json         ← Workflow 1: Procesar pagos
├── 📋 partner_handler.json         ← Workflow 2: Webhooks de partners
├── 📋 mcp_input_handler.json       ← Workflow 3: Telegram/Email → AI
├── 📋 scheduled_tasks.json         ← Workflow 4: Tareas programadas
│
├── 📁 n8n-data/                    ← Almacenamiento local (auto-generado)
└── 🚀 run-n8n.ps1                  ← Script para ejecutar n8n
```

---

## 🚀 Instalación (3 pasos)

### 1. n8n ya está instalado globalmente
```
$ node --version
v22.21.0

$ npm list -g n8n
n8n@2.4.6
```

### 2. Navega a UleamBack y ejecuta
```powershell
cd C:\Users\ASUS\Desktop\ReservasUleam2026\ReservasUleam2025\UleamBack
.\run-n8n.ps1
```

### 3. Abre en navegador
```
http://localhost:5678
```

---

## 🔄 Los 4 Workflows

### 1️⃣ Payment Handler
**Objetivo:** Procesar pagos de inicio a fin

**Flujo:**
```
webhook (pago) 
  → validar 
  → activar reserva (REST) 
  → notificar WebSocket 
  → email 
  → webhook partner
```

**URL:** `http://localhost:5678/webhook/payment-handler`

**Trigger:** Webhook desde MockAdapter/Stripe/MercadoPago

**Nodos:**
- Webhook Trigger
- Validar Payload (JavaScript)
- HTTP: Activar Reserva
- HTTP: Notificar WebSocket
- Email (opcional)
- HTTP: Webhook Partner
- Log & Finish

---

### 2️⃣ Partner Handler
**Objetivo:** Procesar webhooks bidireccionales de otros grupos

**Flujo:**
```
webhook (partner) 
  → verificar HMAC 
  → normalizar evento 
  → ejecutar acción 
  → responder ACK
```

**URL:** `http://localhost:5678/webhook/partner-handler`

**Trigger:** Webhook desde otro grupo (tour comprado, servicio activado, etc.)

**Nodos:**
- Webhook Trigger
- Verificar HMAC-SHA256
- Normalizar Evento (mapear fields)
- HTTP: Ejecutar Acción
- ACK Response

---

### 3️⃣ MCP Input Handler (Opcional)
**Objetivo:** Procesar mensajes de IA desde Telegram/Email

**Flujo:**
```
mensaje Telegram 
  → extraer contenido 
  → procesar adjuntos 
  → enviar a AI 
  → responder por canal
```

**Trigger:** Mensaje en bot Telegram

**Estado:** Desactivado por defecto (activar si se usa Chat UI)

---

### 4️⃣ Scheduled Tasks
**Objetivo:** Tareas programadas automáticas

**Triggers:**
- Cron 1: Diariamente a las 23:59 (reporte diario)
- Cron 2: Cada 6 horas (health checks)

**Acciones:**
- Generar reporte (HTTP → REST)
- Health check a todos los servicios
- Enviar email con resultado
- Registrar logs

---

## 🔐 Seguridad: HMAC-SHA256

### Cálculo de Firma

```javascript
// n8n (Function node)
const crypto = require('crypto');
const secret = 'shared_secret_key';
const body = JSON.stringify(payload);
const signature = crypto
  .createHmac('sha256', secret)
  .update(body)
  .digest('hex');

const header = `sha256:${signature}`;
```

### Verificación

```javascript
// En n8n al recibir webhook
const crypto = require('crypto');
const expectedSignature = crypto
  .createHmac('sha256', secret)
  .update(JSON.stringify($input.body))
  .digest('hex');

const isValid = expectedSignature === $input.body.hmac_signature.split(':')[1];
if (!isValid) throw new Error('Invalid signature');
```

---

## 🌍 Endpoints Integrados

| Servicio | Endpoint | Método | Usado Por |
|----------|----------|--------|-----------|
| REST | `GET /api/health` | GET | Scheduled Tasks (health check) |
| REST | `POST /api/reservas/{id}/confirm` | POST | Payment Handler |
| REST | `POST /api/webhooks/reserva-actualizada` | POST | Payment Handler |
| REST | `GET /api/partners/{id}` | GET | Partner Handler (lookup) |
| REST | `POST /api/partners/register` | POST | Admin |
| REST | `POST /api/partner-webhooks/log` | POST | Payment Handler (auditoría) |
| REST | `POST /api/reports/daily` | POST | Scheduled Tasks |
| GraphQL | `/graphql` | POST | Queries/Mutations (futuro) |
| WebSocket | `POST /api/webhooks/*` | POST | Payment/Partner Handlers |
| Payment | `POST /api/payments/{id}/confirm` | POST | Payment Handler |

---

## 📋 Contrato Normalizado de Eventos

Todos los eventos en n8n deben tener esta estructura:

```json
{
  "event": "payment.success | booking.confirmed | tour.purchased",
  "source": "stripe | mock | partner_name",
  "timestamp": "2026-01-23T14:30:00Z",
  "trace_id": "unique_id_for_logging",
  "payload": { /* datos específicos */ },
  "partner_id": "uuid | null",
  "hmac_signature": "sha256:hash_value",
  "retry_count": 0
}
```

---

## 🧪 Testing Rápido

### Test 1: ¿n8n está corriendo?
```powershell
curl http://localhost:5678
```

### Test 2: Enviar webhook de pago
```powershell
$payload = @{
    event = "payment.success"
    source = "mock"
    timestamp = (Get-Date -AsUTC).ToString("yyyy-MM-ddTHH:mm:ssZ")
    trace_id = "test-" + [guid]::NewGuid()
    payload = @{ payment_id = "pm_test"; booking_id = 1; amount = 100 }
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

---

## 📊 Componentes Relacionados (Pilar 1, 2, 3)

### Pilar 1: Auth Service
- **Proporciona:** JWT tokens válidos
- **Necesario para:** n8n requiere JWT en headers de REST calls

### Pilar 2: Payment Service + Webhooks B2B
- **Webhook entrada:** MockAdapter → n8n Payment Handler
- **Webhook salida:** n8n → Partner registrado
- **Firma:** HMAC-SHA256 (implementada en n8n)

### Pilar 3: MCP AI Orchestrator
- **Integración:** n8n MCP Input Handler → AI Orchestrator API
- **Multimodal:** Texto, imágenes, PDFs procesadas por n8n antes de enviar a IA
- **Respuesta:** Telegram/Email feedback

### Pilar 1 (Previo): REST, GraphQL, WebSocket
- **REST:** CRUD, reservas, data
- **GraphQL:** Reportes y analytics
- **WebSocket:** Notificaciones en tiempo real (n8n notifica, WS emite)

---

## ✅ Checklist de Implementación

- [x] n8n instalado localmente
- [x] 4 workflows en JSON
- [x] Contrato de eventos definido
- [x] Utilidades HMAC documentadas
- [x] Endpoints configurados
- [x] Pasos de demo detallados
- [ ] **Endpoints en servicios (verificar/crear)**:
  - [ ] REST: `POST /api/reservas/{id}/confirm`
  - [ ] REST: `GET /api/partners/{id}`
  - [ ] REST: `POST /api/partners/register`
  - [ ] REST: `POST /api/partner-webhooks/log`
  - [ ] REST: `POST /api/reports/daily`
  - [ ] Payment: `POST /api/payments/{id}/confirm`
- [ ] Pruebas end-to-end
- [ ] Demo presentable

---

## 🐛 Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| n8n no inicia | `rm -Path $env:USERPROFILE\.n8n -Recurse`; `n8n start` |
| Puerto 5678 en uso | `$env:N8N_PORT = "5679"; n8n start` |
| Webhook no llega | Verificar firewall; test `curl http://localhost:5678` |
| HMAC inválido | Usar secret correcto; JSON sin espacios; SHA256 |
| REST no responde | Verificar REST está corriendo: `curl http://localhost:8000/api/health` |
| JWT expirado | Obtener nuevo token: `POST http://localhost:8000/api/auth/login` |

---

## 📚 Documentación Importante

| Documento | Propósito |
|-----------|----------|
| `README.md` | Guía completa (arquitectura, instalación, uso) |
| `QUICKSTART.md` | Inicio en 5 minutos |
| `DEMO_STEPS.md` | **Leer antes de presentar** - Demo paso-a-paso |
| `CONTRACT_EVENTS.md` | Formato de eventos (para partners y logs) |
| `ENDPOINTS_CONFIG.md` | URLs exactas, headers, payloads |
| `HMAC_UTILS.md` | Código para integrar en servicios |
| `REQUIRED_ENDPOINTS.md` | Checklist de endpoints a crear/verificar |

---

## 🎯 Próximos Pasos (Prioridad)

### 🔴 Crítico (Hoy)
1. Ejecutar n8n: `.\run-n8n.ps1`
2. Abrir UI: `http://localhost:5678`
3. Importar 4 workflows JSON
4. Verificar endpoints en REST (usar `REQUIRED_ENDPOINTS.md`)

### 🟠 Importante (Esta semana)
5. Crear endpoints faltantes en REST/Payment
6. Probar Payment Handler con webhook mock
7. Probar Partner Handler con partner simulado
8. Hacer Scheduled Tasks cron work

### 🟡 Mejoras (Si hay tiempo)
9. Integrar SMTP para emails reales
10. Configurar Telegram bot para MCP Input Handler
11. Añadir más health checks
12. Logging y auditoría avanzada

---

## 💾 Guardado y Entrega

### Archivos a entregar (YA LISTOS)
```
UleamBack/n8n-workflows/
├── payment_handler.json ✅
├── partner_handler.json ✅
├── mcp_input_handler.json ✅
├── scheduled_tasks.json ✅
├── *.md (6 documentos) ✅
└── run-n8n.ps1 ✅
```

### Base de datos
- Modelo `Partner` ya existe en payment-service
- Webhooks en REST/WS ya están implementados

### Código a crear (Opcional pero recomendado)
- Endpoints en REST para partners (POST /register, GET /{id})
- Endpoint en Payment para confirmar pago
- Utilidad HMAC en Payment service

---

## 🎓 Conceptos Clave

| Concepto | Explicación | Ejemplo |
|----------|-----------|---------|
| **Event Bus** | Sistema centralizado para procesar eventos | n8n recibe pago → procesa → notifica |
| **Webhook** | HTTP POST que dispara un proceso | Payment service → n8n |
| **HMAC** | Firma criptográfica para verificar origen | Partner A → n8n: `X-Hub-Signature` |
| **Normalización** | Convertir múltiples formatos a uno estándar | Stripe payload → contrato n8n |
| **Trace ID** | ID único para seguir evento de inicio a fin | UUID registrado en todos los logs |
| **Orchestration** | Coordinar múltiples servicios | n8n: valida → activa → notifica → firma |

---

## 📞 Preguntas Frecuentes

**¿n8n es obligatorio?**
Sí, es parte de Pilar 4 (15% de la nota).

**¿Puedo usar Docker en lugar de local?**
No (requisito del usuario: "local, no Docker").

**¿Qué pasa si un webhook falla?**
n8n reintentar (máx 3 veces) y registrar en logs.

**¿Debo implementar todos los endpoints ahora?**
No, hay templates. Prioridad: Payment Handler primero.

**¿MCP Input Handler es obligatorio?**
Opcional, pero recomendado si hay Chat UI.

---

## ✨ Estado Final

**Pilar 4 - n8n Event Bus:** ✅ **LISTO PARA IMPLEMENTAR**

- Todas las dependencias instaladas
- Documentación completa
- Workflows templates creados
- Guías de integración disponibles
- Ejemplos de código listos

**Próximo:** Ejecutar `.\run-n8n.ps1` y comenzar a trabajar con los workflows. 🚀
