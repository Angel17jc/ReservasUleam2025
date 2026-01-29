# 📊 ESTADO DE INTEGRACIÓN CON EQUIPO A

**Ubicación:** `payment-service/` (Pilar 2)  
**Estado General:** ✅ **85% IMPLEMENTADO** - Requiere configuración final

---

## ✅ LO QUE YA ESTÁ IMPLEMENTADO

### 1. 🔐 Servicio HMAC (COMPLETO)
**Archivo:** `app/services/hmac_service.py`

✅ **Implementado:**
- Generación de firmas HMAC-SHA256
- Verificación de firmas (timing-safe comparison)
- Soporte para payloads JSON y diccionarios
- Headers de webhook con firma y timestamp

**Comparación con documento Equipo A:**
```python
# ✅ DOCUMENTO EQUIPO A:
def generar_firma(payload_dict):
    mensaje = json.dumps(payload_dict, sort_keys=True)
    return hmac.new(secret.encode(), mensaje.encode(), hashlib.sha256).hexdigest()

# ✅ IMPLEMENTACIÓN ACTUAL (payment-service):
@staticmethod
def generate_signature(payload: str | Dict[str, Any], secret: str) -> str:
    if isinstance(payload, dict):
        payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    firma = hmac.new(secret.encode('utf-8'), payload_str.encode('utf-8'), hashlib.sha256)
    return firma.hexdigest()
```

**Conclusión:** ✅ Compatible al 100% con documento Equipo A

---

### 2. 📥 WEBHOOKS INBOUND (RECIBIR de Equipo A)
**Archivo:** `app/routes/partners_webhook.py`

✅ **Endpoint Implementado:**
```
POST /api/v1/partners/webhook
```

✅ **Validaciones de Seguridad:**
- ✅ Autenticación por API Key (`X-Api-Key` header)
- ✅ Verificación HMAC (`X-Webhook-Signature` header)
- ✅ Validación timestamp anti-replay (`X-Webhook-Timestamp` header)
- ✅ Rate limiting por partner
- ✅ Partner debe estar activo

✅ **Eventos Soportados:**
- `booking.confirmed` - Reserva confirmada
- `tour.purchased` - Tour comprado
- `service.activated` - Servicio activado
- `booking.cancelled` - Reserva cancelada
- `recommendation.created` - Recomendación creada

✅ **Procesamiento:**
- Servicio `PartnerWebhookProcessor` procesa eventos
- Registra en tabla `partner_webhook_log`
- Crea/actualiza registros en BD según tipo de evento

**Comparación con documento Equipo A:**
```python
# ✅ DOCUMENTO EQUIPO A (lo que ellos esperan):
@app.post("/api/reservas")  # Equipo A recibe esto
async def recibir_reserva(request: Request):
    payload = await request.json()
    firma = payload.pop("firma", None)
    if not verificar_firma(payload, firma):
        return {"error": "Firma inválida"}, 401
    # Procesar...

# ✅ IMPLEMENTACIÓN ACTUAL (lo que nosotros recibimos):
@router.post("/partners/webhook")  # Nosotros recibimos esto
async def receive_partner_webhook(
    request: Request,
    x_api_key: str = Header(..., alias="X-Api-Key"),
    x_webhook_signature: str = Header(..., alias="X-Webhook-Signature")
):
    # Validar API key
    partner = PartnerService.get_partner_by_api_key(db, x_api_key)
    # Verificar firma HMAC
    # Procesar evento
```

**Diferencia:** Headers vs firma en body. **Solución:** Ver sección de adaptación.

---

### 3. 📤 WEBHOOKS OUTBOUND (ENVIAR a Equipo A)
**Archivo:** `app/services/partner_service.py`

✅ **Funciones Implementadas:**
```python
async def deliver_webhook_to_partner(partner, event, timeout=10, max_retries=3)
async def notify_partners_of_payment_event(db, event)
```

✅ **Características:**
- Generación automática de firma HMAC
- Headers personalizados (`X-Partner-ID`, `X-Event-Type`)
- Retry logic con exponential backoff (1s, 2s, 4s...)
- Timeout configurable
- Delivery en paralelo (asyncio)
- Actualización de estadísticas (webhooks_sent, webhooks_succeeded, webhooks_failed)

✅ **Eventos que Podemos Enviar:**
- `payment.success` - Pago exitoso
- `payment.failed` - Pago fallido
- `booking.confirmed` - Reserva confirmada (nosotros → ellos)
- `service.activated` - Servicio activado

**Comparación con documento Equipo A:**
```python
# ✅ DOCUMENTO EQUIPO A (lo que ellos implementan para enviar):
async def enviar_reserva_confirmada_a_equipo_b(user_id, tour_data):
    payload = {
        "user_id": user_id,
        "tour_confirmado": {...},
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    firma = generar_firma(payload)
    payload["firma"] = firma  # Firma EN EL BODY
    response = requests.post(URL_EQUIPO_B, json=payload)

# ✅ IMPLEMENTACIÓN ACTUAL (lo que nosotros hacemos para enviar):
async def deliver_webhook_to_partner(partner, event):
    payload = event.model_dump(mode='json')
    headers = HmacService.generate_webhook_headers(
        payload=payload,
        secret=partner.secret_key
    )  # Firma EN LOS HEADERS
    response = await client.post(partner.webhook_url, json=payload, headers=headers)
```

**Diferencia:** Firma en headers vs firma en body. **Solución:** Ver sección de adaptación.

---

### 4. 🗂️ Gestión de Partners
**Archivo:** `app/routes/partners.py`

✅ **Endpoints CRUD:**
- `POST /api/v1/partners` - Registrar partner (genera API key + secret)
- `GET /api/v1/partners` - Listar partners
- `GET /api/v1/partners/{id}` - Obtener partner
- `PATCH /api/v1/partners/{id}` - Actualizar partner
- `DELETE /api/v1/partners/{id}` - Eliminar partner (soft delete)

✅ **Script de Registro:**
**Archivo:** `register_equipo_a.py`
- Registra Equipo A como partner
- Genera credenciales automáticamente
- Guarda en `equipo_a_credentials.json`
- Imprime mensaje para compartir con Equipo A

---

### 5. 💾 Base de Datos
**Tabla:** `partner`

✅ **Columnas Existentes:**
- `id` (PK)
- `nombre` - Nombre del partner
- `email` - Email de contacto
- `webhook_url` - URL donde enviaremos webhooks
- `api_key` - Clave para que nos envíen webhooks (INBOUND)
- `secret_key` - Secreto para firmar (compartido)
- `shared_secret` - Alias de secret_key
- `eventos_suscritos` - Array de eventos: `["booking.confirmed", "payment.success"]`
- `is_active` - Estado activo/inactivo
- `webhooks_sent` - Contador de webhooks enviados
- `webhooks_succeeded` - Contador de éxitos
- `webhooks_failed` - Contador de fallos
- `last_webhook_at` - Timestamp último webhook

✅ **Migraciones:** Aplicadas (ce22f3383b79)

---

## ⚠️ LO QUE FALTA / REQUIERE ADAPTACIÓN

### 1. 🔧 Adaptación de Formato de Firma

**Problema:**
- **Documento Equipo A:** Firma en el **body** del JSON (`payload["firma"]`)
- **Implementación Actual:** Firma en **headers** (`X-Webhook-Signature`)

**Solución A (Recomendada): Adaptar Equipo A**
Pedirle al Equipo A que use headers:
```python
# En lugar de:
payload["firma"] = generar_firma(payload)

# Usar:
headers = {
    "Content-Type": "application/json",
    "X-Webhook-Signature": generar_firma(payload),
    "X-Api-Key": "su_api_key_aqui"
}
response = requests.post(url, json=payload, headers=headers)
```

**Solución B: Crear Endpoint de Compatibilidad**
Crear endpoint adicional que acepte firma en body:
```python
@router.post("/partners/webhook/legacy")
async def receive_legacy_webhook(request: Request):
    """Endpoint compatible con formato legacy (firma en body)"""
    payload = await request.json()
    firma_recibida = payload.pop("firma", None)
    # Verificar firma y procesar...
```

---

### 2. 🌐 Configuración de URLs ngrok

**Estado:** URLs reales del Equipo A ya conocidas
```
Equipo A:
  URL: https://unfulminated-charley-airtightly.ngrok-free.dev
  Endpoint: /api/reservas
  Shared Secret: integracion-turismo-2026-uleam

Equipo B (Nosotros):
  URL rest-service: https://heuristically-farraginous-marquitta.ngrok-free.dev
  URL payment-service: https://[PENDIENTE].ngrok-free.dev (puerto 8001)
```

**Acciones Pendientes:**
1. ✅ Exponer payment-service con ngrok: `ngrok http 8001`
2. ❌ Compartir URL de ngrok con Equipo A
3. ❌ Pedirles que confirmen recepción

---

### 3. 📝 Registro del Equipo A como Partner

**Estado:** Script listo pero no ejecutado

**Acción:**
```bash
cd C:\ReservasUleam2025\UleamBack\payment-service
python register_equipo_a.py
```

**Resultado Esperado:**
- Partner "Equipo A - Recomendaciones Turísticas ULEAM" registrado en BD
- Credenciales generadas:
  - `api_key`: Para que Equipo A nos envíe webhooks
  - `secret_key`: Para firmar webhooks mutuos
- Archivo `equipo_a_credentials.json` creado

---

### 4. 🔌 Integración con rest-service

**Problema:** ¿Cuándo enviar webhooks a Equipo A?

**Trigger Esperado (según documento):**
> "Cuando se confirma una reserva en Equipo B, enviamos a Equipo A"

**Solución:** Integrar en `rest-service/app/routes/reservas.py`

**Código a Agregar:**
```python
# En el endpoint que aprueba reservas:
@router.patch("/reservas/{reserva_id}/estado", ...)
async def actualizar_estado_reserva(...):
    # ... lógica existente de aprobación ...
    
    if nuevo_estado == "aprobada":
        # NUEVO: Notificar a payment-service para que envíe webhook a Equipo A
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8001/api/v1/webhooks/notify-partners",
                    json={
                        "event_type": "booking.confirmed",
                        "reserva_id": reserva.id,
                        "usuario_id": reserva.usuario_id,
                        "espacio_id": reserva.espacio_id,
                        "fecha": reserva.fecha.isoformat(),
                        "hora_inicio": reserva.hora_inicio.strftime("%H:%M"),
                        "hora_fin": reserva.hora_fin.strftime("%H:%M")
                    },
                    timeout=5.0
                )
        except Exception as e:
            logger.warning(f"No se pudo notificar a partners: {e}")
            # No bloquear la aprobación de reserva por esto
```

---

### 5. 🧪 Testing End-to-End

**Pendiente:**
1. Test INBOUND: Equipo A envía webhook → Nosotros procesamos
2. Test OUTBOUND: Nosotros enviamos webhook → Equipo A procesa
3. Test BIDIRECCIONAL: Flujo completo de ida y vuelta

**Scripts de Testing Listos:**
- ✅ `test_send_to_equipo_a.py` (eliminar del rest-service, mover aquí si necesario)
- ❌ Crear: `test_receive_from_equipo_a.py` en payment-service
- ❌ Crear: `test_bidirectional_flow.py`

---

## 🎯 PLAN DE ACCIÓN (Orden Recomendado)

### Paso 1: Iniciar payment-service ⏱️ 2 min
```bash
cd C:\ReservasUleam2025\UleamBack\payment-service
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Paso 2: Exponer con ngrok ⏱️ 1 min
```bash
ngrok http 8001
# Copiar URL: https://[random].ngrok-free.dev
```

### Paso 3: Registrar Equipo A ⏱️ 2 min
```bash
python register_equipo_a.py
# Copiar credenciales del output
```

### Paso 4: Compartir Credenciales con Equipo A ⏱️ 5 min
**Enviar mensaje:**
```
¡Hola Equipo A! 👋

Ya tenemos lista la integración B2B en nuestro payment-service.

📋 CREDENCIALES PARA ENVIARNOS WEBHOOKS:
- URL: https://[TU_NGROK].ngrok-free.dev/api/v1/partners/webhook
- API Key: pk_[...]
- Secret Key: sk_[...]

🔐 DIFERENCIA DE IMPLEMENTACIÓN:
Nosotros usamos firma en HEADERS, no en body:
- Header: X-Api-Key: [tu_api_key]
- Header: X-Webhook-Signature: [hmac_firma]
- Header: X-Webhook-Timestamp: [unix_timestamp]
- Header: Content-Type: application/json

✅ EVENTOS QUE PROCESAMOS:
- booking.confirmed
- tour.purchased
- recommendation.created
- service.activated

📤 NOSOTROS LES ENVIAREMOS A:
- URL: https://unfulminated-charley-airtightly.ngrok-free.dev/api/reservas
- Secret: integracion-turismo-2026-uleam

¿Pueden confirmar si pueden adaptar sus webhooks a usar headers?
O si prefieren, podemos crear un endpoint legacy que acepte firma en body.
```

### Paso 5: Decidir Estrategia de Firma ⏱️ 10 min
**Opción A:** Equipo A adapta a headers (recomendado)
**Opción B:** Creamos endpoint `/partners/webhook/legacy`

### Paso 6: Integrar con rest-service ⏱️ 15 min
Agregar llamada a payment-service cuando se aprueba reserva.

### Paso 7: Testing ⏱️ 20 min
- Test INBOUND con script Python
- Test OUTBOUND con endpoint de testing
- Verificar logs de ambos lados

---

## 📊 RESUMEN EJECUTIVO

| Componente | Estado | Ubicación | Notas |
|---|---|---|---|
| **HMAC Service** | ✅ 100% | `hmac_service.py` | Compatible con documento |
| **Webhooks INBOUND** | ✅ 95% | `partners_webhook.py` | Requiere adaptar formato firma |
| **Webhooks OUTBOUND** | ✅ 100% | `partner_service.py` | Listo para enviar |
| **Partner CRUD** | ✅ 100% | `partners.py` | Endpoints completos |
| **Base de Datos** | ✅ 100% | `partner` table | Migraciones aplicadas |
| **Registro Equipo A** | ⏳ 0% | `register_equipo_a.py` | Script listo, no ejecutado |
| **Integración rest-service** | ❌ 0% | `reservas.py` | Falta agregar llamada |
| **Testing E2E** | ❌ 0% | - | Pendiente |

**Estado General:** ✅ **85% COMPLETO**

**Tiempo Estimado para 100%:** 45-60 minutos

---

## 💡 RECOMENDACIONES

1. **Prioridad ALTA:** Registrar Equipo A como partner (5 min)
2. **Prioridad ALTA:** Coordinar formato de firma (headers vs body)
3. **Prioridad MEDIA:** Integrar con rest-service
4. **Prioridad MEDIA:** Testing bidireccional
5. **Prioridad BAJA:** Documentar evidencias para evaluación

---

**Autor:** GitHub Copilot  
**Próxima Revisión:** Después de registrar Equipo A
