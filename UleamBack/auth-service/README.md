# Auth Service - Sistema de Reservas ULEAM

Servicio de autenticación centralizado para el sistema de reservas ULEAM. Construido con NestJS, TypeORM, PostgreSQL y Redis.

## 🚀 Características

- ✅ Registro y login de usuarios
- ✅ Autenticación JWT (Access + Refresh tokens)
- ✅ Blacklist de tokens en Redis
- ✅ Rate limiting
- ✅ Protección contra ataques de fuerza bruta
- ✅ Validación de esquemas con class-validator
- ✅ Documentación Swagger
- ✅ TypeScript + arquitectura limpia

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

# Iniciar Redis con Docker
docker-compose up -d

# Ejecutar en desarrollo
npm run start:dev
```

## 🌐 Endpoints

### Autenticación

- `POST /api/v1/auth/register` - Registrar usuario
- `POST /api/v1/auth/login` - Iniciar sesión
- `POST /api/v1/auth/refresh` - Refrescar access token
- `POST /api/v1/auth/logout` - Cerrar sesión
- `GET /api/v1/auth/me` - Obtener perfil

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
