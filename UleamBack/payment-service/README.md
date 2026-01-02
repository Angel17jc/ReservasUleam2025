# 💳 Payment Service - ULEAM Reservas

> **Pilar 2:** Webhooks e Interoperabilidad B2B  
> **Microservicio de Pagos** con abstracción de pasarelas y comunicación bidireccional

---

## 📋 Descripción

Microservicio independiente que maneja:

- ✅ **Abstracción de pasarelas de pago** (Patrón Adapter)
- ✅ **MockAdapter** para desarrollo y testing
- ✅ **StripeAdapter** para pagos reales (modo test)
- ✅ **Registro de Partners** para integración B2B
- ✅ **Autenticación HMAC-SHA256** en webhooks
- ✅ **Eventos bidireccionales** con otros sistemas

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                   PAYMENT SERVICE (Puerto 9001)             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           PaymentProvider (Interface)                │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│       ┌───────────┼───────────┬───────────────┐            │
│       │           │           │               │            │
│  ┌────▼────┐ ┌───▼─────┐ ┌──▼──────┐   ┌───▼────────┐    │
│  │  Mock   │ │ Stripe  │ │Mercado  │...│  Future    │    │
│  │ Adapter │ │ Adapter │ │  Pago   │   │  Adapters  │    │
│  └─────────┘ └─────────┘ └─────────┘   └────────────┘    │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Payment Controller & Service                │  │
│  │  - POST /payments                                    │  │
│  │  - GET /payments/:id                                 │  │
│  │  - GET /payments/reserva/:reservaId                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Database (PostgreSQL)                   │  │
│  │  - payments                                          │  │
│  │  - partners (Commit 3)                               │  │
│  │  - webhook_logs (Commit 3)                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Instalación y Configuración

### Prerrequisitos

- Node.js 18+
- PostgreSQL 14+
- npm o yarn

### Paso 1: Instalar dependencias

```bash
cd payment-service
npm install
```

### Paso 2: Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus credenciales
```

### Paso 3: Crear base de datos

```bash
# Conectar a PostgreSQL
psql -U postgres

# Verificar que la base de datos 'reservasuleam' existe
# (Ya debería existir del REST Service)
\l

# Si no existe:
CREATE DATABASE reservasuleam;
```

### Paso 4: Ejecutar migración

```bash
# Conectar a la base de datos y ejecutar:
psql -U postgres -d reservasuleam -f src/database/migrations/001_create_payments_table.sql
```

### Paso 5: Iniciar el servicio

```bash
# Modo desarrollo
npm run start:dev

# Modo producción
npm run build
npm run start:prod
```

**Servicio corriendo en:** `http://localhost:9001`  
**Swagger docs:** `http://localhost:9001/api`

---

## 📦 Commit 1: MockAdapter (Estado Actual)

### ✅ Implementado

- [x] Estructura completa del microservicio NestJS
- [x] Interface `PaymentProvider` abstracta
- [x] `MockAdapter` para desarrollo
- [x] Entidad `Payment` con TypeORM
- [x] Controller con endpoints básicos
- [x] Service con lógica de negocio
- [x] Migración de base de datos
- [x] Documentación Swagger

### 🧪 Testing

```bash
# 1. Crear pago con MockAdapter
POST http://localhost:9001/payments
Content-Type: application/json

{
  "reserva_id": 1,
  "usuario_id": 1,
  "amount": 150.00,
  "currency": "USD",
  "provider": "mock"
}

# Respuesta esperada:
{
  "id": 1,
  "transaction_id": "mock_txn_abc123def456",
  "status": "completed",
  "amount": 150.00,
  "currency": "USD",
  "provider": "mock",
  "reserva_id": 1,
  "usuario_id": 1,
  "created_at": "2026-01-14T10:00:00.000Z"
}

# 2. Consultar pago por ID
GET http://localhost:9001/payments/1

# 3. Consultar pagos de una reserva
GET http://localhost:9001/payments/reserva/1
```

---

## 🔌 Endpoints API

### POST /payments

Crear un nuevo pago.

**Body:**
```json
{
  "reserva_id": 1,
  "usuario_id": 1,
  "amount": 150.00,
  "currency": "USD",
  "provider": "mock",
  "metadata": {
    "espacio": "Auditorio Principal",
    "fecha": "2026-02-15"
  }
}
```

**Response:**
```json
{
  "id": 1,
  "transaction_id": "mock_txn_...",
  "status": "completed",
  "amount": 150.00,
  "currency": "USD",
  "provider": "mock",
  "reserva_id": 1,
  "usuario_id": 1,
  "metadata": {...},
  "created_at": "2026-01-14T10:00:00.000Z",
  "updated_at": "2026-01-14T10:00:00.000Z"
}
```

### GET /payments/:id

Obtener un pago por ID.

### GET /payments/reserva/:reservaId

Obtener todos los pagos de una reserva.

---

## 🎯 Próximos Commits

### Commit 2: StripeAdapter + Normalización
- [ ] Implementar `StripeAdapter`
- [ ] Webhook receiver para Stripe
- [ ] Normalización de eventos
- [ ] Testing con Stripe CLI

### Commit 3: Partners API + HMAC
- [ ] Modelo `Partner`
- [ ] POST /partners/register
- [ ] HMAC verification
- [ ] Webhook sender/receiver

### Commit 4: Eventos Bidireccionales
- [ ] Event handlers
- [ ] Integración con REST Service
- [ ] Integración con WebSocket Service

### Commit 5: Integración con Tours
- [ ] Testing con ngrok
- [ ] Documentación de integración
- [ ] Casos de uso reales

---

## 🗄️ Modelo de Datos

### Tabla `payments`

```sql
id              SERIAL PRIMARY KEY
reserva_id      INTEGER NOT NULL
usuario_id      INTEGER NOT NULL
provider        VARCHAR(50) NOT NULL
transaction_id  VARCHAR(255) UNIQUE NOT NULL
amount          DECIMAL(10,2) NOT NULL
currency        VARCHAR(3) DEFAULT 'USD'
status          VARCHAR(50) NOT NULL
metadata        JSONB
created_at      TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP DEFAULT NOW()
```

**Status posibles:**
- `pending` - Pago iniciado
- `completed` - Pago completado
- `failed` - Pago fallido
- `refunded` - Pago reembolsado

---

## 🔧 Configuración de Providers

### MockAdapter (Actual)

Siempre disponible para desarrollo. No requiere configuración adicional.

```typescript
// Uso en request
{
  "provider": "mock"
}

// Comportamiento:
// - Genera transaction_id único
// - Siempre retorna status: "completed"
// - Simula delay de 100ms
```

### StripeAdapter (Commit 2)

Requiere cuenta Stripe (modo test).

```env
STRIPE_SECRET_KEY=sk_test_51xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
STRIPE_ENABLED=true
```

---

## 📊 Logs y Monitoreo

El servicio registra todos los eventos:

```
[Payment Service] Payment created: ID 1, Provider: mock, Amount: 150.00 USD
[Payment Service] Transaction completed: mock_txn_abc123
```

---

## 🤝 Contribuciones

Este servicio es parte del Proyecto Final - ULEAM 2025

---

## 📄 Licencia

MIT License - ULEAM 2025
