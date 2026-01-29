# 📢 INFORMACIÓN PARA EQUIPO B - CORRECCIONES REQUERIDAS

**De:** Equipo A (ULEAM - Recomendaciones Turísticas)  
**Para:** Equipo B  
**Estado:**  Nuestro lado está listo |  Correcciones necesarias en su lado

---

## ✅ CONFIRMACIONES - LO QUE YA FUNCIONA

1. **Su ngrok funciona perfectamente:**
   - URL: `https://unfulminated-charley-airtightly.ngrok-free.dev`
   - Health: ✅ Responde 200 OK
   - Status: ✅ Responde con información correcta

2. **Nuestro servicio está listo:**
   - URL: `https://heuristically-farraginous-marquitta.ngrok-free.dev`
   - Todos los endpoints funcionando
   - HMAC configurado correctamente

---

## ❌ PROBLEMA 1: URL INCORRECTA DE NUESTRO WEBHOOK

### ⚠️ Tienen configurado (INCORRECTO):

```json
{
  "send_to_equipo_a": "https://heuristically-farraginous-marquitta.ngrok-free.dev/api/reservas"
}
```

### ✅ URL CORRECTA (actualizar en su código):

```json
{
  "send_to_equipo_a": "https://heuristically-farraginous-marquitta.ngrok-free.dev/api/v1/equipo-a/webhook"
}
```

**Cambio necesario:** Agregar `/v1/equipo-a` antes de `/webhook`

---

## ❌ PROBLEMA 2: VALIDACIÓN HMAC FALLA

### Síntomas:
- Todos los webhooks responden: `401 Unauthorized`
- Mensaje: `"Invalid HMAC signature"`
- Hemos recibido 4 intentos, todos con firma inválida

### Causa probable:
El cálculo de la firma HMAC-SHA256 no coincide entre sistemas.

### ✅ MÉTODO CORRECTO DE CÁLCULO (implementar exactamente así):

```python
import json
import hmac
import hashlib

# Secreto compartido (DEBE SER IDÉNTICO EN AMBOS LADOS)
SECRET = "integracion-turismo-2026-uleam"

def generar_firma_correcta(payload_dict):
    """
    Genera firma HMAC-SHA256 compatible con Equipo A.
    
    IMPORTANTE:
    1. Serializar JSON con separators=(',', ':') (sin espacios)
    2. Usar UTF-8 encoding
    3. HMAC-SHA256
    4. Hexdigest (minúsculas)
    """
    # PASO 1: Serializar payload a JSON (SIN ESPACIOS)
    mensaje = json.dumps(payload_dict, separators=(',', ':'), sort_keys=True)
    
    # PASO 2: Codificar a bytes UTF-8
    mensaje_bytes = mensaje.encode('utf-8')
    secret_bytes = SECRET.encode('utf-8')
    
    # PASO 3: Generar HMAC-SHA256
    firma = hmac.new(secret_bytes, mensaje_bytes, hashlib.sha256).hexdigest()
    
    return firma


# EJEMPLO DE USO:
payload = {
    "event": "test.connection",
    "timestamp": "2026-01-28T10:00:00Z",
    "data": {"test": True}
}

# Generar firma
firma = generar_firma_correcta(payload)
print(f"Firma generada: {firma}")

# Enviar webhook
import requests
headers = {
    "Content-Type": "application/json",
    "X-Signature": firma  # ⚠️ FIRMA VA EN HEADER, NO EN BODY
}

response = requests.post(
    "https://heuristically-farraginous-marquitta.ngrok-free.dev/api/v1/equipo-a/webhook",
    json=payload,  # ⚠️ NO incluir "firma" en el payload
    headers=headers,
    timeout=10
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

---

## 🔧 DIFERENCIAS CLAVE CON SU IMPLEMENTACIÓN ACTUAL

### ❌ Incorrecto (lo que probablemente están haciendo):

```python
# MAL: Incluir firma en el body
payload = {
    "event": "test",
    "timestamp": "...",
    "data": {...},
    "firma": "abc123..."  # ❌ NO incluir en el body
}

# MAL: Espacios en JSON
mensaje = json.dumps(payload, indent=2)  # ❌ Espacios cambian el hash

# MAL: No usar sort_keys
mensaje = json.dumps(payload)  # ❌ Orden diferente = hash diferente
```

### ✅ Correcto (implementar así):

```python
# BIEN: Firma en header X-Signature
payload = {
    "event": "test",
    "timestamp": "...",
    "data": {...}
    # ✅ NO incluir "firma" aquí
}

# BIEN: JSON compacto con sort_keys
mensaje = json.dumps(payload, separators=(',', ':'), sort_keys=True)

# BIEN: HMAC sobre el mensaje completo
firma = hmac.new(secret.encode(), mensaje.encode(), hashlib.sha256).hexdigest()

# BIEN: Firma en header
headers = {"X-Signature": firma}
```

---

## 🧪 PRUEBA RÁPIDA PARA VERIFICAR HMAC

### Ejecuten este script para validar su implementación:

**Archivo: `test_hmac_equipo_a.py`**

```python
import json
import hmac
import hashlib
import requests

SECRET = "integracion-turismo-2026-uleam"
URL_EQUIPO_A = "https://heuristically-farraginous-marquitta.ngrok-free.dev/api/v1/equipo-a/webhook"

def test_hmac_validation():
    """
    Prueba que la firma HMAC se calcula correctamente.
    Si reciben 200 OK, la integración funciona.
    """
    # Payload de prueba mínimo
    payload = {
        "event": "test.connection",
        "timestamp": "2026-01-28T10:00:00Z",
        "data": {
            "test": True,
            "message": "Testing HMAC from Equipo B"
        }
    }
    
    # Calcular firma (método correcto)
    mensaje = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    firma = hmac.new(
        SECRET.encode('utf-8'),
        mensaje.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    print("=" * 60)
    print("🧪 TEST: Validación HMAC con Equipo A")
    print("=" * 60)
    print(f"📤 URL: {URL_EQUIPO_A}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    print(f"🔐 Firma: {firma}")
    print(f"📝 Mensaje (para debug): {mensaje}")
    print("=" * 60)
    
    try:
        # Enviar webhook
        response = requests.post(
            URL_EQUIPO_A,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-Signature": firma
            },
            timeout=10
        )
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📥 Response: {response.json()}")
        
        if response.status_code == 200:
            print("\n🎉 ¡ÉXITO! La firma HMAC es correcta.")
            print("✅ Su implementación está funcionando.")
            return True
        else:
            print("\n❌ ERROR: La firma HMAC aún no es correcta.")
            print("⚠️  Revisar la función de generación de firma.")
            return False
            
    except Exception as e:
        print(f"\n❌ EXCEPCIÓN: {str(e)}")
        return False

if __name__ == "__main__":
    test_hmac_validation()
```

**Ejecutar:**

```bash
python test_hmac_equipo_a.py
```

**Resultado esperado:**

```
============================================================
🧪 TEST: Validación HMAC con Equipo A
============================================================
📤 URL: https://heuristically-farraginous-marquitta.ngrok-free.dev/api/v1/equipo-a/webhook
📦 Payload: {
  "event": "test.connection",
  "timestamp": "2026-01-28T10:00:00Z",
  "data": {
    "test": true,
    "message": "Testing HMAC from Equipo B"
  }
}
🔐 Firma: [calculada automáticamente]
============================================================
✅ Status Code: 200
📥 Response: {"status":"ok","event":"test.connection","message":"Event received"}

🎉 ¡ÉXITO! La firma HMAC es correcta.
✅ Su implementación está funcionando.
```

---

## 📋 CHECKLIST DE CORRECCIONES

### Equipo B - Por Favor Verificar:

- [ ] **URL actualizada:** Cambiar de `/api/reservas` a `/api/v1/equipo-a/webhook`
- [ ] **Función HMAC corregida:** Usar `separators=(',', ':')` y `sort_keys=True`
- [ ] **Firma en header:** Enviar como `X-Signature`, NO en el body
- [ ] **Secreto verificado:** Confirmar que usan `"integracion-turismo-2026-uleam"`
- [ ] **Script de prueba ejecutado:** Correr `test_hmac_equipo_a.py` y recibir 200 OK
- [ ] **Encoding UTF-8:** Asegurar que usan `.encode('utf-8')`
- [ ] **Sin espacios en JSON:** No usar `indent` al serializar para HMAC

---

## 📞 INFORMACIÓN DE CONTACTO

**Nuestros Endpoints (Equipo A):**

```
┌─ EQUIPO A: ULEAM Recomendaciones Turísticas ───────────┐
│                                                          │
│ Base URL: https://heuristically-farraginous-marquitta.ngrok-free.dev
│                                                          │
│ RECIBIMOS DE USTEDES:                                   │
│ ✅ POST /api/v1/equipo-a/webhook                        │
│    - Autenticación: X-Signature (HMAC-SHA256)          │
│    - Content-Type: application/json                     │
│    - Eventos que recibimos:                             │
│      • tour.purchased                                   │
│      • booking.confirmed                                │
│      • recommendation.created                           │
│                                                          │
│ ENVIAMOS A USTEDES:                                     │
│ 📤 POST https://unfulminated-charley-airtightly.ngrok-free.dev/api/reservas
│    - Autenticación: X-Signature (HMAC-SHA256)          │
│    - Eventos que enviamos:                              │
│      • booking.confirmed                                │
│      • payment.success                                  │
│      • service.activated                                │
│                                                          │
│ HEALTH CHECK:                                           │
│ 🏥 GET /api/v1/health                                   │
│                                                          │
│ VERIFICACIÓN:                                           │
│ 📊 GET /api/v1/equipo-a/status                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 PRÓXIMOS PASOS

1. **Equipo B:** Actualizar URL en su configuración
2. **Equipo B:** Corregir función de generación HMAC
3. **Equipo B:** Ejecutar `test_hmac_equipo_a.py` → Debe retornar 200 OK
4. **Ambos equipos:** Realizar prueba coordinada de evento real
5. **Ambos equipos:** Verificar logs y confirmar recepción exitosa

---

## 📝 FORMATO DE PAYLOAD ESPERADO

### Cuando ustedes nos envían (Equipo B → Equipo A):

```json
POST https://heuristically-farraginous-marquitta.ngrok-free.dev/api/v1/equipo-a/webhook
Content-Type: application/json
X-Signature: [HMAC-SHA256-HEX]

{
  "event": "tour.purchased",
  "timestamp": "2026-01-28T10:30:00Z",
  "data": {
    "tour_id": "tour_123",
    "user_id": "user_456",
    "tour_name": "Volcán Cotopaxi",
    "price": 120.00,
    "destination": "Latacunga"
  },
  "source": "equipo-b-sistema-xyz"
}
```

**⚠️ IMPORTANTE:** NO incluir campo `"firma"` en el body, va en header `X-Signature`

---

## ❓ PREGUNTAS FRECUENTES

### P: ¿Por qué falla el HMAC?
**R:** El orden de operaciones debe ser exacto:
1. Serializar JSON con `separators=(',', ':')` y `sort_keys=True`
2. Codificar a UTF-8
3. Calcular HMAC-SHA256
4. Enviar como hexdigest en header `X-Signature`

### P: ¿Dónde va la firma?
**R:** En el **header HTTP** como `X-Signature`, NO en el body JSON.

### P: ¿Puedo probar sin HMAC?
**R:** No, todos los webhooks requieren HMAC válido por seguridad.

### P: ¿Qué eventos debo enviar?
**R:** Pueden enviar: `tour.purchased`, `booking.confirmed`, `recommendation.created`

---

## 🎯 RESUMEN EJECUTIVO

| Aspecto | Estado | Acción Requerida |
|---------|--------|------------------|
| ngrok Equipo B | ✅ Funciona | Ninguna |
| URL webhook | ❌ Incorrecta | Cambiar a `/api/v1/equipo-a/webhook` |
| HMAC | ❌ Falla validación | Corregir función según documento |
| Secreto compartido | ✅ Correcto | Ninguna |
| ngrok Equipo A | ✅ Funciona | Ninguna |

**Estimación:** Con las correcciones, la integración debería funcionar en **15-30 minutos**.

---

**¿Preguntas o dudas?** Estamos disponibles para coordinar una prueba en vivo una vez implementen las correcciones.

**Versión:** 1.0  
**Equipo A - ULEAM Recomendaciones Turísticas**
