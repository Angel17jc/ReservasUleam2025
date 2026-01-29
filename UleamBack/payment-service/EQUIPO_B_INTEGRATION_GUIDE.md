# 🤝 GUÍA DE INTEGRACIÓN PARA EQUIPO B

**Proyecto:** Integración Bidireccional Reservas ULEAM ↔ Equipo B  
**Estado:**  Servicios activos, ajustando formato HMAC

---

## 📡 INFORMACIÓN DE NUESTROS SERVICIOS (EQUIPO A - ULEAM)

### ✅ URLs Disponibles:
```
Base URL (ngrok):  https://heuristically-farraginous-marquitta.ngrok-free.dev
Health Check:      https://heuristically-farraginous-marquitta.ngrok-free.dev/api/v1/health
Docs (Swagger):    https://heuristically-farraginous-marquitta.ngrok-free.dev/docs

🎯 WEBHOOK ENDPOINT (envíen aquí):
   https://heuristically-farraginous-marquitta.ngrok-free.dev/api/v1/equipo-a/webhook
```

### 🔐 Autenticación:
```
Método:      HMAC-SHA256
Header:      X-Signature
Secret:      integracion-turismo-2026-uleam
```

---

## 📥 CÓMO ENVIARNOS WEBHOOKS (EQUIPO B → EQUIPO A)

### 1️⃣ Formato del Payload:

```json
{
  "event": "booking.confirmed",
  "timestamp": "2026-01-27T10:30:00Z",
  "data": {
    "booking_id": "booking_123",
    "user_email": "usuario@example.com",
    "tour_name": "Tour Manta",
    "amount": 150.00,
    "persons": 2
  },
  "source": "equipo-b-sistema"
}
```

**Campos requeridos:**
- ✅ `event` (string): Tipo de evento
- ✅ `timestamp` (string): ISO 8601 format
- ✅ `data` (object): Datos del evento
- ✅ `source` (string): Identificador de su sistema

**Eventos que aceptamos:**
- `booking.confirmed` - Reserva confirmada
- `payment.success` - Pago exitoso
- `service.activated` - Servicio activado

---

### 2️⃣ Generar Firma HMAC (⚠️ IMPORTANTE):

**❌ PROBLEMA COMÚN:** No usar la misma serialización JSON

**✅ MÉTODO CORRECTO en Python:**

```python
import json
import hmac
import hashlib

# 1. Crear payload como dict
payload = {
    "event": "booking.confirmed",
    "timestamp": "2026-01-27T10:30:00Z",
    "data": {
        "booking_id": "test_123",
        "user_email": "test@example.com"
    },
    "source": "equipo-b-sistema"
}

# 2. ⚠️ CRÍTICO: Serializar con separators=(',', ':') y sort_keys=True
message = json.dumps(payload, sort_keys=True, separators=(',', ':'))

# 3. Generar firma HMAC-SHA256
secret = "integracion-turismo-2026-uleam"
signature = hmac.new(
    secret.encode('utf-8'),
    message.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# 4. Firma resultante (64 caracteres hexadecimales)
print(f"Signature: {signature}")
```

**⚠️ Errores comunes:**
- ❌ Usar `json.dumps(payload)` sin parámetros
- ❌ No ordenar las claves (`sort_keys=True`)
- ❌ Usar espacios en JSON (`separators` incorrectos)
- ❌ Diferentes codificaciones (usar `utf-8`)

---

### 3️⃣ Enviar Request HTTP:

**✅ MÉTODO CORRECTO:**

```python
import requests

url = "https://heuristically-farraginous-marquitta.ngrok-free.dev/api/v1/equipo-a/webhook"

# Usar el mismo payload serializado
message = json.dumps(payload, sort_keys=True, separators=(',', ':'))
signature = hmac.new(
    secret.encode('utf-8'),
    message.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# Headers
headers = {
    "Content-Type": "application/json",
    "X-Signature": signature
}

# POST request
response = requests.post(url, data=message, headers=headers, timeout=10)

if response.status_code == 200:
    print("✅ Webhook enviado exitosamente")
    print(response.json())
else:
    print(f"❌ Error {response.status_code}: {response.text}")
```

---

## 🧪 SCRIPT DE PRUEBA COMPLETO

**Archivo: `test_send_to_uleam.py`**

```python
#!/usr/bin/env python3
"""
Test Script: Equipo B → Equipo A (ULEAM)
Envía un webhook de prueba con firma HMAC correcta
"""

import requests
import json
import hmac
import hashlib
from datetime import datetime

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
ULEAM_WEBHOOK_URL = "https://heuristically-farraginous-marquitta.ngrok-free.dev/api/v1/equipo-a/webhook"
SHARED_SECRET = "integracion-turismo-2026-uleam"

# ============================================================================
# FUNCIÓN PARA GENERAR FIRMA
# ============================================================================
def generate_hmac_signature(payload_dict: dict, secret: str) -> str:
    """
    Genera firma HMAC-SHA256 compatible con Equipo A (ULEAM)
    
    ⚠️ IMPORTANTE: Usar json.dumps con:
       - sort_keys=True
       - separators=(',', ':')
    """
    message = json.dumps(payload_dict, sort_keys=True, separators=(',', ':'))
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature, message

# ============================================================================
# TEST 1: Evento booking.confirmed
# ============================================================================
def test_booking_confirmed():
    print("\n" + "="*70)
    print("🧪 TEST 1: Enviar evento 'booking.confirmed' a ULEAM")
    print("="*70)
    
    payload = {
        "event": "booking.confirmed",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "booking_id": "test_booking_001",
            "user_email": "test@equipob.com",
            "user_id": "user_test_456",
            "tour_name": "Tour Manta Beach",
            "amount": 120.50,
            "currency": "USD",
            "persons": 2,
            "booking_date": "2026-01-30"
        },
        "source": "equipo-b-sistema"
    }
    
    # Generar firma
    signature, message = generate_hmac_signature(payload, SHARED_SECRET)
    
    print(f"\n📦 Payload:")
    print(json.dumps(payload, indent=2))
    print(f"\n📝 Mensaje serializado (usado para HMAC):")
    print(message)
    print(f"\n🔐 Firma HMAC-SHA256:")
    print(signature)
    
    # Enviar request
    headers = {
        "Content-Type": "application/json",
        "X-Signature": signature
    }
    
    try:
        print(f"\n📤 Enviando a: {ULEAM_WEBHOOK_URL}")
        response = requests.post(
            ULEAM_WEBHOOK_URL,
            data=message,  # Usar el mismo string serializado
            headers=headers,
            timeout=10
        )
        
        print(f"\n📥 Respuesta HTTP {response.status_code}")
        print(response.text)
        
        if response.status_code == 200:
            print("\n✅ ¡ÉXITO! Webhook enviado y procesado correctamente")
            return True
        elif response.status_code == 401:
            print("\n❌ ERROR: Firma HMAC inválida")
            print("💡 Revisar:")
            print("   1. Secret key es correcto")
            print("   2. Usar json.dumps con sort_keys=True y separators=(',', ':')")
            print("   3. UTF-8 encoding")
            return False
        else:
            print(f"\n⚠️ Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ TIMEOUT: Servidor no responde en 10 segundos")
        return False
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR: No se puede conectar al servidor")
        print("💡 Verificar que ngrok de ULEAM esté corriendo")
        return False
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        return False

# ============================================================================
# TEST 2: Evento payment.success
# ============================================================================
def test_payment_success():
    print("\n" + "="*70)
    print("🧪 TEST 2: Enviar evento 'payment.success' a ULEAM")
    print("="*70)
    
    payload = {
        "event": "payment.success",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "payment_id": "pay_test_789",
            "booking_id": "booking_test_123",
            "amount": 250.00,
            "currency": "USD",
            "payment_method": "card",
            "status": "completed"
        },
        "source": "equipo-b-sistema"
    }
    
    signature, message = generate_hmac_signature(payload, SHARED_SECRET)
    
    print(f"\n📦 Payload: {json.dumps(payload, indent=2)}")
    print(f"\n🔐 Firma: {signature}")
    
    headers = {
        "Content-Type": "application/json",
        "X-Signature": signature
    }
    
    try:
        response = requests.post(ULEAM_WEBHOOK_URL, data=message, headers=headers, timeout=10)
        print(f"\n📥 Respuesta: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ ¡ÉXITO!")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# ============================================================================
# EJECUTAR TESTS
# ============================================================================
if __name__ == "__main__":
    print("\n🚀 INICIANDO TESTS DE INTEGRACIÓN: EQUIPO B → ULEAM")
    print(f"🎯 Endpoint: {ULEAM_WEBHOOK_URL}")
    print(f"🔑 Secret: {SHARED_SECRET[:10]}...")
    
    results = []
    
    # Test 1
    results.append(("booking.confirmed", test_booking_confirmed()))
    
    # Test 2 (opcional)
    respuesta = input("\n¿Ejecutar Test 2 (payment.success)? (s/n): ")
    if respuesta.lower() == 's':
        results.append(("payment.success", test_payment_success()))
    
    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE TESTS")
    print("="*70)
    for evento, resultado in results:
        status = "✅ PASÓ" if resultado else "❌ FALLÓ"
        print(f"{status}: {evento}")
    
    total = len(results)
    exitosos = sum(1 for _, r in results if r)
    print(f"\nTotal: {exitosos}/{total} tests exitosos")
    
    if exitosos == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON! Integración funcionando correctamente")
    else:
        print("\n⚠️ Algunos tests fallaron. Revisar logs arriba.")
```

**Para ejecutar:**
```bash
python test_send_to_uleam.py
```

---

## 📤 QUÉ ESPERAMOS DE USTEDES (EQUIPO B)

### Endpoints que deben exponer:

```
POST /api/reservas   (o el endpoint que definan)
```

**Formato que nosotros enviaremos:**
```json
{
  "event": "tour.purchased",
  "timestamp": "2026-01-27T10:30:00Z",
  "data": {
    "tour_id": "tour_123",
    "user_id": "user_456",
    "tour_name": "Tour Baños",
    "price": 150.00,
    "persons": 2
  },
  "source": "equipo-a-recomendaciones"
}
```

**Ustedes deben:**
1. Validar la firma HMAC en header `X-Signature`
2. Usar el mismo método de validación (json.dumps con sort_keys y separators)
3. Responder `200 OK` si todo es correcto
4. Responder `401` si la firma es inválida

---

## 🔍 DEBUGGING

### Si reciben 401 Unauthorized:

1. **Verificar serialización JSON:**
   ```python
   # Correcto:
   message = json.dumps(payload, sort_keys=True, separators=(',', ':'))
   
   # Incorrecto:
   message = json.dumps(payload)  # ❌ Diferentes espacios
   ```

2. **Verificar secret:**
   ```python
   secret = "integracion-turismo-2026-uleam"  # ✅ Exacto
   ```

3. **Verificar encoding:**
   ```python
   secret.encode('utf-8')  # ✅
   message.encode('utf-8')  # ✅
   ```

4. **Ver logs en nuestro lado:**
   - Cuando reciban 401, nosotros loggeamos el payload esperado
   - Pueden pedirme los logs para comparar

### Test manual con curl:

```bash
# 1. Generar firma con Python
python3 -c "
import json, hmac, hashlib
payload = {'event':'test','timestamp':'2026-01-27T10:00:00Z','data':{},'source':'equipo-b'}
msg = json.dumps(payload, sort_keys=True, separators=(',', ':'))
sig = hmac.new(b'integracion-turismo-2026-uleam', msg.encode(), hashlib.sha256).hexdigest()
print(f'Payload: {msg}')
print(f'Signature: {sig}')
"

# 2. Copiar la firma y enviar con curl
curl -X POST https://heuristically-farraginous-marquitta.ngrok-free.dev/api/v1/equipo-a/webhook \
  -H "Content-Type: application/json" \
  -H "X-Signature: PEGAR_FIRMA_AQUI" \
  -d '{"data":{},"event":"test","source":"equipo-b","timestamp":"2026-01-27T10:00:00Z"}'
```

---

## ✅ CHECKLIST DE INTEGRACIÓN

### Para que todo funcione:

- [ ] Usar URL correcta: `.../api/v1/equipo-a/webhook`
- [ ] Incluir header `Content-Type: application/json`
- [ ] Incluir header `X-Signature` con firma HMAC
- [ ] Usar `json.dumps(payload, sort_keys=True, separators=(',', ':'))`
- [ ] Secret exacto: `integracion-turismo-2026-uleam`
- [ ] Payload incluye: event, timestamp, data, source
- [ ] Timestamp en formato ISO 8601 (con Z al final)
- [ ] Encoding UTF-8 en todo

---

## 📞 CONTACTO Y SOPORTE

**Si tienen problemas:**

1. **Ejecutar el script de prueba** (`test_send_to_uleam.py`)
2. **Revisar el output detallado** (muestra el payload y firma)
3. **Si falla con 401:** Comparar su método de firma con el del script
4. **Contactarme** con:
   - El payload que están enviando
   - La firma que generaron
   - El mensaje de error que reciben

**Estado de servicios:**
- ✅ ngrok activo: https://heuristically-farraginous-marquitta.ngrok-free.dev
- ✅ payment-service corriendo en puerto 8001
- ✅ Endpoint `/api/v1/equipo-a/webhook` listo y esperando webhooks

---

## 🎯 PRÓXIMOS PASOS

1. **Ustedes:** Ejecuten `test_send_to_uleam.py` y verifiquen que reciben `200 OK`
2. **Nosotros:** Configuraremos su URL y les enviaremos webhooks de prueba
3. **Ambos:** Validar integración bidireccional completa

**¡Estamos listos del lado de ULEAM! 🚀**

---

**Válido hasta:** URL de ngrok cambia al reiniciar (avisar si cambia)  
**Versión:** 1.1 (Corregida validación HMAC)
