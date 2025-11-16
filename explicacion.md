# Sistema de Reservas ULEAM – Explicación Integral (Backend + Frontend)

Este documento resume cómo se conectan los tres servicios backend (REST Python, GraphQL Go, WebSocket TypeScript) con el frontend React/Vite, qué tecnologías usan, puertos, env vars y el flujo de datos end-to-end.

---

## Arquitectura General

```
                ┌──────────────────────────┐
                │ Frontend (React/Vite)    │
                │ - REST client (fetch)    │
                │ - GraphQL client         │
                │ - Socket.IO client       │
                └─────────────┬────────────┘
                              │
                 ┌────────────┼────────────┐
                 │            │            │
          REST API (8000)  GraphQL (8080)  WebSocket (3001)
          FastAPI (Python) Go + graphql-go NestJS + Socket.IO
                 │            │            │
                 └────────────┴────────────┘
                         PostgreSQL
```

- **Base de datos única (PostgreSQL)** para todos los servicios.
- **Clave JWT compartida** entre REST, GraphQL y WS (`SECRET_KEY`/`JWT_SECRET`).
- **Webhooks**: REST/GraphQL notifican al servicio WS via HTTP (`/api/webhooks/*`), luego WS re-emite por canales Socket.IO.
- **Frontend**:
  - REST: CRUD, autenticación, reservas, catálogos.
  - GraphQL: reportes/analytics (stats, top, agrupaciones).
  - WS: tiempo real (notificaciones, reservas, dashboard).

---

## Puertos y Variables de Entorno (local)
- REST: `http://localhost:8000/api`
- GraphQL: `http://localhost:8080/graphql`
- WebSocket: `http://localhost:3001`
- Frontend (dev): `http://localhost:5173`

Env frontend (`UleamFront/.env.local`):
```
VITE_REST_BASE_URL=http://localhost:8000
VITE_GRAPHQL_URL=http://localhost:8080/graphql
VITE_WS_URL=http://localhost:3001
```

Env backend (clave compartida y DB):
```
DATABASE_URL=postgres://...
SECRET_KEY=...             # mismo valor en REST/GraphQL/WS
WEBSOCKET_SERVICE_URL=http://localhost:3001  # para webhooks desde REST/GraphQL
```

---

## Backend – Servicios y Responsabilidades

### 1) REST API (FastAPI, Python) – `UleamBack/rest-service`
- **Puerto 8000** (`/api/*`).
- Autenticación: `POST /api/auth/login`, `GET /api/auth/me`, `PUT /api/auth/change-password`.
- Usuarios y roles: `GET /api/usuarios`, `PATCH /api/usuarios/{id}/estado`, `POST /api/usuarios/{id}/avatar`, `GET /api/tipos-usuario`.
- Catálogos: `GET/POST/PUT/DELETE /api/categorias-espacio`, `/api/espacios`, `/api/tipos-evento`, `/api/espacios/{id}/caracteristicas`.
- Reservas: `POST /api/reservas` (estado inicial **Pendiente = 1**), `GET /api/reservas`, `PATCH /api/reservas/{id}/estado`, `DELETE /api/reservas/{id}`.
- Disponibilidad: `GET /api/disponibilidad?espacio_id=...&fecha=YYYY-MM-DD&incluir_pendientes=true`.
- Notificaciones: `GET /api/notificaciones?usuario_id={id}`. Cada creación/actualización emite webhook a WS.
- **Webhooks salientes** (hacia WS `WEBSOCKET_SERVICE_URL`):
  - `reserva-creada`, `reserva-actualizada` (aprobada/rechazada/cancelada), `notificacion`, `stats-update`, `disponibilidad-actualizada`.
- **Estado de reserva**: seeds en BD (1 Pendiente, 2 Aprobada, 3 Rechazada, etc.). Al aprobar una, las pendientes solapadas se rechazan automáticamente y se emiten webhooks.

### 2) GraphQL (Go) – `UleamBack/graphql-service`
- **Puerto 8080** (`/graphql`).
- JWT en `Authorization: Bearer <token>`.
- Queries clave:
  - `reservas(...)`, `reserva(id)`.
  - Analítica admin: `estadisticas`, `espaciosMasReservados`, `usuariosMasActivos`, `reservasPorEstado`, `reservasPorTipoEvento`.
  - Disponibilidad: `disponibilidad(espacio_id, fecha, incluir_pendientes)`.
- **Webhooks salientes** (opcionales): `stats_update` a WS si `WEBSOCKET_SERVICE_URL` está configurada.

### 3) WebSocket (NestJS + Socket.IO) – `UleamBack/websocket-service`
- **Puerto 3001** (`io('http://localhost:3001', { auth: { token } })`).
- Handshake con JWT (usa misma clave `SECRET_KEY`).
- Canales usados por el frontend:
  - `notificaciones:user:{id}` (personal).
  - `reservas:usuario:{id}` (eventos del usuario).
  - `reservas:todas` (solo admin).
  - `dashboard:admin` (stats en vivo).
  - `disponibilidad:all` (cambios globales).
- **Webhooks entrantes** (desde REST/GraphQL):
  - `POST /api/webhooks/reserva-creada`
  - `POST /api/webhooks/reserva-actualizada`
  - `POST /api/webhooks/reserva-cancelada`
  - `POST /api/webhooks/notificacion`
  - `POST /api/webhooks/stats-update`
  - `POST /api/webhooks/disponibilidad-actualizada`
  - `POST /api/webhooks/recordatorio-evento`
- Reemite por Socket.IO los eventos `reserva_creada`, `reserva_aprobada`, `reserva_rechazada`, `reserva_cancelada`, `nueva_notificacion`, `stats_update`, etc.

---

## Frontend – Estructura y Conexión (React/Vite) – `UleamFront/client/src`

### Configuración
- `config/env.ts`: lee `VITE_REST_BASE_URL`, `VITE_GRAPHQL_URL`, `VITE_WS_URL`.
- `api/rest/client.ts`: construye URLs REST (`/api/...`) con fetch + JWT.
- `api/graphql/client.ts` (implícito): usa `graphqlRequest` con JWT.
- `hooks/useWebSocket.ts`: cliente Socket.IO, suscribiéndose según rol.

### Vistas principales (páginas)
- Usuario: `/app/inicio`, `/app/espacios`, `/app/reservas`, `/app/reservas/nueva`, `/app/notificaciones`, `/app/perfil`, `/app/calendario`.
- Admin: `/admin/dashboard`, `/admin/usuarios`, `/admin/espacios`, `/admin/categorias`, `/admin/eventos`, `/admin/aprobaciones`, `/admin/reportes`.

### Conexión por módulo
- **Auth**: `api/rest/authApi.ts` login en REST → guarda JWT en `authStorage`. `AuthContext` expone `isAdmin` (dep. de `tipo_usuario_id`).
- **Reservas**:
  - REST: `reservasApi` (`/api/reservas`, `/api/reservas/{id}/estado`, `DELETE`).
  - GraphQL (reportes): `api/graphql/queries/reservas.ts` (solo lectura/reportes).
  - WS: actualiza dashboards/notificaciones en vivo (`reserva_creada`, `reserva_aprobada`, etc.).
- **Notificaciones**:
  - REST: `GET /api/notificaciones?usuario_id`.
  - WS: canal `notificaciones:user:{id}` (`nueva_notificacion`, `notificacion_actualizada`).
- **Catálogos**: `categoriasApi`, `espaciosApi`, `tiposEventoApi` (REST CRUD).
- **Usuarios**: `usuariosApi` + `tiposUsuarioApi` (cambiar rol/estado desde admin).
- **Reportes** (admin): `AdminReportesPage` usa GraphQL (`estadisticas`, `topEspacios`, `reservasPorEstado`, `reservasPorTipoEvento`, `topUsuarios`). Fallback a datos REST si GraphQL da 0.

### WS: suscripciones por rol (lógica en `useWebSocket`)
- Siempre: `notificaciones:user:{id}`, `reservas:usuario:{id}`.
- Admin (rol `tipo_usuario_id == 1`): `dashboard:admin`, `reservas:todas`, `disponibilidad:all`.

---

## Flujos End-to-End

### 1) Crear reserva (usuario)
1. Front → REST `POST /api/reservas` (estado se fuerza a **Pendiente** en backend).
2. REST guarda en BD y envía webhook `reserva_creada` a WS → WS emite `reserva_creada` a:
   - `reservas:usuario:{id}` y `reservas:todas` (admin).
3. Front escucha WS y refresca queries (React Query invalidate) + muestra notificación si corresponde.

### 2) Aprobar/Rechazar (admin)
1. Admin → REST `PATCH /api/reservas/{id}/estado` (1=Pendiente, 2=Aprobada, 3=Rechazada, etc.).
2. REST actualiza BD, rechaza pendientes solapadas y envía webhooks:
   - `reserva_actualizada` / `reserva_aprobada` / `reserva_rechazada` a WS.
   - Notificación creada en REST → webhook `notificacion` a WS.
3. WS emite eventos a canales de usuario y admin; Front refresca dashboards y notificaciones en vivo.

### 3) Notificaciones
- Creación en REST (por acción de reserva o manual) → hook `POST /api/webhooks/notificacion` → WS → canal `notificaciones:user:{id}` → Front `useNotificaciones` actualiza lista y badge en tiempo real.

### 4) Reportes
- Front (admin) llama GraphQL (`estadisticas`, `reservasPorEstado`, `reservasPorTipoEvento`, `topUsuarios`, `topEspacios`).
- Si GraphQL devuelve 0, se deriva de REST (`reservasApi`, `espaciosApi`, `usuariosApi`).
- WS `stats_update` forza refetch para dashboard/reportes en vivo.

---

## Archivos Clave (front)
- `config/env.ts`: variables de entorno.
- `api/rest/*.ts`: clientes REST (reservas, usuarios, espacios, categorías, tipos-evento, notificaciones).
- `api/graphql/queries/*.ts`: consultas de reportes/estadísticas/reservas.
- `hooks/useWebSocket.ts`: cliente Socket.IO y suscripciones.
- Páginas admin: `pages/admin/AdminAprobacionesPage.tsx`, `AdminEspaciosPage.tsx`, `AdminCategoriasPage.tsx`, `AdminEventosPage.tsx`, `AdminUsuariosPage.tsx`, `AdminDashboardPage.tsx`, `AdminReportesPage.tsx`.
- Páginas usuario: `pages/Home.tsx`, `reservas/*`, `notificaciones/*`, `perfil/*`.

---

## Archivos Clave (back)
- REST FastAPI: `rest-service/app/routes/*.py` (auth, usuarios, reservas, notificaciones, catálogos), `app/services/reserva_service.py` (lógica de estado/conflictos), `app/config.py` (env).
- GraphQL Go: `graphql-service/cmd/server`, `internal/*` (resolvers, DB).
- WebSocket NestJS: `websocket-service/src/main.ts`, `notifications.gateway.ts`, controladores de webhooks en `src/webhooks`.

---

## Diagramas de Mensajes (simplificado)

**Reserva creada:**
```
Frontend ── POST /api/reservas ──► REST
REST ── webhook reserva_creada ──► WS
WS ── socket emit reserva_creada ─► clientes canal reservas:usuario:{id} / reservas:todas
Frontend ── refetch (React Query) ─► Actualiza UI
```

**Aprobación:**
```
Admin Front ── PATCH /api/reservas/{id}/estado ─► REST
REST ── webhook reserva_aprobada/rechazada ─► WS
REST ── webhook notificacion ─► WS
WS ── emite eventos a usuario/admin ─► Front actualiza dashboard + notificaciones
```

---

## Tecnologías
- Frontend: React 18, Vite, Tailwind, shadcn/ui (Radix), Wouter, TanStack Query, Recharts, Socket.IO client.
- REST: FastAPI, SQLAlchemy, Pydantic, JWT (python-jose), Bcrypt.
- GraphQL: Go, graphql-go, JWT middleware.
- WS: NestJS, Socket.IO, TypeORM/TypeORM-like config para DB/notificaciones si aplica.
- BD: PostgreSQL (11 entidades).

---

## Credenciales de prueba (backend real)
Todos con contraseña `password123`:
- Admin: `admin@uleam.edu.ec`
- Profesor: `profesor1@uleam.edu.ec`
- Estudiante: `estudiante1@uleam.edu.ec`

---

## Puesta en marcha rápida (local)
1) REST: `cd UleamBack/rest-service && uvicorn app.main:app --reload --port 8000`
2) GraphQL: `cd UleamBack/graphql-service && go run ./cmd/server`
3) WS: `cd UleamBack/websocket-service && npm install && npm run dev`
4) Front: `cd UleamFront && npm install && npm run dev` (VITE_* configuradas).

Con esto, el frontend mostrará datos reales, métricas en vivo y notificaciones en tiempo real.
