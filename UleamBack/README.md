# 🎯 Sistema de Reservas ULEAM — Backend (REST + GraphQL + WebSocket)

Arquitectura distribuida para reservas de espacios universitarios, alineada con la rúbrica del curso (REST, GraphQL, WebSockets y frontend integrado).

## Arquitectura y puertos
| Servicio | Tecnología | Puerto | Rol |
|----------|------------|--------|-----|
| REST API | Python + FastAPI | `8000` | CRUD completo, autenticación/autorización, notificaciones |
| GraphQL  | Go + graphql-go  | `8080` | Reportes, métricas y consultas analíticas |
| WebSocket| TypeScript + NestJS (Socket.IO) | `3001` | Tiempo real: reservas, notificaciones, dashboard |

Base de datos única: **PostgreSQL** (11 entidades: tipo_usuario, usuario, categoria_espacio, espacio, caracteristica_espacio, tipo_evento, estado_reserva, reserva, disponibilidad_espacio, notificacion, referencia).

## Variables de entorno clave
- `DATABASE_URL` (PostgreSQL compartida)
- `SECRET_KEY` / `JWT_SECRET` (misma clave en REST, GraphQL y WS)
- `WEBSOCKET_SERVICE_URL` (REST/GraphQL → webhooks al WS, ej. `http://localhost:3001`)
- REST opcionales: `ACCESS_TOKEN_EXPIRE_MINUTES`, `ALLOWED_ORIGINS`
- WS opcionales: `PORT` (default 3001), `CORS_ORIGIN`, credenciales DB si consulta notificaciones

## Puesta en marcha rápida
1. **REST API (Python/FastAPI)**
   ```bash
   cd rest-service
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Docs: `http://localhost:8000/docs`
   Endpoints clave: `/api/auth/*`, `/api/usuarios`, `/api/espacios`, `/api/categorias-espacio`, `/api/tipos-evento`, `/api/reservas`, `/api/reservas/{id}/estado`, `/api/notificaciones`, `/api/disponibilidad`.

2. **GraphQL (Go)**
   ```bash
   cd graphql-service
   go run ./cmd/server
   ```
   Endpoint: `http://localhost:8080/graphql` (requiere JWT). Queries principales: `reservas`, `reserva`, `estadisticas`, `espaciosMasReservados`, `usuariosMasActivos`, `reservasPorEstado`, `reservasPorTipoEvento`, `disponibilidad`.

3. **WebSocket / Socket.IO (NestJS)**
   ```bash
   cd websocket-service
   npm install
   npm run dev   # o npm run start
   ```
   Handshake con JWT. Canales que usa el frontend: `notificaciones:user:{id}`, `reservas:usuario:{id}`, `reservas:todas` (admin), `dashboard:admin`, `disponibilidad:all`.

## Flujo funcional resumido
- **Reservar**: el usuario crea reserva vía REST (`POST /api/reservas`). Se guarda en estado **Pendiente (id=1)** y se emite notificación + evento WS `reserva_creada`.
- **Aprobación**: admin/profesor cambia estado con `PATCH /api/reservas/{id}/estado`. Al aprobar, las pendientes solapadas se rechazan automáticamente y se emiten webhooks WS (`reserva_aprobada`/`reserva_rechazada`).
- **Disponibilidad**: `/api/disponibilidad` y el resolver GraphQL `disponibilidad` consideran Aprobadas (y opcionalmente Pendientes) para marcar bloques ocupados.
- **Notificaciones**: REST persiste notificaciones y dispara webhook `POST /api/webhooks/notificacion` al WS, que reenvía en `notificaciones:user:{id}`. También se consumen las notificaciones históricas con `GET /api/notificaciones`.
- **Dashboard/Reportes**: GraphQL entrega métricas (estadísticas, top espacios, reservas por estado/tipo) y el WS puede recibir `stats_update` para refrescar en vivo.

## Usuarios de prueba
Todos con contraseña `password123` (ajustables en `database/init.sql`):
- Admin: `admin@uleam.edu.ec`
- Profesor: `profesor1@uleam.edu.ec`
- Estudiante: `estudiante1@uleam.edu.ec`

## Tests y utilidades
- REST: `pytest` dentro de `rest-service` (ignora `__pycache__` y `.pytest_cache`).
- GraphQL: `go test ./...` dentro de `graphql-service`.
- WebSocket: prueba rápida con `npx wscat -c ws://localhost:3001/socket.io/?EIO=4&transport=websocket` (envía `42["subscribe", {"channels":["notificaciones:user:1"]}]`).

---
Para detalle por servicio, revisa:
- `rest-service/REST_ENDPOINTS.md` (cobertura REST)
- `rest-service/README.md` (setup REST)
- `graphql-service/README.md` (queries y entorno)
- `websocket-service/README.md` (canales, eventos y webhooks)
