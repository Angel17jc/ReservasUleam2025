# 🔐 PILAR 1: Servicio de Autenticación Centralizado

**Versión:** 1.0  
**Fecha:** 27 de Enero de 2026  
**Estado:** ✅ Producción  
**Líder Técnico:** Equipo Auth Service

---

## 📋 Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Arquitectura y Componentes](#arquitectura-y-componentes)
3. [Stack Tecnológico](#stack-tecnológico)
4. [Características Principales](#características-principales)
5. [Instalación y Configuración](#instalación-y-configuración)
6. [Endpoints de API](#endpoints-de-api)
7. [Flujos de Autenticación](#flujos-de-autenticación)
8. [Seguridad](#seguridad)
9. [Integración con Otros Pilares](#integración-con-otros-pilares)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Visión General

El **Pilar 1** es el corazón del sistema de seguridad de ULEAM Reservas. Proporciona autenticación centralizada para todos los microservicios mediante JWT tokens, gestión de usuarios, y control de acceso basado en roles (RBAC).

### Responsabilidades Principales
- ✅ Registro e identificación de usuarios
- ✅ Generación y validación de JWT tokens
- ✅ Gestión de refresh tokens con rotación automática
- ✅ Blacklist centralizada de tokens revocados
- ✅ Validación remota de tokens para otros servicios
- ✅ Rate limiting y protección contra fuerza bruta
- ✅ Persistencia de usuarios y sesiones

---

## 🏗️ Arquitectura y Componentes

### Diagrama de Flujo de Autenticación

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO DE AUTENTICACIÓN PILAR 1                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Cliente                                                      │
│     ├─→ POST /api/v1/auth/register (email, password)           │
│     ├─→ POST /api/v1/auth/login (email, password)              │
│     └─→ Recibe: { accessToken, refreshToken, expiresIn }       │
│                                                                  │
│  2. Auth Service (NestJS)                                       │
│     ├─→ Validar credenciales (Bcrypt)                          │
│     ├─→ Verificar estado usuario (activo/bloqueado)            │
│     ├─→ Generar JWT (HS256)                                     │
│     ├─→ Guardar refresh token en BD                            │
│     ├─→ Registrar en Redis para caché                          │
│     └─→ Responder con tokens                                    │
│                                                                  │
│  3. Cliente Almacena                                             │
│     ├─→ accessToken (localStorage/sessionStorage)              │
│     └─→ refreshToken (cookie httpOnly o localStorage)          │
│                                                                  │
│  4. Solicitud a Otros Servicios                                │
│     ├─→ Header: Authorization: Bearer {accessToken}            │
│     └─→ Otros servicios validan localmente o en Auth Service   │
│                                                                  │
│  5. Refresh Token                                               │
│     ├─→ POST /api/v1/auth/refresh                              │
│     ├─→ Validar refresh token en BD                            │
│     ├─→ Generar nuevo accessToken                              │
│     ├─→ Opcional: rotar refreshToken (nuevo refresh)           │
│     └─→ Responder con nuevo accessToken                        │
│                                                                  │
│  6. Logout/Revocación                                           │
│     ├─→ POST /api/v1/auth/logout                               │
│     ├─→ Añadir token a blacklist en Redis                      │
│     └─→ Eliminar refresh token de BD                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Componentes Clave

| Componente | Descripción | Ubicación |
|-----------|-----------|-----------|
| **Auth Module** | Módulo central de autenticación | `src/auth/` |
| **User Module** | Gestión de usuarios | `src/users/` |
| **JWT Strategy** | Estrategia Passport para JWT | `src/auth/strategies/` |
| **Auth Guards** | Protección de rutas | `src/auth/guards/` |
| **Auth Service** | Lógica de negocio | `src/auth/auth.service.ts` |
| **Auth Controller** | Endpoints REST | `src/auth/auth.controller.ts` |
| **Entities** | Modelos TypeORM | `src/auth/entities/` |
| **PostgreSQL** | Base de datos principal | Tables: user, refresh_token, blacklisted_token |
| **Redis** | Caché y blacklist | Almacenamiento de tokens revocados |

---

## 💻 Stack Tecnológico

### Backend Framework
- **NestJS** v10+ - Framework modular para Node.js
- **TypeScript** - Tipado estático
- **TypeORM** - ORM para PostgreSQL
- **Passport.js** - Autenticación modular

### Base de Datos
- **PostgreSQL** 14+ - Almacenamiento persistente
- **Redis** 7+ - Caché y blacklist

### Seguridad
- **bcryptjs** - Hash de contraseñas (12 rounds)
- **jsonwebtoken (JWT)** - Tokens firmados con HMAC-SHA256
- **class-validator** - Validación de esquemas
- **helmet.js** - Headers de seguridad HTTP

### DevTools
- **Swagger/OpenAPI** - Documentación interactiva
- **Hot Reload** - Desarrollo iterativo
- **Jest** - Testing unitario

### Puertos
- **Auth Service:** Puerto 9000
- **PostgreSQL:** Puerto 5432
- **Redis:** Puerto 6379

---

## ✨ Características Principales

### 1. Autenticación JWT Dual
```
Tokens Generados:
├─ Access Token
│   ├─ Duración: 15 minutos
│   ├─ Payload: { sub, email, role, iat, exp }
│   ├─ Algoritmo: HS256 (HMAC-SHA256)
│   └─ Almacenamiento: Cliente (localStorage)
│
└─ Refresh Token
    ├─ Duración: 7 días
    ├─ Almacenamiento: BD PostgreSQL + cliente
    ├─ Rotación: Automática en cada refresh
    └─ Revocación: Anterior token invalidado
```

### 2. Validación Local sin Roundtrips
- Otros servicios **validan JWT localmente** sin llamar a Auth Service
- Verifican firma usando JWT_SECRET compartido
- Reducen latencia y aumentan escalabilidad

### 3. Blacklist Centralizada (Redis)
- Tokens revocados se almacenan en Redis
- TTL automático basado en exp del JWT
- Sincronización con BD para persistencia

### 4. Rate Limiting Inteligente
```
Límites:
├─ Login: 5 intentos / minuto por IP
├─ Register: 3 intentos / minuto por email
├─ Refresh: 10 intentos / minuto por usuario
└─ General: 20 intentos / minuto por IP
```

### 5. Gestión de Usuarios Completa
- Estados: Activo, Bloqueado, Inactivo, Pendiente Validación
- Roles: Admin, Docente, Estudiante, Invitado
- Perfiles: Avatar, Teléfono, Dirección, Departamento
- Auditoría: Fecha creación, última actualización, IP última sesión

### 6. Validación de Estado
```javascript
// Validaciones antes de login exitoso:
├─ Usuario existe
├─ Contraseña correcta (Bcrypt)
├─ Usuario activo (no bloqueado ni inactivo)
├─ Email verificado (si aplica)
└─ Datos mínimos requeridos completos
```

---

## 🛠️ Instalación y Configuración

### Requisitos Previos
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- npm o yarn
- Git

### Paso 1: Clonar y Navegar
```bash
cd c:\Users\ASUS\OneDrive\Desktop\ReservasUleam2026\ReservasUleam2025\UleamBack\auth-service
```

### Paso 2: Instalar Dependencias
```bash
npm install
```

### Paso 3: Configurar Variables de Entorno
```bash
# Copiar plantilla
cp .env.example .env

# Editar .env con:
```

**Contenido de `.env`:**
```env
# Database PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=Reservas_ULEAM
DB_PASSWORD=123456
DB_DATABASE=reservasuleam_auth

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# JWT
JWT_SECRET=<JWT_SECRET-definido-en-.env>
JWT_EXPIRES_IN=15m
REFRESH_TOKEN_EXPIRES_IN=7d
REFRESH_TOKEN_SECRET=mi-secreto-refresh-token-2025

# Server
PORT=9000
HOST=0.0.0.0
NODE_ENV=development

# Email (opcional)
MAIL_HOST=smtp.gmail.com
MAIL_PORT=587
MAIL_USER=noreply@uleam.edu.ec
MAIL_PASSWORD=app_password_aqui

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Logging
LOG_LEVEL=debug
```

### Paso 4: Iniciar Redis y PostgreSQL
```powershell
# PowerShell - Iniciar Docker compose
cd c:\Users\ASUS\OneDrive\Desktop\ReservasUleam2026\ReservasUleam2025\UleamBack\auth-service
docker-compose up -d
```

### Paso 5: Ejecutar Migraciones de BD
```bash
# TypeORM auto-sincroniza si synchronize=true en ormconfig
npm run typeorm migration:run
# O confía en auto-sync (desarrollo)
```

### Paso 6: Iniciar Servicio
```bash
# Modo desarrollo (hot reload)
npm run start:dev

# Modo producción
npm run build
npm run start:prod
```

### Verificación
```powershell
# Verificar que está corriendo
curl http://localhost:9000/api/v1/docs

# Debe abrir Swagger en navegador
```

---

## 📡 Endpoints de API

### Autenticación Pública

#### 1. Registro de Usuario
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "usuario@uleam.edu.ec",
  "password": "MiContraseña123!",
  "firstName": "Juan",
  "lastName": "Pérez",
  "tipoUsuarioId": 3
}
```

**Response 201 Created:**
```json
{
  "id": "uuid",
  "email": "usuario@uleam.edu.ec",
  "firstName": "Juan",
  "lastName": "Pérez",
  "estado": "activo",
  "createdAt": "2026-01-27T14:30:00Z"
}
```

---

#### 2. Login
```http
POST /api/v1/auth/login
Content-Type: application/json
X-Forwarded-For: 192.168.1.100

{
  "email": "usuario@uleam.edu.ec",
  "password": "MiContraseña123!"
}
```

**Response 200 OK:**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": 900,
  "tokenType": "Bearer",
  "user": {
    "id": "uuid",
    "email": "usuario@uleam.edu.ec",
    "firstName": "Juan",
    "tipoUsuario": { "id": 3, "nombre": "Estudiante" }
  }
}
```

**Response 401 Unauthorized (limpiado por rate limiting):**
```json
{
  "statusCode": 401,
  "message": "Credenciales inválidas",
  "error": "Unauthorized"
}
```

---

#### 3. Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response 200 OK:**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": 900
}
```

---

#### 4. Obtener Perfil del Usuario (Protegido)
```http
GET /api/v1/auth/me
Authorization: Bearer {accessToken}
```

**Response 200 OK:**
```json
{
  "id": "uuid",
  "email": "usuario@uleam.edu.ec",
  "firstName": "Juan",
  "lastName": "Pérez",
  "tipoUsuario": {
    "id": 3,
    "nombre": "Estudiante",
    "permisos": ["read:reservas", "create:reservas"]
  },
  "estado": "activo",
  "avatar": "https://api.example.com/avatars/uuid.jpg",
  "lastLogin": "2026-01-27T10:00:00Z",
  "createdAt": "2026-01-15T08:30:00Z"
}
```

---

#### 5. Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer {accessToken}
Content-Type: application/json

{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response 200 OK:**
```json
{
  "message": "Sesión cerrada exitosamente"
}
```

---

### Integración P1 (Para Otros Servicios)

#### 6. Validar Token Remotamente
```http
POST /api/v1/auth/validate
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response 200 OK:**
```json
{
  "valid": true,
  "payload": {
    "sub": "uuid",
    "email": "usuario@uleam.edu.ec",
    "tipoUsuario": "Estudiante",
    "iat": 1706364600,
    "exp": 1706365500
  }
}
```

**Response 401 Unauthorized:**
```json
{
  "valid": false,
  "message": "Token inválido o expirado"
}
```

---

#### 7. Obtener Configuración Pública JWT
```http
GET /api/v1/auth/public-key
```

**Response 200 OK:**
```json
{
  "algorithm": "HS256",
  "secret": "configuración-pública-para-validación-local",
  "expiresIn": "15m",
  "publicKey": "-----BEGIN PUBLIC KEY-----\n..."
}
```

---

### Usuarios (Protegido - Admin)

#### 8. Listar Usuarios
```http
GET /api/v1/users?page=1&limit=20&estado=activo
Authorization: Bearer {adminToken}
```

**Response 200 OK:**
```json
{
  "data": [
    {
      "id": "uuid",
      "email": "usuario@uleam.edu.ec",
      "firstName": "Juan",
      "tipoUsuario": "Estudiante",
      "estado": "activo",
      "lastLogin": "2026-01-27T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150
  }
}
```

---

#### 9. Cambiar Estado de Usuario
```http
PATCH /api/v1/users/{userId}/estado
Authorization: Bearer {adminToken}
Content-Type: application/json

{
  "estado": "bloqueado",
  "razon": "Incumplimiento de normas"
}
```

**Response 200 OK:**
```json
{
  "id": "uuid",
  "email": "usuario@uleam.edu.ec",
  "estado": "bloqueado",
  "modificadoPor": "admin_uuid",
  "fechaModificacion": "2026-01-27T14:35:00Z"
}
```

---

## 🔄 Flujos de Autenticación

### Flujo 1: Primer Acceso (Registro + Login)
```
Usuario
   │
   ├─→ [1] POST /register (email, password, datos)
   │        ↓
   │      Auth Service valida y crea usuario
   │        ↓
   │   [2] Usuario recibe confirmación
   │
   ├─→ [3] POST /login (email, password)
   │        ↓
   │      Auth Service genera JWT + RefreshToken
   │        ↓
   │   [4] Usuario almacena tokens
   │
   └─→ [5] Headers: Authorization: Bearer {accessToken}
          ↓
       Otros servicios validan localmente
```

### Flujo 2: Mantenimiento de Sesión
```
Cliente
   │
   ├─→ Usar accessToken en Headers
   │        ↓
   │   ¿Token válido y no expirado?
   │        ├─→ Sí: Acceso concedido ✓
   │        └─→ No: Token expirado
   │
   └─→ [1] POST /refresh (refreshToken)
          │
          ├─ Validar refreshToken en BD
          ├─ Generar nuevo accessToken
          ├─ Rotar refreshToken (nuevo)
          └─ Responder con nuevos tokens
```

### Flujo 3: Revocación de Sesión
```
Cliente decide logout
   │
   └─→ [1] POST /logout (accessToken + refreshToken)
          │
          ├─ Validar tokens
          ├─ Agregar a blacklist (Redis)
          ├─ Eliminar de BD
          ├─ Invalidar en caché
          └─ Responder 200 OK
```

### Flujo 4: Sincronización Entre Servicios
```
REST Service recibe solicitud
   │
   ├─→ Extrae JWT del header
   │
   ├─→ Valida localmente:
   │    ├─ Verificar firma (HS256)
   │    ├─ Verificar exp (no expirado)
   │    └─ Extraer payload
   │
   ├─→ Opcional: Verificar en blacklist
   │    │
   │    ├─ Llamar a POST /auth/validate
   │    │ (si es crítico o requiere seguridad extra)
   │    │
   │    └─ Redis consulta local (más rápido)
   │
   └─→ Procesar solicitud o rechazar
```

---

## 🔒 Seguridad

### 1. Hashing de Contraseñas
```typescript
// Bcrypt con 12 rounds
const hashedPassword = await bcrypt.hash(password, 12);
// Verificación: bcrypt.compare(plainPassword, hashedPassword)
```

**Ventajas:**
- Irreversible
- Resistente a fuerza bruta (lento por diseño)
- Salt único por contraseña

---

### 2. JWT Firmado
```
Estructura JWT:
HEADER.PAYLOAD.SIGNATURE

Header: { alg: "HS256", typ: "JWT" }
Payload: { sub: uuid, email, tipoUsuario, iat, exp }
Signature: HMAC-SHA256(Header + "." + Payload, JWT_SECRET)

Validación:
├─ Verificar firma con JWT_SECRET compartido
├─ Verificar exp no superado
├─ Verificar no en blacklist
└─ Extraer payload seguro
```

---

### 3. Rate Limiting
```javascript
// Protección contra fuerza bruta
LoginRateLimit: 5 intentos / minuto por IP
RegisterRateLimit: 3 intentos / minuto por email
RefreshRateLimit: 10 intentos / minuto por usuario

Implementación: express-rate-limit + Redis
```

---

### 4. Blacklist y Revocación
```
Token revocado:
├─ Se añade a Redis
├─ TTL = exp_timestamp - now
├─ Sincronización con BD para reinicios
└─ Consulta en cada validación

Beneficio: Logout inmediato, sin esperar a exp
```

---

### 5. Headers de Seguridad
```javascript
// Implementados por helmet.js
├─ X-Content-Type-Options: nosniff
├─ X-Frame-Options: DENY
├─ X-XSS-Protection: 1; mode=block
├─ Content-Security-Policy: ...
├─ Strict-Transport-Security: max-age=31536000
└─ CORS: Orígenes permitidos configurados
```

---

### 6. HTTPS en Producción
```env
NODE_ENV=production
PROTOCOL=https
JWT_SECRET=generado-fuerte (min 32 caracteres)
REFRESH_TOKEN_SECRET=generado-fuerte (min 32 caracteres)
```

---

### 7. Validación de Input
```typescript
// class-validator en DTOs
email: string ✓ email format
password: string ✓ minLength(8), maxLength(128)
firstName: string ✓ minLength(2), maxLength(50)

Beneficio: Rechaza datos malformados antes de procesar
```

---

## 🔗 Integración con Otros Pilares

### Integración con Pilar 2 (REST Service)
```
REST Service:
├─→ Lee JWT_SECRET desde config (compartido)
├─→ Valida JWT localmente en cada request
├─→ Extrae { sub, email, tipoUsuario } del payload
├─→ Usa sub (user_id) para queries a BD
└─→ Opcional: Llamada a /auth/validate si es crítico
```

**Flujo:**
```
Cliente → Authorization: Bearer {token}
             ↓
          REST Service
             ├─ Verifica firma
             ├─ Verifica exp
             ├─ Consulta BD con user_id (sub)
             └─ Procesa solicitud
```

---

### Integración con Pilar 3 (AI Service)
```
AI Service:
├─→ Recibe JWT en header Authorization
├─→ Valida JWT (mismo secret compartido)
├─→ Usa user_id para contextualización de IA
├─→ Ejemplo: "Usuario Estudiante con ID X solicita análisis de espacio Y"
└─→ Responde respetando permisos del usuario
```

---

### Integración con Pilar 4 (n8n)
```
n8n Workflows:
├─→ Obtiene JWT valido desde cliente
├─→ Incluye en headers: Authorization: Bearer {token}
├─→ Llama REST / GraphQL / WebSocket
│   ├─ POST /api/reservas/{id}/confirm
│   ├─ GET /api/partners/{id}
│   └─ POST /api/webhooks/...
└─→ Validación de token ocurre en destino
```

---

### Compartición de JWT_SECRET
```env
# Todos los servicios deben tener el MISMO:
JWT_SECRET=<JWT_SECRET-definido-en-.env>

# Ubicaciones:
├─ auth-service/.env
├─ rest-service/.env
├─ graphql-service/.env (go: JWT_SECRET env var)
├─ websocket-service/.env
├─ ai-service/.env
└─ n8n environment variables
```

---

## 🐛 Troubleshooting

### Problema 1: "Token inválido"
**Causa:** JWT_SECRET diferente entre servicios  
**Solución:**
```bash
# Verificar mismo secret en todos los servicios
echo $JWT_SECRET  # en cada .env
# Deben ser idénticos
```

---

### Problema 2: "Rate limit exceeded"
**Causa:** Demasiados intentos de login  
**Solución:**
```powershell
# Esperar 60 segundos o usar otra IP
# O resetear Redis:
redis-cli FLUSHALL
```

---

### Problema 3: "Token expirado"
**Solución:**
```bash
# Usar refresh token
POST /api/v1/auth/refresh
Body: { "refreshToken": "..." }

# Obtener nuevo accessToken
```

---

### Problema 4: "Usuario bloqueado"
**Causa:** Admin bloqueó usuario  
**Solución:**
```powershell
# Admin desbloquea:
PATCH /api/v1/users/{userId}/estado
Body: { "estado": "activo" }
```

---

### Problema 5: PostgreSQL no accesible
**Solución:**
```powershell
# Iniciar Docker
docker-compose up -d

# Verificar conexión
psql -U Reservas_ULEAM -d reservasuleam_auth -c "SELECT 1;"
```

---

### Problema 6: Redis no accesible
**Solución:**
```powershell
# Iniciar Redis
redis-server

# Verificar
redis-cli ping
# Debe responder: PONG
```

---

## 📊 Monitoreo y Auditoría

### Logs Importantes
```
[AuthService] Login exitoso: usuario@uleam.edu.ec
[AuthService] Login fallido: 3 intentos desde 192.168.1.100
[AuthService] Token revocado: usuario_uuid
[AuthService] Refresh exitoso: usuario_uuid
[AuthService] Usuario bloqueado: usuario_uuid (razón: X)
```

### Métricas a Monitorear
```
├─ Tiempo respuesta /login (< 500ms)
├─ Tasa error autenticación
├─ Tokens generados/min
├─ Refresh tokens rotados/min
├─ Blacklist size (Redis)
└─ Conexiones BD activas
```

---

## ✅ Checklist de Implementación

- [x] NestJS configurado
- [x] PostgreSQL con tablas de usuarios
- [x] Redis para caché/blacklist
- [x] JWT generación y validación
- [x] Refresh token rotation
- [x] Rate limiting implementado
- [x] Endpoints de API documentados
- [x] Swagger integrado
- [x] Seguridad (Bcrypt, HTTPS, CORS)
- [x] Integración con otros servicios
- [x] Tests unitarios (Jest)
- [x] Scripts PowerShell para setup

---

## 📚 Referencias

- [NestJS Docs](https://docs.nestjs.com)
- [JWT.io](https://jwt.io)
- [Passport.js](http://www.passportjs.org/)
- [Bcrypt](https://www.npmjs.com/package/bcryptjs)
- [TypeORM](https://typeorm.io)
- [Redis](https://redis.io)

---

**Última Actualización:** 27 de Enero de 2026  
**Contacto:** Team ULEAM Reservas
