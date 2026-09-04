# Guía de Integración Auth Service con Servicios P1

Esta guía explica cómo integrar el Auth Service (Pilar 2) con los servicios existentes del Pilar 1 (REST, GraphQL y WebSocket).

## Tabla de Contenidos

1. [Arquitectura de Integración](#arquitectura-de-integración)
2. [Configuración de JWT Compartido](#configuración-de-jwt-compartido)
3. [Endpoints de Validación](#endpoints-de-validación)
4. [Integración por Servicio](#integración-por-servicio)
   - [REST Service (FastAPI)](#rest-service-fastapi)
   - [GraphQL Service (Go)](#graphql-service-go)
   - [WebSocket Service (NestJS)](#websocket-service-nestjs)
5. [Flujo de Autenticación](#flujo-de-autenticación)
6. [Manejo de Errores](#manejo-de-errores)
7. [Testing](#testing)

---

## Arquitectura de Integración

### Modelo de Validación LOCAL (Pilar 1)

```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │ 1. Login/Register
       ▼
┌──────────────────┐
│  Auth Service    │ ◄─── Gestión de usuarios, JWT, blacklist
│  (Puerto 9000)   │      (Solo para autenticación)
└──────────────────┘
       │ 2. Retorna JWT firmado
       ▼
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │ 3. Request con JWT
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌────────────┐    ┌─────────────┐
│ REST (8000)│    │GraphQL(8080)│
│            │    │             │
│ VALIDA JWT │    │ VALIDA JWT  │
│ LOCALMENTE │    │ LOCALMENTE  │
│ con        │    │ con         │
│ JWT_SECRET │    │ JWT_SECRET  │
└────────────┘    └─────────────┘

❌ NO llaman a Auth Service en cada request
✅ Validan firma y expiración localmente
✅ Evita el antipatrón de validación remota constante
```

### Principios de Diseño (Pilar 1)

1. **Single Source of Truth**: Auth Service es la única fuente de verdad para autenticación
2. **Stateless JWT**: Tokens autocontenidos con información del usuario
3. **Validación LOCAL**: Servicios P1 validan JWT localmente usando JWT_SECRET compartido
4. **Blacklist Distribuida**: Cache local o estrategias asíncronas para tokens revocados
5. **Zero Network Calls**: Sin latencia adicional por llamadas HTTP en cada request

---

## Configuración de JWT Compartido

### 1. Secreto Compartido (JWT_SECRET)

**CRÍTICO**: Todos los servicios deben usar el mismo `JWT_SECRET` para poder validar tokens.

#### Auth Service (.env)
```bash
JWT_SECRET=<JWT_SECRET-definido-en-.env>
JWT_ACCESS_EXPIRATION=15m
JWT_REFRESH_EXPIRATION=7d
```

#### REST Service (.env)
```bash
# DEBE ser el mismo que Auth Service
SECRET_KEY=<JWT_SECRET-definido-en-.env>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### GraphQL Service (.env)
```bash
# DEBE ser el mismo que Auth Service
JWT_SECRET=<JWT_SECRET-definido-en-.env>
```

#### WebSocket Service (.env)
```bash
# DEBE ser el mismo que Auth Service
JWT_SECRET=<JWT_SECRET-definido-en-.env>
```

### 2. Variables de Entorno de Integración

Agregar en todos los servicios P1:

```bash
# URL del Auth Service
AUTH_SERVICE_URL=http://localhost:9000
AUTH_VALIDATE_ENDPOINT=/api/v1/auth/validate
AUTH_PUBLIC_KEY_ENDPOINT=/api/v1/auth/public-key
```

---

## Endpoints de Validación

### POST /api/v1/auth/validate

⚠️ **NOTA IMPORTANTE**: Este endpoint es **OPCIONAL** y solo debe usarse en casos especiales (debugging, admin panel, validación desde servicios externos que no pueden compartir JWT_SECRET).

**Para operación normal, los servicios P1 deben validar JWT LOCALMENTE** para evitar el antipatrón de llamadas constantes al Auth Service.

Valida un token JWT y retorna información del usuario.

**Request:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (Token Válido):**
```json
{
  "valid": true,
  "user": {
    "id": 1,
    "email": "juan.perez@uleam.edu.ec",
    "nombre": "Juan",
    "apellido": "Pérez",
    "tipoUsuarioId": 2,
    "estado": "activo"
  }
}
```

**Response (Token Inválido):**
```json
{
  "valid": false,
  "error": "Token expirado"
}
```

**Errores Posibles:**
- `Token expirado`
- `Token inválido`
- `Token revocado (blacklist)`
- `Usuario no encontrado`
- `Usuario bloqueado`
- `Token no es de tipo access`

**Casos de uso apropiados:**
- Debugging y testing
- Admin panel que necesita validar tokens de usuarios
- Servicios externos sin acceso a JWT_SECRET
- Migración gradual de sistemas legacy

**❌ NO usar para:**
- Validación en cada request de servicios P1 (usar validación local)
- Endpoints de alta frecuencia

### GET /api/v1/auth/public-key

Obtiene configuración pública del JWT.

**Response:**
```json
{
  "algorithm": "HS256",
  "issuer": "auth-service",
  "accessTokenExpiration": "15m",
  "refreshTokenExpiration": "7d"
}
```

---

## Integración por Servicio

### REST Service (FastAPI)

#### 1. Instalar Dependencias JWT

```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

#### 2. Crear Utilidad de Validación LOCAL

**Archivo:** `app/utils/jwt_validator.py`

```python
from jose import JWTError, jwt
from datetime import datetime
from typing import Optional, Dict, Any
from app.config import Settings

class JWTValidator:
    """
    Validador LOCAL de tokens JWT.
    NO hace llamadas HTTP al Auth Service en cada request.
    """
    
    def __init__(self, settings: Settings):
        self.secret_key = settings.SECRET_KEY  # Mismo que Auth Service
        self.algorithm = settings.ALGORITHM    # HS256
        
    def validate_token_local(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Valida un token JWT LOCALMENTE verificando:
        1. Firma válida (usando JWT_SECRET compartido)
        2. Token no expirado
        3. Estructura correcta del payload
        
        Retorna el payload del token si es válido, None si no lo es.
        """
        try:
            # Decodificar y verificar firma + expiración
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Verificar que sea un access token (no refresh)
            if payload.get('type') != 'access':
                return None
                
            # Extraer información del usuario
            user_id = payload.get('sub')
            if not user_id:
                return None
            
            return {
                'user_id': int(user_id),
                'email': payload.get('email'),
                'tipo_usuario_id': payload.get('tipoUsuarioId'),
                'exp': payload.get('exp'),
                'iat': payload.get('iat')
            }
            
        except JWTError as e:
            # Token inválido, expirado o con firma incorrecta
            return None
        except Exception as e:
            # Cualquier otro error
            return None
```

#### 3. Crear Dependency de Autenticación LOCAL

**Archivo:** `app/dependencies.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.jwt_validator import JWTValidator
from app.config import get_settings, Settings

security = HTTPBearer()

def get_jwt_validator(settings: Settings = Depends(get_settings)) -> JWTValidator:
    """Crea una instancia del validador JWT"""
    return JWTValidator(settings)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt_validator: JWTValidator = Depends(get_jwt_validator)
) -> dict:
    """
    Valida el token JWT LOCALMENTE sin llamar al Auth Service.
    
    Esta es la implementación correcta del Pilar 1:
    - Valida firma y expiración localmente
    - No hace HTTP calls al Auth Service
    - Evita latencia adicional
    - Escala horizontalmente sin bottleneck
    """
    token = credentials.credentials
    
    # Validación LOCAL usando JWT_SECRET compartido
    payload = jwt_validator.validate_token_local(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # ⚠️ NOTA sobre BLACKLIST:
    # En validación local, hay una ventana de tiempo donde un token
    # revocado puede seguir siendo válido hasta que expire.
    # Para aplicaciones que requieren revocación inmediata, ver
    # sección "Estrategias de Blacklist" más abajo.
    
    return payload
```

#### 4. Usar en Rutas Protegidas

```python
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/reservas")
async def get_reservas(current_user: dict = Depends(get_current_user)):
    """
    Endpoint protegido - requiere JWT válido.
    La validación es LOCAL, sin llamadas al Auth Service.
    """
    user_id = current_user["user_id"]
    
    # Lógica para obtener reservas del usuario
    return {
        "user_id": user_id,
        "reservas": []
    }

@router.post("/reservas")
async def create_reserva(
    reserva_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Crear reserva - validación JWT local
    """
    user_id = current_user["user_id"]
    
    # Lógica de creación
    return {"message": "Reserva creada", "user_id": user_id}
```

#### 5. Estrategias de Blacklist (Opcional)

**Opción A: Cache Local con Redis Pub/Sub** (Recomendado para alta seguridad)

```python
import redis
from typing import Optional, Dict, Any

class JWTValidatorWithBlacklist(JWTValidator):
    """Validador con verificación de blacklist en cache local"""
    
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        # Suscribirse a eventos de blacklist (pub/sub)
        self._subscribe_to_blacklist_updates()
    
    def _subscribe_to_blacklist_updates(self):
        """Suscribirse a actualizaciones de blacklist desde Auth Service"""
        # Implementar Redis Pub/Sub para recibir tokens revocados
        pass
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Verifica si el token está en blacklist (cache local)"""
        key = f"blacklist:{token}"
        return self.redis_client.exists(key) > 0
    
    def validate_token_local(self, token: str) -> Optional[Dict[str, Any]]:
        """Validación con verificación de blacklist"""
        # 1. Validar firma y expiración localmente
        payload = super().validate_token_local(token)
        if not payload:
            return None
        
        # 2. Verificar blacklist en cache local (rápido)
        if self.is_token_blacklisted(token):
            return None
        
        return payload
```

**Opción B: Verificación Asíncrona** (Menor latencia, ventana de riesgo aceptable)

```python
import asyncio
import httpx

async def check_blacklist_async(token: str, auth_service_url: str):
    """
    Verificación no bloqueante de blacklist.
    Se ejecuta en background sin bloquear el request.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{auth_service_url}/api/v1/auth/validate",
                json={"token": token},
                timeout=0.1  # Timeout muy bajo
            )
            if response.status_code == 200:
                result = response.json()
                if not result.get("valid"):
                    # Agregar a cache local de blacklist
                    pass
        except:
            # Si falla, no bloquear el request
            pass

async def get_current_user_with_async_blacklist(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt_validator: JWTValidator = Depends(get_jwt_validator)
) -> dict:
    """Validación local + verificación async de blacklist"""
    token = credentials.credentials
    payload = jwt_validator.validate_token_local(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Lanzar verificación de blacklist en background (no bloqueante)
    asyncio.create_task(
        check_blacklist_async(token, "http://localhost:9000")
    )
    
    return payload
```

**Opción C: Ventana de Riesgo Aceptable** (Máxima performance)

```python
# Simplemente validar localmente sin verificar blacklist
# Aceptar que tokens revocados pueden funcionar hasta expirar
# Apropiado para:
# - Aplicaciones de baja criticidad
# - Tokens de muy corta duración (5-10 min)
# - Sistemas con logout solo informativo

async def get_current_user_simple(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt_validator: JWTValidator = Depends(get_jwt_validator)
) -> dict:
    """
    Validación LOCAL pura sin verificación de blacklist.
    Máxima performance, ventana de riesgo = duración del access token.
    """
    token = credentials.credentials
    payload = jwt_validator.validate_token_local(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    return payload
```

---

### GraphQL Service (Go)

#### 1. Instalar Dependencias JWT

```bash
go get github.com/golang-jwt/jwt/v5
```

#### 2. Crear Utilidad de Validación LOCAL

**Archivo:** `internal/auth/jwt_validator.go`

```go
package auth

import (
    "errors"
    "fmt"
    "time"
    
    "github.com/golang-jwt/jwt/v5"
)

type JWTValidator struct {
    SecretKey []byte
}

type TokenClaims struct {
    UserID        int    `json:"sub"`
    Email         string `json:"email"`
    TipoUsuarioID int    `json:"tipoUsuarioId"`
    TokenType     string `json:"type"`
    jwt.RegisteredClaims
}

func NewJWTValidator(secretKey string) *JWTValidator {
    return &JWTValidator{
        SecretKey: []byte(secretKey),
    }
}

// ValidateTokenLocal valida un token JWT LOCALMENTE
// sin hacer llamadas HTTP al Auth Service.
// Verifica firma y expiración usando el JWT_SECRET compartido.
func (v *JWTValidator) ValidateTokenLocal(tokenString string) (*TokenClaims, error) {
    // Parsear y validar el token
    token, err := jwt.ParseWithClaims(
        tokenString,
        &TokenClaims{},
        func(token *jwt.Token) (interface{}, error) {
            // Verificar algoritmo
            if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
                return nil, fmt.Errorf("método de firma inesperado: %v", token.Header["alg"])
            }
            return v.SecretKey, nil
        },
    )
    
    if err != nil {
        return nil, fmt.Errorf("error al parsear token: %w", err)
    }
    
    // Extraer claims
    claims, ok := token.Claims.(*TokenClaims)
    if !ok || !token.Valid {
        return nil, errors.New("token inválido")
    }
    
    // Verificar que sea un access token (no refresh)
    if claims.TokenType != "access" {
        return nil, errors.New("el token no es de tipo access")
    }
    
    // Verificar expiración (jwt.ParseWithClaims ya lo verifica, pero doble check)
    if claims.ExpiresAt != nil && claims.ExpiresAt.Before(time.Now()) {
        return nil, errors.New("token expirado")
    }
    
    return claims, nil
}
```

#### 3. Crear Middleware de Autenticación LOCAL

**Archivo:** `internal/auth/middleware.go`

```go
package auth

import (
    "context"
    "net/http"
    "strings"
)

type contextKey string

const UserContextKey contextKey = "user"

type AuthMiddleware struct {
    jwtValidator *JWTValidator
}

func NewAuthMiddleware(jwtSecret string) *AuthMiddleware {
    return &AuthMiddleware{
        jwtValidator: NewJWTValidator(jwtSecret),
    }
}

// Authenticate valida el token JWT LOCALMENTE
// Esta es la implementación correcta del Pilar 1:
// - Valida firma y expiración localmente
// - NO hace llamadas HTTP al Auth Service
// - Evita latencia adicional y bottleneck
func (m *AuthMiddleware) Authenticate(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Extraer token del header Authorization
        authHeader := r.Header.Get("Authorization")
        if authHeader == "" {
            http.Error(w, "Token requerido", http.StatusUnauthorized)
            return
        }

        // Remover prefijo "Bearer "
        token := strings.TrimPrefix(authHeader, "Bearer ")
        if token == authHeader {
            http.Error(w, "Formato de token inválido", http.StatusUnauthorized)
            return
        }

        // Validar LOCALMENTE usando JWT_SECRET compartido
        claims, err := m.jwtValidator.ValidateTokenLocal(token)
        if err != nil {
            http.Error(w, fmt.Sprintf("Token inválido: %v", err), http.StatusUnauthorized)
            return
        }

        // Agregar claims al contexto
        ctx := context.WithValue(r.Context(), UserContextKey, claims)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// GetUserFromContext extrae los claims del usuario del contexto
func GetUserFromContext(ctx context.Context) *TokenClaims {
    claims, _ := ctx.Value(UserContextKey).(*TokenClaims)
    return claims
}
```

#### 4. Estrategia de Blacklist con Redis (Opcional)

**Archivo:** `internal/auth/blacklist.go`

```go
package auth

import (
    "context"
    "fmt"
    "time"
    
    "github.com/redis/go-redis/v9"
)

type BlacklistChecker struct {
    redisClient *redis.Client
}

func NewBlacklistChecker(redisAddr string) *BlacklistChecker {
    client := redis.NewClient(&redis.Options{
        Addr: redisAddr,
    })
    
    return &BlacklistChecker{
        redisClient: client,
    }
}

// IsTokenBlacklisted verifica si un token está en la blacklist local (Redis cache)
func (b *BlacklistChecker) IsTokenBlacklisted(ctx context.Context, token string) bool {
    key := fmt.Sprintf("blacklist:%s", token)
    exists, err := b.redisClient.Exists(ctx, key).Result()
    
    if err != nil {
        // En caso de error de Redis, permitir el request (fail-open)
        // O fail-closed si la seguridad es crítica
        return false
    }
    
    return exists > 0
}

// AuthMiddleware con verificación de blacklist
type AuthMiddlewareWithBlacklist struct {
    jwtValidator     *JWTValidator
    blacklistChecker *BlacklistChecker
}

func NewAuthMiddlewareWithBlacklist(jwtSecret string, redisAddr string) *AuthMiddlewareWithBlacklist {
    return &AuthMiddlewareWithBlacklist{
        jwtValidator:     NewJWTValidator(jwtSecret),
        blacklistChecker: NewBlacklistChecker(redisAddr),
    }
}

func (m *AuthMiddlewareWithBlacklist) Authenticate(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        authHeader := r.Header.Get("Authorization")
        if authHeader == "" {
            http.Error(w, "Token requerido", http.StatusUnauthorized)
            return
        }

        token := strings.TrimPrefix(authHeader, "Bearer ")
        if token == authHeader {
            http.Error(w, "Formato de token inválido", http.StatusUnauthorized)
            return
        }

        // 1. Validar LOCALMENTE
        claims, err := m.jwtValidator.ValidateTokenLocal(token)
        if err != nil {
            http.Error(w, fmt.Sprintf("Token inválido: %v", err), http.StatusUnauthorized)
            return
        }

        // 2. Verificar blacklist en cache local (rápido)
        if m.blacklistChecker.IsTokenBlacklisted(r.Context(), token) {
            http.Error(w, "Token revocado", http.StatusUnauthorized)
            return
        }

        // Agregar claims al contexto
        ctx := context.WithValue(r.Context(), UserContextKey, claims)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}
```

#### 5. Usar en Servidor GraphQL

**Archivo:** `cmd/server/main.go`

```go
package main

import (
    "log"
    "net/http"
    "os"
    
    "your-project/internal/auth"
    "your-project/internal/graphql"
)

func main() {
    // Cargar JWT_SECRET desde environment
    jwtSecret := os.Getenv("JWT_SECRET")
    if jwtSecret == "" {
        log.Fatal("JWT_SECRET no configurado")
    }
    
    // Crear middleware de autenticación
    authMiddleware := auth.NewAuthMiddleware(jwtSecret)
    
    // O con verificación de blacklist:
    // redisAddr := os.Getenv("REDIS_ADDR")
    // authMiddleware := auth.NewAuthMiddlewareWithBlacklist(jwtSecret, redisAddr)
    
    // Configurar handler GraphQL
    graphqlHandler := graphql.NewHandler()
    
    // Aplicar middleware de autenticación
    http.Handle("/graphql", authMiddleware.Authenticate(graphqlHandler))
    
    log.Println("GraphQL Server running on :8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

#### 6. Usar en Resolvers GraphQL

```go
package graph

import (
    "context"
    "fmt"
    
    "your-project/internal/auth"
)

type Resolver struct {
    // ... servicios
}

func (r *Resolver) GetReservas(ctx context.Context) ([]*Reserva, error) {
    // Obtener usuario del contexto (ya validado por middleware)
    user := auth.GetUserFromContext(ctx)
    if user == nil {
        return nil, fmt.Errorf("usuario no autenticado")
    }

    // Lógica para obtener reservas del usuario
    userID := user.UserID
    return r.reservaService.GetByUserID(userID)
}
```

---

### WebSocket Service (NestJS)

#### 1. Crear Módulo de Validación LOCAL

**Archivo:** `src/modules/auth/jwt-validator.service.ts`

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { JwtService } from '@nestjs/jwt';

export interface JWTPayload {
  sub: number;
  email: string;
  tipoUsuarioId: number;
  type: string;
  iat: number;
  exp: number;
}

@Injectable()
export class JwtValidatorService {
  private readonly logger = new Logger(JwtValidatorService.name);
  private readonly jwtSecret: string;

  constructor(
    private jwtService: JwtService,
    private configService: ConfigService,
  ) {
    this.jwtSecret = this.configService.get<string>('JWT_SECRET');
    if (!this.jwtSecret) {
      throw new Error('JWT_SECRET no configurado');
    }
  }

  /**
   * Valida un token JWT LOCALMENTE sin llamar al Auth Service.
   * Esta es la implementación correcta del Pilar 1.
   * 
   * Verifica:
   * - Firma válida (usando JWT_SECRET compartido)
   * - Token no expirado
   * - Estructura correcta del payload
   */
  async validateTokenLocal(token: string): Promise<JWTPayload | null> {
    try {
      // Verificar y decodificar el token localmente
      const payload = await this.jwtService.verifyAsync<JWTPayload>(token, {
        secret: this.jwtSecret,
      });

      // Verificar que sea un access token (no refresh)
      if (payload.type !== 'access') {
        this.logger.warn('Token no es de tipo access');
        return null;
      }

      // Verificar campos requeridos
      if (!payload.sub || !payload.email) {
        this.logger.warn('Payload incompleto');
        return null;
      }

      return payload;
    } catch (error) {
      // Token inválido, expirado o con firma incorrecta
      this.logger.warn(`Token inválido: ${error.message}`);
      return null;
    }
  }
}
```

#### 2. Actualizar Socket Auth Service

**Archivo:** `src/services/socket-auth.service.ts`

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { Socket } from 'socket.io';
import { JwtValidatorService, JWTPayload } from '../modules/auth/jwt-validator.service';

@Injectable()
export class SocketAuthService {
  private readonly logger = new Logger(SocketAuthService.name);

  constructor(private jwtValidatorService: JwtValidatorService) {}

  /**
   * Autentica un socket validando el JWT LOCALMENTE.
   * NO hace llamadas HTTP al Auth Service.
   */
  async authenticateSocket(socket: Socket): Promise<boolean> {
    try {
      // Extraer token del handshake
      const token = this.extractTokenFromSocket(socket);
      
      if (!token) {
        this.logger.warn('No token provided in socket handshake');
        return false;
      }

      // Validar LOCALMENTE usando JWT_SECRET compartido
      const payload = await this.jwtValidatorService.validateTokenLocal(token);

      if (!payload) {
        this.logger.warn('Token validation failed');
        return false;
      }

      // Guardar payload en socket data
      socket.data.user = {
        id: payload.sub,
        email: payload.email,
        tipoUsuarioId: payload.tipoUsuarioId,
      };
      
      this.logger.log(`Socket authenticated for user ${payload.sub}`);
      return true;
    } catch (error) {
      this.logger.error('Error en autenticación de socket', error);
      return false;
    }
  }

  private extractTokenFromSocket(socket: Socket): string | null {
    // Opción 1: Token en query params
    const tokenFromQuery = socket.handshake.query.token as string;
    if (tokenFromQuery) {
      return tokenFromQuery;
    }

    // Opción 2: Token en auth header
    const authHeader = socket.handshake.headers.authorization;
    if (authHeader) {
      return authHeader.replace('Bearer ', '');
    }

    return null;
  }

  getUserFromSocket(socket: Socket) {
    return socket.data.user;
  }
}
```

#### 3. Estrategia de Blacklist con Redis (Opcional)

**Archivo:** `src/modules/auth/blacklist.service.ts`

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import Redis from 'ioredis';

@Injectable()
export class BlacklistService {
  private readonly logger = new Logger(BlacklistService.name);
  private readonly redisClient: Redis;

  constructor(private configService: ConfigService) {
    const redisHost = this.configService.get<string>('REDIS_HOST', 'localhost');
    const redisPort = this.configService.get<number>('REDIS_PORT', 6379);

    this.redisClient = new Redis({
      host: redisHost,
      port: redisPort,
    });
  }

  /**
   * Verifica si un token está en la blacklist local (Redis cache).
   * Esto es opcional y depende de los requisitos de seguridad.
   */
  async isTokenBlacklisted(token: string): Promise<boolean> {
    try {
      const key = `blacklist:${token}`;
      const exists = await this.redisClient.exists(key);
      return exists === 1;
    } catch (error) {
      this.logger.error('Error verificando blacklist', error);
      // Fail-open: en caso de error, permitir el acceso
      // Cambiar a fail-closed si la seguridad es crítica
      return false;
    }
  }

  onModuleDestroy() {
    this.redisClient.disconnect();
  }
}
```

**Archivo:** `src/services/socket-auth-with-blacklist.service.ts`

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { Socket } from 'socket.io';
import { JwtValidatorService } from '../modules/auth/jwt-validator.service';
import { BlacklistService } from '../modules/auth/blacklist.service';

@Injectable()
export class SocketAuthWithBlacklistService {
  private readonly logger = new Logger(SocketAuthWithBlacklistService.name);

  constructor(
    private jwtValidatorService: JwtValidatorService,
    private blacklistService: BlacklistService,
  ) {}

  async authenticateSocket(socket: Socket): Promise<boolean> {
    try {
      const token = this.extractTokenFromSocket(socket);
      
      if (!token) {
        return false;
      }

      // 1. Validar LOCALMENTE
      const payload = await this.jwtValidatorService.validateTokenLocal(token);
      if (!payload) {
        return false;
      }

      // 2. Verificar blacklist en cache local (rápido)
      const isBlacklisted = await this.blacklistService.isTokenBlacklisted(token);
      if (isBlacklisted) {
        this.logger.warn(`Token blacklisted for user ${payload.sub}`);
        return false;
      }

      // Guardar payload en socket data
      socket.data.user = {
        id: payload.sub,
        email: payload.email,
        tipoUsuarioId: payload.tipoUsuarioId,
      };
      
      return true;
    } catch (error) {
      this.logger.error('Error en autenticación', error);
      return false;
    }
  }

  private extractTokenFromSocket(socket: Socket): string | null {
    const tokenFromQuery = socket.handshake.query.token as string;
    if (tokenFromQuery) {
      return tokenFromQuery;
    }

    const authHeader = socket.handshake.headers.authorization;
    if (authHeader) {
      return authHeader.replace('Bearer ', '');
    }

    return null;
  }

  getUserFromSocket(socket: Socket) {
    return socket.data.user;
  }
}
```

#### 4. Configurar Módulo de Autenticación

**Archivo:** `src/modules/auth/auth.module.ts`

```typescript
import { Module } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { JwtValidatorService } from './jwt-validator.service';
import { BlacklistService } from './blacklist.service';

@Module({
  imports: [
    JwtModule.registerAsync({
      imports: [ConfigModule],
      useFactory: async (configService: ConfigService) => ({
        secret: configService.get<string>('JWT_SECRET'),
        signOptions: {
          expiresIn: '15m', // Debe coincidir con Auth Service
        },
      }),
      inject: [ConfigService],
    }),
  ],
  providers: [JwtValidatorService, BlacklistService],
  exports: [JwtValidatorService, BlacklistService],
})
export class AuthModule {}
```

#### 5. Usar en WebSocket Gateway

**Archivo:** `src/gateways/notifications.gateway.ts`

```typescript
import {
  WebSocketGateway,
  WebSocketServer,
  OnGatewayConnection,
  OnGatewayDisconnect,
  SubscribeMessage,
  MessageBody,
  ConnectedSocket,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { SocketAuthService } from '../services/socket-auth.service';

@WebSocketGateway({
  cors: {
    origin: '*',
  },
})
export class NotificationsGateway
  implements OnGatewayConnection, OnGatewayDisconnect
{
  @WebSocketServer()
  server: Server;

  constructor(private socketAuthService: SocketAuthService) {}

  async handleConnection(socket: Socket) {
    // Validar JWT LOCALMENTE (sin llamar al Auth Service)
    const isAuthenticated = await this.socketAuthService.authenticateSocket(socket);

    if (!isAuthenticated) {
      socket.emit('error', { message: 'Autenticación fallida' });
      socket.disconnect();
      return;
    }

    const user = this.socketAuthService.getUserFromSocket(socket);
    socket.emit('connected', { message: `Bienvenido ${user.email}` });
  }

  handleDisconnect(socket: Socket) {
    const user = this.socketAuthService.getUserFromSocket(socket);
    console.log(`Usuario ${user?.id} desconectado`);
  }

  @SubscribeMessage('subscribe-notifications')
  handleSubscribe(@ConnectedSocket() socket: Socket) {
    const user = this.socketAuthService.getUserFromSocket(socket);
    socket.join(`user-${user.id}`);
    return { event: 'subscribed', data: { userId: user.id } };
  }
}
```

---

## Flujo de Autenticación

### 1. Registro/Login (Cliente → Auth Service)

```
Cliente
  │
  │ POST /api/v1/auth/register o /login
  │ { email, password, ... }
  │
  ▼
Auth Service
  │
  │ 1. Valida credenciales
  │ 2. Hashea password (solo register)
  │ 3. Guarda en DB
  │ 4. Genera JWT firmado con JWT_SECRET (access + refresh)
  │
  ▼
Cliente recibe:
{
  "user": {...},
  "accessToken": "eyJhbGc...",  ← Firmado con JWT_SECRET
  "refreshToken": "eyJhbGc...",
  "expiresIn": 900
}
```

### 2. Request a Servicio P1 con VALIDACIÓN LOCAL (Cliente → REST/GraphQL/WebSocket)

```
Cliente
  │
  │ GET /api/reservas
  │ Authorization: Bearer eyJhbGc...
  │
  ▼
Servicio P1 (REST/GraphQL/WS)
  │
  │ 1. Extrae token del header
  │ 2. Decodifica JWT usando JWT_SECRET compartido
  │ 3. Verifica firma LOCALMENTE
  │ 4. Verifica expiración LOCALMENTE
  │ 5. (Opcional) Verifica blacklist en cache local
  │
  │ ✅ Token válido (sin llamadas HTTP)
  │
  ▼
Procesa request con datos del usuario
  │
  ▼
Cliente recibe respuesta

⚠️ IMPORTANTE: NO se llama al Auth Service
✅ Validación 100% local
✅ Zero latencia adicional
✅ Evita bottleneck en Auth Service
```

### 3. Refresh Token

```
Cliente
  │
  │ POST /api/v1/auth/refresh
  │ { "refreshToken": "eyJhbGc..." }
  │
  ▼
Auth Service
  │
  │ 1. Valida refresh token
  │ 2. Verifica en DB (no revocado)
  │ 3. Revoca refresh token anterior
  │ 4. Genera nuevos tokens (rotation)
  │
  ▼
Cliente recibe nuevos tokens:
{
  "accessToken": "nuevo_token",
  "refreshToken": "nuevo_refresh",
  "expiresIn": 900
}
```

### 4. Logout

```
Cliente
  │
  │ POST /api/v1/auth/logout
  │ Authorization: Bearer eyJhbGc...
  │
  ▼
Auth Service
  │
  │ 1. Extrae user_id del JWT
  │ 2. Revoca todos los refresh tokens del usuario
  │ 3. Agrega access token a blacklist (Redis)
  │ 4. (Opcional) Publica evento de revocación (Pub/Sub)
  │
  ▼
Cliente recibe:
{
  "message": "Sesión cerrada exitosamente"
}

Siguiente request a P1:
  │
  │ GET /api/reservas
  │ Authorization: Bearer token_revocado
  │
  ▼
Servicio P1 valida localmente:
  │
  │ 1. Decodifica JWT ✅
  │ 2. Verifica firma ✅
  │ 3. Verifica expiración ✅
  │ 4. Verifica blacklist en cache local
  │    (si usa estrategia de blacklist)
  │
  ▼
Opción A (con blacklist cache):
  └─> ✗ Token en blacklist → 401 Unauthorized

Opción B (sin blacklist cache):
  └─> ✅ Token válido hasta expirar (ventana de riesgo)
      Consideración: access tokens de corta duración (15min)
```

---

## Manejo de Errores

### Escenarios de Error Comunes

#### 1. Auth Service No Disponible

**Síntoma**: Servicios P1 no pueden validar tokens

**Solución**: Implementar fallback o circuit breaker

```typescript
// Ejemplo en NestJS
async validateToken(token: string): Promise<ValidateTokenResponse> {
  try {
    const response = await this.httpClient.post('/api/v1/auth/validate', { token });
    return response.data;
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      // Auth Service no disponible
      this.logger.error('Auth Service no disponible');
      
      // Opción 1: Rechazar todas las requests
      return { valid: false, error: 'Servicio de autenticación no disponible' };
      
      // Opción 2: Validar localmente (modo degradado - NO RECOMENDADO en producción)
      // return this.fallbackValidation(token);
    }
    throw error;
  }
}
```

#### 2. Token Expirado

**Respuesta de Auth Service**:
```json
{
  "valid": false,
  "error": "Token expirado"
}
```

**Acción en Cliente**: Usar refresh token para obtener nuevo access token

#### 3. Usuario Bloqueado

**Respuesta de Auth Service**:
```json
{
  "valid": false,
  "error": "Usuario bloqueado"
}
```

**Acción en P1**: Retornar 401 y forzar logout en cliente

#### 4. Token en Blacklist

**Respuesta de Auth Service**:
```json
{
  "valid": false,
  "error": "Token revocado (blacklist)"
}
```

**Acción en P1**: Retornar 401, cliente debe hacer login nuevamente

---

## Testing

### Test de Integración: REST Service → Auth Service

**Archivo**: `rest-service/tests/test_auth_integration.py`

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_protected_endpoint_with_valid_token():
    """Verifica que endpoint protegido acepta token válido"""
    # 1. Obtener token de Auth Service
    async with AsyncClient(base_url="http://localhost:9000") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@uleam.edu.ec",
                "password": "Test123456!"
            }
        )
        assert response.status_code == 200
        token = response.json()["accessToken"]
    
    # 2. Usar token en REST Service
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/reservas",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token():
    """Verifica que endpoint protegido rechaza token inválido"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/reservas",
            headers={"Authorization": "Bearer token_invalido"}
        )
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_protected_endpoint_after_logout():
    """Verifica que token no funciona después de logout"""
    # 1. Login
    async with AsyncClient(base_url="http://localhost:9000") as client:
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@uleam.edu.ec", "password": "Test123456!"}
        )
        token = login_response.json()["accessToken"]
        
        # 2. Logout
        await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    # 3. Intentar usar token después de logout
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/reservas",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
```

### Test Manual con cURL

#### 1. Login y obtener token
```bash
curl -X POST http://localhost:9000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "juan.perez@uleam.edu.ec",
    "password": "Test123456!"
  }'

# Respuesta:
# {
#   "user": {...},
#   "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   ...
# }
```

#### 2. Validar token manualmente
```bash
curl -X POST http://localhost:9000/api/v1/auth/validate \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'

# Respuesta:
# {
#   "valid": true,
#   "user": {
#     "id": 1,
#     "email": "juan.perez@uleam.edu.ec",
#     ...
#   }
# }
```

#### 3. Usar token en REST Service
```bash
curl -X GET http://localhost:8000/api/reservas \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### 4. Logout y verificar blacklist
```bash
# Logout
curl -X POST http://localhost:9000/api/v1/auth/logout \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Intentar validar token después de logout
curl -X POST http://localhost:9000/api/v1/auth/validate \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'

# Respuesta:
# {
#   "valid": false,
#   "error": "Token revocado (blacklist)"
# }
```

---

## Checklist de Implementación

### Auth Service (P2)
- [x] Implementar endpoints de validación (`/validate`, `/public-key`)
- [x] Método `validateTokenForP1()` en AuthService
- [x] Verificación de blacklist en validación
- [x] Verificación de estado de usuario
- [x] DTOs y documentación Swagger

### REST Service (P1)
- [ ] Agregar `AUTH_SERVICE_URL` a `.env`
- [ ] Configurar `JWT_SECRET` compartido
- [ ] Implementar `AuthServiceClient`
- [ ] Actualizar `get_current_user()` dependency
- [ ] Agregar tests de integración
- [ ] Actualizar documentación de API

### GraphQL Service (P1)
- [ ] Agregar `AUTH_SERVICE_URL` a `.env`
- [ ] Configurar `JWT_SECRET` compartido
- [ ] Implementar `AuthServiceClient` en Go
- [ ] Actualizar middleware de autenticación
- [ ] Agregar context user en resolvers
- [ ] Agregar tests de integración

### WebSocket Service (P1)
- [ ] Agregar `AUTH_SERVICE_URL` a `.env`
- [ ] Configurar `JWT_SECRET` compartido
- [ ] Implementar `AuthClientService`
- [ ] Actualizar `SocketAuthService`
- [ ] Modificar handshake de conexión
- [ ] Agregar tests de integración

### Testing General
- [ ] Test: Login → Usar token en REST
- [ ] Test: Login → Usar token en GraphQL
- [ ] Test: Login → Conectar con WebSocket
- [ ] Test: Logout → Verificar blacklist en todos los servicios
- [ ] Test: Token expirado → Refresh en todos los servicios
- [ ] Test: Auth Service caído → Manejo de errores

---

## Problemas Conocidos y Soluciones

### 1. Latencia en Validación

**Problema**: Cada request a P1 hace un HTTP call a Auth Service (latencia adicional)

**Soluciones**:
- **Opción 1**: Cachear validaciones (Redis en P1) con TTL corto (30-60s)
- **Opción 2**: Validar localmente + verificar blacklist solo
- **Opción 3**: Usar gRPC en lugar de HTTP REST (más rápido)

### 2. Single Point of Failure

**Problema**: Si Auth Service cae, todos los servicios P1 dejan de funcionar

**Soluciones**:
- **Load Balancer**: Múltiples instancias de Auth Service
- **Circuit Breaker**: Implementar en clientes de P1
- **Fallback**: Modo degradado con validación local (cuidado con blacklist)

### 3. Sincronización de Secretos

**Problema**: Difícil mantener `JWT_SECRET` sincronizado entre 4 servicios

**Soluciones**:
- **Vault**: Usar HashiCorp Vault o similar
- **Secrets Manager**: AWS Secrets Manager, Azure Key Vault
- **Variables de Entorno Compartidas**: Docker Compose con .env global

---

## Recursos Adicionales

- [Documentación Swagger Auth Service](http://localhost:9000/api)
- [JWT.io - Debugger de Tokens](https://jwt.io)
- [NestJS Passport JWT](https://docs.nestjs.com/security/authentication)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

---

**Autor**: Auth Service Team  
**Versión**: 1.0.0
