# 🤖 PILAR 3: Servicio de IA Multimodal con MCP Tools

**Versión:** 1.0  
**Fecha:** 27 de Enero de 2026  
**Estado:** ✅ Desarrollo Avanzado (20% Completado)  
**Líder Técnico:** Equipo AI Service

---

## 📋 Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Arquitectura de IA](#arquitectura-de-ia)
3. [Capabilities Multimodales](#capabilities-multimodales)
4. [Stack Tecnológico](#stack-tecnológico)
5. [MCP Tools Integration](#mcp-tools-integration)
6. [Instalación y Setup](#instalación-y-setup)
7. [API Endpoints](#api-endpoints)
8. [Ejemplos de Uso](#ejemplos-de-uso)
9. [Integración con Otros Pilares](#integración-con-otros-pilares)
10. [Roadmap y Mejoras](#roadmap-y-mejoras)

---

## 🎯 Visión General

El **Pilar 3** es el cerebro inteligente de ULEAM Reservas. Proporciona un chatbot multimodal que entiende texto, procesa imágenes, y se conecta directamente con la lógica de negocio mediante herramientas de IA (MCP - Model Context Protocol).

### Responsabilidades Principales
- ✅ Chat conversacional con context awareness
- ✅ Procesamiento de imágenes (OCR, análisis)
- ✅ Integración con herramientas de backend (MCP Tools)
- ✅ Análisis de disponibilidad de espacios
- ✅ Sugerencias inteligentes de reservas
- ✅ Soporte multiidioma (español/inglés)
- ✅ Persistencia de conversaciones

### Casos de Uso Principales
```
Usuario: "¿Qué salas tenemos disponibles mañana de 14:00 a 16:00?"
AI: [Usa MCP Tool] → consulta REST → "Salas A101, B202, C303 disponibles"

Usuario: [Sube foto de documento]
AI: [OCR] → "Encontré reserva para evento grande, ¿necesitas espacio grande?"

Usuario: "Quiero reservar la sala A101 mañana a las 15:00"
AI: [Usa MCP Tool] → crea reserva → "Listo, tu reserva RES-2026-123 está pendiente"
```

---

## 🏗️ Arquitectura de IA

### Diagrama Completo

```
┌──────────────────────────────────────────────────────────────────┐
│                    PILAR 3: IA MULTIMODAL                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Cliente (Navegador / Telegram Bot)                             │
│         │                                                         │
│         ├─→ Texto: "¿Espacios libres mañana?"                   │
│         ├─→ Imagen: Foto de documento                           │
│         └─→ Audio: (futuro)                                      │
│                                                                   │
│  ┌──────────────────────────────────────────┐                   │
│  │      FastAPI + FastAPI WebSocket          │                   │
│  │      Port: 5000                           │                   │
│  │  ┌────────────────────────────────────┐  │                   │
│  │  │ POST /api/v1/chat/message         │  │                   │
│  │  │ POST /api/v1/chat/upload-image    │  │                   │
│  │  │ GET /api/v1/conversations/{id}    │  │                   │
│  │  └────────────────────────────────────┘  │                   │
│  └──────────────────────────────────────────┘                   │
│         │                                                         │
│  ┌──────▼──────────────────────────────────┐                    │
│  │   LLM Providers (Strategy Pattern)       │                    │
│  │  ┌────────────────────────────────────┐ │                    │
│  │  │ • Google Gemini Pro                │ │                    │
│  │  │ • Groq (Llama 3, Mixtral)          │ │                    │
│  │  │ • OpenAI GPT (futuro)              │ │                    │
│  │  └────────────────────────────────────┘ │                    │
│  └──────────────────────────────────────────┘                    │
│         │            │            │                              │
│  ┌──────▼────────┐ ┌──▼─────────┐ ┌───▼──────────┐              │
│  │ Conversation  │ │ Tool Engine│ │ OCR/Vision   │              │
│  │  Service      │ │            │ │   Processor  │              │
│  │  (persistencia)│ │ MCP Tools  │ │              │              │
│  └──────┬────────┘ └──┬─────────┘ └───┬──────────┘              │
│         │             │                │                        │
│         └─────────────┼────────────────┘                        │
│                       │                                         │
│         ┌─────────────▼──────────────────┐                      │
│         │  MCP Tools (5 herramientas)    │                      │
│         │                                │                      │
│         │ 1. get_available_spaces       │                      │
│         │ 2. create_booking             │                      │
│         │ 3. check_user_bookings        │                      │
│         │ 4. get_space_details          │                      │
│         │ 5. send_notification          │                      │
│         └─────────────┬──────────────────┘                      │
│                       │                                         │
│         ┌─────────────▼──────────────────┐                      │
│         │  REST Service (Pilar 2)        │                      │
│         │  + WebSocket (Real-time)       │                      │
│         │  + Auth Service (Pilar 1)      │                      │
│         │  + n8n (Pilar 4)               │                      │
│         └────────────────────────────────┘                      │
│                                                                   │
│  ┌──────────────────────────────────────┐                       │
│  │  PostgreSQL: ai_service_db            │                       │
│  │  ├─ Conversations                     │                       │
│  │  ├─ Messages                          │                       │
│  │  └─ ToolExecutions                   │                       │
│  └──────────────────────────────────────┘                       │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Componentes Clave

| Componente | Descripción |
|-----------|-----------|
| **FastAPI** | Framework web asíncrono |
| **PostgreSQL** | Almacenamiento de conversaciones |
| **LLM Adapters** | Integración con Google Gemini y Groq |
| **MCP Tools** | 5 herramientas de negocio |
| **Strategy Pattern** | Intercambio dinámico de LLM |
| **Repository Pattern** | Abstracción de datos |
| **Pydantic v2** | Validación de esquemas |

---

## 🎬 Capabilities Multimodales

### 1. Texto (Text-to-Text)
```
Entrada: "¿Cuántas reservas tengo próximos 7 días?"
Procesamiento:
├─ Parsed intent: "check_user_bookings"
├─ Contexto: usuario_id del JWT
└─ Respuesta: Genera descripción natural

Salida: "Tienes 3 reservas pendientes: Lab A101 (hoy 10:00), 
         Aula B202 (mañana 14:00), Sala C303 (jueves 15:30)"
```

---

### 2. Visión (Image-to-Text + Análisis)
```
Entrada: [Foto de documento]
Procesamiento:
├─ Carga imagen → Gemini Vision
├─ OCR → extrae texto
├─ Análisis semántico:
│   ├─ ¿Es formulario de eventos?
│   ├─ ¿Contiene fechas?
│   └─ ¿Requiere espacio específico?
└─ Generación de respuesta

Salida: "Vi que tu evento será el 2026-02-15 con 50 asistentes.
         Te recomiendo la Sala de Conferencias (cap. 100)"
```

---

### 3. MCP Tools (Acción)
```
Entrada: "Reservar Aula 101 mañana de 10:00 a 12:00"
Procesamiento:
├─ LLM entiende intención
├─ Valida parámetros:
│   ├─ espacioId = lookup("Aula 101")
│   ├─ fecha = mañana
│   ├─ horaInicio = 10:00
│   └─ horaFin = 12:00
├─ Ejecuta MCP Tool: create_booking({...})
├─ Tool llama REST: POST /api/reservas
└─ LLM genera confirmación

Salida: "✓ Reserva RES-2026-564 creada con éxito.
         Espacio: Aula 101
         Fecha: 2026-02-28 | 10:00-12:00"
```

---

## 💻 Stack Tecnológico

### Backend Framework
```
FastAPI v0.100+
├─ Python 3.11+
├─ Uvicorn (ASGI)
├─ Pydantic v2 (validación)
└─ SQLAlchemy 2.0 (ORM)
```

### LLM Providers
```
Google Gemini Pro
├─ Texto y visión
├─ Multimodal
├─ API Key: generocontent.googleapis.com
└─ Gratis (uso limitado)

Groq (Llama 3, Mixtral)
├─ Ultra-rápido (inference)
├─ Modelos open-source
├─ API Key: console.groq.com
└─ Gratis (uso limitado)
```

### Base de Datos
```
PostgreSQL 17
├─ Conversations (sesiones)
├─ Messages (historial)
├─ ToolExecutions (auditoría)
└─ Indices para query rápido
```

### Patrones de Diseño
```
✓ Strategy Pattern → Adapters para LLMs
✓ Factory Pattern → Creación de adapters
✓ Repository Pattern → Acceso a datos
✓ Dependency Injection → FastAPI Depends()
```

---

## 🛠️ MCP Tools Integration

### Herramienta 1: get_available_spaces
```json
{
  "name": "get_available_spaces",
  "description": "Obtener espacios disponibles en una fecha y rango de horas",
  "input_schema": {
    "type": "object",
    "properties": {
      "fecha": {
        "type": "string",
        "format": "date",
        "description": "Fecha en formato YYYY-MM-DD"
      },
      "horaInicio": {
        "type": "string",
        "format": "time",
        "description": "Hora inicio en formato HH:MM"
      },
      "horaFin": {
        "type": "string",
        "format": "time",
        "description": "Hora fin en formato HH:MM"
      },
      "capacidad_minima": {
        "type": "integer",
        "description": "Capacidad mínima requerida"
      }
    },
    "required": ["fecha", "horaInicio", "horaFin"]
  }
}
```

**Implementación (Python):**
```python
async def get_available_spaces(
    fecha: str,
    horaInicio: str,
    horaFin: str,
    capacidad_minima: int = 0
) -> list:
    """Llama REST: GET /api/disponibilidad"""
    response = await rest_client.get(
        f"/api/disponibilidad",
        params={
            "fecha": fecha,
            "horaInicio": horaInicio,
            "horaFin": horaFin,
            "capacidad_minima": capacidad_minima
        }
    )
    return response["data"]
```

---

### Herramienta 2: create_booking
```json
{
  "name": "create_booking",
  "description": "Crear nueva reserva",
  "input_schema": {
    "type": "object",
    "properties": {
      "espacioId": { "type": "string", "description": "UUID del espacio" },
      "titulo": { "type": "string", "description": "Título del evento" },
      "fecha": { "type": "string", "format": "date" },
      "horaInicio": { "type": "string", "format": "time" },
      "horaFin": { "type": "string", "format": "time" },
      "asistentes_estimada": { "type": "integer" },
      "tipoEventoId": { "type": "integer", "description": "ID tipo evento" }
    },
    "required": ["espacioId", "fecha", "horaInicio", "horaFin"]
  }
}
```

---

### Herramienta 3: check_user_bookings
```json
{
  "name": "check_user_bookings",
  "description": "Ver reservas del usuario autenticado",
  "input_schema": {
    "type": "object",
    "properties": {
      "estado": {
        "type": "string",
        "enum": ["Pendiente", "Aprobada", "Rechazada", "Cancelada"],
        "description": "Filtrar por estado"
      },
      "fecha_desde": { "type": "string", "format": "date" },
      "fecha_hasta": { "type": "string", "format": "date" }
    }
  }
}
```

---

### Herramienta 4: get_space_details
```json
{
  "name": "get_space_details",
  "description": "Obtener detalles completos de un espacio",
  "input_schema": {
    "type": "object",
    "properties": {
      "espacioId": {
        "type": "string",
        "description": "UUID del espacio"
      }
    },
    "required": ["espacioId"]
  }
}
```

---

### Herramienta 5: send_notification
```json
{
  "name": "send_notification",
  "description": "Enviar notificación al usuario",
  "input_schema": {
    "type": "object",
    "properties": {
      "titulo": { "type": "string" },
      "mensaje": { "type": "string" },
      "tipo": {
        "type": "string",
        "enum": ["info", "success", "warning", "error"],
        "description": "Tipo de notificación"
      }
    },
    "required": ["titulo", "mensaje"]
  }
}
```

---

## 🚀 Instalación y Setup

### Requisitos Previos
- Python 3.11+
- PostgreSQL 17
- Google Gemini API Key (gratis)
- Groq API Key (gratis)
- Redis 7+ (opcional)

### Paso 1: Crear Base de Datos
```powershell
# Conectar a PostgreSQL
cd "C:\Program Files\PostgreSQL\17\bin"

# Crear database
.\psql.exe -U postgres -c "CREATE DATABASE ai_service_db OWNER Reservas_ULEAM;"

# Ejecutar schema
.\psql.exe -U postgres -d ai_service_db -f "C:\ReservasUleam2025\UleamBack\ai-service\init_ai_db.sql"

# Verificar tablas
.\psql.exe -U postgres -d ai_service_db -c "\dt"
```

### Paso 2: Obtener API Keys

**Google Gemini:**
1. Ir a https://makersuite.google.com/app/apikey
2. Click "Create API key"
3. Copiar token

**Groq:**
1. Ir a https://console.groq.com/keys
2. Click "Create new API key"
3. Copiar token

### Paso 3: Configurar Variables de Entorno
```bash
cd C:\ReservasUleam2025\UleamBack\ai-service
cp .env.example .env

# Editar .env
```

**Contenido `.env`:**
```env
# Database
DATABASE_URL=postgresql://Reservas_ULEAM:123456@localhost:5432/ai_service_db

# LLM Providers
GEMINI_API_KEY=tu_key_aqui_desde_makersuite
GROQ_API_KEY=tu_key_aqui_desde_console_groq
DEFAULT_LLM_PROVIDER=gemini  # o groq

# JWT (compartido con otros servicios)
JWT_SECRET=<JWT_SECRET-definido-en-.env>

# Server
PORT=5000
HOST=0.0.0.0
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# REST Service (para MCP Tools)
REST_SERVICE_URL=http://localhost:8000
REST_SERVICE_AUTH_TOKEN=

# WebSocket (para notificaciones)
WEBSOCKET_SERVICE_URL=http://localhost:3001
```

### Paso 4: Instalar Dependencias
```bash
cd C:\ReservasUleam2025\UleamBack\ai-service
pip install -r requirements.txt
```

### Paso 5: Iniciar Servicio
```bash
# Modo desarrollo
python main.py

# O con uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
```

### Verificación
```powershell
# Debe estar accesible en:
curl http://localhost:5000/api/v1/docs

# Abrir en navegador:
http://localhost:5000/api/v1/docs
```

---

## 📡 API Endpoints

### 1. Crear Conversación
```http
POST /api/v1/chat/conversations
Authorization: Bearer {token}
Content-Type: application/json

{
  "titulo": "Consulta de espacios para evento",
  "contexto": "Buscando sala para 50 personas"
}

Response 201:
{
  "id": "uuid",
  "usuarioId": "uuid",
  "titulo": "Consulta de espacios para evento",
  "createdAt": "2026-01-27T14:50:00Z"
}
```

---

### 2. Enviar Mensaje
```http
POST /api/v1/chat/message
Authorization: Bearer {token}
Content-Type: application/json

{
  "conversationId": "uuid",
  "contenido": "¿Qué salas tenemos disponibles mañana de 14:00 a 16:00?",
  "tipo": "texto"
}

Response 200:
{
  "id": "uuid",
  "conversationId": "uuid",
  "usuario": { "id": "uuid", "email": "..." },
  "contenido": "¿Qué salas tenemos disponibles mañana de 14:00 a 16:00?",
  "tipo": "texto",
  "timestamp": "2026-01-27T14:51:00Z",
  "respuestaIA": {
    "id": "uuid",
    "contenido": "Encontré 3 salas disponibles: Aula A101 (cap. 30), Sala B202 (cap. 60), Auditorio C303 (cap. 200)",
    "timestamp": "2026-01-27T14:51:03Z"
  }
}
```

---

### 3. Cargar Imagen
```http
POST /api/v1/chat/upload-image
Authorization: Bearer {token}
Content-Type: multipart/form-data

files: [documento.jpg]
conversationId: uuid

Response 200:
{
  "id": "uuid",
  "tipo": "imagen",
  "url": "https://api.example.com/images/uuid.jpg",
  "analisis": {
    "texto_detectado": "Evento: Conferencia 2026...",
    "interpretacion_ia": "Documento de evento con 50 asistentes..."
  }
}
```

---

### 4. Obtener Conversación
```http
GET /api/v1/chat/conversations/{conversationId}
Authorization: Bearer {token}

Response 200:
{
  "id": "uuid",
  "titulo": "Consulta de espacios",
  "messages": [
    {
      "id": "uuid",
      "rol": "usuario",
      "contenido": "¿Salas disponibles mañana?",
      "timestamp": "2026-01-27T14:51:00Z"
    },
    {
      "id": "uuid",
      "rol": "asistente",
      "contenido": "Encontré 3 salas...",
      "timestamp": "2026-01-27T14:51:03Z"
    }
  ]
}
```

---

### 5. Listar Conversaciones
```http
GET /api/v1/chat/conversations?page=1&limit=10
Authorization: Bearer {token}

Response 200:
{
  "data": [
    {
      "id": "uuid",
      "titulo": "Consulta de espacios",
      "ultimoMensaje": "Encontré 3 salas...",
      "createdAt": "2026-01-27T14:50:00Z"
    }
  ],
  "pagination": { "page": 1, "limit": 10, "total": 5 }
}
```

---

### 6. Obtener Configuración MCP Tools
```http
GET /api/v1/chat/tools
Authorization: Bearer {token}

Response 200:
{
  "tools": [
    {
      "name": "get_available_spaces",
      "description": "Obtener espacios disponibles...",
      "input_schema": { ... }
    },
    {
      "name": "create_booking",
      "description": "Crear nueva reserva...",
      "input_schema": { ... }
    },
    ...
  ]
}
```

---

## 💬 Ejemplos de Uso

### Ejemplo 1: Consulta Texto Simple
```
Usuario: "Hola, ¿tienes disponibilidad en Aula 101 el martes de 10:00 a 12:00?"

Sistema:
├─ JWT: Extrae user_id = "user_123"
├─ LLM: Usa Gemini Pro
├─ Parsing: 
│   ├─ Espacio: "Aula 101" → lookup → UUID
│   ├─ Fecha: "martes" → +1 día
│   └─ Horario: 10:00-12:00
├─ MCP Tool: get_available_spaces(...)
├─ REST Call: GET /api/disponibilidad?...
└─ Respuesta: "Sí, el aula 101 está libre ese día"
```

---

### Ejemplo 2: Análisis de Imagen
```
Usuario: [Sube foto de documento]

Sistema:
├─ FastAPI recibe imagen
├─ Envía a Gemini Vision
├─ OCR extrae:
│   ├─ "Evento: Taller de IA"
│   ├─ "Fecha: 15 Feb 2026"
│   └─ "Asistentes: 40 personas"
├─ Análisis semántico:
│   ├─ Es evento de capacitación
│   ├─ Necesita sala mediana
│   └─ Requiere proyector
└─ Respuesta: "Vi tu evento. Recomiendo Sala B202 
             (cap. 60, proyector incluido)"
```

---

### Ejemplo 3: Crear Reserva Automática
```
Usuario: "Reserva Aula 101 para mañana a las 15:00 
         para mi clase de 25 estudiantes"

Sistema:
├─ LLM: Entiende intención
├─ Valida parámetros:
│   ├─ Espacio: Aula 101 → UUID_A101
│   ├─ Fecha: mañana → 2026-01-28
│   ├─ Hora: 15:00-17:00 (default 2 horas)
│   ├─ Asistentes: 25
│   └─ Tipo evento: clase
├─ MCP Tool: create_booking({...})
├─ REST: POST /api/reservas
│   Response: { id: "uuid", codigo: "RES-2026-999" }
├─ Webhook: WebSocket notificación
└─ Respuesta: "✓ Reserva RES-2026-999 creada!
             Aula 101, 2026-01-28, 15:00-17:00"
```

---

## 🔗 Integración con Otros Pilares

### Integración con Pilar 1 (Auth)
```
✓ Extrae user_id del JWT
✓ Valida token en cada request
✓ Contexto de usuario usado en MCP Tools
✓ Usa mismo JWT_SECRET compartido
```

---

### Integración con Pilar 2 (REST/GraphQL)
```
✓ MCP Tools llaman REST Service
✓ Ejemplo: create_booking → POST /api/reservas
✓ GET requests para disponibilidad
✓ Respeta mismos validaciones de negocio
✓ Webhooks bidireccionales posibles
```

---

### Integración con Pilar 4 (n8n)
```
✓ n8n puede disparar AI para procesamiento
✓ Ejemplo: n8n recibe imagen → pasa a AI
✓ AI análiza → envía respuesta a n8n
✓ n8n ejecuta acciones (crear reserva, notificar, etc.)
✓ Orquestación de flujos complejos
```

---

## 🗺️ Roadmap y Mejoras

### Fase 1 (Actual - 20%)
- [x] Setup básico FastAPI
- [x] Integración Google Gemini
- [x] Integración Groq
- [x] 5 MCP Tools básicos
- [x] Persistencia conversaciones
- [ ] Tests unitarios
- [ ] Performance optimization

### Fase 2 (Próxima - 40%)
- [ ] Audio input/output (whisper)
- [ ] Histórico de conversaciones avanzado
- [ ] Análisis de sentimiento
- [ ] Recomendaciones proactivas
- [ ] A/B testing de modelos LLM

### Fase 3 (Futura - 60%)
- [ ] Fine-tuning con datos ULEAM
- [ ] Retrieval Augmented Generation (RAG)
- [ ] Integración con calendar sincronización
- [ ] Soporte multiidioma robusto

### Fase 4 (Visión - 100%)
- [ ] Predicción de demanda
- [ ] Chatbot autónomo 24/7
- [ ] Integración Telegram/WhatsApp
- [ ] Reportes automáticos

---

## 📊 Monitoreo

### Métricas Clave
```
├─ Tiempo respuesta LLM (< 3 segundos)
├─ Tasa acierto MCP Tools (>90%)
├─ Conversaciones por día
├─ Usuarios activos
├─ Errores de parsing
└─ Uso de tokens LLM
```

### Logs
```
[AI] LLM Request: usuario_id=X, provider=gemini, tokens=150
[AI] MCP Tool Exec: tool=create_booking, status=success
[AI] MCP Tool Exec: tool=get_available_spaces, status=error
[AI] Conversation saved: conv_id=Y, messages=5
```

---

## ✅ Checklist de Implementación

- [x] FastAPI configurado
- [x] PostgreSQL con schema AI
- [x] Google Gemini integrado
- [x] Groq integrado
- [x] 5 MCP Tools implementadas
- [x] Repository Pattern implementado
- [x] JWT authentication
- [x] Swagger documentación
- [ ] Tests al 70%+ cobertura
- [ ] Rate limiting
- [ ] Caching de responses
- [ ] Monitoring y alertas

---

## 📚 Referencias

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Google Gemini API](https://ai.google.dev)
- [Groq API](https://console.groq.com)
- [MCP Protocol](https://modelcontextprotocol.io)
- [SQLAlchemy](https://sqlalchemy.org)
- [Pydantic](https://docs.pydantic.dev/latest/)

---

**Última Actualización:** 27 de Enero de 2026  
**Contacto:** Team AI Service ULEAM Reservas
