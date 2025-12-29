# Auth Service - Sistema de Reservas ULEAM

Servicio de autenticación centralizado para el sistema de reservas ULEAM. Construido con NestJS, TypeORM, PostgreSQL y Redis.

## 🚀 Características

### Core
- ✅ Registro y login de usuarios
- ✅ Autenticación JWT (Access + Refresh tokens)
- ✅ Refresh token rotation con revocación automática
- ✅ Logout con blacklist centralizada
- ✅ Endpoints protegidos con JWT Guards
- ✅ Validación de estado de usuario (activo/bloqueado/inactivo)

### Integración P1
- ✅ Endpoint de validación de tokens para servicios P1 (REST, GraphQL, WebSocket)
- ✅ Endpoint de configuración pública JWT
- ✅ Verificación de blacklist en validación remota
- ✅ Documentación completa de integración
- ✅ Scripts de testing automatizados

### Seguridad
- ✅ Blacklist de tokens en Redis con TTL automático
- ✅ Rate limiting (20 req/min global, 5 req/min login)
- ✅ Protección contra ataques de fuerza bruta
- ✅ Bcrypt con 12 rounds para hashing
- ✅ JWT con firma HMAC-SHA256

### DevEx
- ✅ Validación de esquemas con class-validator
- ✅ Documentación Swagger completa
- ✅ TypeScript + arquitectura limpia
- ✅ Hot reload en desarrollo
- ✅ Scripts de testing

## 📋 Requisitos

- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- npm o yarn

## 🛠️ Instalación

```bash
# Instalar dependencias
npm install

# Copiar variables de entorno
cp .env.example .env

# Editar .env y configurar:
# - DB_HOST, DB_PORT, DB_USERNAME, DB_PASSWORD, DB_DATABASE
# - REDIS_HOST, REDIS_PORT
# - JWT_SECRET (debe ser el mismo en todos los servicios)

# Iniciar Redis con Docker
docker-compose up -d

# Ejecutar en desarrollo
npm run start:dev
```

## 🌐 Endpoints

### Autenticación Principal

- `POST /api/v1/auth/register` - Registrar usuario
- `POST /api/v1/auth/login` - Iniciar sesión (rate limited: 5 req/min)
- `POST /api/v1/auth/refresh` - Refrescar access token con rotation
- `POST /api/v1/auth/logout` - Cerrar sesión y revocar tokens
- `GET /api/v1/auth/me` - Obtener perfil del usuario autenticado (protegido)

### Integración P1 (Para servicios REST/GraphQL/WebSocket)

- `POST /api/v1/auth/validate` - Validar token JWT remotamente
- `GET /api/v1/auth/public-key` - Obtener configuración pública JWT

### Usuarios

- `GET /api/v1/users/me` - Obtener perfil completo (protegido)

### Documentación

- Swagger: http://localhost:9000/api/v1/docs

## 🏗️ Estructura del Proyecto

```
src/
├── auth/               # Módulo de autenticación
│   ├── dto/           # DTOs de validación
│   ├── entities/      # Entidades de TypeORM
│   ├── guards/        # Guards de autorización
│   ├── strategies/    # Estrategias de Passport
│   ├── auth.controller.ts
│   ├── auth.service.ts
│   └── auth.module.ts
├── users/             # Módulo de usuarios
│   ├── entities/
│   ├── users.controller.ts
│   ├── users.service.ts
│   └── users.module.ts
├── database/          # Configuración de TypeORM
├── redis/             # Servicio de Redis
├── common/            # Utilidades compartidas
├── app.module.ts      # Módulo principal
└── main.ts            # Punto de entrada
```

## 🔐 Seguridad

- Passwords hasheados con bcrypt (12 rounds)
- JWT con expiración: 15min (access), 7 días (refresh)
- Tokens revocados en Redis blacklist
- Rate limiting: 10 req/min
- Bloqueo de cuenta tras 5 intentos fallidos (15 min)
- Helmet para headers HTTP seguros
- CORS configurado

## 🧪 Testing

```bash
# Unit tests
npm run test

# E2E tests
npm run test:e2e

# Coverage
npm run test:cov
```

## 📊 Variables de Entorno

Ver `.env.example` para la lista completa de variables configurables.

## 🔄 Migraciones

```bash
# Generar migración
npm run migration:generate -- src/database/migrations/NombreMigracion

# Ejecutar migraciones
npm run migration:run

# Revertir migración
npm run migration:revert
```

## 📝 Commit 1: Scaffold Completo

✅ Estructura base del proyecto NestJS
✅ Configuración TypeORM + PostgreSQL
✅ Configuración Redis + Docker Compose
✅ Entidades: User, RefreshToken
✅ Módulos: Auth, Users, Database, Redis
✅ Servicios base implementados
✅ Validación de variables de entorno
✅ Swagger configurado
✅ Rate limiting habilitado

## 🚧 Próximos Pasos

- [ ] Commit 2: Implementar registro y login
- [ ] Commit 3: Sistema de refresh tokens y revocación
- [ ] Commit 4: Integración con servicios P1

## 👥 Autor

ULEAM Team - Sistema de Reservas 2025
