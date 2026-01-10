# 🧪 Guía de Pruebas con Postman - AI Service

## 📥 Importar Colección

1. Abrir Postman
2. Click en **Import**
3. Seleccionar el archivo: `AI_Service_Postman_Collection.json`
4. La colección se importará con 7 carpetas de pruebas

---

## 🚀 Orden Recomendado de Pruebas

### 1️⃣ Health Checks (Verificar Servicio)

**A. Health Check Básico**
```
GET http://localhost:5000/api/v1/health
```
**Respuesta esperada:**
```json
{
  "status": "healthy",
  "service": "ai-service",
  "version": "1.0.0"
}
```

**B. Health Check Detallado**
```
GET http://localhost:5000/api/v1/health/detailed
```
**Respuesta esperada:**
```json
{
  "status": "healthy",
  "service": "ai-service",
  "version": "1.0.0",
  "database": {
    "status": "healthy",
    "url": "localhost:5432/ai_service_db"
  },
  "llm_providers": {
    "gemini": "configured",
    "groq": "configured"
  },
  "default_provider": "gemini",
  "config": {
    "port": 5000,
    "api_prefix": "/api/v1"
  }
}
```

---

### 2️⃣ Listar Providers Disponibles

```
GET http://localhost:5000/api/v1/chat/providers
```

**Respuesta esperada:**
```json
{
  "providers": [
    {
      "name": "gemini",
      "is_configured": true,
      "is_default": true,
      "models": ["gemini-2.5-flash"]
    },
    {
      "name": "groq",
      "is_configured": true,
      "is_default": false,
      "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
    }
  ],
  "default_provider": "gemini"
}
```

---

### 3️⃣ Primera Conversación con Gemini

**Request:**
```http
POST http://localhost:5000/api/v1/chat/message
Content-Type: application/json

{
  "content": "Hola, ¿cómo puedo reservar un espacio en la universidad?",
  "usuario_id": 1,
  "provider": "gemini",
  "temperature": 0.7
}
```

**Respuesta esperada:**
```json
{
  "conversation_id": 1,
  "user_message": {
    "id": 1,
    "role": "user",
    "content": "Hola, ¿cómo puedo reservar un espacio en la universidad?",
    "created_at": "2026-01-23T01:15:00"
  },
  "assistant_message": {
    "id": 2,
    "role": "assistant",
    "content": "¡Hola! Para reservar un espacio en la universidad...",
    "created_at": "2026-01-23T01:15:02"
  },
  "model": "gemini-2.5-flash",
  "provider": "gemini",
  "tokens_used": 245
}
```

**✅ Copia el `conversation_id` para continuar la conversación**

---

### 4️⃣ Continuar Conversación

**Request:**
```http
POST http://localhost:5000/api/v1/chat/message
Content-Type: application/json

{
  "content": "¿Qué espacios están disponibles?",
  "usuario_id": 1,
  "conversation_id": 1,
  "provider": "gemini",
  "temperature": 0.7
}
```

**Nota:** El AI recordará el contexto de la conversación anterior

---

### 5️⃣ Comparar Providers (Gemini vs Groq)

**A. Gemini (más detallado):**
```json
{
  "content": "¿Cuáles son los requisitos para reservar el auditorio?",
  "usuario_id": 3,
  "provider": "gemini",
  "temperature": 0.7
}
```

**B. Groq (ultra rápido):**
```json
{
  "content": "¿Cuáles son los requisitos para reservar el auditorio?",
  "usuario_id": 3,
  "provider": "groq",
  "temperature": 0.7
}
```

**Observa:**
- ⚡ Groq responde en <1 segundo
- 📝 Gemini da respuestas más elaboradas
- Ambos mantienen context awareness

---

### 6️⃣ Gestión de Conversaciones

**A. Listar conversaciones de un usuario:**
```
GET http://localhost:5000/api/v1/chat/conversations/1?limit=10&offset=0
```

**Respuesta:**
```json
{
  "conversations": [
    {
      "id": 1,
      "usuario_id": 1,
      "title": "Hola, ¿cómo puedo reservar un espacio...",
      "message_count": 4,
      "created_at": "2026-01-23T01:15:00",
      "updated_at": "2026-01-23T01:18:30"
    }
  ],
  "total": 1
}
```

**B. Ver todos los mensajes de una conversación:**
```
GET http://localhost:5000/api/v1/chat/conversations/1/messages
```

**C. Eliminar conversación:**
```
DELETE http://localhost:5000/api/v1/chat/conversations/1
```

---

## 🎯 Tests Avanzados

### Test de Context Awareness (3 mensajes secuenciales)

**Mensaje 1:**
```json
{
  "content": "Quiero reservar un espacio para 50 personas",
  "usuario_id": 4,
  "provider": "gemini"
}
```

**Mensaje 2** (usa el conversation_id del anterior):
```json
{
  "content": "¿Cuánto cuesta?",
  "usuario_id": 4,
  "conversation_id": <ID_DEL_ANTERIOR>,
  "provider": "gemini"
}
```

**Mensaje 3:**
```json
{
  "content": "¿Y si son solo 30 personas?",
  "usuario_id": 4,
  "conversation_id": <ID_DEL_ANTERIOR>,
  "provider": "gemini"
}
```

**Resultado esperado:** El AI debe recordar que hablas de reservas y capacidades

---

## 🎛️ Parámetros del Request

### Campos Obligatorios
- `content` (string): El mensaje del usuario
- `usuario_id` (integer): ID del usuario

### Campos Opcionales
- `conversation_id` (integer): Para continuar conversación existente
- `provider` (string): `"gemini"` o `"groq"` (default: gemini)
- `temperature` (float): 0.0 - 1.0
  - `0.0-0.3`: Respuestas precisas y determinísticas
  - `0.4-0.7`: Balanceado (recomendado)
  - `0.8-1.0`: Creativo e impredecible

---

## 📊 Métricas a Observar

### En el Response
- `tokens_used`: Tokens consumidos (para monitoreo de costos)
- Timestamps: Para medir latencia
- `model`: Modelo LLM utilizado
- `provider`: Provider usado

### En la Terminal del Servicio
```
INFO: → POST /api/v1/chat/message
INFO: Processing chat message: usuario_id=1, conversation_id=None, provider=gemini
INFO: Message processed: conversation_id=1, tokens=245
INFO: ← POST /api/v1/chat/message status=200 time=1234.56ms
```

---

## ⚠️ Errores Comunes

### 400 Bad Request
```json
{
  "detail": "Validation error: content cannot be empty"
}
```
**Solución:** Verifica que `content` y `usuario_id` estén presentes

### 404 Not Found
```json
{
  "detail": "Conversation 999 not found"
}
```
**Solución:** Verifica que el `conversation_id` exista

### 500 Internal Server Error
```json
{
  "detail": "Failed to process message: ..."
}
```
**Solución:** Revisa logs del servidor

---

## 🎨 Variables de Entorno en Postman (Opcional)

Puedes crear variables para reutilizar valores:

```
{{base_url}} = http://localhost:5000
{{api_prefix}} = /api/v1
{{usuario_id}} = 1
{{conversation_id}} = 1
```

Luego usar: `{{base_url}}{{api_prefix}}/chat/message`

---

## 📈 Benchmarking

### Comparar Velocidad de Providers

1. Enviar el mismo prompt a Gemini y Groq
2. Observar el header `X-Process-Time`
3. Comparar calidad de respuestas

**Esperado:**
- Groq: ~500-1000ms
- Gemini: ~1500-3000ms

---

## 🔒 Autenticación (Commit 2)

Actualmente no hay autenticación implementada. En Commit 2 se agregará:
```http
Authorization: Bearer <JWT_TOKEN>
```

---

## 📝 Notas Importantes

1. **Primera ejecución**: La primera request puede tardar más (carga de modelos)
2. **Context limit**: Máximo 20 mensajes por conversación (configurable en .env)
3. **Rate limits**: 
   - Gemini: 60 requests/minuto (free tier)
   - Groq: Muy alto (prácticamente ilimitado)
4. **Costos**: Ambos providers son GRATIS con las API keys

---

## 🎯 Ejemplos de Prompts para Probar

### Informativos
- "¿Qué necesito para hacer una reserva?"
- "Explícame el proceso de cancelación"
- "¿Qué espacios tiene disponibles la universidad?"

### Con Contexto
- "Quiero reservar para 100 personas" → "¿Cuánto cuesta?" → "¿Y para 50?"

### Creativos (temp: 0.9)
- "Dame 10 ideas para un evento universitario"
- "Sugiere nombres creativos para un auditorio"

### Precisos (temp: 0.3)
- "Lista los pasos exactos para crear una reserva"
- "¿Cuál es el horario de atención?"

---

¡Listo! Empieza con los **Health Checks** y luego prueba las conversaciones. 🚀
