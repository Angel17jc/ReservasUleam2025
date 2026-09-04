# Payment Service - Pilar 2 ✅ COMPLETO

Microservicio de pagos con abstracción de pasarelas y webhooks B2B bidireccionales para el sistema de reservas ULEAM.

**Estado**: ✅ **100% COMPLETO** - Listo para producción  
**Tests**: 27/27 pasando (100%)  
**Cobertura**: 55%

---

## 🎯 Características

### ✅ Completamente Implementado

#### Payment Provider Layer (Patrón Adapter)
- ✅ Interface abstracta `PaymentProvider`
- ✅ `MockAdapter` para desarrollo/testing
- ✅ `StripeAdapter` para producción
- ✅ Factory Pattern para instanciación
- ✅ Normalización de webhooks

#### Webhooks Bidireccionales
- ✅ **OUTBOUND**: Envío de eventos a partners
  - `payment.success`, `payment.failed`, `payment.refunded`, `payment.cancelled`
  - Firma HMAC-SHA256 automática
  - Retry logic para fallos
- ✅ **INBOUND**: Recepción de eventos de partners
  - `booking.confirmed`, `tour.purchased`, `service.activated`, `booking.cancelled`
  - Validación HMAC + timestamp (anti-replay)
  - Procesamiento asíncrono

#### Seguridad B2B
- ✅ HMAC-SHA256 para integridad de webhooks
- ✅ API Keys para autenticación de partners
- ✅ JWT para autenticación de usuarios
- ✅ Validación de timestamp (tolerancia 5min)
- ✅ Timing-safe comparison

#### Integración con Servicios
- ✅ auth-service (JWT validation)
- ✅ rest-service (reservations)
- ✅ websocket-service (real-time notifications)

#### Testing y Documentación
- ✅ 27 tests unitarios e integración
- ✅ Cobertura 55% (> 50% requerido)
- ✅ OpenAPI/Swagger completa
- ✅ Guía de integración B2B

---

## 🏗️ Arquitectura

```
payment-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application ✅
│   ├── config.py            # Configuration with Pydantic ✅
│   ├── database.py          # SQLAlchemy setup ✅
│   ├── adapters/            # Payment Provider Adapters ✅
│   │   ├── base.py          # Abstract interface
│   │   ├── stripe_adapter.py
│   │   ├── mock_adapter.py
│   │   └── adapter_factory.py
│   ├── clients/             # Service clients ✅
│   │   ├── auth_client.py   # auth-service integration
│   │   ├── rest_client.py   # rest-service integration
│   │   └── websocket_client.py # websocket-service integration
│   ├── models/              # Database models ✅
│   │   ├── payment.py       # Payment transactions
│   │   ├── partner.py       # B2B partners
│   │   ├── payment_provider.py  # Provider configs
│   │   └── webhook_event.py # Normalized events
│   ├── routes/              # API endpoints ✅
│   │   ├── payments.py      # Payment CRUD
│   │   ├── partners.py      # Partner management
│   │   ├── partners_webhook.py # INBOUND webhooks ✅ NEW
│   │   └── webhooks.py      # OUTBOUND webhooks
│   ├── schemas/             # Pydantic schemas ✅
│   │   ├── payment.py
│   │   ├── partner.py
│   │   ├── partner_event.py # Partner events ✅ NEW
│   │   └── webhook.py
│   └── services/            # Business logic ✅
│       ├── payment_service.py
│       ├── partner_service.py
│       ├── partner_webhook_processor.py # INBOUND processor ✅ NEW
│       └── hmac_service.py  # HMAC signatures ✅ UPDATED
├── tests/                   # Test suite ✅
│   ├── test_integration.py  # Integration tests (11)
│   ├── test_payment_service.py # Unit tests (4)
│   └── test_partner_webhooks.py # Webhook tests (12) ✅ NEW
├── alembic/                 # Database migrations ✅
├── docs/                    # Documentation ✅
│   ├── PILAR_2_COMPLETE.md  # Implementation summary ✅ NEW
│   └── B2B_INTEGRATION_GUIDE.md # Partner guide ✅ NEW
├── requirements.txt         ✅
├── .env.example            ✅
└── README.md
```

---

## 📊 Modelos de Base de Datos

### Payment
Transacciones de pago con integración de providers externos.

```sql
- id: PK
- external_payment_id: ID del provider (único)
- reserva_id: FK a reserva
- usuario_id: FK a usuario  
- provider_name: stripe, mercadopago, mock
- amount: Monto (Decimal)
- currency: Moneda ISO 4217
- status: pending, completed, failed, refunded, cancelled
- metadata_json: Datos adicionales (JSONB)
- error_message: Mensaje de error si aplica
- creado_en, actualizado_en
```

### Partner
Partners externos para webhooks B2B.

```sql
- id: PK
- nombre: Nombre único del partner
- webhook_url: URL del webhook del partner
- shared_secret: Secret para HMAC (64+ chars)
- eventos_suscritos: Array de eventos (JSONB)
- is_active: Estado del partner
- descripcion: Notas adicionales
- creado_en, actualizado_en
```

### PartnerWebhookLog
Auditoría de webhooks con partners.

```sql
- id: PK
- partner_id: FK a partner
- event_type: Tipo de evento
- payload_json: Payload completo
- response_status: HTTP status code
- response_body: Respuesta del partner
- signature_valid: Validación HMAC
- error_message: Error si falla
- direction: outgoing/incoming
- creado_en
```

### PaymentProviderConfig
Configuración de payment providers.

```sql
- id: PK
- name: stripe, mercadopago, mock
- is_active: Estado del provider
- config_json: API keys y config (JSONB)
- creado_en, actualizado_en
```

### WebhookEvent
Eventos normalizados de webhooks.

```sql
- id: PK
- event_type: Tipo de evento normalizado
- source: stripe, mercadopago, mock, partner:{id}
- payload_json: Payload normalizado
- processed: Estado de procesamiento
- error_message: Error si falla
- creado_en, actualizado_en
```

## 🚀 Instalación y Configuración

### 1. Crear entorno virtual

```powershell
# Windows PowerShell
cd payment-service
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```powershell
cp .env.example .env
# Editar .env con tus configuraciones
```

**Variables importantes:**
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/payment_service_db
SECRET_KEY=<JWT_SECRET-definido-en-.env>  # Mismo que auth-service
MOCK_PROVIDER_ENABLED=true
REST_SERVICE_URL=http://localhost:8000
WEBSOCKET_SERVICE_URL=http://localhost:3001
```

### 4. Crear base de datos

```powershell
# Crear base de datos PostgreSQL
psql -U postgres -c "CREATE DATABASE payment_service_db;"
```

### 5. Ejecutar migraciones

```powershell
# Aplicar migraciones de Alembic
alembic upgrade head
```

**Verificar tablas creadas:**
```powershell
psql -U postgres -d payment_service_db -c "\dt"
```

Deberías ver:
- payment
- payment_provider_config
- partner
- partner_webhook_log
- webhook_event
- alembic_version

## 🏃 Ejecutar el Servicio

### Modo desarrollo (con hot-reload)

```powershell
uvicorn app.main:app --reload --port 8001
```

### Modo producción

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4
```

### Usando Python directamente

```powershell
python -m app.main
```

## 📚 Documentación API

Una vez iniciado el servicio, accede a:

- **Swagger UI**: http://localhost:8001/api/v1/docs
- **ReDoc**: http://localhost:8001/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8001/api/v1/openapi.json

## 🔍 Endpoints Disponibles (Commit 1)

### Root
```http
GET /
```
Información básica del servicio.

### Health Check
```http
GET /api/v1/health
```
Estado de salud del servicio con estadísticas de BD.

**Respuesta:**
```json
{
  "status": "healthy",
  "service": "ULEAM Payment Service",
  "version": "1.0.0",
  "environment": "development",
  "database": {
    "connected": true,
    "pool_stats": {
      "pool_size": 5,
      "checked_in": 3,
      "checked_out": 2
    }
  },
  "payment_providers": {
    "mock": true,
    "stripe": false,
    "mercadopago": false
  }
}
```

### Service Info
```http
GET /api/v1/info
```
Información detallada de configuración.

## 🧪 Verificación

### 1. Health Check
```powershell
curl http://localhost:8001/api/v1/health
```

### 2. Base de datos
```powershell
# Verificar conexión
psql -U postgres -d payment_service_db -c "SELECT COUNT(*) FROM payment;"
```

### 3. Logs
Los logs deberían mostrar:
```
✓ Database connection established
✓ Payment providers configured:
  ✓ mock: enabled
  ✗ stripe: disabled
  ✗ mercadopago: disabled
Server starting on 0.0.0.0:8001
```

## 🗄️ Gestión de Migraciones

### Crear nueva migración
```powershell
alembic revision --autogenerate -m "descripcion del cambio"
```

### Aplicar migraciones pendientes
```powershell
alembic upgrade head
```

### Revertir última migración
```powershell
alembic downgrade -1
```

### Ver historial de migraciones
```powershell
alembic history
```

### Ver estado actual
```powershell
alembic current
```

## 🔧 Desarrollo

### Estructura de Código

**Principios aplicados:**
- ✅ **SOLID Principles**: Separation of Concerns, Single Responsibility
- ✅ **Clean Architecture**: Capas bien definidas (models, services, routes)
- ✅ **Type Safety**: Type hints en todo el código
- ✅ **Dependency Injection**: FastAPI Depends
- ✅ **Error Handling**: Global exception handlers

**Patrones de diseño:**
- ✅ **Repository Pattern**: Acceso a datos via SQLAlchemy
- ⏳ **Adapter Pattern**: Abstracción de payment providers (Commit 2)
- ⏳ **Factory Pattern**: Creación de adapters (Commit 2)
- ⏳ **Strategy Pattern**: Selección de provider (Commit 2)

### Convenciones

**Nombres:**
- Modelos: PascalCase (`Payment`, `Partner`)
- Funciones: snake_case (`create_payment`, `get_payment`)
- Constantes: UPPER_CASE (`MOCK_PROVIDER_ENABLED`)

**Comentarios:**
- Docstrings en español para funciones públicas
- Comentarios inline en inglés
- Type hints obligatorios

**Commits:**
- Formato: `feat(payment-service): descripción breve`
- Commits atómicos y descriptivos
- Referencias a Pilar y número de commit

## 📝 Configuración de Environment

### Desarrollo (.env)
```env
ENVIRONMENT=development
MOCK_PROVIDER_ENABLED=true
LOG_LEVEL=DEBUG
```

### Producción (.env)
```env
ENVIRONMENT=production
MOCK_PROVIDER_ENABLED=false
LOG_LEVEL=INFO
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## 🔐 Seguridad

**Implementado:**
- ✅ Validación de tipos con Pydantic
- ✅ SQL Injection prevention (SQLAlchemy ORM)
- ✅ Environment variables para secretos
- ✅ CORS configurado
- ✅ Logging de requests

**Por implementar:**
- ⏳ JWT validation (Commit 3)
- ⏳ HMAC signature validation (Commit 3)
- ⏳ Rate limiting (Commit 3)
- ⏳ Input sanitization (Commit 2)

## 📊 Estado del Proyecto

### Commit 1: ✅ COMPLETADO
- [x] Estructura del proyecto
- [x] Configuración con Pydantic
- [x] Modelos SQLAlchemy (5 tablas)
- [x] Migraciones Alembic
- [x] FastAPI application
- [x] Health check endpoints
- [x] Documentación OpenAPI
- [x] README completo

### Próximos pasos:
1. **Commit 2**: Implementar Adapter Pattern para payment providers
2. **Commit 3**: Sistema de webhooks bidireccionales con HMAC
3. **Commit 4**: Integración con servicios existentes y testing

## 🤝 Integración con Otros Servicios

El Payment Service se integrará con:

- **Auth Service** (Puerto 9000): Validación JWT
- **REST Service** (Puerto 8000): Actualización de estado de reservas
- **WebSocket Service** (Puerto 3001): Notificaciones en tiempo real
- **Partners Externos**: Webhooks B2B con otros grupos

## 📖 Referencias

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Stripe API](https://stripe.com/docs/api)

## 👥 Equipo

**Equipo ULEAM Reservas**  
Pilar 2 - Segundo Parcial  
Universidad Laica Eloy Alfaro de Manabí

---

**Version:** 1.0.0  
**Last Updated:** 15 de enero de 2026  
**Commit:** 1/4 - Setup Inicial ✅
