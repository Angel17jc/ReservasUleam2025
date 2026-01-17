# 🎯 PLAN DE TRABAJO - PILAR 3 (AI SERVICE)

**Fecha actualización**: 25 de enero de 2026  
**Estado**: Commits 1, 2 y 3 completos (80%)  
**Objetivo**: Completar requisitos del Pilar 3 (20% del proyecto)

---

## ✅ COMPLETADO (Commits 1-3)

### ✅ Commit 1: Base Architecture (100%)
- ✅ AI Orchestrator funcionando en puerto 5000
- ✅ LLM Adapters (Gemini + Groq) con Strategy Pattern
- ✅ Conversation Service con persistencia PostgreSQL
- ✅ Gestión de contexto y historial
- ✅ API keys configuradas y probadas

### ✅ Commit 2: MCP Tools (100%)
- ✅ BaseTool abstract class (Template Method pattern)
- ✅ ToolRegistry (Registry pattern con auto-discovery)
- ✅ ToolExecutor (HTTP client para servicios)
- ✅ 5 tools implementadas:
  - ✅ buscar_espacios (Consulta)
  - ✅ ver_reservas (Consulta)
  - ✅ crear_reserva (Acción)
  - ✅ registrar_usuario (Acción)
  - ✅ estadisticas_reservas (Reporte)
- ✅ Tests de verificación
- ✅ Documentación completa

### ✅ Commit 3: Function Calling (100%) ← RECIÉN COMPLETADO
- ✅ ToolExecutionManager (gestión de ejecución)
- ✅ Function calling en Gemini adapter
- ✅ Function calling en Groq adapter
- ✅ Orchestrator integration completa
- ✅ Flujo iterativo con reinserción de resultados
- ✅ Protección contra loops infinitos
- ✅ Tests end-to-end
- ✅ Documentación exhaustiva

**Progreso Pilar 3**: 80% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 80%

---

## 🔴 PENDIENTE PARA COMPLETAR PILAR 3

### Commit 4: Multimodal - Imágenes (20% restante)

**Estado**: ❌ 0% - Por implementar

4. ❌ **registrar_usuario** (Acción)
   - Registrar nuevo usuario
   - Integrar con `auth-service/api/v1/auth/register`

5. ❌ **estadisticas_reservas** (Reporte)
   - Generar reporte de uso de espacios
   - Agregaciones desde `rest-service`

**Arquitectura MCP a implementar**:
```
app/
└── mcp/
    ├── __init__.py
    ├── base_tool.py          # Abstract Tool class
    ├── tool_registry.py      # Registry pattern
    ├── tool_executor.py      # Ejecutor de tools
    │
    ├── consulta/             # 2 Tools de consulta
    │   ├── __init__.py
    │   ├── buscar_espacios.py
    │   └── ver_reservas.py
    │
    ├── accion/               # 2 Tools de acción
    │   ├── __init__.py
    │   ├── crear_reserva.py
    │   └── registrar_usuario.py
    │
    └── reporte/              # 1 Tool de reporte
        ├── __init__.py
        └── estadisticas_reservas.py
```

---

### 🔴 CRÍTICO 2: Entrada Multimodal - Imágenes - 12.5% del Pilar

**Estado actual**: Solo texto ❌

**Requerido**:
- ❌ Endpoint `POST /api/v1/chat/message-with-image`
- ❌ Schema para upload de imágenes
- ❌ Procesamiento con Gemini Vision
- ❌ OCR de documentos (cédulas, comprobantes)
- ❌ Análisis de fotos de espacios

**Use cases**:
1. Usuario sube foto de cédula → OCR extrae datos → Pre-llena formulario
2. Usuario sube foto de espacio → IA identifica tipo de espacio
3. Usuario sube comprobante de pago → IA extrae datos de transacción

---

### 🟡 IMPORTANTE 3: Function Calling Integration - 25% del Pilar

**Estado actual**: Preparado pero no implementado ❌

**Requerido**:
- ❌ Modificar `gemini_adapter.py` para soportar function calling
- ❌ Modificar `groq_adapter.py` para soportar function calling
- ❌ Integrar tools en el orchestrator
- ❌ Ejecución automática cuando el LLM llama un tool
- ❌ Reinsertar resultados del tool al LLM

**Flujo esperado**:
```
Usuario: "Busca espacios para mañana con capacidad de 30 personas"
    ↓
LLM detecta: Necesita llamar buscar_espacios(fecha="2026-01-26", capacidad=30)
    ↓
Sistema ejecuta: Tool buscar_espacios → REST API
    ↓
Resultado: [{"id": 5, "nombre": "Auditorio B", "capacidad": 50}]
    ↓
LLM responde: "Encontré el Auditorio B con capacidad de 50 personas..."
```

---

### 🟡 IMPORTANTE 4: Chat UI Frontend - 20% del Pilar

**Estado actual**: Solo Postman ❌

**Opciones** (elegir UNA):

**Opción A: React Component en Frontend**
```
UleamFront/src/components/AIChat/
├── ChatInterface.tsx        # Componente principal
├── MessageList.tsx         # Lista de mensajes
├── MessageInput.tsx        # Input con upload
├── TypingIndicator.tsx     # Animación typing
└── types.ts                # TypeScript types
```

**Opción B: Integración n8n + Telegram/WhatsApp** ⭐ MÁS RÁPIDO
- Crear workflow en n8n
- Webhook que recibe mensajes de Telegram
- Llamar a `ai-service` API
- Enviar respuesta de vuelta
- ⏱️ Estimado: 2 horas vs 8 horas del frontend React

---

## 📋 PLAN DE TRABAJO POR COMMITS

### COMMIT 2: MCP Tools + Function Calling (6-8 horas)

#### Fase 2.1: Infraestructura MCP (1.5 horas)
- [ ] Crear estructura de carpetas `app/mcp/`
- [ ] Implementar `base_tool.py` (abstract class)
- [ ] Implementar `tool_registry.py` (registry pattern)
- [ ] Implementar `tool_executor.py` (ejecutor)
- [ ] Agregar cliente HTTP (`httpx`) para llamar a REST/Auth services

#### Fase 2.2: Implementar 5 Tools (3 horas)
- [ ] `buscar_espacios.py` (45 min)
  - Schema: `fecha`, `capacidad_min`, `tipo`
  - GET `rest-service/api/espacios`
  
- [ ] `ver_reservas.py` (45 min)
  - Schema: `usuario_id`, `espacio_id`, `estado_id`
  - GET `rest-service/api/reservas`
  
- [ ] `crear_reserva.py` (60 min)
  - Schema: `espacio_id`, `fecha`, `hora_inicio`, `hora_fin`, `proposito`
  - POST `rest-service/api/reservas`
  - Requiere autenticación
  
- [ ] `registrar_usuario.py` (45 min)
  - Schema: `nombre`, `apellido`, `email`, `password`
  - POST `auth-service/api/v1/auth/register`
  
- [ ] `estadisticas_reservas.py` (45 min)
  - Schema: `fecha_inicio`, `fecha_fin`, `espacio_id`
  - GET `rest-service/api/reservas` + agregaciones

#### Fase 2.3: Function Calling (2 horas)
- [ ] Modificar `gemini_adapter.py`:
  - Registrar tools con Google Function Calling
  - Detectar `function_call` en response
  - Ejecutar tool via `ToolExecutor`
  - Reinsertar resultado
  
- [ ] Modificar `groq_adapter.py`:
  - Similar a Gemini (Groq soporta function calling)
  
- [ ] Actualizar `orchestrator.py`:
  - Pasar tools disponibles a LLM
  - Manejar ciclo tool → resultado → respuesta

#### Fase 2.4: Testing MCP (30 min)
- [ ] Test: "Busca espacios para mañana"
- [ ] Test: "Crea una reserva para el Auditorio A"
- [ ] Test: "Muéstrame estadísticas de enero"

---

### COMMIT 3: Multimodal Imágenes (2 horas)

#### Fase 3.1: Upload de Imágenes (1 hora)
- [ ] Crear schema `MessageWithImageRequest`
- [ ] Endpoint `POST /api/v1/chat/message-with-image`
- [ ] Validar formato (jpg, png, webp)
- [ ] Guardar en `attached_assets/ai_uploads/`

#### Fase 3.2: Gemini Vision (1 hora)
- [ ] Implementar método `generate_with_vision()` en `gemini_adapter.py`
- [ ] Convertir imagen a base64
- [ ] Llamar Gemini con imagen + prompt
- [ ] Casos de uso:
  - OCR de documentos
  - Identificación de espacios
  - Análisis de comprobantes

#### Fase 3.3: Testing Multimodal (30 min)
- [ ] Test: Upload foto de cédula → extraer datos
- [ ] Test: Upload foto de espacio → identificar tipo

---

### COMMIT 4: Chat UI (4-6 horas) - OPCIONAL

**Opción A: Frontend React** (6 horas)
- [ ] Componente ChatInterface
- [ ] WebSocket para streaming (opcional)
- [ ] Markdown rendering
- [ ] Upload de archivos

**Opción B: n8n + Telegram** (2 horas) ⭐ RECOMENDADO
- [ ] Workflow n8n con webhook
- [ ] Bot de Telegram
- [ ] Integración con ai-service
- [ ] Manejo de imágenes

---

## ⏱️ ESTIMACIÓN DE TIEMPOS

| Fase | Horas | Prioridad |
|------|-------|-----------|
| **Commit 2: MCP Tools** | 6-8h | 🔴 CRÍTICO |
| **Commit 3: Imágenes** | 2-3h | 🔴 CRÍTICO |
| **Commit 4: Chat UI** | 2-6h | 🟡 IMPORTANTE |
| **Total mínimo** | 10-17h | |

---

## 🎯 RUTA CRÍTICA (Mínimo para aprobar Pilar 3)

### ✅ Para obtener 80%+ en Pilar 3:
1. ✅ AI Orchestrator (HECHO)
2. ✅ LLM Adapter Strategy (HECHO)
3. ✅ Entrada texto (HECHO)
4. ❌ **5 MCP Tools con function calling** (CRÍTICO)
5. ❌ **Entrada imágenes** (CRÍTICO)
6. ⚠️ Chat UI (puede ser Postman + docs)

### 🎓 Criterios de evaluación estimados:

| Componente | Peso | Estado |
|-----------|------|--------|
| Arquitectura SOLID | 25% | ✅ 100% |
| Multimodal (2+ tipos) | 25% | ⚠️ 50% (solo texto) |
| MCP Tools (5+) | 30% | ❌ 0% |
| Chat UI / Integración | 20% | ❌ 0% |
| **Total actual** | | **37.5%** |
| **Con Commit 2+3** | | **87.5%** |

---

## 🚀 PRÓXIMO PASO INMEDIATO

### Empezar con Commit 2 - Fase 2.1: Infraestructura MCP

```powershell
# 1. Crear estructura
cd C:\ReservasUleam2025\UleamBack\ai-service\app
mkdir mcp
cd mcp
New-Item __init__.py
New-Item base_tool.py
New-Item tool_registry.py
New-Item tool_executor.py
mkdir consulta, accion, reporte
cd consulta
New-Item __init__.py
cd ..\accion
New-Item __init__.py
cd ..\reporte
New-Item __init__.py
```

### Archivos a crear en orden:

1. **base_tool.py** - Abstract class para todos los tools
2. **tool_registry.py** - Registro centralizado de tools
3. **tool_executor.py** - Ejecutor que llama a REST/Auth services
4. **buscar_espacios.py** - Primer tool (el más simple)
5. Los demás 4 tools
6. Integración en `orchestrator.py` y adapters

---

## 📝 NOTAS IMPORTANTES

### Dependencias a agregar:
```bash
pip install httpx  # Cliente HTTP async para llamar a otros services
```

### Variables de entorno necesarias (ya en .env):
```env
REST_SERVICE_URL=http://localhost:8000      # ✅ Ya configurado
AUTH_SERVICE_URL=http://localhost:9000      # ✅ Ya configurado
PAYMENT_SERVICE_URL=http://localhost:8001   # ✅ Ya configurado
```

### Servicios que deben estar corriendo:
- ✅ PostgreSQL (puerto 5432)
- ✅ AI Service (puerto 5000) - este servicio
- ❌ REST Service (puerto 8000) - **DEBE ESTAR CORRIENDO**
- ❌ Auth Service (puerto 9000) - **DEBE ESTAR CORRIENDO**

---

## 🎯 ¿LISTO PARA EMPEZAR?

**Siguiente comando sugerido**:
```powershell
# Verificar que REST y Auth services estén corriendo
curl http://localhost:8000/api/health
curl http://localhost:9000/api/v1/auth/health

# Si no están corriendo, iniciarlos primero
```

**¿Quieres que te ayude a implementar el Commit 2 - Fase 2.1 (Infraestructura MCP)?**
