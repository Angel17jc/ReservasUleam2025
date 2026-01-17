# 📑 Índice Completo - Pilar 4: n8n Event Bus

## 🎯 ¿De Qué Trata Este Pilar?

**Pilar 4 (15% de la nota):** Implementar n8n como **Event Bus centralizado** que orqueste:
- Webhooks de pagos
- Webhooks bidireccionales con partners
- Mensajes de IA desde Telegram/Email
- Tareas programadas (cron)

**Principio:** "Todo evento externo pasa por n8n"

---

## 📂 Archivos Entregados (11 archivos)

### 🚀 Ejecución y Setup
1. **run-n8n.ps1** - Script PowerShell para ejecutar n8n localmente
   - Configura variables de entorno
   - Usa carpeta `n8n-data/` para persistencia

### 📋 Workflows (4 Archivos JSON)
2. **payment_handler.json** - Procesar pagos de inicio a fin
   - Webhook → Validar → Activar reserva → Notificar WS → Email → Partner
   
3. **partner_handler.json** - Webhooks bidireccionales de otros grupos
   - Recibir → Verificar HMAC → Normalizar → Ejecutar acción → ACK
   
4. **mcp_input_handler.json** - Mensajes de IA (Telegram/Email)
   - Mensaje → Extraer adjuntos → Enviar a AI → Responder
   - Estado: **Desactivado por defecto**
   
5. **scheduled_tasks.json** - Tareas programadas
   - Cron diario (reporte 23:59)
   - Cron cada 6h (health checks)

### 📚 Documentación (7 Archivos Markdown)

#### Inicio Rápido
6. **QUICKSTART.md** ⭐ **LEER PRIMERO** (5 minutos)
   - Cómo instalar y ejecutar n8n
   - Comandos de prueba
   - Troubleshooting básico

#### Guía Completa
7. **README.md** - Documentación detallada
   - Instalación completa (npm, global, ejecutable)
   - Variables de entorno
   - Estructura de carpetas
   - Troubleshooting avanzado

#### Especificación Técnica
8. **CONTRACT_EVENTS.md** - Formato normalizado de eventos
   - Estructura base de todo evento en n8n
   - Campos obligatorios y opcionales
   - Ejemplos por tipo de evento (payment, booking, tour, scheduled)
   - Cálculo de HMAC
   - Testing con curl

9. **ENDPOINTS_CONFIG.md** - URLs y configuración de servicios
   - Endpoints de REST, GraphQL, WebSocket, Payment
   - Headers requeridos
   - Ejemplos de payloads
   - Testeo desde n8n

10. **HMAC_UTILS.md** - Cifrado y seguridad
    - Código Python, TypeScript, JavaScript
    - Generar firmas HMAC-SHA256
    - Verificar firmas
    - Implementación en n8n (Function nodes)
    - Testing local

#### Implementación y Demo
11. **REQUIRED_ENDPOINTS.md** - Endpoints necesarios en servicios
    - Checklist de endpoints a crear/verificar
    - Código FastAPI de ejemplo
    - Endpoints existentes vs. faltantes
    - Autenticación y headers de seguridad

12. **DEMO_STEPS.md** ⭐ **LEER ANTES DE PRESENTAR**
    - Demo paso-a-paso (30-45 minutos)
    - 3 demos: Payment Handler, Partner Handler, Scheduled Tasks
    - Código de prueba en PowerShell
    - Verificación de resultados
    - Troubleshooting

#### Resumen Ejecutivo
13. **TECHNICAL_SUMMARY.md** - Resumen técnico
    - Objetivos del Pilar 4
    - Estructura entregada
    - Los 4 workflows explicados
    - Seguridad (HMAC)
    - Endpoints integrados
    - Checklist de implementación
    - Próximos pasos con prioridades
    - FAQ

---

## 🚀 ¿Cómo Empezar? (Paso-a-Paso)

### Paso 1: Instalar (YA HECHO)
```powershell
# n8n está instalado globalmente
npm list -g n8n  # Verificar

# Resultado esperado: n8n@2.4.6
```

### Paso 2: Ejecutar n8n
```powershell
cd C:\Users\ASUS\Desktop\ReservasUleam2026\ReservasUleam2025\UleamBack
.\run-n8n.ps1
```

Abre en navegador: `http://localhost:5678`

### Paso 3: Importar Workflows
1. Dashboard → Import
2. Selecciona:
   - `payment_handler.json`
   - `partner_handler.json`
   - `scheduled_tasks.json`
   - `mcp_input_handler.json` (opcional)

### Paso 4: Configurar Variables
```powershell
# Antes de levantar n8n, configura:
$env:REST_JWT_TOKEN = "tu_jwt_token"
$env:PARTNER_SECRET = "shared_secret"
```

### Paso 5: Probar
```powershell
# Enviar webhook de prueba
$payload = @{
    event = "payment.success"
    source = "mock"
    timestamp = (Get-Date -AsUTC).ToString("yyyy-MM-ddTHH:mm:ssZ")
    trace_id = "test-001"
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

---

## 📖 Flujo de Lectura Recomendado

| # | Documento | Propósito | Tiempo |
|---|-----------|----------|--------|
| 1 | **QUICKSTART.md** | Entender n8n y empezar | 5 min |
| 2 | **TECHNICAL_SUMMARY.md** | Visión general de Pilar 4 | 10 min |
| 3 | **README.md** | Detalles de instalación | 10 min |
| 4 | **CONTRACT_EVENTS.md** | Formato de eventos | 15 min |
| 5 | **ENDPOINTS_CONFIG.md** | URLs de servicios | 10 min |
| 6 | **HMAC_UTILS.md** | Seguridad (si necesitas implementar) | 10 min |
| 7 | **DEMO_STEPS.md** | Pasos de demo (ANTES de presentar) | 30 min |
| 8 | **REQUIRED_ENDPOINTS.md** | Verificar endpoints (si hay falta) | 15 min |

---

## 🎯 Los 4 Workflows Explicados Rápido

```
┌─────────────────────────────────────────────────────────────┐
│ WORKFLOW 1: PAYMENT HANDLER                                 │
├─────────────────────────────────────────────────────────────┤
│ webhook (pago) → validar → activar reserva → WS → email    │
│                                           → partner webhook │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ WORKFLOW 2: PARTNER HANDLER                                 │
├─────────────────────────────────────────────────────────────┤
│ webhook (partner) → HMAC ✓ → normalizar → acción → ACK    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ WORKFLOW 3: MCP INPUT HANDLER (Opcional)                    │
├─────────────────────────────────────────────────────────────┤
│ Telegram/Email → adjuntos → AI Orchestrator → respuesta    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ WORKFLOW 4: SCHEDULED TASKS                                 │
├─────────────────────────────────────────────────────────────┤
│ Cron 23:59 → reporte diario                                 │
│ Cron 6h → health checks (REST, GraphQL, WS, Payment)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Seguridad: HMAC-SHA256 (Resumen)

Todos los webhooks entre partners se firman con HMAC-SHA256:

```javascript
// Generar firma
const crypto = require('crypto');
const secret = "partner_shared_secret";
const payload = { event: "booking.confirmed", booking_id: 1 };
const body = JSON.stringify(payload);
const signature = crypto
  .createHmac('sha256', secret)
  .update(body)
  .digest('hex');

// Header: X-Hub-Signature: sha256:abcd1234...
```

Ver `HMAC_UTILS.md` para código completo en Python, TypeScript, JavaScript.

---

## 🌍 Endpoints Clave

| Endpoint | Método | Función | Usado por |
|----------|--------|---------|----------|
| `POST /webhook/payment-handler` | POST | Recibir pagos | MockAdapter/Stripe |
| `POST /webhook/partner-handler` | POST | Recibir webhooks de partners | Grupos partners |
| `POST /api/reservas/{id}/confirm` | POST | Activar reserva | Payment Handler |
| `POST /api/webhooks/reserva-actualizada` | POST | Notificar WebSocket | Payment Handler |
| `GET /api/partners/{id}` | GET | Obtener partner | Partner Handler |
| `POST /api/reports/daily` | POST | Generar reporte | Scheduled Tasks |

Ver `REQUIRED_ENDPOINTS.md` para lista completa y checklist.

---

## ✅ Checklist Pre-Demo

- [ ] n8n ejecutando en `http://localhost:5678`
- [ ] REST API en `http://localhost:8000`
- [ ] GraphQL en `http://localhost:8080`
- [ ] WebSocket en `http://localhost:3001`
- [ ] 4 workflows importados
- [ ] JWT token válido obtenido
- [ ] Partner registrado en BD
- [ ] DEMO_STEPS.md leído completamente

---

## 🐛 Problemas Comunes

| Problema | Solución |
|----------|----------|
| n8n no inicia | `rm -r $env:USERPROFILE\.n8n`; `n8n start` |
| Puerto en uso | `$env:N8N_PORT = "5679"; n8n start` |
| Webhook no llega | Verificar firewall; `curl http://localhost:5678` |
| HMAC inválido | Secret correcto; JSON sin espacios; SHA256 |
| REST no responde | Verificar: `curl http://localhost:8000/api/health` |

Ver `QUICKSTART.md` para más soluciones.

---

## 📊 Estado del Proyecto (Pilar 4)

### ✅ Completado
- n8n instalado localmente
- 4 workflows en JSON
- Documentación completa (7 documentos MD)
- Contrato de eventos definido
- Utilidades HMAC documentadas
- Endpoints configurados
- Pasos de demo detallados

### ⚠️ Por Verificar/Completar
- Endpoints en servicios (REST/Payment):
  - `POST /api/reservas/{id}/confirm`
  - `GET /api/partners/{id}`
  - `POST /api/partners/register`
  - Otros (ver `REQUIRED_ENDPOINTS.md`)

### 🔄 Próximos Pasos
1. **Hoy:** Ejecutar `.\run-n8n.ps1` e importar workflows
2. **Esta semana:** Verificar/crear endpoints faltantes
3. **Pruebas:** Ejecutar DEMO_STEPS.md
4. **Presentación:** Demo funcional del flujo end-to-end

---

## 📞 Referencias Rápidas

- **n8n Docs:** https://docs.n8n.io/
- **RFC HMAC:** https://tools.ietf.org/html/rfc2104
- **GitHub Webhooks:** https://docs.github.com/en/developers/webhooks-and-events

---

## 🎁 Resumen de Entrega

**Carpeta:** `UleamBack/n8n-workflows/`

**Archivos:**
- ✅ 4 workflows JSON (listos para importar)
- ✅ 7 documentos MD (guías completas)
- ✅ Script PowerShell (ejecutar n8n)
- ✅ Almacenamiento local (`n8n-data/`)

**Estado:** **LISTO PARA IMPLEMENTAR** ✨

---

## 🎯 Tu Próxima Acción

```powershell
# 1. Abre PowerShell y ve a UleamBack
cd C:\Users\ASUS\Desktop\ReservasUleam2026\ReservasUleam2025\UleamBack

# 2. Ejecuta n8n
.\run-n8n.ps1

# 3. Abre navegador
# http://localhost:5678

# 4. Importa workflows (tab: Import)
# Selecciona los 4 archivos JSON

# 5. Activa y prueba
# ¡Listo! 🚀
```

---

## 📚 Documentación Recomendada por Caso

**Si quieres entender qué es n8n:**
→ `QUICKSTART.md`

**Si quieres saber cómo implementar:**
→ `TECHNICAL_SUMMARY.md` + `DEMO_STEPS.md`

**Si necesitas detalles técnicos:**
→ `CONTRACT_EVENTS.md` + `ENDPOINTS_CONFIG.md`

**Si debes implementar seguridad:**
→ `HMAC_UTILS.md` + `REQUIRED_ENDPOINTS.md`

**Si vas a presentar:**
→ `DEMO_STEPS.md` (OBLIGATORIO)

---

**¡Bienvenido a Pilar 4! 🎉**

Tienes todo lo que necesitas para implementar un Event Bus robusto con n8n.

**¿Preguntas?** Consulta `DEMO_STEPS.md` o `TECHNICAL_SUMMARY.md`.
