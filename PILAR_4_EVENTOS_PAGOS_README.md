# 🎛️ PILAR 4: Event Bus Centralizado con WebSocket + GraphQL + Payment

**Versión:** 1.0  
**Fecha:** 27 de Enero de 2026  
**Estado:** ✅ En Desarrollo  
**Líderes Técnicos:** Equipos WebSocket, GraphQL, Payment

---

## 📋 Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Componentes del Pilar 4](#componentes-del-pilar-4)
3. [WebSocket Service (NestJS)](#websocket-service-nestjs)
4. [Payment Service (FastAPI)](#payment-service-fastapi)
5. [GraphQL Service Analytics](#graphql-service-analytics)
6. [Flujos de Integración](#flujos-de-integración)
7. [Instalación](#instalación)
8. [Testing y Deployment](#testing-y-deployment)

---

## 🎯 Visión General

El **Pilar 4** es el corazón del sistema de notificaciones, pagos y análisis en tiempo real. Proporciona tres servicios complementarios:

- **WebSocket Service:** Notificaciones push en tiempo real
- **Payment Service:** Procesamiento de pagos y transacciones
- **GraphQL Analytics:** Reportes y estadísticas avanzadas

### Responsabilidades Principales
- ✅ Notificaciones en tiempo real (WebSocket)
- ✅ Procesamiento de pagos (múltiples proveedores)
- ✅ Webhooks bidireccionales con partners
- ✅ Análisis de datos en vivo (GraphQL)
- ✅ Health checks automáticos
- ✅ Auditoría y logging de transacciones

---

## 🏗️ Componentes del Pilar 4

### Diagrama General

```
┌──────────────────────────────────────────────────────────────────┐
│                    PILAR 4: EVENTOS Y PAGOS                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Frontend (React)                                                │
│      │                                                            │
│      ├─→ WebSocket: Escucha eventos                              │
│      ├─→ GraphQL: Queries analíticas                             │
│      └─→ REST: Iniciar proceso de pago                           │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │         WebSocket Service (NestJS)                     │     │
│  │         Port: 3001                                      │     │
│  │  ┌──────────────────────────────────────────────────┐  │     │
│  │  │ • Socket.IO server                               │  │     │
│  │  │ • Webhook listeners (REST → WS emitter)          │  │     │
│  │  │ • Rooms por usuario                              │  │     │
│  │  │ • Events: reserva_creada, reserva_actualizada    │  │     │
│  │  │ • Broadcast de stats                             │  │     │
│  │  └──────────────────────────────────────────────────┘  │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │      Payment Service (FastAPI)                         │     │
│  │      Port: 8001                                         │     │
│  │  ┌──────────────────────────────────────────────────┐  │     │
│  │  │ • Integration Stripe                             │  │     │
│  │  │ • Integration MercadoPago                        │  │     │
│  │  │ • Integration MockAdapter (testing)              │  │     │
│  │  │ • Webhook processing                             │  │     │
│  │  │ • Fraud detection                                │  │     │
│  │  │ • Payment history                                │  │     │
│  │  └──────────────────────────────────────────────────┘  │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │    GraphQL Service (Go) - Reportes                    │     │
│  │    Port: 8080                                          │     │
│  │  ┌──────────────────────────────────────────────────┐  │     │
│  │  │ • Queries: estadísticas, top espacios            │  │     │
│  │  │ • Agregaciones en tiempo real                    │  │     │
│  │  │ • Reportes PDF (futuro)                          │  │     │
│  │  │ • Dashboard analytics                            │  │     │
│  │  └──────────────────────────────────────────────────┘  │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                   │
│  Integraciones Externas:                                         │
│  ├─ Stripe (pagos)                                              │
│  ├─ MercadoPago (pagos)                                         │
│  ├─ Email Service (notificaciones)                              │
│  ├─ Partners B2B (webhooks)                                     │
│  └─ n8n (Pilar 4 - orquestación)                                │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔌 WebSocket Service (NestJS)

### Descripción
Servicio de notificaciones en tiempo real usando Socket.IO. Emite eventos de reservas, pagos y estadísticas a clientes conectados.

### Stack
```
NestJS v10+
├─ Node.js 18+
├─ TypeScript
├─ Socket.IO
├─ TypeORM
└─ PostgreSQL
```

### Puerto y URL
```
URL: http://localhost:3001
WebSocket: ws://localhost:3001/socket.io
Docs: http://localhost:3001/api/v1/docs
```

### Estructura
```
websocket-service/
├── src/
│   ├── main.ts
│   ├── app.module.ts
│   ├── gateway/
│   │   └── events.gateway.ts          # Socket.IO gateway
│   ├── modules/
│   │   ├── webhook/
│   │   │   ├── webhook.controller.ts
│   │   │   ├── webhook.service.ts
│   │   │   └── webhook.module.ts
│   │   └── events/
│   │       ├── events.service.ts
│   │       └── events.module.ts
│   └── entities/
│       └── notification.entity.ts
└── docker-compose.yml
```

### Variables de Entorno
```env
DATABASE_URL=postgresql://Reservas_ULEAM:123456@localhost:5432/reservasuleam
JWT_SECRET=mi-secreto-auth-service-super-seguro-2025
PORT=3001
CORS_ORIGIN=http://localhost:5173,http://localhost:3000
LOG_LEVEL=debug
```

### Instalación
```bash
cd websocket-service
npm install
npm run start:dev
```

### Webhooks Soportados

#### 1. Reserva Creada
```http
POST /api/webhooks/reserva-creada
Content-Type: application/json
Authorization: Bearer {token}

{
  "reservaId": "uuid",
  "usuarioId": "uuid",
  "espacioId": "uuid",
  "fecha": "2026-02-10",
  "horaInicio": "10:00",
  "horaFin": "12:00",
  "codigo": "RES-2026-001"
}
```

**Emisión WebSocket:**
```javascript
socket.emit('reserva:creada', {
  id: 'uuid',
  codigo: 'RES-2026-001',
  usuario: { firstName: 'Juan' },
  espacio: { nombre: 'Aula 101' },
  fecha: '2026-02-10',
  timestamp: '2026-01-27T14:45:00Z'
});
```

---

#### 2. Reserva Actualizada
```http
POST /api/webhooks/reserva-actualizada
Content-Type: application/json

{
  "reservaId": "uuid",
  "nuevoEstado": "Aprobada",
  "motivo": "Pago confirmado"
}
```

**Emisión WebSocket:**
```javascript
socket.emit('reserva:actualizada', {
  id: 'uuid',
  codigo: 'RES-2026-001',
  estado: 'Aprobada',
  timestamp: '2026-01-27T14:50:00Z'
});
```

---

#### 3. Notificación Genérica
```http
POST /api/webhooks/notificacion
Content-Type: application/json

{
  "usuarioId": "uuid",
  "titulo": "Reserva Confirmada",
  "mensaje": "Tu reserva RES-2026-001 ha sido confirmada",
  "tipo": "success"
}
```

---

#### 4. Update de Estadísticas
```http
POST /api/webhooks/stats-update
Content-Type: application/json

{
  "evento": "stats.update",
  "payload": {
    "totalReservas": 150,
    "reservasHoy": 12,
    "usuariosActivos": 45
  }
}
```

---

### Cliente WebSocket (JavaScript)
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:3001', {
  auth: {
    token: localStorage.getItem('accessToken')
  }
});

// Escuchar reserva creada
socket.on('reserva:creada', (data) => {
  console.log('Nueva reserva:', data);
  // Actualizar UI
});

// Escuchar actualización de reserva
socket.on('reserva:actualizada', (data) => {
  console.log('Reserva actualizada:', data);
});

// Escuchar notificaciones
socket.on('notificacion', (data) => {
  console.log('Notificación:', data);
  // Mostrar toast
});

// Desconectar
socket.disconnect();
```

---

## 💳 Payment Service (FastAPI)

### Descripción
Servicio de procesamiento de pagos que se integra con múltiples proveedores (Stripe, MercadoPago, MockAdapter para testing).

### Stack
```
FastAPI v0.100+
├─ Python 3.11+
├─ Stripe SDK
├─ MercadoPago SDK
├─ SQLAlchemy 2.0
├─ Pydantic v2
└─ Uvicorn
```

### Puerto y URL
```
URL Base: http://localhost:8001
API: http://localhost:8001/api
Docs: http://localhost:8001/docs
```

### Estructura
```
payment-service/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── payment.py
│   │   ├── provider.py
│   │   └── transaction.py
│   ├── schemas/
│   │   ├── payment.py
│   │   └── provider.py
│   ├── providers/
│   │   ├── base.py                    # Abstract Provider
│   │   ├── stripe_provider.py
│   │   ├── mercadopago_provider.py
│   │   └── mock_provider.py           # Para testing
│   ├── routers/
│   │   ├── payments.py
│   │   ├── webhooks.py
│   │   └── providers.py
│   └── services/
│       ├── payment_service.py
│       └── webhook_service.py
├── alembic/
│   └── versions/
└── requirements.txt
```

### Variables de Entorno
```env
# Database
DATABASE_URL=postgresql://Reservas_ULEAM:123456@localhost:5432/reservasuleam

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# MercadoPago
MERCADOPAGO_ACCESS_TOKEN=APP_USR_...
MERCADOPAGO_PUBLIC_KEY=APP_USR_...

# MockAdapter
MOCK_PAYMENT_ENABLED=true

# Webhooks
WEBHOOK_SECRET_STRIPE=whsec_...
WEBHOOK_SECRET_MERCADOPAGO=...

# JWT
JWT_SECRET=mi-secreto-auth-service-super-seguro-2025

# Notification
WEBSOCKET_SERVICE_URL=http://localhost:3001
NOTIFICATION_EMAIL=noreply@uleam.edu.ec

# Server
PORT=8001
HOST=0.0.0.0
ENVIRONMENT=development
```

### Instalación
```bash
cd payment-service
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8001
```

### Endpoints Principales

#### 1. Crear Pago
```http
POST /api/payments
Authorization: Bearer {token}
Content-Type: application/json

{
  "reservaId": "uuid",
  "monto": 150.00,
  "moneda": "USD",
  "proveedor": "stripe",
  "metadata": {
    "espacio": "Aula 101",
    "fecha": "2026-02-10"
  }
}

Response 201:
{
  "id": "payment_uuid",
  "reservaId": "uuid",
  "estado": "pendiente",
  "monto": 150.00,
  "proveedor": "stripe",
  "url_pago": "https://checkout.stripe.com/pay/...",
  "referencia_externa": "py_123abc",
  "createdAt": "2026-01-27T14:55:00Z"
}
```

---

#### 2. Confirmar Pago
```http
POST /api/payments/{paymentId}/confirm
Authorization: Bearer {token}
Content-Type: application/json

{
  "token_pago": "tok_1234567",
  "tres_d_secure": false
}

Response 200:
{
  "id": "payment_uuid",
  "estado": "confirmado",
  "referencia_externa": "py_123abc",
  "timestamp_confirmacion": "2026-01-27T15:00:00Z"
}
```

---

#### 3. Obtener Pago
```http
GET /api/payments/{paymentId}
Authorization: Bearer {token}

Response 200:
{
  "id": "payment_uuid",
  "reservaId": "uuid",
  "estado": "confirmado",
  "monto": 150.00,
  "moneda": "USD",
  "proveedor": "stripe",
  "referencia_externa": "py_123abc",
  "historial": [
    {
      "estado": "pendiente",
      "timestamp": "2026-01-27T14:55:00Z"
    },
    {
      "estado": "confirmado",
      "timestamp": "2026-01-27T15:00:00Z"
    }
  ],
  "createdAt": "2026-01-27T14:55:00Z"
}
```

---

#### 4. Webhook de Stripe
```http
POST /api/webhooks/stripe
X-Stripe-Signature: t=...,v1=...
Content-Type: application/json

{
  "type": "payment_intent.succeeded",
  "data": {
    "object": {
      "id": "py_123abc",
      "amount": 15000,
      "status": "succeeded",
      "metadata": {
        "reserva_id": "uuid"
      }
    }
  }
}
```

**Procesamiento:**
```
1. Verificar firma Stripe
2. Actualizar pago a "confirmado"
3. Webhook → REST: /api/reservas/{id}/confirm
4. Webhook → WebSocket: payment confirmado
5. Email: confirmación al usuario
6. Webhook → n8n: para orquestación
```

---

## 📊 Modelos de Datos - Payment

### Payment Entity
```sql
CREATE TABLE payments (
  id UUID PRIMARY KEY,
  reservaId UUID REFERENCES reservas(id),
  usuarioId UUID REFERENCES usuarios(id),
  monto DECIMAL(10, 2) NOT NULL,
  moneda VARCHAR(3) DEFAULT 'USD',
  proveedor VARCHAR(50) NOT NULL,  -- stripe, mercadopago, mock
  referencia_externa VARCHAR(255),
  estado VARCHAR(50) DEFAULT 'pendiente',  -- pendiente, confirmado, fallido, reembolsado
  metadata JSONB,
  createdAt TIMESTAMP DEFAULT NOW(),
  updatedAt TIMESTAMP DEFAULT NOW()
);

CREATE TABLE payment_transactions (
  id UUID PRIMARY KEY,
  paymentId UUID REFERENCES payments(id),
  tipo VARCHAR(50),  -- captura, reembolso, reversa
  monto DECIMAL(10, 2),
  estado VARCHAR(50),
  respuesta_proveedor JSONB,
  createdAt TIMESTAMP DEFAULT NOW()
);
```

---

## 🔄 Flujos de Integración

### Flujo 1: Pago Completo
```
1. Usuario hace clic en "Confirmar pago"
2. Frontend: POST /api/payments
   └─ Recibe URL de Stripe/MercadoPago
3. Usuario completa pago en pasarela
4. Pasarela webhook → Payment Service
5. Payment Service:
   ├─ Valida firma del webhook
   ├─ Actualiza estado a "confirmado"
   ├─ Webhook → REST: POST /api/reservas/{id}/confirm
   ├─ Webhook → WebSocket: "pago_confirmado"
   ├─ Email: confirmación
   ├─ Webhook → n8n: para tareas adicionales
   └─ GraphQL: stats actualizado
6. Frontend: Recibe notificación y actualiza UI
```

---

### Flujo 2: Reembolso
```
1. Admin o usuario: PATCH /api/payments/{id}/refund
2. Payment Service:
   ├─ Valida estado = "confirmado"
   ├─ Llama API proveedor: refund()
   ├─ Actualiza estado a "reembolsado"
   ├─ Crea transacción de reversa
   ├─ Email: confirmación reembolso
   └─ WebSocket: notifica usuario
```

---

## 🔗 Integración con Otros Pilares

### Integración con Pilar 1 (Auth)
```
✓ Payment Service requiere JWT válido
✓ Extrae user_id del token
✓ Usa mismo JWT_SECRET
✓ Valida usuario activo
```

---

### Integración con Pilar 2 (REST)
```
✓ REST: POST /api/reservas/{id}/confirm (llamado por payment)
✓ REST: GET /api/disponibilidad (para validar)
✓ Payment guarda referencia a reserva
✓ Payment notifica REST cuando se confirma
```

---

### Integración con Pilar 3 (AI)
```
✓ AI puede sugerir "¿Quieres proceder con el pago?"
✓ AI puede listar métodos de pago disponibles
✓ AI responde después de que pago se confirma
```

---

### Integración con Pilar 4 (n8n)
```
✓ n8n recibe webhook de pasarela
✓ n8n procesa: validate → activate → notify
✓ Payment Service emite webhooks que n8n consume
✓ n8n orquesta: Payment → REST → WebSocket → Email
```

---

## 🛠️ Instalación General

### Todos los Servicios del Pilar 4

#### WebSocket Service
```bash
cd c:\Users\ASUS\OneDrive\Desktop\ReservasUleam2026\ReservasUleam2025\UleamBack\websocket-service
npm install
npm run start:dev
```

#### Payment Service
```bash
cd c:\Users\ASUS\OneDrive\Desktop\ReservasUleam2026\ReservasUleam2025\UleamBack\payment-service
pip install -r requirements.txt
python main.py
```

#### Verificación
```powershell
# WebSocket
curl http://localhost:3001

# Payment
curl http://localhost:8001/docs

# GraphQL (Pilar 2 - incluido aquí)
curl -X POST http://localhost:8080/graphql
```

---

## 🧪 Testing

### Test Payment Flow
```bash
# 1. Crear pago (MockAdapter)
curl -X POST http://localhost:8001/api/payments \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "reservaId": "uuid",
    "monto": 100.00,
    "proveedor": "mock"
  }'

# 2. Simular webhook
curl -X POST http://localhost:8001/api/webhooks/mock \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": "payment_uuid",
    "status": "success"
  }'
```

---

## ✅ Checklist de Implementación

- [x] WebSocket Service (NestJS)
- [x] Payment Service (FastAPI)
- [x] GraphQL Service (Go)
- [x] Webhook listeners
- [x] Socket.IO rooms por usuario
- [x] Stripe integration
- [x] MercadoPago integration
- [x] MockAdapter para testing
- [ ] Tests completos
- [ ] Fraud detection avanzada
- [ ] Reembolsos automáticos
- [ ] Analytics en tiempo real

---

**Última Actualización:** 27 de Enero de 2026  
**Contacto:** Team ULEAM Reservas
