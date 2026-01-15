# 🛠️ MCP TOOLS DOCUMENTATION

**AI Service - Sistema de Reservas ULEAM**  
**Pilar 3: MCP Tools Implementation**

---

## 📋 TOOLS OVERVIEW

Se han implementado **5 MCP Tools** que permiten al LLM interactuar con el sistema de reservas:

| # | Tool | Categoría | Función |
|---|------|-----------|---------|
| 1 | `buscar_espacios` | 🔍 Consulta | Busca espacios disponibles |
| 2 | `ver_reservas` | 🔍 Consulta | Consulta reservas existentes |
| 3 | `crear_reserva` | ⚡ Acción | Crea nueva reserva |
| 4 | `registrar_usuario` | ⚡ Acción | Registra nuevo usuario |
| 5 | `estadisticas_reservas` | 📊 Reporte | Genera estadísticas de uso |

---

## 🔍 TOOLS DE CONSULTA (2/2)

### 1. buscar_espacios

**Descripción**: Busca espacios disponibles en el sistema de reservas ULEAM.

**Categoría**: CONSULTA (read-only)

**Parámetros**:
```json
{
  "capacidad_min": {
    "type": "integer",
    "description": "Capacidad mínima de personas",
    "required": false
  },
  "tipo_espacio": {
    "type": "string",
    "description": "Tipo de espacio a buscar",
    "required": false,
    "enum": ["aula", "laboratorio", "auditorio", "sala_reuniones", "espacio_deportivo"]
  },
  "disponible": {
    "type": "boolean",
    "description": "Si debe estar disponible",
    "required": false,
    "default": true
  },
  "nombre": {
    "type": "string",
    "description": "Buscar por nombre (búsqueda parcial)",
    "required": false
  }
}
```

**Ejemplo de uso**:
```python
# Usuario pregunta: "Busca auditorios con capacidad para 50 personas"
LLM llama -> buscar_espacios(capacidad_min=50, tipo_espacio="auditorio")
```

**Respuesta**:
```json
{
  "success": true,
  "data": {
    "total": 2,
    "espacios": [
      {
        "id": 5,
        "nombre": "Auditorio Principal",
        "capacidad": 100,
        "tipo_espacio": {"nombre": "auditorio"}
      }
    ],
    "summary": "Se encontraron 2 espacio(s):\n- Auditorio Principal (Capacidad: 100, Tipo: auditorio)"
  }
}
```

**Integración**: `GET http://localhost:8000/api/espacios`

---

### 2. ver_reservas

**Descripción**: Consulta reservas existentes con filtros opcionales.

**Categoría**: CONSULTA (read-only)

**Parámetros**:
```json
{
  "usuario_id": {
    "type": "integer",
    "description": "ID del usuario",
    "required": false
  },
  "espacio_id": {
    "type": "integer",
    "description": "ID del espacio",
    "required": false
  },
  "estado_id": {
    "type": "integer",
    "description": "Estado: 1=pendiente, 2=confirmada, 3=cancelada, 4=completada",
    "required": false,
    "enum": [1, 2, 3, 4]
  }
}
```

**Ejemplo de uso**:
```python
# Usuario: "Muéstrame mis reservas"
LLM llama -> ver_reservas(usuario_id=6)

# Usuario: "¿Qué reservas tiene el Auditorio A?"
LLM llama -> ver_reservas(espacio_id=5)
```

**Respuesta**:
```json
{
  "success": true,
  "data": {
    "total": 3,
    "reservas": [...],
    "summary": "Se encontraron 3 reserva(s):\n- Auditorio Principal el 2026-01-26 de 14:00 a 16:00 (Estado: Confirmada)"
  }
}
```

**Integración**: `GET http://localhost:8000/api/reservas`

---

## ⚡ TOOLS DE ACCIÓN (2/2)

### 3. crear_reserva

**Descripción**: Crea una nueva reserva de espacio.

**Categoría**: ACCIÓN (write operation)

**Parámetros**:
```json
{
  "usuario_id": {
    "type": "integer",
    "description": "ID del usuario",
    "required": true
  },
  "espacio_id": {
    "type": "integer",
    "description": "ID del espacio a reservar",
    "required": true
  },
  "fecha_reserva": {
    "type": "string",
    "description": "Fecha YYYY-MM-DD",
    "required": true
  },
  "hora_inicio": {
    "type": "string",
    "description": "Hora inicio HH:MM",
    "required": true
  },
  "hora_fin": {
    "type": "string",
    "description": "Hora fin HH:MM",
    "required": true
  },
  "proposito": {
    "type": "string",
    "description": "Propósito de la reserva",
    "required": true
  }
}
```

**Ejemplo de uso**:
```python
# Usuario: "Reserva el Auditorio A para mañana de 2pm a 4pm para una conferencia"
LLM llama -> crear_reserva(
    usuario_id=6,
    espacio_id=5,
    fecha_reserva="2026-01-26",
    hora_inicio="14:00",
    hora_fin="16:00",
    proposito="Conferencia de tecnología"
)
```

**Respuesta**:
```json
{
  "success": true,
  "data": {
    "reserva": {...},
    "summary": "✅ Reserva creada exitosamente!\n\n📍 Espacio: Auditorio A\n📅 Fecha: 2026-01-26\n🕐 Horario: 14:00 - 16:00\n📝 Propósito: Conferencia de tecnología\n🆔 ID de reserva: 123\n⏳ Estado: Pendiente"
  }
}
```

**Integración**: `POST http://localhost:8000/api/reservas`

---

### 4. registrar_usuario

**Descripción**: Registra un nuevo usuario en el sistema.

**Categoría**: ACCIÓN (write operation)

**Parámetros**:
```json
{
  "nombre": {
    "type": "string",
    "description": "Nombre del usuario",
    "required": true
  },
  "apellido": {
    "type": "string",
    "description": "Apellido",
    "required": true
  },
  "email": {
    "type": "string",
    "description": "Email único (@uleam.edu.ec)",
    "required": true
  },
  "password": {
    "type": "string",
    "description": "Contraseña (mínimo 8 caracteres)",
    "required": true
  },
  "tipo_usuario_id": {
    "type": "integer",
    "description": "Tipo: 1=admin, 2=docente, 3=estudiante, 4=externo",
    "required": false,
    "default": 3
  }
}
```

**Ejemplo de uso**:
```python
# Usuario: "Registra un nuevo estudiante: Juan Pérez, email juan.perez@uleam.edu.ec"
LLM llama -> registrar_usuario(
    nombre="Juan",
    apellido="Pérez",
    email="juan.perez@uleam.edu.ec",
    password="SecurePass123!",
    tipo_usuario_id=3
)
```

**Respuesta**:
```json
{
  "success": true,
  "data": {
    "user": {...},
    "summary": "✅ Usuario registrado exitosamente!\n\n👤 Nombre: Juan Pérez\n📧 Email: juan.perez@uleam.edu.ec\n🏷️ Tipo: Estudiante\n🆔 ID: 15"
  }
}
```

**Integración**: `POST http://localhost:9000/api/v1/auth/register`

---

## 📊 TOOL DE REPORTE (1/1)

### 5. estadisticas_reservas

**Descripción**: Genera estadísticas y reportes sobre uso de espacios.

**Categoría**: REPORTE (analytics)

**Parámetros**:
```json
{
  "espacio_id": {
    "type": "integer",
    "description": "ID del espacio (opcional)",
    "required": false
  },
  "dias": {
    "type": "integer",
    "description": "Días hacia atrás",
    "required": false,
    "default": 30
  },
  "incluir_canceladas": {
    "type": "boolean",
    "description": "Incluir reservas canceladas",
    "required": false,
    "default": false
  }
}
```

**Ejemplo de uso**:
```python
# Usuario: "Dame estadísticas de los últimos 15 días"
LLM llama -> estadisticas_reservas(dias=15)

# Usuario: "Cuántas reservas tiene el Auditorio A en enero?"
LLM llama -> estadisticas_reservas(espacio_id=5, dias=30)
```

**Respuesta**:
```json
{
  "success": true,
  "data": {
    "total_reservas": 45,
    "promedio_por_dia": 1.5,
    "distribucion_estados": {
      "1": 5,  // Pendientes
      "2": 30, // Confirmadas
      "4": 10  // Completadas
    },
    "top_espacios": [
      ["Auditorio Principal", 15],
      ["Aula 201", 12]
    ],
    "summary": "📊 REPORTE DE ESTADÍSTICAS - Últimos 15 días\n\n📈 Total: 45 reservas\n..."
  }
}
```

**Integración**: `GET http://localhost:8000/api/reservas` + agregaciones locales

---

## 🔧 ARQUITECTURA DE TOOLS

### Estructura de archivos
```
app/mcp/
├── __init__.py              # Importa todos los tools
├── base_tool.py             # Clase abstracta BaseTool
├── tool_registry.py         # Registry Pattern
├── tool_executor.py         # HTTP client para servicios
│
├── consulta/                # Tools de consulta
│   ├── buscar_espacios.py
│   └── ver_reservas.py
│
├── accion/                  # Tools de acción
│   ├── crear_reserva.py
│   └── registrar_usuario.py
│
└── reporte/                 # Tools de reporte
    └── estadisticas_reservas.py
```

### Patrones de diseño implementados

1. **Strategy Pattern**: Cada tool es una estrategia intercambiable
2. **Registry Pattern**: `ToolRegistry` centraliza el registro
3. **Template Method**: `BaseTool.execute()` define flujo común
4. **Factory Pattern**: `@register_tool` decorator auto-registra
5. **Dependency Injection**: `ToolExecutor` inyectado implícitamente

---

## 🚀 CÓMO USAR LOS TOOLS

### 1. Auto-registro al iniciar la app

```python
# En main.py
from app import mcp  # Importar ejecuta auto-registro

# Al iniciar:
# 2026-01-25 15:09:23 - INFO - Registered tool: buscarespacios (category: consulta)
# 2026-01-25 15:09:23 - INFO - Registered tool: verreservas (category: consulta)
# ...
```

### 2. Obtener schemas para LLM

```python
from app.mcp import ToolRegistry

# Obtener todos los schemas
schemas = ToolRegistry.get_all_schemas()

# Pasar al LLM para function calling
response = await llm_adapter.generate_response(
    messages=messages,
    tools=schemas  # LLM sabe qué tools puede llamar
)
```

### 3. Ejecutar un tool

```python
from app.mcp import ToolRegistry

# Obtener tool por nombre
tool = ToolRegistry.get("buscar_espacios")

# Ejecutar con parámetros
result = await tool.execute(
    capacidad_min=30,
    tipo_espacio="auditorio"
)

if result.success:
    print(result.data["summary"])
else:
    print(f"Error: {result.error}")
```

---

## 📊 CUMPLIMIENTO PILAR 3

| Requisito | Requerido | Implementado | Estado |
|-----------|-----------|--------------|--------|
| Tools de consulta | 2 | 2 | ✅ |
| Tools de acción | 2 | 2 | ✅ |
| Tools de reporte | 1 | 1 | ✅ |
| **TOTAL** | **5** | **5** | **✅ 100%** |

---

## 🧪 TESTING

### Test de registro
```bash
cd C:\ReservasUleam2025\UleamBack\ai-service
python test_tools.py
```

**Output esperado**:
```
✅ Total tools registered: 5
✅ 2 tools de consulta: 2/2
✅ 2 tools de acción: 2/2
✅ 1 tool de reporte: 1/1
✅ TODOS LOS REQUISITOS CUMPLIDOS!
```

### Test manual de un tool

```bash
cd C:\ReservasUleam2025\UleamBack\ai-service
python -c "
import asyncio
from app.mcp import ToolRegistry

async def test():
    tool = ToolRegistry.get('buscarespacios')
    result = await tool.execute(capacidad_min=20)
    print(result.to_dict())

asyncio.run(test())
"
```

---

## 🔗 SERVICIOS REQUERIDOS

Para que los tools funcionen, estos servicios deben estar corriendo:

1. **REST Service** (puerto 8000):
   - `/api/espacios` - Para buscar_espacios
   - `/api/reservas` - Para ver_reservas, crear_reserva, estadisticas

2. **Auth Service** (puerto 9000):
   - `/api/v1/auth/register` - Para registrar_usuario

3. **Database** (PostgreSQL):
   - Database: `reservasuleam`
   - User: `Reservas_ULEAM`

---

## 📝 PRÓXIMOS PASOS (Commit 3)

- [ ] Integrar tools con function calling en Gemini Adapter
- [ ] Integrar tools con function calling en Groq Adapter
- [ ] Actualizar Orchestrator para ejecutar tools automáticamente
- [ ] Testing end-to-end con conversaciones reales
- [ ] Procesamiento de imágenes (multimodal)
- [ ] Chat UI en frontend

---

**Autor**: Sistema de Reservas ULEAM  
**Fecha**: 25 de enero de 2026  
**Versión**: 1.0.0
