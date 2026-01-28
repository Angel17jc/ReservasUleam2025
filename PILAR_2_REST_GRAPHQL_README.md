# 📊 PILAR 2: Servicios REST, GraphQL y Gestión de Datos

**Versión:** 1.0  
**Fecha:** 27 de Enero de 2026  
**Estado:** ✅ Producción  
**Líderes Técnicos:** Equipo REST y GraphQL Services

---

## 📋 Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Arquitectura del Pilar 2](#arquitectura-del-pilar-2)
3. [REST Service (FastAPI)](#rest-service-fastapi)
4. [GraphQL Service (Go)](#graphql-service-go)
5. [Modelos de Datos](#modelos-de-datos)
6. [Endpoints Principales](#endpoints-principales)
7. [Flujos de Negocio](#flujos-de-negocio)
8. [Integración con Otros Pilares](#integración-con-otros-pilares)
9. [Testing y Deployment](#testing-y-deployment)

---

## 🎯 Visión General

El **Pilar 2** es el corazón de la lógica de negocio de ULEAM Reservas. Proporciona dos interfaces complementarias:

- **REST Service:** CRUD completo, operaciones transaccionales, webhooks
- **GraphQL Service:** Queries analíticas, reportes, lectura eficiente

### Responsabilidades Principales
- ✅ CRUD de Reservas, Espacios, Usuarios
- ✅ Gestión de disponibilidad y conflictos de horarios
- ✅ Estados y flujos de reserva
- ✅ Webhooks hacia otros servicios
- ✅ Reportes y estadísticas (GraphQL)
- ✅ Validación de reglas de negocio

---

## 🏗️ Arquitectura del Pilar 2

### Diagrama General

```
┌──────────────────────────────────────────────────────────────────┐
│                      PILAR 2: DATOS Y LÓGICA                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Frontend (React + Vite)                                         │
│  │                    │                                          │
│  ├─→ REST (CRUD)     ├─→ GraphQL (Reportes)                     │
│  │   Port: 8000      │   Port: 8080                             │
│  │                   │                                          │
│  └───────────┬───────┘                                          │
│              │                                                   │
│  ┌───────────▼──────────────────────────────────────┐          │
│  │    PostgreSQL Database: reservasuleam            │          │
│  │  ┌────────────────────────────────────────────┐  │          │
│  │  │ Usuarios, Espacios, Reservas, Estados,    │  │          │
│  │  │ Categorías, Características, Tipos Evento │  │          │
│  │  │ Notificaciones, Logs                      │  │          │
│  │  └────────────────────────────────────────────┘  │          │
│  └────────────────────────────────────────────────────┘          │
│              │                    │                              │
│              │                    │                              │
│    ┌─────────▼─────────┐  ┌──────▼──────────┐                  │
│    │ REST Service      │  │ GraphQL Service │                  │
│    │ (FastAPI)         │  │ (Go)            │                  │
│    │                   │  │                 │                  │
│    │ • CRUD            │  │ • Queries       │                  │
│    │ • Transacciones   │  │ • Analytics     │                  │
│    │ • Webhooks        │  │ • Agregaciones  │                  │
│    │ • Validaciones    │  │ • Reportes      │                  │
│    │ • Auth Guard      │  │ • Aceso Roling  │                  │
│    └───────────────────┘  └─────────────────┘                  │
│              │                    │                              │
│              ├─→ Pilar 3 (AI)     │                              │
│              ├─→ Pilar 4 (n8n)    │                              │
│              └─→ Notificaciones   │                              │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Componentes Clave

| Componente | Tipo | Descripción |
|-----------|------|-----------|
| **REST Service** | Python/FastAPI | Servidor CRUD principal |
| **GraphQL Service** | Go/Graph-gophers | Servidor de queries |
| **PostgreSQL DB** | SQL Database | Almacenamiento persistente |
| **SQLAlchemy** | ORM Python | Mapeo objeto-relacional |
| **TypeORM** (Go) | ORM Go | Mapeo objeto-relacional Go |
| **Alembic** | Migration Tool | Versionado de esquema DB |

---

## 🔴 REST Service (FastAPI)

### Descripción
Servicio principal de CRUD para todas las entidades del sistema. Proporciona operaciones transaccionales, validaciones de negocio, y webhooks hacia otros servicios.

### Stack Tecnológico
```
FastAPI v0.100+
├─ Python 3.11+
├─ SQLAlchemy 2.0 (ORM)
├─ Alembic (Migraciones)
├─ Pydantic (Validación)
├─ Uvicorn (ASGI Server)
├─ PyJWT (Token validation)
└─ httpx (Cliente HTTP)
```

### Puertos y URLs
```
URL Base: http://localhost:8000
API: http://localhost:8000/api
Docs: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
```

### Instalación Rápida
```bash
cd rest-service
python -m pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Editar con credenciales

# Ejecutar migraciones
alembic upgrade head

# Iniciar
uvicorn main:app --reload --port 8000
```

### Variables de Entorno
```env
# Database
DATABASE_URL=postgresql://Reservas_ULEAM:123456@localhost:5432/reservasuleam

# JWT (compartido con otros servicios)
SECRET_KEY=mi-secreto-auth-service-super-seguro-2025
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Webhooks
WEBSOCKET_SERVICE_URL=http://localhost:3001
PAYMENT_SERVICE_URL=http://localhost:8001
AI_SERVICE_URL=http://localhost:5000

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Logging
LOG_LEVEL=DEBUG
```

### Estructura de Carpetas
```
rest-service/
├── main.py                          # Aplicación FastAPI
├── requirements.txt                 # Dependencias
├── .env.example                     # Template env
├── alembic/                         # Migraciones
│   ├── versions/                   # Scripts de migración
│   └── env.py
├── app/
│   ├── __init__.py
│   ├── main.py                     # App FastAPI
│   ├── config.py                   # Configuración
│   ├── database.py                 # Conexión BD
│   ├── security.py                 # JWT, Auth
│   │
│   ├── models/                     # SQLAlchemy Models
│   │   ├── user.py
│   │   ├── espacio.py
│   │   ├── reserva.py
│   │   ├── notificacion.py
│   │   └── ...
│   │
│   ├── schemas/                    # Pydantic Schemas
│   │   ├── user.py
│   │   ├── reserva.py
│   │   └── ...
│   │
│   ├── crud/                       # CRUD Operations
│   │   ├── usuario.py
│   │   ├── reserva.py
│   │   └── ...
│   │
│   └── routers/                    # Endpoints
│       ├── auth.py
│       ├── usuarios.py
│       ├── reservas.py
│       ├── espacios.py
│       ├── disponibilidad.py
│       └── notificaciones.py
└── tests/                          # Tests pytest
```

---

## 🟦 GraphQL Service (Go)

### Descripción
Servicio complementario para queries de solo lectura, análisis y reportes. Optimizado para consultas complejas sin crear nuevas reservas.

### Stack Tecnológico
```
Go 1.21+
├─ graphql-go (GraphQL resolver)
├─ sqlc (Type-safe SQL)
├─ lib/pq (PostgreSQL driver)
├─ golang-jwt (JWT validation)
└─ chi (HTTP router)
```

### Puertos y URLs
```
URL: http://localhost:8080/graphql
Método: POST (GraphQL queries)
```

### Instalación Rápida
```bash
cd graphql-service
go mod tidy

# Configurar .env
export DATABASE_URL=postgresql://Reservas_ULEAM:123456@localhost:5432/reservasuleam
export JWT_SECRET=mi-secreto-auth-service-super-seguro-2025
export PORT=8080

# Ejecutar
go run ./cmd/server
```

### Variables de Entorno
```env
# Database
DATABASE_URL=postgresql://Reservas_ULEAM:123456@localhost:5432/reservasuleam

# JWT (compartido)
JWT_SECRET=mi-secreto-auth-service-super-seguro-2025

# Server
PORT=8080
HOST=0.0.0.0
NODE_ENV=development

# Webhooks (opcional)
WEBSOCKET_SERVICE_URL=http://localhost:3001
```

### Estructura de Carpetas
```
graphql-service/
├── go.mod                          # Dependencias Go
├── go.sum                          # Lock file
├── cmd/
│   └── server/
│       └── main.go                 # Entry point
├── internal/
│   ├── graph/
│   │   ├── resolver.go             # Resolvers GraphQL
│   │   ├── schema.graphql          # Schema
│   │   └── models.go               # Modelos
│   ├── db/
│   │   └── database.go             # Conexión DB
│   └── auth/
│       └── jwt.go                  # JWT validation
└── Dockerfile                      # Containerización
```

---

## 📦 Modelos de Datos

### Entidad: Usuario
```sql
CREATE TABLE usuarios (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  firstName VARCHAR(100),
  lastName VARCHAR(100),
  tipoUsuarioId INTEGER REFERENCES tipos_usuario(id),
  estado ENUM('activo', 'bloqueado', 'inactivo') DEFAULT 'activo',
  avatar_url VARCHAR(500),
  telefono VARCHAR(20),
  direccion TEXT,
  departamento VARCHAR(100),
  createdAt TIMESTAMP DEFAULT NOW(),
  updatedAt TIMESTAMP DEFAULT NOW(),
  lastLogin TIMESTAMP
);
```

### Entidad: Espacio
```sql
CREATE TABLE espacios (
  id UUID PRIMARY KEY,
  codigo VARCHAR(50) UNIQUE NOT NULL,
  nombre VARCHAR(255) NOT NULL,
  categoriaId INTEGER REFERENCES categorias_espacio(id),
  capacidad INTEGER,
  ubicacion VARCHAR(255),
  piso INTEGER,
  equipamiento TEXT,
  estado ENUM('disponible', 'mantenimiento', 'no_disponible') DEFAULT 'disponible',
  createdAt TIMESTAMP DEFAULT NOW(),
  updatedAt TIMESTAMP DEFAULT NOW()
);
```

### Entidad: Reserva (Núcleo del Sistema)
```sql
CREATE TABLE reservas (
  id UUID PRIMARY KEY,
  codigo VARCHAR(50) UNIQUE,
  usuarioId UUID REFERENCES usuarios(id),
  espacioId UUID REFERENCES espacios(id),
  tipoEventoId INTEGER REFERENCES tipos_evento(id),
  estadoId INTEGER REFERENCES estados_reserva(id) DEFAULT 1,
  titulo VARCHAR(255),
  descripcion TEXT,
  fecha DATE NOT NULL,
  horaInicio TIME NOT NULL,
  horaFin TIME NOT NULL,
  asistentes_estimada INTEGER,
  es_bloqueo BOOLEAN DEFAULT FALSE,
  createdAt TIMESTAMP DEFAULT NOW(),
  updatedAt TIMESTAMP DEFAULT NOW(),
  
  -- Constraint: no overlaps en mismo espacio
  CONSTRAINT unique_espacio_horario_aprobado 
    EXCLUDE USING gist (espacioId WITH =, 
                        fecha WITH =, 
                        horaInicio WITH &&, 
                        horaFin WITH &&)
    WHERE (estadoId = 2) -- solo reservas aprobadas
);
```

### Estados de Reserva
```
1 = Pendiente (recién creada)
2 = Aprobada (confirmada, pasó pago)
3 = Rechazada (admin rechazó)
4 = Cancelada (usuario canceló)
5 = Completada (evento ocurrió)
```

### Relaciones Clave
```
Usuarios 1──────N Reservas
         1──────N Notificaciones

Espacios 1──────N Reservas
        1──────N Características

TiposEvento 1──────N Reservas

CategoriasEspacio 1──────N Espacios
```

---

## 📡 Endpoints Principales

### REST Service: Autenticación (compartido con Pilar 1)

```http
POST /api/auth/login
POST /api/auth/register
POST /api/auth/logout
POST /api/auth/refresh
GET /api/auth/me
```

---

### REST Service: Usuarios (Protegido)

#### Listar Usuarios
```http
GET /api/usuarios?page=1&limit=20&estado=activo
Authorization: Bearer {token}

Response 200:
{
  "data": [
    {
      "id": "uuid",
      "email": "usuario@uleam.edu.ec",
      "firstName": "Juan",
      "tipoUsuario": { "id": 3, "nombre": "Estudiante" },
      "estado": "activo",
      "lastLogin": "2026-01-27T10:00:00Z"
    }
  ],
  "pagination": { "page": 1, "limit": 20, "total": 150 }
}
```

---

#### Obtener Perfil Completo
```http
GET /api/usuarios/{userId}
Authorization: Bearer {token}

Response 200:
{
  "id": "uuid",
  "email": "usuario@uleam.edu.ec",
  "firstName": "Juan",
  "lastName": "Pérez",
  "tipoUsuario": { "id": 3, "nombre": "Estudiante" },
  "avatar": "https://...",
  "telefono": "+593987654321",
  "direccion": "Calle 123, Manta",
  "departamento": "Informática",
  "estado": "activo",
  "createdAt": "2026-01-15T08:30:00Z",
  "lastLogin": "2026-01-27T10:00:00Z"
}
```

---

#### Cambiar Estado de Usuario (Admin)
```http
PATCH /api/usuarios/{userId}/estado
Authorization: Bearer {adminToken}
Content-Type: application/json

{
  "estado": "bloqueado",
  "razon": "Incumplimiento de normas"
}

Response 200:
{
  "id": "uuid",
  "estado": "bloqueado",
  "modificadoPor": "admin_uuid",
  "fechaModificacion": "2026-01-27T14:35:00Z"
}
```

---

### REST Service: Espacios

#### Listar Espacios
```http
GET /api/espacios?categoriaId=1&estado=disponible&page=1&limit=10
Authorization: Bearer {token}

Response 200:
{
  "data": [
    {
      "id": "uuid",
      "codigo": "AULA-101",
      "nombre": "Aula 101 (Bloque A)",
      "categoria": { "id": 1, "nombre": "Aula Teórica" },
      "capacidad": 40,
      "ubicacion": "Bloque A, Piso 1",
      "equipamiento": ["pizarra", "proyector", "aire_acondicionado"],
      "estado": "disponible"
    }
  ],
  "pagination": { "total": 45 }
}
```

---

#### Crear Espacio (Admin)
```http
POST /api/espacios
Authorization: Bearer {adminToken}
Content-Type: application/json

{
  "codigo": "SALA-201",
  "nombre": "Sala de Conferencias 201",
  "categoriaId": 2,
  "capacidad": 100,
  "ubicacion": "Bloque B, Piso 2",
  "equipamiento": ["proyector", "videoconferencia", "audio_system"]
}

Response 201:
{
  "id": "uuid",
  "codigo": "SALA-201",
  "nombre": "Sala de Conferencias 201",
  "estado": "disponible",
  "createdAt": "2026-01-27T14:40:00Z"
}
```

---

### REST Service: Reservas (Críticas)

#### Crear Reserva
```http
POST /api/reservas
Authorization: Bearer {token}
Content-Type: application/json

{
  "espacioId": "uuid",
  "tipoEventoId": 1,
  "titulo": "Reunión de Proyecto",
  "descripcion": "Discusión sobre avances",
  "fecha": "2026-02-10",
  "horaInicio": "10:00",
  "horaFin": "12:00",
  "asistentes_estimada": 8,
  "es_bloqueo": false
}

Response 201:
{
  "id": "uuid",
  "codigo": "RES-2026-001",
  "estado": "Pendiente",
  "estadoId": 1,
  "createdAt": "2026-01-27T14:45:00Z"
}
```

**Validaciones Internas:**
- Espacio existe y disponible
- No hay conflicto de horario con aprobadas
- Usuario tiene permisos
- Horario dentro del horario de funcionamiento (08:00-18:00)

---

#### Listar Reservas del Usuario
```http
GET /api/reservas?usuarioId={id}&estado=Pendiente&fecha_desde=2026-02-01
Authorization: Bearer {token}

Response 200:
{
  "data": [
    {
      "id": "uuid",
      "codigo": "RES-2026-001",
      "espacio": {
        "id": "uuid",
        "codigo": "AULA-101",
        "nombre": "Aula 101"
      },
      "usuario": { "id": "uuid", "firstName": "Juan" },
      "tipoEvento": { "id": 1, "nombre": "Clase" },
      "estado": "Pendiente",
      "fecha": "2026-02-10",
      "horaInicio": "10:00",
      "horaFin": "12:00",
      "asistentes_estimada": 8,
      "createdAt": "2026-01-27T14:45:00Z"
    }
  ]
}
```

---

#### Confirmar Reserva (Aprob por pago)
```http
POST /api/reservas/{reservaId}/confirm
Authorization: Bearer {token}
Content-Type: application/json

{
  "payment_id": "pm_123abc",
  "status": "confirmed"
}

Response 200:
{
  "id": "uuid",
  "estado": "Aprobada",
  "estadoId": 2,
  "confirmadoAt": "2026-01-27T14:50:00Z"
}

Efectos secundarios:
├─ Webhook → WebSocket service
├─ Notificación al usuario
├─ Email de confirmación
└─ Disponibilidad actualizada
```

---

#### Cambiar Estado de Reserva (Admin)
```http
PATCH /api/reservas/{reservaId}/estado
Authorization: Bearer {adminToken}
Content-Type: application/json

{
  "nuevoEstado": "Aprobada" | "Rechazada" | "Cancelada",
  "comentario": "Motivo opcional"
}

Response 200:
{
  "id": "uuid",
  "estado": "Aprobada",
  "estadoId": 2,
  "comentario": "Aprobado por admin"
}
```

---

### REST Service: Disponibilidad

#### Verificar Disponibilidad de Espacio
```http
GET /api/disponibilidad?espacioId=uuid&fecha=2026-02-10&incluir_pendientes=true
Authorization: Bearer {token}

Response 200:
{
  "espacioId": "uuid",
  "fecha": "2026-02-10",
  "horarios_libres": [
    { "horaInicio": "08:00", "horaFin": "10:00" },
    { "horaInicio": "12:00", "horaFin": "14:00" },
    { "horaInicio": "16:00", "horaFin": "18:00" }
  ],
  "horarios_ocupados": [
    {
      "horaInicio": "10:00",
      "horaFin": "12:00",
      "reservaId": "uuid",
      "estado": "Aprobada"
    },
    {
      "horaInicio": "14:00",
      "horaFin": "16:00",
      "reservaId": "uuid",
      "estado": "Pendiente"
    }
  ]
}
```

---

### GraphQL Service: Queries Analíticas

#### Query: Listar Reservas con Filtros
```graphql
query {
  reservas(
    limit: 20,
    offset: 0,
    usuarioId: "uuid",
    espacioId: "uuid",
    estado: "Aprobada",
    fecha_desde: "2026-01-01",
    fecha_hasta: "2026-12-31"
  ) {
    id
    codigo
    usuario { firstName lastName email }
    espacio { nombre codigo }
    estado
    fecha
    horaInicio
    horaFin
    tipoEvento
    asistentes_estimada
  }
}
```

---

#### Query: Estadísticas de Reservas (Admin)
```graphql
query {
  estadisticas {
    totalReservas
    reservasPorEstado {
      estado
      cantidad
    }
    usuariosActivos
    espaciosMasReservados(limit: 5) {
      espacio { nombre }
      cantidad
    }
    usuariosMasActivos(limit: 5) {
      usuario { firstName }
      cantidad
    }
  }
}
```

---

#### Query: Disponibilidad
```graphql
query {
  disponibilidad(
    espacioId: "uuid",
    fecha: "2026-02-10",
    incluir_pendientes: true
  ) {
    espacioId
    fecha
    libres { horaInicio horaFin }
    ocupados { horaInicio horaFin estado }
  }
}
```

---

## 🔄 Flujos de Negocio

### Flujo 1: Crear Reserva (Usuario)
```
1. Usuario selecciona espacio y fecha
2. Frontend: GET /api/disponibilidad?espacioId=X&fecha=Y
3. Frontend muestra slots libres
4. Usuario selecciona horario
5. Frontend: POST /api/reservas (nueva reserva)
6. REST valida:
   ├─ Espacio existe
   ├─ No hay solapamiento
   ├─ Usuario no está bloqueado
   └─ Horario válido (08:00-18:00)
7. Crear en DB con estado "Pendiente"
8. Webhook → WebSocket: "reserva_creada"
9. Email: "Se creó tu reserva"
10. Frontend: Mostrar confirmación
```

---

### Flujo 2: Procesar Pago (n8n)
```
1. n8n recibe webhook de pasarela
2. n8n: POST /api/reservas/{id}/confirm (con payment_id)
3. REST:
   ├─ Validar payment_id
   ├─ Cambiar estado a "Aprobada"
   ├─ Liberar conflictos pendientes
   └─ Guardar payment_id en DB
4. Webhook → WebSocket: "reserva_actualizada"
5. Email: "Reserva confirmada"
6. n8n: Enviar webhook a partner (si aplica)
7. GraphQL: stats_update emitido
```

---

### Flujo 3: Rechazar Reserva (Admin)
```
1. Admin: PATCH /api/reservas/{id}/estado → "Rechazada"
2. REST valida estado actual
3. Cambiar estado en BD
4. Webhook → WebSocket: "reserva_rechazada"
5. Email: "Tu reserva fue rechazada"
6. Notificación en app
7. Espacio vuelve a estar disponible
```

---

## 🔗 Integración con Otros Pilares

### Integración con Pilar 1 (Auth)
```
Todos los endpoints REST/GraphQL requieren:
├─ Authorization: Bearer {JWT}
├─ JWT válido y no expirado
├─ Usuario activo (no bloqueado)
└─ Roles/permisos verificados
```

---

### Integración con Pilar 3 (AI)
```
REST Service:
├─ GET /api/reservas/{id} → AI puede analizar reserva
├─ GET /api/espacios/{id} → AI puede describir espacio
├─ GET /api/disponibilidad → AI sugiere horarios
└─ POST /api/notificaciones → AI genera notificación
```

---

### Integración con Pilar 4 (n8n)
```
n8n Calls REST:
├─ POST /api/reservas/{id}/confirm (payment handler)
├─ GET /api/partners/{id} (partner handler)
├─ POST /api/partners/register (setup)
├─ GET /api/health (health check)
└─ POST /api/reports/daily (scheduled tasks)
```

---

## 🧪 Testing y Deployment

### Tests Unitarios (REST)
```bash
cd rest-service
pytest

# O con cobertura
pytest --cov=app tests/
```

---

### Tests Unitarios (GraphQL)
```bash
cd graphql-service
go test ./...

# Con cobertura
go test -cover ./...
```

---

### Deployment

#### REST Service (Docker)
```bash
docker build -t uleam-rest:latest .
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e SECRET_KEY=... \
  uleam-rest:latest
```

---

#### GraphQL Service (Docker)
```bash
docker build -t uleam-graphql:latest .
docker run -p 8080:8080 \
  -e DATABASE_URL=postgresql://... \
  -e JWT_SECRET=... \
  uleam-graphql:latest
```

---

## ✅ Checklist de Implementación

- [x] REST Service (FastAPI) funcionando
- [x] GraphQL Service (Go) funcionando
- [x] PostgreSQL con tablas core
- [x] Endpoints CRUD completos
- [x] Validación de conflictos horarios
- [x] Webhooks implementados
- [x] JWT integrado
- [x] GraphQL queries analíticas
- [x] Documentación Swagger/ReDoc
- [ ] Tests al 80%+ cobertura
- [ ] Performance optimization
- [ ] Caching layer

---

## 📚 Referencias

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [SQLAlchemy](https://sqlalchemy.org)
- [Alembic](https://alembic.sqlalchemy.org)
- [GraphQL](https://graphql.org)
- [Go GraphQL](https://github.com/graphql-go/graphql)
- [PostgreSQL Docs](https://www.postgresql.org/docs)

---

**Última Actualización:** 27 de Enero de 2026  
**Contacto:** Team ULEAM Reservas
