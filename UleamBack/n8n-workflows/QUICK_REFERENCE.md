# ⚡ Quick Reference - Pilar 4 n8n

## 🚀 Start n8n (1 comando)

```powershell
cd C:\Users\ASUS\Desktop\ReservasUleam2026\ReservasUleam2025\UleamBack
.\run-n8n.ps1
```

**URL:** http://localhost:5678

---

## 4️⃣ Los Workflows

| # | Nombre | Webhook URL | Trigger | Estado |
|---|--------|------------|---------|--------|
| 1 | Payment Handler | `/webhook/payment-handler` | Pago completado | ✅ Active |
| 2 | Partner Handler | `/webhook/partner-handler` | Webhook de partner | ✅ Active |
| 3 | MCP Input | (Telegram config) | Mensaje en bot | ⚠️ Disabled |
| 4 | Scheduled Tasks | (Cron) | 23:59 & cada 6h | ✅ Active |

---

## 📌 Endpoints Clave

```
REST:      http://localhost:8000/api
GraphQL:   http://localhost:8080/graphql
WebSocket: http://localhost:3001
n8n:       http://localhost:5678
Payment:   http://localhost:8001/api (si existe)
```

---

## 🔐 HMAC-SHA256 (1 minuto)

**Firma:** `sha256:` + HMAC-SHA256(secret, body)

```javascript
// n8n Function node
const crypto = require('crypto');
const sig = crypto.createHmac('sha256', secret).update(JSON.stringify(payload)).digest('hex');
```

---

## 🧪 Test Payment Handler

```powershell
curl -X POST http://localhost:5678/webhook/payment-handler `
  -H "Content-Type: application/json" `
  -d '{
    "event":"payment.success",
    "source":"mock",
    "timestamp":"2026-01-23T14:30:00Z",
    "trace_id":"test-001",
    "payload":{"payment_id":"pm_test","booking_id":1,"amount":100}
  }'
```

---

## 📝 Event Structure (Template)

```json
{
  "event": "payment.success",
  "source": "mock",
  "timestamp": "2026-01-23T14:30:00Z",
  "trace_id": "unique-id",
  "payload": { /* event data */ },
  "partner_id": null,
  "hmac_signature": "sha256:...",
  "retry_count": 0
}
```

---

## ✅ Checklist

- [ ] n8n running (`http://localhost:5678`)
- [ ] REST running (`http://localhost:8000/api/health`)
- [ ] 4 workflows imported
- [ ] JWT token configured
- [ ] Partner registered in DB

---

## 📚 Doc Map

| Need | Read |
|------|------|
| How to start | `QUICKSTART.md` |
| Full setup | `README.md` |
| Events format | `CONTRACT_EVENTS.md` |
| URLs & payloads | `ENDPOINTS_CONFIG.md` |
| HMAC code | `HMAC_UTILS.md` |
| Demo steps | `DEMO_STEPS.md` |
| Endpoints missing | `REQUIRED_ENDPOINTS.md` |
| Technical overview | `TECHNICAL_SUMMARY.md` |

---

## 🐛 Quick Fixes

| Problem | Fix |
|---------|-----|
| n8n won't start | `rm -Path $env:USERPROFILE\.n8n -Recurse` |
| Port 5678 busy | `$env:N8N_PORT=5679; n8n start` |
| Webhook not arriving | Verify: `curl http://localhost:5678` |
| HMAC invalid | Check secret + JSON format (no spaces) |
| REST down | `curl http://localhost:8000/api/health` |

---

## 🎯 Payment Handler Flow

```
1. webhook arrives at n8n
2. validate payload
3. POST /api/reservas/{id}/confirm (REST)
4. POST /api/webhooks/reserva-actualizada (WS)
5. send email
6. POST to partner with HMAC signature
```

---

## 🎯 Partner Handler Flow

```
1. webhook arrives at n8n
2. verify HMAC-SHA256 signature
3. normalize event type
4. execute business action (POST /api/orders, etc)
5. respond ACK 200
```

---

## 🎯 Scheduled Tasks

**Cron 1:** Daily 23:59 → Generate report (`POST /api/reports/daily`)

**Cron 2:** Every 6h → Health check all services

---

## Variables to Set

```powershell
$env:REST_JWT_TOKEN = "your_jwt_token"
$env:PARTNER_SECRET = "shared_secret"
$env:SMTP_HOST = "smtp.gmail.com"
```

---

## Files You Need to Know

```
n8n-workflows/
├── ✅ payment_handler.json
├── ✅ partner_handler.json
├── ✅ scheduled_tasks.json
├── ⚠️  mcp_input_handler.json
├── 📖 QUICKSTART.md          (START HERE)
├── 📖 DEMO_STEPS.md          (BEFORE DEMO)
├── 📖 CONTRACT_EVENTS.md
├── 📖 ENDPOINTS_CONFIG.md
└── ...
```

---

## Running Demo

1. `.\run-n8n.ps1`
2. Open `http://localhost:5678`
3. Import 4 JSON workflows
4. Test payment: `curl ...` (see above)
5. Check WS got notified
6. Check partner webhook sent
7. ✅ Success!

---

## Important Notes

⚠️ **MCP Input Handler** is disabled by default (Telegram integration optional)

⚠️ **HMAC verification** is critical for security - test carefully

⚠️ **JWT tokens expire** - refresh if getting 401 errors

✅ **Trace IDs** are in every log for debugging

✅ **Retry logic** built into Payment Handler (3 attempts)

---

## Contact Points

- REST: `POST /api/reservas/{id}/confirm`
- WebSocket: `POST /api/webhooks/reserva-actualizada`
- Partners: `GET /api/partners/{id}`
- Reports: `POST /api/reports/daily`

---

## One More Time: Start n8n

```powershell
.\run-n8n.ps1
```

Then go to **http://localhost:5678** 🚀
