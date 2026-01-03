# Pilar 2: Análisis del Sistema y Arquitectura del Payment Service

## 📊 ANÁLISIS DEL SISTEMA ACTUAL

### 1. Arquitectura Actual del Backend

El sistema **ULEAM Reservas** cuenta con una arquitectura distribuida de microservicios:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA ACTUAL                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Auth Service │  │ REST Service │  │GraphQL Serv. │         │
│  │  (NestJS)    │  │  (FastAPI)   │  │    (Go)      │         │
│  │  Port: 9000  │  │  Port: 8000  │  │  Port: 8080  │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│         │     ┌────────────┴────────────┐    │                 │
│         │     │   WebSocket Service      │    │                 │
│         │     │  (NestJS + Socket.IO)    │    │                 │
│         │     │      Port: 3001          │    │                 │
│         │     └──────────┬───────────────┘    │                 │
│         │                │                     │                 │
│         └────────────────┴─────────────────────┘                │
│                          │                                       │
│                ┌─────────▼──────────┐                           │
│                │   PostgreSQL DB     │                           │
│                │  reservasuleam      │                           │
│                │   + Redis (Auth)    │                           │
│                └─────────────────────┘                           │
│                                                                  │
│  Frontend: React + Vite (Port: 5173)                            │
│  - REST API para CRUD y autenticación                           │
│  - GraphQL para reportes y analytics                            │
│  - WebSocket para notificaciones en tiempo real                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Servicios Existentes

#### 2.1 Auth Service (NestJS - TypeScript)
**Puerto:** 9000  
**Propósito:** Microservicio de autenticación (Pilar 1)  
**Características:**
- ✅ JWT con access tokens (15min)
- ✅ Refresh tokens (7 días) almacenados en BD
- ✅ Validación local de tokens (sin llamadas al auth service)
- ✅ Base de datos propia: tablas `user`, `refresh_token`, `blacklisted_token`
- ✅ Redis para caché y blacklist
- ✅ Rate limiting en endpoints de login
- ✅ Bcrypt para hashing (12 rounds)
- ✅ Swagger docs en `/api/v1/docs`

**Endpoints:**
- POST `/api/v1/auth/register`
- POST `/api/v1/auth/login`
- POST `/api/v1/auth/logout`
- POST `/api/v1/auth/refresh`
- GET `/api/v1/auth/me`
- GET `/api/v1/users/profile`

**Stack Técnico:**
- NestJS + TypeORM
- PostgreSQL para persistencia
- Redis para caché
- Passport + JWT

#### 2.2 REST Service (FastAPI - Python)
**Puerto:** 8000  
**Propósito:** CRUD de reservas, espacios, usuarios, notificaciones  
**Características:**
- SQLAlchemy ORM
- Alembic para migraciones
- JWT compartido con auth-service
- Webhooks hacia WebSocket service
- Gestión completa de reservas con estados

**Endpoints principales:**
- `/api/auth/*` - Login/Register/Refresh (replicado)
- `/api/reservas` - CRUD de reservas
- `/api/espacios` - Gestión de espacios
- `/api/usuarios` - Gestión de usuarios
- `/api/notificaciones` - Notificaciones de usuario
- `/api/disponibilidad` - Cálculo de slots libres/ocupados

**Modelos principales:**
- Usuario, TipoUsuario
- Espacio, CategoriaEspacio, CaracteristicaEspacio
- Reserva, EstadoReserva, TipoEvento
- Notificacion

#### 2.3 GraphQL Service (Go)
**Puerto:** 8080  
**Propósito:** Consultas y reportes analíticos  
**Características:**
- GraphQL schema para queries complejas
- JWT validation
- Solo lectura (queries, no mutations)
- Reportes de estadísticas

**Queries principales:**
- `reservas(filters)` - Listado con filtros
- `estadisticas` - Conteos generales
- `espaciosMasReservados` - Top espacios
- `usuariosMasActivos` - Top usuarios
- `disponibilidad(espacio_id, fecha)` - Slots disponibles

#### 2.4 WebSocket Service (NestJS - TypeScript)
**Puerto:** 3001  
**Propósito:** Notificaciones en tiempo real  
**Características:**
- Socket.IO para comunicación bidireccional
- Autenticación JWT en handshake
- Sistema de canales por usuario/espacio/admin
- Webhooks HTTP de entrada

**Canales:**
- `notificaciones:user:{id}`
- `reservas:usuario:{id}`
- `reservas:espacio:{id}`
- `reservas:todas` (admin)
- `disponibilidad:espacio:{id}`
- `dashboard:admin`

**Eventos emitidos:**
- `reserva_creada`, `reserva_actualizada`, `reserva_cancelada`
- `nueva_notificacion`, `notificacion_actualizada`
- `disponibilidad_actualizada`
- `stats_update`

### 3. Base de Datos PostgreSQL

**Esquema actual:**
```sql
tipo_usuario (roles: admin, staff, estudiante)
usuario (email, password_hash, tipo_usuario_id, estado)
categoria_espacio
espacio (codigo, nombre, capacidad, categoria_id)
caracteristica_espacio
tipo_evento
estado_reserva (Pendiente, Aprobada, Rechazada, Cancelada)
reserva (codigo, usuario_id, espacio_id, fecha, hora_inicio, hora_fin)
notificacion (usuario_id, titulo, mensaje, leida)
disponibilidad_espacio (horarios por día)

-- Auth Service tables (misma BD):
refresh_token (token, usuario_id, expira_en, revocado)
```

### 4. Flujo de Negocio Actual

#### Flujo de Reserva:
```
1. Usuario autenticado crea reserva → POST /api/reservas
2. REST valida disponibilidad (sin conflictos)
3. Crea reserva en estado "Pendiente" (si requiere aprobación) o "Aprobada"
4. Genera código único de reserva
5. Emite webhook → WebSocket Service
6. WebSocket emite evento → canales suscritos
7. Frontend recibe notificación en tiempo real
8. Admin puede aprobar/rechazar desde dashboard
```

---

## 🏗️ ARQUITECTURA PROPUESTA: PAYMENT SERVICE (Pilar 2)

### 1. Objetivo del Payment Service

Implementar un **microservicio de pagos** con:
- ✅ Abstracción de pasarelas mediante **Adapter Pattern**
- ✅ Sistema de webhooks **bidireccionales** con firma HMAC
- ✅ Registro de partners externos (otros grupos)
- ✅ Normalización de eventos de diferentes proveedores
- ✅ Base de datos propia para transacciones y partners

### 2. Arquitectura del Payment Service

```
┌────────────────────────────────────────────────────────────────┐
│                     PAYMENT SERVICE                             │
│                  (Python + FastAPI + SQLAlchemy)               │
│                        Port: 8001                               │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              API Layer (FastAPI Routes)                   │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │ POST /api/v1/payments/create                             │ │
│  │ POST /api/v1/payments/webhook/stripe                     │ │
│  │ POST /api/v1/payments/webhook/mercadopago               │ │
│  │ POST /api/v1/payments/webhook/mock                       │ │
│  │ GET  /api/v1/payments/{payment_id}                       │ │
│  │                                                            │ │
│  │ POST /api/v1/partners/register                           │ │
│  │ GET  /api/v1/partners                                    │ │
│  │ POST /api/v1/partners/webhook (recibe de partners)      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           │                                     │
│  ┌────────────────────────▼─────────────────────────────────┐ │
│  │           Business Logic Layer (Services)                 │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │ PaymentService                                            │ │
│  │ - create_payment()                                        │ │
│  │ - process_webhook()                                       │ │
│  │ - get_payment_status()                                    │ │
│  │                                                            │ │
│  │ PartnerService                                            │ │
│  │ - register_partner()                                      │ │
│  │ - notify_partner(event, payload)                         │ │
│  │ - verify_partner_signature()                             │ │
│  │                                                            │ │
│  │ HMACService                                               │ │
│  │ - generate_signature(payload, secret)                    │ │
│  │ - verify_signature(payload, signature, secret)           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           │                                     │
│  ┌────────────────────────▼─────────────────────────────────┐ │
│  │    Payment Provider Layer (Adapter Pattern)               │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │                                                            │ │
│  │  ┌───────────────────────────────────────────────────┐   │ │
│  │  │  PaymentProvider (Abstract Interface)             │   │ │
│  │  ├───────────────────────────────────────────────────┤   │ │
│  │  │  + create_payment()                               │   │ │
│  │  │  + get_payment_status()                           │   │ │
│  │  │  + normalize_webhook(raw_data) → NormalizedEvent │   │ │
│  │  │  + validate_webhook_signature()                   │   │ │
│  │  └───────────────────────────────────────────────────┘   │ │
│  │                         ▲                                  │ │
│  │         ┌───────────────┼───────────────┐                 │ │
│  │         │               │               │                 │ │
│  │   ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐          │ │
│  │   │  Stripe   │  │ MercadoPago│  │   Mock    │          │ │
│  │   │  Adapter  │  │  Adapter   │  │  Adapter  │          │ │
│  │   └───────────┘  └───────────┘  └───────────┘          │ │
│  │                                                            │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           │                                     │
│  ┌────────────────────────▼─────────────────────────────────┐ │
│  │               Data Layer (SQLAlchemy ORM)                 │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │ Models:                                                   │ │
│  │ - Payment (transaction)                                   │ │
│  │ - PaymentProvider (configuración de providers)           │ │
│  │ - Partner (registro de grupos externos)                  │ │
│  │ - PartnerWebhookLog (auditoría de webhooks)             │ │
│  │ - WebhookEvent (eventos normalizados)                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           │                                     │
│                ┌──────────▼──────────┐                         │
│                │   PostgreSQL DB     │                         │
│                │ payment_service_db  │                         │
│                └─────────────────────┘                         │
└────────────────────────────────────────────────────────────────┘
```

### 3. Modelos de Base de Datos

```python
# payment_provider
- id (PK)
- name (stripe, mercadopago, mock)
- is_active
- config_json (API keys, secrets)
- creado_en, actualizado_en

# payment
- id (PK)
- payment_id_externo (ID del provider)
- reserva_id (FK a rest-service.reserva)
- usuario_id (FK a rest-service.usuario)
- provider_name (stripe, mercadopago, mock)
- amount (Decimal)
- currency (USD, MXN, etc.)
- status (pending, completed, failed, refunded)
- metadata_json (datos adicionales)
- creado_en, actualizado_en

# partner
- id (PK)
- nombre (Grupo B - Tours)
- webhook_url (https://partner.com/webhook)
- shared_secret (para HMAC)
- eventos_suscritos (JSON array: ["booking.confirmed", "payment.success"])
- is_active
- creado_en, actualizado_en

# partner_webhook_log
- id (PK)
- partner_id (FK)
- event_type (booking.confirmed, payment.success)
- payload_json (payload enviado)
- response_status (200, 500, etc.)
- response_body (respuesta del partner)
- signature_valid (boolean)
- creado_en

# webhook_event (eventos normalizados)
- id (PK)
- event_type (payment.success, payment.failed)
- source (stripe, mercadopago, mock, partner)
- payload_json (payload normalizado)
- processed (boolean)
- creado_en
```

### 4. Patrón Adapter - PaymentProvider

```python
# adapters/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from ..schemas.payment import NormalizedWebhookEvent

class PaymentProvider(ABC):
    """
    Interface abstracta que define el contrato para todos los
    payment providers. Implementa el Adapter Pattern.
    """
    
    @abstractmethod
    def create_payment(self, amount: float, currency: str, 
                      metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un pago en el provider externo"""
        pass
    
    @abstractmethod
    def get_payment_status(self, payment_id: str) -> str:
        """Obtiene el estado actual del pago"""
        pass
    
    @abstractmethod
    def normalize_webhook(self, raw_data: Dict[str, Any]) -> NormalizedWebhookEvent:
        """
        Normaliza el webhook del provider a un formato común.
        Esto es crucial para abstraer las diferencias entre providers.
        """
        pass
    
    @abstractmethod
    def validate_webhook_signature(self, payload: bytes, 
                                   signature: str) -> bool:
        """Valida la firma del webhook del provider"""
        pass


# adapters/stripe_adapter.py
class StripeAdapter(PaymentProvider):
    def __init__(self, api_key: str, webhook_secret: str):
        self.api_key = api_key
        self.webhook_secret = webhook_secret
    
    def create_payment(self, amount, currency, metadata):
        # Llamada a Stripe API
        pass
    
    def normalize_webhook(self, raw_data):
        # Convierte formato Stripe → formato común
        event_type = raw_data.get('type')
        if event_type == 'payment_intent.succeeded':
            return NormalizedWebhookEvent(
                event_type='payment.success',
                payment_id=raw_data['data']['object']['id'],
                status='completed',
                amount=raw_data['data']['object']['amount'] / 100,
                currency=raw_data['data']['object']['currency'],
                metadata=raw_data['data']['object']['metadata']
            )
        # ... más eventos


# adapters/mock_adapter.py
class MockAdapter(PaymentProvider):
    """Adapter para desarrollo sin APIs reales"""
    
    def create_payment(self, amount, currency, metadata):
        return {
            'payment_id': f'mock_{uuid.uuid4()}',
            'status': 'completed',
            'amount': amount,
            'currency': currency
        }
    
    def normalize_webhook(self, raw_data):
        # Ya viene en formato normalizado
        return NormalizedWebhookEvent(**raw_data)
```

### 5. Sistema de Webhooks Bidireccionales

#### 5.1 Flujo de Registro de Partner

```
Grupo A (Nosotros)          Grupo B (Partner)
      │                           │
      │←─── POST /partners/register
      │      {
      │        "nombre": "Grupo B - Tours",
      │        "webhook_url": "https://grupob.com/webhook",
      │        "eventos": ["booking.confirmed", "payment.success"]
      │      }
      │                           │
      │──────── Response ────────→│
      │      {
      │        "partner_id": 1,
      │        "shared_secret": "abc123...xyz",
      │        "status": "active"
      │      }
```

#### 5.2 Flujo de Notificación a Partner

```
                    NUESTRO PAYMENT SERVICE
                           │
1. Evento interno          │
   (pago completado)       │
                           │
2. PaymentService          │
   .notify_partners()      │
                           │
3. Buscar partners         │
   suscritos al evento     │
                           │
4. Para cada partner:      │
   ┌────────────────────────┴─────────────────────┐
   │ a) Generar firma HMAC                        │
   │    signature = hmac(payload, partner.secret) │
   │                                               │
   │ b) Enviar POST a partner.webhook_url         │
   │    Headers:                                   │
   │    - X-Webhook-Signature: {signature}        │
   │    - X-Event-Type: payment.success           │
   │    Body: {payload_json}                      │
   │                                               │
   │ c) Registrar en partner_webhook_log          │
   └───────────────────────────────────────────────┘
                           │
                           ▼
                    Partner recibe
                    y verifica firma
```

#### 5.3 Flujo de Recepción desde Partner

```
Partner envía evento          NUESTRO PAYMENT SERVICE
      │                              │
      │───── POST /partners/webhook ─→│
      │  Headers:                     │
      │  X-Webhook-Signature: xyz...  │
      │  X-Partner-Id: 1              │
      │  Body: {                      │
      │    "event": "tour.purchased", │
      │    "data": {...}              │
      │  }                            │
      │                               │
      │                        1. Identificar partner
      │                        2. Obtener shared_secret
      │                        3. Verificar firma HMAC
      │                        4. Si válida → procesar
      │                        5. Ejecutar acción de negocio
      │                        6. Responder 200 OK
      │                               │
      │←────── 200 OK { "ack": true } ──────┘
```

### 6. Integración con Servicios Existentes

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUJO COMPLETO E2E                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Usuario crea reserva                                    │
│     ↓ POST /api/reservas (REST Service)                    │
│                                                              │
│  2. Reserva creada con estado "Pendiente"                   │
│     ↓ Genera código de reserva                              │
│                                                              │
│  3. Frontend solicita pago                                   │
│     ↓ POST /api/v1/payments/create (Payment Service)       │
│     {                                                        │
│       "reserva_id": 123,                                    │
│       "amount": 50.00,                                      │
│       "currency": "USD",                                    │
│       "provider": "mock"                                    │
│     }                                                        │
│                                                              │
│  4. Payment Service crea pago                               │
│     ↓ Usa MockAdapter.create_payment()                     │
│     ↓ Almacena en BD (tabla payment)                       │
│                                                              │
│  5. Provider procesa pago                                   │
│     ↓ Envía webhook → POST /payments/webhook/mock          │
│                                                              │
│  6. Payment Service recibe webhook                          │
│     ↓ Normaliza evento (MockAdapter.normalize_webhook)     │
│     ↓ Actualiza payment.status = "completed"               │
│     ↓ Llama REST Service: PATCH /api/reservas/123/estado   │
│        {"estado_id": 2}  // Aprobada                       │
│                                                              │
│  7. REST Service actualiza reserva                          │
│     ↓ reserva.estado_id = 2 (Aprobada)                     │
│     ↓ Emite webhook → WebSocket Service                    │
│                                                              │
│  8. WebSocket emite evento en tiempo real                   │
│     ↓ Evento: reserva_aprobada                             │
│     ↓ Canal: notificaciones:user:{usuario_id}              │
│                                                              │
│  9. Payment Service notifica partners                       │
│     ↓ PartnerService.notify_partners()                     │
│     ↓ Evento: "booking.confirmed"                          │
│     ↓ Para cada partner suscrito:                          │
│       - Genera firma HMAC                                   │
│       - POST partner.webhook_url                            │
│                                                              │
│ 10. Partner recibe evento                                   │
│     ↓ Verifica firma                                        │
│     ↓ Ejecuta acción (ej: ofrecer tours)                   │
│     ↓ Puede responder con su propio evento                 │
│                                                              │
│ 11. Frontend recibe notificación                            │
│     ↓ Socket.IO: reserva_aprobada                          │
│     ↓ Actualiza UI en tiempo real                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 7. Seguridad: HMAC-SHA256

```python
# services/hmac_service.py
import hmac
import hashlib
import json
from typing import Dict, Any

class HMACService:
    @staticmethod
    def generate_signature(payload: Dict[str, Any], secret: str) -> str:
        """
        Genera una firma HMAC-SHA256 del payload.
        """
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    @staticmethod
    def verify_signature(payload: Dict[str, Any], 
                        received_signature: str, 
                        secret: str) -> bool:
        """
        Verifica que la firma recibida coincida con la calculada.
        """
        expected_signature = HMACService.generate_signature(payload, secret)
        return hmac.compare_digest(expected_signature, received_signature)
```

**Uso en endpoints:**
```python
@router.post("/partners/webhook")
async def receive_partner_webhook(
    request: Request,
    partner_id: int = Header(..., alias="X-Partner-Id"),
    signature: str = Header(..., alias="X-Webhook-Signature"),
    db: Session = Depends(get_db)
):
    # 1. Obtener partner y su secret
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(404, "Partner not found")
    
    # 2. Leer payload
    payload = await request.json()
    
    # 3. Verificar firma
    if not HMACService.verify_signature(payload, signature, partner.shared_secret):
        raise HTTPException(401, "Invalid signature")
    
    # 4. Procesar evento
    # ...
    
    return {"ack": True}
```

### 8. Stack Tecnológico del Payment Service

```yaml
Framework: FastAPI 0.104+
ORM: SQLAlchemy 2.0+
Migraciones: Alembic
Validación: Pydantic v2
Base de Datos: PostgreSQL 15+
HTTP Client: httpx (async)
Testing: pytest + pytest-asyncio
Documentación: OpenAPI/Swagger (automático con FastAPI)
```

### 9. Variables de Entorno

```bash
# Payment Service (.env)
DATABASE_URL=postgresql://postgres:password@localhost:5432/payment_service_db
SECRET_KEY=shared-jwt-secret-with-auth-service

# Provider Configs
STRIPE_API_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
MERCADOPAGO_ACCESS_TOKEN=TEST-...
MOCK_PROVIDER_ENABLED=true

# REST Service URL (para callback de estado de reserva)
REST_SERVICE_URL=http://localhost:8000

# WebSocket Service URL (para notificaciones)
WEBSOCKET_SERVICE_URL=http://localhost:3001

PORT=8001
API_PREFIX=api/v1
CORS_ORIGINS=http://localhost:5173
```

---

## 🎯 PLAN DE IMPLEMENTACIÓN EN 4 COMMITS

### **Commit 1: Setup Inicial y Estructura Base**
- Crear directorio `payment-service/`
- Configurar FastAPI + SQLAlchemy
- Definir modelos (Payment, PaymentProvider, Partner, WebhookEvent)
- Configurar Alembic y crear migraciones
- Setup de entorno (.env, requirements.txt)
- README básico

**Archivos:**
```
payment-service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   └── models/
│       ├── __init__.py
│       ├── payment.py
│       ├── partner.py
│       └── webhook_event.py
├── alembic/
│   └── versions/
├── requirements.txt
├── .env.example
└── README.md
```

### **Commit 2: Payment Provider Layer (Adapter Pattern)**
- Implementar interface `PaymentProvider` (ABC)
- Crear `MockAdapter` completo
- Crear `StripeAdapter` (básico)
- Esquemas Pydantic para normalización
- Servicio de pagos básico

**Archivos:**
```
payment-service/app/
├── adapters/
│   ├── __init__.py
│   ├── base.py (PaymentProvider ABC)
│   ├── mock_adapter.py
│   └── stripe_adapter.py
├── schemas/
│   ├── __init__.py
│   ├── payment.py
│   └── webhook.py
└── services/
    ├── __init__.py
    └── payment_service.py
```

### **Commit 3: Sistema de Webhooks y Partners**
- Endpoints de partners (register, list)
- Servicio HMAC para firmas
- Endpoints de webhooks (recibir de providers)
- Endpoints de webhooks (enviar/recibir de partners)
- Logging de webhooks

**Archivos:**
```
payment-service/app/
├── routes/
│   ├── __init__.py
│   ├── payments.py
│   └── partners.py
├── services/
│   ├── hmac_service.py
│   └── partner_service.py
└── utils/
    ├── __init__.py
    └── webhook_logger.py
```

### **Commit 4: Integración con Servicios y Testing**
- Integrar con REST service (actualizar estado de reserva)
- Integrar con WebSocket service (notificar pagos)
- Middleware de autenticación JWT
- Tests unitarios (pytest)
- Documentación completa (README + API docs)
- Scripts de demostración

**Archivos:**
```
payment-service/
├── app/
│   ├── middleware/
│   │   └── auth.py
│   └── integrations/
│       ├── rest_service.py
│       └── websocket_service.py
├── tests/
│   ├── test_payment_service.py
│   ├── test_adapters.py
│   ├── test_hmac.py
│   └── test_webhooks.py
├── scripts/
│   ├── test_payment_flow.py
│   └── register_partner_demo.py
└── docs/
    ├── INTEGRATION_GUIDE.md
    └── PARTNER_GUIDE.md
```

---

## 📋 CHECKLIST DE REQUISITOS DEL PILAR 2

### Componentes Requeridos (20%)

- [ ] **Payment Service Wrapper (8%)**
  - [ ] Interface `PaymentProvider` abstracta
  - [ ] `MockAdapter` implementado (obligatorio)
  - [ ] `StripeAdapter` implementado
  - [ ] Normalización de webhooks a formato común

- [ ] **Registro de Partners (4%)**
  - [ ] POST `/partners/register`
  - [ ] Generación de `shared_secret` para HMAC
  - [ ] Almacenamiento de `webhook_url` y eventos suscritos

- [ ] **Autenticación HMAC (4%)**
  - [ ] Generación de firma HMAC-SHA256
  - [ ] Verificación de firma en webhooks entrantes
  - [ ] Envío de firma en webhooks salientes

- [ ] **Eventos Bidireccionales (4%)**
  - [ ] Envío de webhooks a partners
  - [ ] Recepción de webhooks de partners
  - [ ] Procesamiento de eventos de partners
  - [ ] Coordinación con al menos otro grupo

### Eventos Sugeridos
```python
OUTGOING_EVENTS = [
    "booking.confirmed",     # Reserva confirmada tras pago
    "payment.success",       # Pago exitoso
    "payment.failed",        # Pago fallido
    "booking.cancelled",     # Reserva cancelada
]

INCOMING_EVENTS = [
    "service.activated",     # Servicio externo activado
    "tour.purchased",        # Tour comprado (ejemplo partner)
    "order.created",         # Orden creada en sistema partner
]
```

---

## 🔄 MEJORES PRÁCTICAS APLICADAS

### 1. Arquitectura
- ✅ **Separation of Concerns**: Capas bien definidas (routes, services, adapters, models)
- ✅ **Adapter Pattern**: Abstracción de payment providers
- ✅ **Dependency Injection**: FastAPI Depends para DB, servicios, auth
- ✅ **Repository Pattern**: Acceso a datos a través de SQLAlchemy ORM

### 2. Código
- ✅ **Type Hints**: Python typing en todos los métodos
- ✅ **Pydantic Schemas**: Validación automática de datos
- ✅ **Async/Await**: Operaciones I/O asíncronas (httpx, FastAPI)
- ✅ **Error Handling**: HTTPException con códigos apropiados
- ✅ **Logging**: Registro de eventos críticos (pagos, webhooks)

### 3. Seguridad
- ✅ **HMAC-SHA256**: Firma de todos los webhooks
- ✅ **JWT Validation**: Endpoints protegidos con JWT del auth-service
- ✅ **Secrets Management**: Variables de entorno para API keys
- ✅ **Input Validation**: Pydantic para validar todos los inputs
- ✅ **SQL Injection Prevention**: SQLAlchemy ORM (no raw queries)

### 4. Base de Datos
- ✅ **Migraciones**: Alembic para versionado de esquema
- ✅ **Índices**: En campos de búsqueda frecuente
- ✅ **Foreign Keys**: Integridad referencial
- ✅ **Timestamps**: created_at, updated_at en todas las tablas

### 5. Testing
- ✅ **Unit Tests**: pytest para lógica de negocio
- ✅ **Integration Tests**: Tests de endpoints con DB de prueba
- ✅ **Mock Tests**: Simular llamadas a APIs externas
- ✅ **Coverage**: Objetivo 80%+ de cobertura

### 6. Documentación
- ✅ **OpenAPI/Swagger**: Generado automáticamente por FastAPI
- ✅ **README completo**: Instalación, configuración, uso
- ✅ **Integration Guide**: Para conectar con REST/WS services
- ✅ **Partner Guide**: Para que otros grupos integren webhooks

---

## 🎨 LÓGICA DE NEGOCIO

### Casos de Uso Principales

#### 1. Procesar Pago de Reserva
```
Input: reserva_id, usuario_id, amount, provider
Process:
  1. Validar reserva existe y está pendiente
  2. Validar usuario es dueño de la reserva
  3. Seleccionar adapter según provider
  4. Crear pago en provider externo
  5. Almacenar transacción en BD
  6. Retornar payment_id
Output: PaymentResponse con estado "pending"
```

#### 2. Webhook de Pago Exitoso
```
Input: Webhook de provider (Stripe/MercadoPago/Mock)
Process:
  1. Validar firma del provider
  2. Normalizar evento a formato común
  3. Buscar payment en BD
  4. Actualizar payment.status = "completed"
  5. Llamar REST service → actualizar reserva a "Aprobada"
  6. Notificar WebSocket service
  7. Notificar partners suscritos a "booking.confirmed"
Output: 200 OK al provider
```

#### 3. Registrar Partner Externo
```
Input: nombre, webhook_url, eventos_suscritos
Process:
  1. Validar URL es válida
  2. Generar shared_secret aleatorio (32 bytes)
  3. Crear registro en tabla partner
  4. Retornar partner_id y shared_secret
Output: PartnerResponse con credenciales
```

#### 4. Notificar Partner
```
Input: event_type, payload
Process:
  1. Buscar partners activos suscritos al evento
  2. Para cada partner:
     a. Construir payload normalizado
     b. Generar firma HMAC con partner.shared_secret
     c. POST a partner.webhook_url con headers:
        - X-Webhook-Signature
        - X-Event-Type
     d. Registrar en partner_webhook_log
     e. Manejar errores (retry con backoff)
Output: Lista de resultados por partner
```

#### 5. Recibir Webhook de Partner
```
Input: Webhook de partner con firma HMAC
Process:
  1. Extraer X-Partner-Id del header
  2. Buscar partner en BD
  3. Verificar firma HMAC con partner.shared_secret
  4. Si válida:
     a. Registrar en partner_webhook_log
     b. Procesar evento según tipo
     c. Ejecutar acción de negocio
     d. Retornar 200 OK
  5. Si inválida: 401 Unauthorized
Output: Acknowledgment
```

### Flujos de Error

#### Pago Fallido
```
Webhook de provider → payment.failed
↓
Actualizar payment.status = "failed"
↓
NO actualizar reserva (sigue en "Pendiente")
↓
Notificar usuario vía WebSocket
↓
Frontend muestra error + opción de reintentar
```

#### Partner No Disponible
```
Intentar notificar partner → timeout/error
↓
Registrar error en partner_webhook_log
↓
Sistema de retry con backoff exponencial:
  - Intento 1: inmediato
  - Intento 2: +1 minuto
  - Intento 3: +5 minutos
  - Intento 4: +30 minutos
↓
Si falla 4 veces → marcar como "failed", alertar admin
```

---

## 🔗 ENDPOINTS COMPLETOS

### Payments

```http
POST /api/v1/payments/create
Authorization: Bearer {jwt}
Content-Type: application/json

{
  "reserva_id": 123,
  "amount": 50.00,
  "currency": "USD",
  "provider": "mock"
}

Response 201:
{
  "payment_id": 1,
  "external_payment_id": "mock_abc123",
  "status": "pending",
  "amount": 50.00,
  "currency": "USD",
  "provider": "mock",
  "created_at": "2025-01-15T10:00:00Z"
}
```

```http
GET /api/v1/payments/{payment_id}
Authorization: Bearer {jwt}

Response 200:
{
  "id": 1,
  "reserva_id": 123,
  "usuario_id": 5,
  "status": "completed",
  "amount": 50.00,
  "currency": "USD",
  "provider": "mock",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:05:00Z"
}
```

### Webhooks (Providers)

```http
POST /api/v1/payments/webhook/mock
Content-Type: application/json
X-Mock-Signature: abc123...

{
  "event_type": "payment.success",
  "payment_id": "mock_abc123",
  "status": "completed",
  "amount": 50.00,
  "currency": "USD"
}

Response 200:
{
  "received": true,
  "processed": true
}
```

### Partners

```http
POST /api/v1/partners/register
Content-Type: application/json

{
  "nombre": "Grupo B - Tours",
  "webhook_url": "https://grupob.uleam.edu.ec/webhook",
  "eventos_suscritos": ["booking.confirmed", "payment.success"]
}

Response 201:
{
  "partner_id": 1,
  "nombre": "Grupo B - Tours",
  "shared_secret": "a1b2c3d4e5f6...",
  "webhook_url": "https://grupob.uleam.edu.ec/webhook",
  "eventos_suscritos": ["booking.confirmed", "payment.success"],
  "is_active": true
}
```

```http
GET /api/v1/partners
Authorization: Bearer {jwt} (admin only)

Response 200:
[
  {
    "id": 1,
    "nombre": "Grupo B - Tours",
    "webhook_url": "https://grupob.uleam.edu.ec/webhook",
    "eventos_suscritos": ["booking.confirmed", "payment.success"],
    "is_active": true,
    "created_at": "2025-01-15T09:00:00Z"
  }
]
```

### Webhooks (Partners - Incoming)

```http
POST /api/v1/partners/webhook
Content-Type: application/json
X-Partner-Id: 1
X-Webhook-Signature: hmac_sha256_signature
X-Event-Type: tour.purchased

{
  "tour_id": 456,
  "reserva_id": 123,
  "usuario_id": 5,
  "tour_name": "City Tour",
  "price": 30.00,
  "scheduled_date": "2025-02-01"
}

Response 200:
{
  "ack": true,
  "message": "Event processed successfully"
}
```

---

## 📊 RESUMEN

Este análisis proporciona:

1. ✅ **Comprensión completa del sistema actual** (4 servicios + BD)
2. ✅ **Arquitectura detallada del Payment Service** (Pilar 2)
3. ✅ **Aplicación del Adapter Pattern** para payment providers
4. ✅ **Sistema de webhooks bidireccionales** con HMAC
5. ✅ **Integración con servicios existentes** (REST, WebSocket)
6. ✅ **Mejores prácticas de Python/FastAPI**
7. ✅ **Lógica de negocio clara y robusta**
8. ✅ **Plan de implementación en 4 commits**

El sistema resultante será:
- 🏗️ **Modular y escalable**
- 🔒 **Seguro** (HMAC, JWT, validaciones)
- 🔄 **Interoperable** (webhooks B2B con otros grupos)
- 🧪 **Testeable** (unit + integration tests)
- 📖 **Bien documentado** (README, API docs, guías)

**Próximo paso:** Implementar los 4 commits según el plan definido.
