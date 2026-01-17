# Utilidades HMAC para n8n y Servicios

Archivo de ayuda para integración HMAC en workflows y endpoints.

## 🔐 Generar y Verificar HMAC-SHA256

### Python (REST/Payment Service)

```python
import hmac
import hashlib
import json
from typing import Tuple

def generate_hmac_signature(secret: str, payload: dict) -> str:
    """
    Generar firma HMAC-SHA256 para un payload.
    
    Args:
        secret: Clave compartida con el partner
        payload: Dict del evento
    
    Returns:
        Firma en formato hexadecimal: "sha256:abcd1234..."
    """
    body = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    signature = hmac.new(
        secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256:{signature}"


def verify_hmac_signature(secret: str, payload: dict, signature: str) -> bool:
    """
    Verificar firma HMAC-SHA256.
    
    Args:
        secret: Clave compartida
        payload: Dict original
        signature: Firma recibida (formato: "sha256:abcd1234...")
    
    Returns:
        True si la firma es válida
    """
    expected = generate_hmac_signature(secret, payload)
    # Comparación segura contra timing attacks
    return hmac.compare_digest(expected, signature)


def generate_partner_secret() -> str:
    """Generar secreto seguro para nuevo partner (32 bytes hex = 64 chars)."""
    return secrets.token_hex(32)
```

### TypeScript/NestJS (WebSocket/Auth Service)

```typescript
import * as crypto from 'crypto';

function generateHmacSignature(secret: string, payload: object): string {
  const body = JSON.stringify(payload, Object.keys(payload).sort());
  const signature = crypto
    .createHmac('sha256', secret)
    .update(body)
    .digest('hex');
  return `sha256:${signature}`;
}

function verifyHmacSignature(secret: string, payload: object, signature: string): boolean {
  const expected = generateHmacSignature(secret, payload);
  return crypto.timingSafeEqual(
    Buffer.from(expected),
    Buffer.from(signature)
  );
}

function generatePartnerSecret(): string {
  return crypto.randomBytes(32).toString('hex');
}
```

### JavaScript (n8n Function Node)

```javascript
const crypto = require('crypto');

// Generar HMAC
function generateHmacSignature(secret, payload) {
  const body = JSON.stringify(payload);
  const signature = crypto
    .createHmac('sha256', secret)
    .update(body)
    .digest('hex');
  return `sha256:${signature}`;
}

// Verificar HMAC
function verifyHmacSignature(secret, payload, signature) {
  const expected = generateHmacSignature(secret, payload);
  return expected === signature;
}

// Uso en n8n:
// const isValid = verifyHmacSignature(
//   $env.PARTNER_SECRET,
//   $input.body.payload,
//   $input.body.hmac_signature
// );
```

---

## 📝 Implementación en Endpoints

### REST API - Endpoint para registrar Partner

```python
# rest-service/app/routes/partners.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.partner import Partner
from ..schemas.partner import PartnerCreate, PartnerResponse

router = APIRouter(prefix="/api/partners", tags=["partners"])

@router.post("/register", response_model=PartnerResponse)
async def register_partner(
    partner: PartnerCreate,
    db: Session = Depends(get_db)
):
    """
    Registrar nuevo partner para integraciones B2B.
    
    Request:
    {
      "nombre": "TourCompany",
      "webhook_url": "https://api.tourcompany.com/webhooks",
      "eventos_suscritos": ["booking.confirmed", "payment.success"],
      "descripcion": "Tours y excursiones"
    }
    
    Response:
    {
      "id": 1,
      "nombre": "TourCompany",
      "webhook_url": "https://...",
      "shared_secret": "sha256_token...",  # ← Comunicar al partner de forma segura
      "eventos_suscritos": [...],
      "is_active": true
    }
    """
    # Verificar no exista partner con mismo nombre
    existing = db.query(Partner).filter(
        Partner.nombre == partner.nombre
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Partner ya existe")
    
    # Generar secret seguro
    secret = generate_partner_secret()
    
    # Crear partner
    new_partner = Partner(
        nombre=partner.nombre,
        webhook_url=partner.webhook_url,
        shared_secret=secret,
        eventos_suscritos=partner.eventos_suscritos,
        descripcion=partner.descripcion or "",
        is_active=True
    )
    db.add(new_partner)
    db.commit()
    db.refresh(new_partner)
    
    return new_partner


@router.get("/{partner_id}", response_model=PartnerResponse)
async def get_partner(partner_id: int, db: Session = Depends(get_db)):
    """Obtener datos del partner (sin secret visible)."""
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner no encontrado")
    return partner


@router.get("/", response_model=list[PartnerResponse])
async def list_partners(db: Session = Depends(get_db)):
    """Listar todos los partners activos."""
    return db.query(Partner).filter(Partner.is_active == True).all()
```

### Payment Service - Webhook Outbound Helper

```python
# payment-service/app/services/webhook_dispatcher.py

import httpx
import json
from typing import Optional
from .hmac_utils import generate_hmac_signature

async def send_partner_webhook(
    partner: Partner,
    event: str,
    payload: dict,
    trace_id: str,
    timeout: int = 10
) -> Tuple[bool, str]:
    """
    Enviar webhook firmado a un partner.
    
    Returns:
        (success: bool, response_or_error: str)
    """
    webhook_payload = {
        "event": event,
        "source": "uleam_system",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "trace_id": trace_id,
        "payload": payload
    }
    
    # Firmar con secret del partner
    signature = generate_hmac_signature(partner.shared_secret, webhook_payload)
    
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature": signature,
        "User-Agent": "n8n-uleam/1.0"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                partner.webhook_url,
                json=webhook_payload,
                headers=headers,
                timeout=timeout
            )
        
        if response.status_code in [200, 204]:
            return (True, f"Webhook enviado: {response.status_code}")
        else:
            return (False, f"Partner respondió {response.status_code}: {response.text}")
    
    except httpx.TimeoutException:
        return (False, f"Timeout enviando webhook a {partner.webhook_url}")
    except Exception as e:
        return (False, f"Error: {str(e)}")
```

---

## 🔗 Flujo Completo: Payment Handler en n8n

### Node 1: Webhook Trigger
- Recibe POST desde MockAdapter/Stripe
- Normaliza estructura a contrato estándar

### Node 2: Validar Payload
Usar **Function** node:
```javascript
// Validar campos obligatorios
const required = ['event', 'source', 'timestamp', 'payload', 'trace_id'];
for (const field of required) {
  if (!$input.body[field]) {
    throw new Error(`Campo requerido: ${field}`);
  }
}
return { valid: true };
```

### Node 3: Activar Reserva (HTTP Request)
```
Method: POST
URL: http://localhost:8000/api/reservas/{{$input.body.payload.booking_id}}/confirm
Headers:
  Content-Type: application/json
  Authorization: Bearer {{$env.REST_JWT_TOKEN}}
Body:
{
  "payment_id": "{{$input.body.payload.payment_id}}",
  "status": "confirmed"
}
```

### Node 4: Notificar WebSocket
```
Method: POST
URL: http://localhost:3001/api/webhooks/reserva-actualizada
Body:
{
  "booking_id": "{{$input.body.payload.booking_id}}",
  "status": "confirmed",
  "timestamp": "{{$input.body.timestamp}}"
}
```

### Node 5: Enviar Email (SMTP)
```
From: noreply@uleam.com
To: {{$input.body.payload.customer_email}}
Subject: Reserva Confirmada - {{$input.body.payload.booking_id}}
Body: 
Tu reserva ha sido confirmada. Referencia: {{$input.body.payload.booking_id}}
Monto: {{$input.body.payload.amount}} {{$input.body.payload.currency}}
```

### Node 6: Webhook a Partner (HTTP Request con HMAC)
Usar **Function** node para generar firma:
```javascript
const crypto = require('crypto');
const secret = $env.PARTNER_SECRET;
const payload = {
  "event": "booking.confirmed",
  "source": "uleam_system",
  "timestamp": new Date().toISOString(),
  "trace_id": $input.body.trace_id,
  "payload": $input.body.payload
};

const body = JSON.stringify(payload);
const signature = crypto
  .createHmac('sha256', secret)
  .update(body)
  .digest('hex');

return {
  payload,
  signature: `sha256:${signature}`
};
```

Luego HTTP Request:
```
Method: POST
URL: {{$env.PARTNER_WEBHOOK_URL}}
Headers:
  Content-Type: application/json
  X-Hub-Signature: {{$input.body.signature}}
Body: {{$input.body.payload}}
```

---

## 🧪 Testing Local

### Test 1: Validar HMAC (Python)

```bash
# En PowerShell o bash
python3 << 'EOF'
import hmac
import hashlib
import json

secret = "test_secret_123"
payload = {"event": "payment.success", "booking_id": "bk_001"}
body = json.dumps(payload)

signature = hmac.new(
    secret.encode(),
    body.encode(),
    hashlib.sha256
).hexdigest()

print(f"Payload: {body}")
print(f"Signature: sha256:{signature}")
EOF
```

### Test 2: Enviar Webhook Firmado (PowerShell)

```powershell
$secret = "test_secret_123"
$body = @{
    event = "booking.confirmed"
    booking_id = "bk_001"
} | ConvertTo-Json

$signature = [System.Security.Cryptography.HMACSHA256]::new([System.Text.Encoding]::UTF8.GetBytes($secret))
$hash = $signature.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($body))
$signatureHex = [System.BitConverter]::ToString($hash).Replace("-", "").ToLower()

$headers = @{
    "Content-Type" = "application/json"
    "X-Hub-Signature" = "sha256:$signatureHex"
}

Invoke-WebRequest -Uri "http://localhost:5678/webhook/partner-handler" `
    -Method POST `
    -Headers $headers `
    -Body $body
```

---

## 📚 Referencias

- [HMAC RFC 2104](https://tools.ietf.org/html/rfc2104)
- [GitHub Webhooks Documentation](https://docs.github.com/en/developers/webhooks-and-events/webhooks)
- [n8n HTTP Request Node](https://docs.n8n.io/nodes/n8n-nodes-base.httpRequest/)
