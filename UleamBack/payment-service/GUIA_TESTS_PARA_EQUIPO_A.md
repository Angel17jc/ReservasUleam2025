# 🧪 GUÍA DE TESTS PARA EQUIPO A

**De:** Equipo B (ULEAM - Sistema de Reservas)  
**Para:** Equipo A (Recomendaciones Turísticas)  

---

## 📦 ARCHIVO DE TESTS

Adjunto: **`tests_para_equipo_a.py`**

Este script contiene **6 tests completos** que pueden ejecutar para verificar la integración con nuestro sistema.

---

## ⚡ EJECUCIÓN RÁPIDA

### Opción 1: Ejecutar todos los tests automáticamente

```bash
python tests_para_equipo_a.py --all
```

**Resultado esperado:**
```
🚀 SUITE DE TESTS PARA EQUIPO A → EQUIPO B (ULEAM)
======================================================================
✅ PASÓ: Health Check
✅ PASÓ: TEST 1: tour.purchased
✅ PASÓ: TEST 2: booking.confirmed
✅ PASÓ: TEST 3: recommendation.created
✅ PASÓ: TEST 4: Payload mínimo
✅ PASÓ: TEST 5: Firma inválida (debe fallar)

📈 Total: 6/6 tests exitosos (100.0%)
🎉 ¡TODOS LOS TESTS PASARON!
```

### Opción 2: Menú interactivo (elegir tests)

```bash
python tests_para_equipo_a.py
```

Muestra un menú donde pueden elegir qué test ejecutar.

---

## 📋 TESTS INCLUIDOS

### ✅ TEST 1: tour.purchased
**¿Qué prueba?** Envía un evento cuando un usuario compra un tour.

**Payload de ejemplo:**
```json
{
  "event": "tour.purchased",
  "timestamp": "2026-01-28T10:00:00Z",
  "data": {
    "tour_id": "tour_001",
    "user_id": "user_123",
    "user_email": "juan.perez@example.com",
    "tour_name": "Tour a Baños de Agua Santa",
    "price": 150.00,
    "persons": 2
  },
  "source": "equipo-a-recomendaciones"
}
```

**Respuesta esperada (200 OK):**
```json
{
  "status": "ok",
  "message": "Webhook received and processed",
  "event": "tour.purchased"
}
```

---

### ✅ TEST 2: booking.confirmed
**¿Qué prueba?** Envía un evento cuando se confirma una reserva.

**Payload de ejemplo:**
```json
{
  "event": "booking.confirmed",
  "timestamp": "2026-01-28T10:00:00Z",
  "data": {
    "booking_id": "booking_456",
    "user_id": "user_789",
    "tour_name": "Tour al Volcán Cotopaxi",
    "amount": 120.00
  },
  "source": "equipo-a-recomendaciones"
}
```

---

### ✅ TEST 3: recommendation.created
**¿Qué prueba?** Envía un evento cuando se crea una recomendación.

**Payload de ejemplo:**
```json
{
  "event": "recommendation.created",
  "timestamp": "2026-01-28T10:00:00Z",
  "data": {
    "recommendation_id": "rec_789",
    "user_id": "user_456",
    "recommended_tour_name": "Tour Galápagos Express",
    "reason": "Basado en tu interés en naturaleza",
    "score": 0.95
  },
  "source": "equipo-a-recomendaciones"
}
```

---

### ✅ TEST 4: Payload mínimo
**¿Qué prueba?** Verifica que nuestro sistema acepta payloads con campos mínimos.

---

### ✅ TEST 5: Firma inválida
**¿Qué prueba?** Envía webhook con firma incorrecta.

**Resultado esperado:** `401 Unauthorized` (esto es correcto, valida que la seguridad funciona)

---

### ✅ TEST 6: Health Check
**¿Qué prueba?** Verifica que nuestro servicio está online.

**URL:** https://heuristically-farraginous-marquitta.ngrok-free.dev/api/v1/health

---

## 🔐 CONFIGURACIÓN USADA EN LOS TESTS

```python
SECRET = "integracion-turismo-2026-uleam"
URL = "https://heuristically-farraginous-marquitta.ngrok-free.dev/api/v1/equipo-a/webhook"
```

**Método de firma:**
```python
mensaje = json.dumps(payload, sort_keys=True, separators=(',', ':'))
firma = hmac.new(SECRET.encode(), mensaje.encode(), hashlib.sha256).hexdigest()
```

**Headers:**
```python
{
  "Content-Type": "application/json",
  "X-Signature": firma
}
```

**⚠️ IMPORTANTE:** Usar `data=mensaje` en vez de `json=payload`

---

## 📊 INTERPRETACIÓN DE RESULTADOS

### ✅ Test exitoso (200 OK):
```
✅ ¡ÉXITO! Webhook enviado y procesado correctamente
📦 Response: {"status": "ok", ...}
```

### ❌ Error 401 (Firma inválida):
```
❌ ERROR 401: Firma HMAC inválida

💡 Verificar:
   1. Secret key: integracion-turismo-2026-uleam
   2. Usar json.dumps con sort_keys=True y separators=(',', ':')
   3. Enviar con data=mensaje (NO json=payload)
```

### ❌ Timeout/Connection Error:
```
❌ TIMEOUT: Servidor de Equipo B no responde
💡 Verificar que ngrok de ULEAM esté corriendo
```

---

## 🎯 EVENTOS QUE PUEDEN ENVIAR

Nuestro sistema acepta estos eventos de Equipo A:

| Evento | Descripción | Cuándo usar |
|--------|-------------|-------------|
| `tour.purchased` | Usuario compró un tour | Al confirmar pago de tour |
| `booking.confirmed` | Reserva confirmada | Al confirmar reserva |
| `recommendation.created` | Recomendación creada | Al generar recomendación para usuario |

---

## 📞 ENDPOINTS DISPONIBLES

### 1. Recibir webhook (POST)
```
POST https://heuristically-farraginous-marquitta.ngrok-free.dev/api/v1/equipo-a/webhook
```

**Headers requeridos:**
- `Content-Type: application/json`
- `X-Signature: [firma HMAC-SHA256]`

**Campos requeridos en payload:**
- `event` (string)
- `timestamp` (string ISO 8601)
- `data` (object)
- `source` (string)

### 2. Health Check (GET)
```
GET https://heuristically-farraginous-marquitta.ngrok-free.dev/api/v1/health
```

Sin autenticación, solo verificar que el servicio está online.

### 3. Status de integración (GET)
```
GET https://heuristically-farraginous-marquitta.ngrok-free.dev/api/v1/equipo-a/status
```

Muestra estadísticas de la integración.

---

## 🚀 PASOS PARA EJECUTAR

1. **Descargar el archivo** `tests_para_equipo_a.py`

2. **Instalar dependencias** (si no las tienen):
   ```bash
   pip install requests
   ```

3. **Ejecutar tests:**
   ```bash
   # Opción A: Todos los tests
   python tests_para_equipo_a.py --all
   
   # Opción B: Menú interactivo
   python tests_para_equipo_a.py
   ```

4. **Revisar resultados**

5. **Si todos pasan:** ✅ Integración lista

6. **Si algunos fallan:** Revisar mensajes de error y ajustar código

---

## 📝 MODIFICAR LOS TESTS

Pueden modificar los datos en el script:

```python
# Cambiar datos de ejemplo en test_tour_purchased()
payload = {
    "event": "tour.purchased",
    "data": {
        "tour_id": "SU_TOUR_ID",  # ← Cambiar aquí
        "user_id": "SU_USER_ID",  # ← Cambiar aquí
        # ...
    }
}
```

---

## ✅ CHECKLIST ANTES DE EJECUTAR

- [ ] Verificar que nuestro ngrok está activo
- [ ] Verificar que payment-service está corriendo (puerto 8001)
- [ ] Tener Python 3.7+ instalado
- [ ] Tener librería `requests` instalada
- [ ] Copiar el archivo `tests_para_equipo_a.py`
- [ ] Ejecutar los tests

---

## 🎯 RESULTADO ESPERADO

Si todo funciona correctamente, verán:

```
🎉 ¡TODOS LOS TESTS PASARON!
✅ La integración Equipo A → Equipo B está funcionando correctamente
```

Esto significa que:
- ✅ Pueden enviarnos webhooks correctamente
- ✅ La firma HMAC está funcionando
- ✅ Nuestro sistema procesa sus eventos
- ✅ La integración está lista para producción

---

## 📞 SOPORTE

**Si tienen problemas:**

1. Ejecutar el test problemático individualmente
2. Copiar el output completo
3. Contactar con el error específico

**Estado de nuestros servicios:**
- Servicio: ONLINE ✅
- ngrok: ACTIVO ✅
- Webhook endpoint: FUNCIONANDO ✅

---

**¡Listos para recibir sus webhooks!** 🚀

**Equipo B - ULEAM**
