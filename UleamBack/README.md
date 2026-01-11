# Sistema de Reservas ULEAM — Backend

Enfoque en **Pilar 1 (Auth Service)** y **Pilar 2 (Pagos + Webhooks B2B)**, integrados con los servicios base del primer parcial (REST, GraphQL y WebSocket). El microservicio de IA no se detalla aquí.

## Servicios y puertos
| Servicio | Tecnología | Puerto por defecto | Rol |
|----------|------------|--------------------|-----|
| Auth Service | NestJS + PostgreSQL + Redis | 9000 | Pilar 1: JWT access/refresh, blacklist, validación local |
| Payment Service | FastAPI + PostgreSQL | 8001 | Pilar 2: pagos, adapters (mock/stripe), webhooks B2B (HMAC) |
| REST API | FastAPI | 8000 | CRUD reservas y catálogos, webhooks hacia WS |
| GraphQL | Go | 8081 (configurable con `PORT`) | Reportes/analítica (requiere JWT) |
| WebSocket | NestJS (Socket.IO) | 3001 | Tiempo real: reservas, notificaciones, dashboard |
| PostgreSQL principal | DB | 5432 | Datos de reservas (P1) |
| PostgreSQL auth | DB | 5432 | Usuarios y tokens (Auth) |
| Redis | Cache | 6379 | Blacklist y refresh tokens (Auth) |

## Bases de datos
- **Principal (reservas)**: scripts en `database/` (`setup_postgres.sql`, `init.sql`, patches). Usan REST/GraphQL/WebSocket.
- **Auth**: usada solo por `auth-service` (TypeORM). Puedes apuntar a la misma instancia de Postgres pero idealmente a una base separada (`DB_NAME`).
- **Payment**: usada por `payment-service` para transacciones, partners y webhooks (`init_payment_db.sql`).

## Pilar 1 — Auth Service (NestJS)
- JWT access (15m) + refresh (7d) con rotación y revocación.
- Endpoints: `POST /api/v1/auth/register`, `/login`, `/logout`, `/refresh`, `GET /api/v1/auth/me`, `POST /api/v1/auth/validate` (validación remota para otros servicios).
- Seguridad: rate limiting, bcrypt, helmet, CORS, blacklist centralizada.
- Redis: claves `blacklist:<token>` (logout/rotación) y `refresh_token:<userId>:<tokenId>` con TTL; validaciones locales revisan la firma con `JWT_SECRET` y rechazan si el token está en blacklist.

**Setup rápido (PowerShell):**
```powershell
cd auth-service
docker rm -f auth-service-redis
docker-compose up -d
copy .env.example .env   # ajusta JWT_SECRET compartido, DB_*, REDIS_*, CORS_ORIGIN
npm install
docker-compose up -d     # levanta Redis declarado en el compose
npm run start:dev        # http://localhost:9000/api/v1/docs
```

## Pilar 2 — Payment Service (FastAPI)
- Adapters: `mock` (dev) y `stripe` (prod). Normaliza webhooks y firma HMAC-SHA256 para partners.
- Partners B2B: `POST /api/v1/partners/register` genera `shared_secret`; outbound events: `payment.success|failed|refunded|cancelled`.
- Endpoints de pagos: `POST /api/v1/payments`, `GET /api/v1/payments`, `GET /api/v1/payments/{id}`.
- Webhooks: `POST /api/v1/webhooks/stripe` (inbound Stripe), `POST /api/v1/partners/webhook` (inbound partner), `POST /api/v1/webhooks/notify-partners` (outbound a partners).

**Variables clave (.env):**
- `DATABASE_URL` (BD de pagos)
- `SECRET_KEY` = mismo `JWT_SECRET` del Auth Service
- `AUTH_SERVICE_URL` (validación JWT): `http://localhost:9000`
- `REST_SERVICE_URL` (reservas): `http://localhost:8000`
- `WEBSOCKET_SERVICE_URL`: `http://localhost:3001`
- `MOCK_PROVIDER_ENABLED=true`
- `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET` (si usas Stripe)

**Setup rápido (PowerShell):**
```powershell
cd payment-service
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # configura DATABASE_URL, SECRET_KEY, AUTH_SERVICE_URL, STRIPE_*
alembic upgrade head
uvicorn app.main:app --reload --port 8001   # http://localhost:8001/api/v1/docs
```

## Servicios base del P1
**REST (FastAPI)**
```powershell
cd rest-service
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**GraphQL (Go)**
```powershell
cd graphql-service
set PORT=8081   # default en el código; evita colisión con otros servicios
go run ./cmd/server
```
Endpoint: http://localhost:8081/graphql (JWT requerido).

**WebSocket (NestJS)**
```powershell
cd websocket-service
npm install
npm run dev   # o npm run start
```

## Claves y validación local
- Usa la misma `JWT_SECRET`/`SECRET_KEY` en Auth, Payment, REST, GraphQL y WebSocket para validar tokens sin llamar al Auth en cada request.
- Redis mantiene blacklist y refresh tokens; si un access token está en `blacklist:<token>`, se rechaza aunque la firma sea válida.

## Documentación adicional
- Detalles REST: [rest-service/README.md](rest-service/README.md)
- Detalles GraphQL: [graphql-service/README.md](graphql-service/README.md)
- Detalles WebSocket: [websocket-service/README.md](websocket-service/README.md)
- Pago y B2B: [payment-service/README.md](payment-service/README.md)
- Auth e integración P1: [auth-service/README.md](auth-service/README.md)

## Cumplimiento de Pilares
**Pilar 1 (Auth Service independiente)**
- Auth-service tiene su propia base `auth_service_db` con usuarios, tokens y blacklist; no comparte tablas con reservas.
- Los demás servicios validan JWT localmente con la `SECRET_KEY` compartida; no llaman al auth en cada request.
- Refresh + blacklist se mantienen en Redis; logout y rotación invalidan tokens sin depender de llamadas cruzadas.
- Rate limiting y CORS configurados en el auth-service.

**Pilar 2 (Pagos + Webhooks B2B)**
- Payment-service abstrae proveedores con adapters (mock y stripe) y normaliza webhooks.
- Webhooks entrantes se verifican con HMAC (`STRIPE_WEBHOOK_SECRET` o shared_secret de partners).
- Partners B2B se registran vía `/api/v1/partners/register` y reciben eventos firmados (`payment.success`, etc.).
- Interoperabilidad bidireccional: puede recibir y emitir eventos a partners usando el secret compartido.

Pendientes conocidos
- Stripe: revisar llaves y `STRIPE_WEBHOOK_SECRET` finales en entorno productivo o demo.
- Verificar aprovisionamiento de usuarios en la BD de reservas para evitar 401 por FK faltante (mientras se mantiene la validación en `auth_service_db`).
