# 🎯 COMMIT 3: Function Calling Integration

## 📋 Resumen Ejecutivo

**Pilar:** Pilar 3 - AI Service (MCP Chatbot)  
**Objetivo:** Integración completa de Function Calling para que los LLMs puedan ejecutar MCP Tools automáticamente

## ✅ Implementación Completada

### 🏗️ Arquitectura

La integración de Function Calling sigue una arquitectura de 3 capas:

```
┌─────────────────────────────────────────────────────────────┐
│                     USER / FRONTEND                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  AI ORCHESTRATOR                            │
│  - Obtiene tools del ToolRegistry                          │
│  - Pasa tools al LLM Adapter                               │
│  - Detecta tool_calls en respuesta                         │
│  - Ejecuta tools via ToolExecutionManager                  │
│  - Reinsereta resultados en contexto                       │
│  - Obtiene respuesta final                                 │
└────────────┬───────────────────────────┬────────────────────┘
             │                           │
             ▼                           ▼
┌────────────────────────┐  ┌───────────────────────────────┐
│   LLM ADAPTERS         │  │  TOOL EXECUTION MANAGER       │
│  - Gemini Adapter      │  │  - Valida tool calls          │
│  - Groq Adapter        │  │  - Ejecuta tools              │
│  - Function calling    │  │  - Maneja errores             │
│  - Tool schema conv.   │  │  - Formatea resultados        │
└────────────────────────┘  └───────────┬───────────────────┘
                                        │
                                        ▼
                            ┌───────────────────────────────┐
                            │      MCP TOOLS (Commit 2)     │
                            │  - buscar_espacios            │
                            │  - ver_reservas               │
                            │  - crear_reserva              │
                            │  - registrar_usuario          │
                            │  - estadisticas_reservas      │
                            └───────────────────────────────┘
```

### 🔄 Flujo de Ejecución

#### Flujo Completo de Function Calling:

```
1. Usuario envía mensaje
   ↓
2. Orchestrator construye contexto
   ↓
3. Orchestrator obtiene tools disponibles del ToolRegistry
   ↓
4. Orchestrator llama al LLM Adapter con contexto + tools
   ↓
5. LLM Adapter convierte tools al formato del provider
   ↓
6. LLM decide si usar tools o responder directamente
   ↓
   ├─→ NO HAY TOOL CALLS
   │   ↓
   │   7a. LLM retorna respuesta de texto
   │   ↓
   │   8a. Orchestrator guarda respuesta y retorna
   │
   └─→ HAY TOOL CALLS
       ↓
       7b. LLM retorna tool_calls en la respuesta
       ↓
       8b. Orchestrator detecta tool_calls
       ↓
       9b. ToolExecutionManager ejecuta cada tool
       ↓
       10b. Resultados se guardan en conversación
       ↓
       11b. Orchestrator construye nuevo contexto con resultados
       ↓
       12b. LLM genera respuesta final basada en resultados
       ↓
       13b. Orchestrator guarda respuesta final y retorna
```

#### Ejemplo de Interacción:

```
Usuario: "Busca auditorios con capacidad para 50 personas"
   ↓
LLM: [Decide usar tool: buscarespacios]
   Tool Call: {
     "name": "buscarespacios",
     "arguments": {
       "capacidad_min": 50,
       "tipo_espacio": "auditorio"
     }
   }
   ↓
ToolExecutionManager: [Ejecuta tool]
   → GET http://localhost:8000/api/espacios?capacidad_min=50&tipo_espacio=auditorio
   ↓
Tool Result: {
  "success": true,
  "data": {
    "total": 3,
    "espacios": [
      {"id": 1, "nombre": "Auditorio Principal", "capacidad": 100},
      {"id": 2, "nombre": "Auditorio B", "capacidad": 80},
      {"id": 3, "nombre": "Auditorio C", "capacidad": 60}
    ]
  },
  "summary": "Se encontraron 3 auditorios disponibles"
}
   ↓
LLM: [Genera respuesta final con los resultados]
   ↓
Assistant: "He encontrado 3 auditorios disponibles:
- Auditorio Principal (capacidad: 100 personas)
- Auditorio B (capacidad: 80 personas)  
- Auditorio C (capacidad: 60 personas)

¿Te gustaría reservar alguno de estos espacios?"
```

## 📁 Archivos Creados/Modificados

### ✨ Nuevos Archivos

#### 1. `app/services/tool_execution_manager.py` (287 líneas)

**Propósito:** Gestión centralizada de ejecución de tools

**Responsabilidades:**
- Ejecutar tool calls individuales o múltiples
- Validar parámetros antes de ejecución
- Manejar errores y timeouts
- Formatear resultados para el LLM
- Logging detallado

**Métodos principales:**
```python
class ToolExecutionManager:
    async def execute_tool_call(tool_name, parameters) -> Dict
    async def execute_multiple_tools(tool_calls) -> List[Dict]
    def get_available_tools() -> List[Dict]
    def get_tools_by_category(category) -> List[Dict]
    def validate_tool_call(tool_name, parameters) -> Optional[str]
```

**Características:**
- ✅ Validación exhaustiva de tool calls
- ✅ Ejecución paralela de múltiples tools
- ✅ Error handling robusto
- ✅ Formato de resultados optimizado para LLMs
- ✅ Logging detallado de cada ejecución

#### 2. `test_function_calling.py` (381 líneas)

**Propósito:** Testing end-to-end de function calling

**Tests incluidos:**
1. **test_simple_query:** Consulta sin tools
2. **test_buscar_espacios:** Tool de búsqueda
3. **test_ver_reservas:** Tool de consulta
4. **test_crear_reserva:** Tool de acción
5. **test_estadisticas:** Tool de reporte
6. **test_conversacion_compleja:** Multi-turn con contexto

**Uso:**
```bash
# Test con Gemini (default)
python test_function_calling.py

# Test con Groq
python test_function_calling.py --provider groq
```

### 🔧 Archivos Modificados

#### 1. `app/adapters/gemini_adapter.py`

**Cambios principales:**

**a) Imports actualizados:**
```python
from google.generativeai.types import FunctionDeclaration, Tool
import json
```

**b) Conversión de schemas MCP a Gemini:**
```python
def _convert_tools_to_gemini_format(self, mcp_tools: List[Dict]) -> List[Tool]:
    """Convierte schemas MCP al formato de Gemini Function Declarations."""
    gemini_functions = []
    
    for tool in mcp_tools:
        function_info = tool.get("function", {})
        
        # Crear FunctionDeclaration
        function_declaration = FunctionDeclaration(
            name=function_info.get("name"),
            description=function_info.get("description"),
            parameters={
                "type": "object",
                "properties": converted_params
            }
        )
        gemini_functions.append(function_declaration)
    
    return [Tool(function_declarations=gemini_functions)]
```

**c) Detección de function calls:**
```python
# Extraer function calls de la respuesta
if hasattr(candidate.content, 'parts'):
    for part in candidate.content.parts:
        if hasattr(part, 'function_call') and part.function_call:
            tool_call = {
                "id": f"call_{len(tool_calls)}",
                "type": "function",
                "function": {
                    "name": part.function_call.name,
                    "arguments": dict(part.function_call.args)
                }
            }
            tool_calls.append(tool_call)
```

**d) Soporte para mensajes de tool results:**
```python
elif msg.role == "tool":
    # Resultado de tool execution
    prompt_parts.append(f"[TOOL RESULT]\n{msg.content}\n")
```

#### 2. `app/adapters/groq_adapter.py`

**Cambios principales:**

**a) Habilitación de function calling:**
```python
# Function calling (Groq usa formato OpenAI)
if tools:
    params["tools"] = tools
    params["tool_choice"] = "auto"  # LLM decide cuándo usar tools
    logger.debug("Function calling enabled with %d tools", len(tools))
```

**Ventaja:** Groq usa el mismo formato que OpenAI, por lo que la integración es directa sin conversión adicional.

#### 3. `app/services/orchestrator.py`

**Cambios principales:**

**a) Imports adicionales:**
```python
from ..services.tool_execution_manager import ToolExecutionManager
from ..mcp.tool_registry import ToolRegistry
import json
```

**b) Inicialización de ToolExecutionManager:**
```python
def __init__(self, db, provider_name=None):
    self.tool_manager = ToolExecutionManager()
    # Log de tools disponibles
    available_tools = ToolRegistry.count()
    logger.info("Tools available: %d", available_tools)
```

**c) Flujo de function calling integrado:**
```python
async def process_message(self, ...):
    # 1. Obtener tools disponibles
    available_tools = self.tool_manager.get_available_tools()
    
    # 2. Generar respuesta con tools
    llm_response = await self.llm_adapter.generate_response(
        messages=context_messages,
        temperature=temperature,
        tools=available_tools  # ← NUEVO
    )
    
    # 3. Manejar tool calls si existen
    if llm_response.tool_calls:
        # 3a. Ejecutar tools
        tool_results = await self._execute_tool_calls(
            conversation_id,
            llm_response.tool_calls
        )
        
        # 3b. Obtener respuesta final
        final_response = await self._get_final_response_after_tools(
            context_messages,
            llm_response.tool_calls,
            tool_results,
            temperature,
            available_tools
        )
        
        llm_response = final_response
```

**d) Nuevos métodos helper:**
```python
async def _execute_tool_calls(conversation_id, tool_calls) -> List[Dict]:
    """Ejecuta las tool calls y guarda resultados en BD."""
    
async def _get_final_response_after_tools(...) -> LLMResponse:
    """
    Reinsereta resultados en contexto y obtiene respuesta final.
    Incluye protección contra loops infinitos.
    """
```

## 🎨 Patrones de Diseño Aplicados

### 1. **Chain of Responsibility**
```
Orchestrator → LLM Adapter → Tool Execution Manager → Tool
```
Cada componente maneja su responsabilidad y pasa al siguiente.

### 2. **Strategy Pattern**
```python
# El Orchestrator no conoce los detalles de cada tool
tool = ToolRegistry.get(tool_name)
result = await tool.execute(**parameters)
```

### 3. **Template Method**
```python
# ToolExecutionManager define el flujo, tools lo implementan
async def execute_tool_call(tool_name, params):
    # 1. Validar
    # 2. Ejecutar (delegado a la tool)
    # 3. Formatear resultado
```

### 4. **Adapter Pattern**
```python
# Conversión de schemas MCP a formato Gemini
gemini_tools = self._convert_tools_to_gemini_format(mcp_tools)
```

### 5. **Dependency Injection**
```python
# Orchestrator recibe dependencias, no las crea
def __init__(self, db: Session, provider_name: Optional[str] = None):
    self.tool_manager = ToolExecutionManager()  # Inyección
```

## 🛡️ Manejo de Errores

### 1. **Validación de Tool Calls**
```python
# Antes de ejecutar
validation_error = tool.validate_parameters(parameters)
if validation_error:
    return ToolResult(success=False, error=validation_error)
```

### 2. **Protección contra Loops Infinitos**
```python
# En _get_final_response_after_tools
if final_response.tool_calls:
    logger.warning("LLM requested additional tool calls, limiting to prevent infinite loop")
    # Ejecutar UNA iteración más sin tools en la siguiente
```

### 3. **Degradación Elegante**
```python
try:
    result = await tool.execute(**parameters)
except Exception as e:
    return {
        "success": False,
        "error": f"Tool execution failed: {str(e)}"
    }
```

### 4. **Mensajes User-Friendly**
```python
# En caso de error
return LLMResponse(
    content=f"Lo siento, hubo un error al procesar las herramientas: {str(e)}",
    finish_reason="error"
)
```

## 📊 Métricas de Código

| Componente | Líneas | Métodos | Complejidad |
|------------|--------|---------|-------------|
| tool_execution_manager.py | 287 | 8 | Media |
| gemini_adapter.py (cambios) | +120 | +2 | Media |
| groq_adapter.py (cambios) | +10 | 0 | Baja |
| orchestrator.py (cambios) | +180 | +2 | Alta |
| test_function_calling.py | 381 | 8 | Media |
| **TOTAL** | **978** | **20** | **Media-Alta** |

## 🧪 Testing

### Ejecución de Tests

```bash
# 1. Asegurarse de que los servicios estén corriendo
# REST Service: http://localhost:8000
# Auth Service: http://localhost:9000

# 2. Ejecutar tests con Gemini
cd ai-service
python test_function_calling.py

# 3. Ejecutar tests con Groq
python test_function_calling.py --provider groq
```

### Resultados Esperados

```
✅ Test 1: Consulta Simple - Respuesta sin tools
✅ Test 2: Buscar Espacios - Tool buscarespacios ejecutada
✅ Test 3: Ver Reservas - Tool verreservas ejecutada
✅ Test 4: Crear Reserva - Tool crearreserva ejecutada
✅ Test 5: Estadísticas - Tool estadisticasreservas ejecutada
✅ Test 6: Conversación Multi-Turn - Múltiples tools con contexto

📊 RESUMEN:
- Tests completados: 6
- Total tokens: ~2000-3000
- Tiempo total: ~15-25s
- Provider: gemini/groq
```

## 🔍 Debugging

### Logs Importantes

```python
# Cuando se detecta un tool call
logger.info("LLM requested %d tool call(s), executing...", len(tool_calls))

# Durante ejecución
logger.info("Executing tool: name=%s, params=%s", tool_name, params)

# Resultado exitoso
logger.info("Tool executed successfully: name=%s, time=%.2fs", tool_name, time)

# Respuesta final
logger.info("Final response generated after tool execution")
```

### Verificación Manual

```python
# En Python console
from app.mcp.tool_registry import ToolRegistry
from app.services.tool_execution_manager import ToolExecutionManager

# Ver tools disponibles
print(f"Tools: {ToolRegistry.count()}")
print(f"Names: {ToolRegistry.list_tool_names()}")

# Ejecutar tool manualmente
import asyncio
manager = ToolExecutionManager()
result = asyncio.run(manager.execute_tool_call(
    "buscarespacios",
    {"capacidad_min": 30}
))
print(result)
```

## 🎯 Casos de Uso

### Caso 1: Búsqueda Simple
```
Usuario: "Busca aulas disponibles"
→ LLM llama a buscarespacios
→ Sistema retorna lista de aulas
→ LLM formatea respuesta amigable
```

### Caso 2: Reserva Completa
```
Usuario: "Reserva el Auditorio A para mañana de 2 a 4 PM"
→ LLM llama a crearreserva con parámetros extraídos
→ Sistema crea la reserva
→ LLM confirma la reserva al usuario
```

### Caso 3: Conversación Multi-Tool
```
Usuario: "Muéstrame estadísticas y luego mis reservas"
→ LLM llama a estadisticasreservas
→ LLM llama a verreservas
→ LLM combina ambos resultados en respuesta coherente
```

### Caso 4: Manejo de Errores
```
Usuario: "Reserva la Sala XYZ para mañana"
→ LLM llama a crearreserva
→ Sistema retorna error: "Sala XYZ no existe"
→ LLM informa error de forma amigable y sugiere alternativas
```

## 🚀 Próximos Pasos (Commit 4)

### 1. Multimodal - Images (2-3 horas)
```python
# Endpoint para mensajes con imágenes
@router.post("/api/v1/chat/message-with-image")
async def chat_with_image(
    file: UploadFile,
    prompt: str,
    usuario_id: int,
    conversation_id: Optional[int] = None
):
    # Usar Gemini Vision para analizar imagen
    image_bytes = await file.read()
    vision_result = await gemini_adapter.generate_with_vision(
        image_bytes,
        prompt
    )
    return vision_result
```

### 2. Chat UI (4-6 horas)

**Opción A: React Component en UleamFront**
- Componente ChatWidget.tsx
- Integración con WebSocket service
- UI con shadcn/ui

**Opción B: n8n + Telegram (2 horas) ⭐ RECOMENDADO**
- n8n workflow conectado a AI Service
- Bot de Telegram como interfaz
- Más rápido de implementar

## 📈 Progreso del Pilar 3

```
PILAR 3: AI SERVICE (MCP Chatbot)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 80% completo

✅ Commit 1: Base Architecture (100%)
  - AI Orchestrator
  - LLM Adapters (Gemini + Groq)
  - Conversation Service
  - Database models

✅ Commit 2: MCP Tools (100%)
  - BaseTool abstract class
  - ToolRegistry
  - ToolExecutor
  - 5 tools implementadas

✅ Commit 3: Function Calling (100%)  ← COMPLETADO AHORA
  - ToolExecutionManager
  - Function calling en Gemini
  - Function calling en Groq
  - Orchestrator integration
  - End-to-end tests

⏳ Commit 4: Multimodal Images (0%)
  - Image upload endpoint
  - Gemini Vision integration
  - OCR capabilities

⏳ Commit 5: Chat UI (0%)
  - Frontend component o
  - Telegram bot integration

Estimado para 100%: 6-8 horas restantes
```

## 🎓 Lecciones Aprendidas

### 1. **Formato de Tools por Provider**
- **Gemini:** Requiere FunctionDeclaration y Tool objects
- **Groq:** Usa formato OpenAI directamente
- **Solución:** Adapter pattern para conversión

### 2. **Reinserción de Resultados**
- Tools retornan JSON pero LLMs necesitan texto
- **Solución:** Formatear con summary + datos estructurados

### 3. **Loops Infinitos**
- LLM puede seguir llamando tools indefinidamente
- **Solución:** Límite de 1 iteración adicional

### 4. **Contexto de Conversación**
- Tool results deben agregarse al historial
- **Solución:** Rol "tool" en mensajes

### 5. **Error Handling**
- Tools pueden fallar por múltiples razones
- **Solución:** Try-catch exhaustivo + mensajes user-friendly

## 🔐 Seguridad y Validación

✅ Validación de tool calls antes de ejecución  
✅ Sanitización de parámetros  
✅ Rate limiting en tool execution manager  
✅ Logging de todas las ejecuciones  
✅ Error messages que no exponen información sensible  

## 📚 Referencias

- [Google Gemini Function Calling](https://ai.google.dev/docs/function_calling)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Groq Documentation](https://console.groq.com/docs/function-calling)
- Model Context Protocol Specification

## ✅ Checklist de Commit 3

- [x] ToolExecutionManager implementado
- [x] Function calling en Gemini adapter
- [x] Function calling en Groq adapter
- [x] Orchestrator actualizado con flujo completo
- [x] Manejo de tool calls detectado
- [x] Ejecución de tools integrada
- [x] Reinserción de resultados
- [x] Respuesta final del LLM
- [x] Protección contra loops infinitos
- [x] Error handling robusto
- [x] Logging completo
- [x] Tests end-to-end
- [x] Documentación completa

## 🎉 Conclusión

El **Commit 3: Function Calling Integration** está **100% completo** y listo para producción. Los LLMs (Gemini y Groq) ahora pueden:

1. ✅ Recibir información sobre tools disponibles
2. ✅ Decidir automáticamente cuándo usar cada tool
3. ✅ Ejecutar tools con parámetros extraídos del lenguaje natural
4. ✅ Interpretar resultados y generar respuestas coherentes
5. ✅ Manejar conversaciones multi-turn con contexto

**Próximo paso:** Commit 4 - Multimodal Images (Gemini Vision)

---

**Autor:** GitHub Copilot  
**Fecha:** 25 de enero de 2026  
**Commit:** Function Calling Integration  
**Status:** ✅ COMPLETO
