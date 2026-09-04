# AI Service - Sistema de Reservas ULEAM

**Pilar 3 (20%)**: Chatbot Multimodal con IA + MCP Tools

Servicio de chat con inteligencia artificial que soporta:
- **Texto**: Conversaciones naturales con context awareness
- **Imagen**: OCR y análisis de imágenes (espacios, documentos)
- **MCP Tools**: 5 herramientas de integración con backend

## 🏗️ Arquitectura

### Stack Tecnológico
- **Framework**: FastAPI + Python 3.14
- **Base de Datos**: PostgreSQL 17
- **LLM Providers**:
  - Google Gemini Pro (texto + visión)
  - Groq (Llama 3, Mixtral - ultra rápido)
- **ORM**: SQLAlchemy 2.0
- **Validación**: Pydantic v2

### Patrones de Diseño Implementados

**SOLID + Clean Code**:
1. **Strategy Pattern** - `app/adapters/`: Intercambio de LLM providers sin modificar código
2. **Factory Pattern** - `adapter_factory.py`: Creación centralizada de adapters
3. **Repository Pattern** - `conversation_service.py`: Abstracción del acceso a datos
4. **Dependency Injection** - FastAPI `Depends()`: Inyección de sesiones de BD

## 📁 Estructura del Proyecto

```
ai-service/
├── main.py                          # Aplicación FastAPI
├── init_ai_db.sql                   # Schema de BD
├── requirements.txt                 # Dependencias Python
├── .env.example                     # Template de variables
├── README.md                        # Este archivo
│
└── app/
    ├── __init__.py
    ├── config.py                    # Configuración (Pydantic Settings)
    ├── database.py                  # SQLAlchemy setup
    │
    ├── models/                      # SQLAlchemy Models
    │   ├── __init__.py
    │   ├── conversation.py          # Modelo Conversation
    │   ├── message.py               # Modelo Message
    │   └── tool_execution.py        # Modelo ToolExecution
    │
    ├── schemas/                     # Pydantic Schemas
    │   ├── __init__.py
    │   └── chat.py                  # Request/Response schemas
    │
    ├── adapters/                    # LLM Providers (Strategy Pattern)
    │   ├── __init__.py
    │   ├── base.py                  # Abstract LLMProvider
    │   ├── gemini_adapter.py        # Google Gemini
    │   ├── groq_adapter.py          # Groq (Llama 3)
    │   └── adapter_factory.py       # Factory Pattern
    │
    ├── services/                    # Lógica de negocio
    │   ├── __init__.py
    │   ├── conversation_service.py  # Repository Pattern
    │   └── orchestrator.py          # Orquestador principal
    │
    └── routes/                      # API Endpoints
        ├── __init__.py
        ├── health.py                # Health checks
        └── chat.py                  # Chat endpoints
```

## 🚀 Setup Rápido

### 1. Crear Base de Datos

```powershell
# Conectar a PostgreSQL
cd "C:\Program Files\PostgreSQL\17\bin"

# Crear database
.\psql.exe -U postgres -c "CREATE DATABASE ai_service_db OWNER Reservas_ULEAM;"

# Ejecutar schema
.\psql.exe -U postgres -d ai_service_db -f "C:\ReservasUleam2025\UleamBack\ai-service\init_ai_db.sql"
```

### 2. Obtener API Keys (Gratis)

**Google Gemini**:
1. Ir a https://makersuite.google.com/app/apikey
2. Crear API key
3. Copiar el token

**Groq**:
1. Ir a https://console.groq.com/keys
2. Crear API key
3. Copiar el token

### 3. Configurar Variables de Entorno

Copiar `.env.example` a `.env`:

```powershell
cd C:\ReservasUleam2025\UleamBack\ai-service
Copy-Item .env.example .env
```

Editar `.env` con tus valores:

```env
# Database
DATABASE_URL=postgresql://Reservas_ULEAM:123456@localhost:5432/ai_service_db

# LLM Providers
GEMINI_API_KEY=tu_api_key_aqui
GROQ_API_KEY=tu_api_key_aqui
DEFAULT_LLM_PROVIDER=gemini

# JWT (mismo secret que otros servicios)
JWT_SECRET=<JWT_SECRET-definido-en-.env>

# Server
PORT=5000
HOST=0.0.0.0
ENVIRONMENT=development
```

### 4. Instalar Dependencias

**IMPORTANTE**: Usar el entorno virtual `.venv-1` (Python 3.14) donde están instaladas las librerías:

```powershell
cd C:\ReservasUleam2025\UleamBack\ai-service
c:\ReservasUleam2025\.venv-1\Scripts\python.exe -m pip install -r requirements.txt
```

### 5. Iniciar Servicio

**IMPORTANTE**: Usar el Python del entorno virtual, no el del sistema:

```powershell
# OPCIÓN 1: Activar entorno virtual primero (RECOMENDADO)
cd C:\ReservasUleam2025\UleamBack\ai-service
c:\ReservasUleam2025\.venv-1\Scripts\Activate.ps1
uvicorn main:app --reload --port 5000

# OPCIÓN 2: Usar Python del entorno directamente
cd C:\ReservasUleam2025\UleamBack\ai-service
c:\ReservasUleam2025\.venv-1\Scripts\python.exe -m uvicorn main:app --reload --port 5000
```

> **Nota**: El módulo es `main:app` (main.py está en la raíz), NO `app.main:app`

El servicio estará disponible en:
- **API**: http://localhost:5000
- **Swagger UI**: http://localhost:5000/api/v1/docs
- **ReDoc**: http://localhost:5000/api/v1/redoc

## 📡 API Endpoints

### Health Check

```bash
# Health básico
GET http://localhost:5000/api/v1/health

Response:
{
  "status": "healthy",
  "service": "ai-service",
  "version": "1.0.0"
}

# Health detallado
GET http://localhost:5000/api/v1/health/detailed

Response:
{
  "status": "healthy",
  "database": {"connected": true, "latency_ms": 12.5},
  "providers": {
    "gemini": {"configured": true, "available": true},
    "groq": {"configured": true, "available": true}
  },
  "default_provider": "gemini"
}
```

### Chat

```bash
# Enviar mensaje
POST http://localhost:5000/api/v1/chat/message
Content-Type: application/json

{
  "content": "Hola, quiero reservar un espacio para mañana",
  "usuario_id": 1,
  "conversation_id": null,
  "provider": "gemini",
  "temperature": 0.7
}

Response:
{
  "conversation_id": 123,
  "user_message": {
    "id": 456,
    "role": "user",
    "content": "Hola, quiero reservar un espacio para mañana",
    "created_at": "2025-01-15T10:30:00Z"
  },
  "assistant_message": {
    "id": 457,
    "role": "assistant",
    "content": "¡Hola! Con gusto te ayudo...",
    "created_at": "2025-01-15T10:30:02Z"
  },
  "model": "gemini-2.5-flash",
  "provider": "gemini",
  "tokens_used": 150
}
```

```bash
# Listar conversaciones de usuario
GET http://localhost:5000/api/v1/chat/conversations/1?limit=20

Response:
{
  "conversations": [
    {
      "id": 123,
      "usuario_id": 1,
      "title": "Reserva de espacio",
      "message_count": 5,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T11:00:00Z"
    }
  ],
  "total": 1
}
```

```bash
# Ver mensajes de conversación
GET http://localhost:5000/api/v1/chat/conversations/123/messages

Response:
{
  "id": 123,
  "usuario_id": 1,
  "title": "Reserva de espacio",
  "message_count": 5,
  "messages": [
    {
      "id": 456,
      "role": "user",
      "content": "Hola...",
      "created_at": "2025-01-15T10:30:00Z"
    },
    {
      "id": 457,
      "role": "assistant",
      "content": "¡Hola!...",
      "created_at": "2025-01-15T10:30:02Z"
    }
  ],
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

```bash
# Listar providers disponibles
GET http://localhost:5000/api/v1/chat/providers

Response:
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

### Multimodal (Imagen)

```bash
# Analizar imagen
POST http://localhost:5000/api/v1/chat/message
Content-Type: application/json

{
  "content": "¿Qué ves en esta imagen?",
  "usuario_id": 1,
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "provider": "gemini"
}

Response:
{
  "assistant_message": {
    "content": "Veo una sala de conferencias con capacidad para 20 personas..."
  }
}
```

## 🧪 Testing

### Test Manual con PowerShell

```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:5000/api/v1/health" | Select-Object -Expand Content

# Chat
$body = @{
    content = "Hola"
    usuario_id = 1
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:5000/api/v1/chat/message" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

### Test con cURL

```bash
# Health check
curl http://localhost:5000/api/v1/health

# Chat
curl -X POST http://localhost:5000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"content": "Hola", "usuario_id": 1}'
```

## 🛠️ Troubleshooting

### Error: Database connection failed

```powershell
# Verificar PostgreSQL está corriendo
Get-Service -Name postgresql*

# Verificar conexión
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -c "SELECT 1"

# Verificar database existe
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -c "\l"
```

### Error: LLM provider not configured

Verificar `.env` tiene las API keys:
```bash
GEMINI_API_KEY=...
GROQ_API_KEY=...
```

### Error: Import errors

```powershell
# Reinstalar dependencias
pip install -r requirements.txt --upgrade
```

### Ver logs

Los logs se guardan en `ai_service.log`:

```powershell
Get-Content ai_service.log -Tail 50 -Wait
```

## 📊 Base de Datos

### Tablas

1. **conversation**: Conversaciones de usuarios
2. **message**: Mensajes (user/assistant/system)
3. **tool_execution**: Ejecuciones de MCP tools

### Índices

15 índices optimizan:
- Búsquedas por usuario
- Filtrado por rol
- Búsqueda en JSONB (tool_calls, parameters)
- Ordenamiento temporal

### Vistas

- `conversation_stats`: Estadísticas por conversación
- `tool_usage_stats`: Uso de herramientas MCP

## 🎯 Próximos Pasos (Commit 2 y 3)

### Commit 2: MCP Tools + Multimodal
- [ ] Implementar 5 MCP tools (consultar espacios, reservas, etc.)
- [ ] Mejorar procesamiento de imágenes
- [ ] Tool calling automático

### Commit 3: UI + Documentación
- [ ] Frontend React chat interface
- [ ] WebSocket para streaming
- [ ] Documentación completa

## 📚 Referencias

- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Google Gemini**: https://ai.google.dev/docs
- **Groq**: https://console.groq.com/docs
- **Pydantic**: https://docs.pydantic.dev/

## 👥 Equipo

**Sistema de Reservas ULEAM**  
Pilar 3 - Chatbot con IA (20%)

---

