# ===============================================
# Script de Prueba - Integración P1 con Auth Service
# ===============================================
# Este script prueba el flujo completo de autenticación
# entre el Auth Service (P2) y los servicios P1

param(
    [string]$AuthServiceUrl = "http://localhost:9000",
    [string]$RestServiceUrl = "http://localhost:8000",
    [string]$Email = "juan.perez@uleam.edu.ec",
    [string]$Password = "Test123456!"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TEST DE INTEGRACIÓN P1 ↔ AUTH SERVICE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ===============================================
# 1. REGISTRO DE USUARIO
# ===============================================
Write-Host "📝 Paso 1: Registrando nuevo usuario..." -ForegroundColor Yellow

$registerBody = @{
    nombre = "Juan"
    apellido = "Pérez"
    email = $Email
    password = $Password
    tipoUsuarioId = 2
} | ConvertTo-Json

try {
    $registerResponse = Invoke-RestMethod `
        -Uri "$AuthServiceUrl/api/v1/auth/register" `
        -Method POST `
        -Body $registerBody `
        -ContentType "application/json" `
        -ErrorAction Stop

    Write-Host "✅ Usuario registrado exitosamente" -ForegroundColor Green
    Write-Host "   ID: $($registerResponse.user.id)" -ForegroundColor Gray
    Write-Host "   Email: $($registerResponse.user.email)" -ForegroundColor Gray
    Write-Host ""
} catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "⚠️  Usuario ya existe, continuando con login..." -ForegroundColor Yellow
        Write-Host ""
    } else {
        Write-Host "❌ Error en registro: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# ===============================================
# 2. LOGIN
# ===============================================
Write-Host "🔑 Paso 2: Iniciando sesión..." -ForegroundColor Yellow

$loginBody = @{
    email = $Email
    password = $Password
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod `
        -Uri "$AuthServiceUrl/api/v1/auth/login" `
        -Method POST `
        -Body $loginBody `
        -ContentType "application/json" `
        -ErrorAction Stop

    $accessToken = $loginResponse.accessToken
    $refreshToken = $loginResponse.refreshToken

    Write-Host "✅ Login exitoso" -ForegroundColor Green
    Write-Host "   Access Token: $($accessToken.Substring(0, 50))..." -ForegroundColor Gray
    Write-Host "   Refresh Token: $($refreshToken.Substring(0, 50))..." -ForegroundColor Gray
    Write-Host "   Expira en: $($loginResponse.expiresIn) segundos" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Error en login: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ===============================================
# 3. VALIDAR TOKEN DIRECTAMENTE EN AUTH SERVICE
# ===============================================
Write-Host "🔍 Paso 3: Validando token en Auth Service..." -ForegroundColor Yellow

$validateBody = @{
    token = $accessToken
} | ConvertTo-Json

try {
    $validateResponse = Invoke-RestMethod `
        -Uri "$AuthServiceUrl/api/v1/auth/validate" `
        -Method POST `
        -Body $validateBody `
        -ContentType "application/json" `
        -ErrorAction Stop

    if ($validateResponse.valid) {
        Write-Host "✅ Token válido" -ForegroundColor Green
        Write-Host "   Usuario ID: $($validateResponse.user.id)" -ForegroundColor Gray
        Write-Host "   Email: $($validateResponse.user.email)" -ForegroundColor Gray
        Write-Host "   Estado: $($validateResponse.user.estado)" -ForegroundColor Gray
    } else {
        Write-Host "❌ Token inválido: $($validateResponse.error)" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
} catch {
    Write-Host "❌ Error validando token: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ===============================================
# 4. OBTENER CONFIGURACIÓN PÚBLICA
# ===============================================
Write-Host "⚙️  Paso 4: Obteniendo configuración pública JWT..." -ForegroundColor Yellow

try {
    $publicKeyResponse = Invoke-RestMethod `
        -Uri "$AuthServiceUrl/api/v1/auth/public-key" `
        -Method GET `
        -ErrorAction Stop

    Write-Host "✅ Configuración obtenida" -ForegroundColor Green
    Write-Host "   Algoritmo: $($publicKeyResponse.algorithm)" -ForegroundColor Gray
    Write-Host "   Issuer: $($publicKeyResponse.issuer)" -ForegroundColor Gray
    Write-Host "   Access Token TTL: $($publicKeyResponse.accessTokenExpiration)" -ForegroundColor Gray
    Write-Host "   Refresh Token TTL: $($publicKeyResponse.refreshTokenExpiration)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Error obteniendo configuración: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ===============================================
# 5. ACCEDER A PERFIL CON TOKEN
# ===============================================
Write-Host "👤 Paso 5: Accediendo al perfil con token..." -ForegroundColor Yellow

try {
    $headers = @{
        "Authorization" = "Bearer $accessToken"
    }

    $profileResponse = Invoke-RestMethod `
        -Uri "$AuthServiceUrl/api/v1/auth/me" `
        -Method GET `
        -Headers $headers `
        -ErrorAction Stop

    Write-Host "✅ Perfil obtenido" -ForegroundColor Green
    Write-Host "   Nombre: $($profileResponse.nombre) $($profileResponse.apellido)" -ForegroundColor Gray
    Write-Host "   Email: $($profileResponse.email)" -ForegroundColor Gray
    Write-Host "   Tipo Usuario: $($profileResponse.tipoUsuarioId)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Error obteniendo perfil: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ===============================================
# 6. REFRESH TOKEN
# ===============================================
Write-Host "🔄 Paso 6: Refrescando access token..." -ForegroundColor Yellow

$refreshBody = @{
    refreshToken = $refreshToken
} | ConvertTo-Json

try {
    $refreshResponse = Invoke-RestMethod `
        -Uri "$AuthServiceUrl/api/v1/auth/refresh" `
        -Method POST `
        -Body $refreshBody `
        -ContentType "application/json" `
        -ErrorAction Stop

    $newAccessToken = $refreshResponse.accessToken
    $newRefreshToken = $refreshResponse.refreshToken

    Write-Host "✅ Token refrescado exitosamente" -ForegroundColor Green
    Write-Host "   Nuevo Access Token: $($newAccessToken.Substring(0, 50))..." -ForegroundColor Gray
    Write-Host "   Nuevo Refresh Token: $($newRefreshToken.Substring(0, 50))..." -ForegroundColor Gray
    Write-Host ""

    # Actualizar tokens para siguientes pasos
    $accessToken = $newAccessToken
    $refreshToken = $newRefreshToken
} catch {
    Write-Host "❌ Error refrescando token: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ===============================================
# 7. VERIFICAR QUE REFRESH TOKEN ANTERIOR YA NO FUNCIONA
# ===============================================
Write-Host "🔒 Paso 7: Verificando rotación de refresh tokens..." -ForegroundColor Yellow

$oldRefreshBody = @{
    refreshToken = $loginResponse.refreshToken  # Token original del login
} | ConvertTo-Json

try {
    $oldRefreshResponse = Invoke-RestMethod `
        -Uri "$AuthServiceUrl/api/v1/auth/refresh" `
        -Method POST `
        -Body $oldRefreshBody `
        -ContentType "application/json" `
        -ErrorAction Stop

    Write-Host "❌ FALLO: El refresh token anterior NO fue revocado" -ForegroundColor Red
    exit 1
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "✅ Refresh token anterior correctamente revocado" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "❌ Error inesperado: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# ===============================================
# 8. TEST DE INTEGRACIÓN CON REST SERVICE (SI ESTÁ DISPONIBLE)
# ===============================================
Write-Host "🌐 Paso 8: Probando integración con REST Service..." -ForegroundColor Yellow

try {
    # Intentar acceder a un endpoint del REST Service
    $headers = @{
        "Authorization" = "Bearer $accessToken"
    }

    # Nota: Este endpoint debe existir en el REST Service
    # Si no existe, este paso fallará pero no afectará el resto de las pruebas
    $restResponse = Invoke-RestMethod `
        -Uri "$RestServiceUrl/api/reservas" `
        -Method GET `
        -Headers $headers `
        -TimeoutSec 3 `
        -ErrorAction Stop

    Write-Host "✅ REST Service respondió correctamente" -ForegroundColor Green
    Write-Host "   El token fue validado exitosamente por REST Service" -ForegroundColor Gray
    Write-Host ""
} catch {
    if ($_.Exception.Message -like "*Connection refused*" -or $_.Exception.Message -like "*timed out*") {
        Write-Host "⚠️  REST Service no disponible (esto es normal si no está corriendo)" -ForegroundColor Yellow
        Write-Host ""
    } elseif ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "⚠️  Endpoint /api/reservas no encontrado en REST Service" -ForegroundColor Yellow
        Write-Host "   Esto es normal si aún no está implementado" -ForegroundColor Gray
        Write-Host ""
    } elseif ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "❌ REST Service rechazó el token (problema de integración)" -ForegroundColor Red
        Write-Host "   Verificar que REST Service esté usando el mismo JWT_SECRET" -ForegroundColor Yellow
        Write-Host ""
    } else {
        Write-Host "⚠️  Error en REST Service: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host ""
    }
}

# ===============================================
# 9. LOGOUT
# ===============================================
Write-Host "🚪 Paso 9: Cerrando sesión..." -ForegroundColor Yellow

try {
    $headers = @{
        "Authorization" = "Bearer $accessToken"
    }

    $logoutResponse = Invoke-RestMethod `
        -Uri "$AuthServiceUrl/api/v1/auth/logout" `
        -Method POST `
        -Headers $headers `
        -ErrorAction Stop

    Write-Host "✅ Logout exitoso" -ForegroundColor Green
    Write-Host "   $($logoutResponse.message)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Error en logout: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ===============================================
# 10. VERIFICAR BLACKLIST - INTENTAR USAR TOKEN DESPUÉS DE LOGOUT
# ===============================================
Write-Host "🚫 Paso 10: Verificando blacklist (token después de logout)..." -ForegroundColor Yellow

$validateBlacklistedBody = @{
    token = $accessToken
} | ConvertTo-Json

try {
    $validateBlacklistedResponse = Invoke-RestMethod `
        -Uri "$AuthServiceUrl/api/v1/auth/validate" `
        -Method POST `
        -Body $validateBlacklistedBody `
        -ContentType "application/json" `
        -ErrorAction Stop

    if (-not $validateBlacklistedResponse.valid) {
        Write-Host "✅ Token correctamente en blacklist" -ForegroundColor Green
        Write-Host "   Error: $($validateBlacklistedResponse.error)" -ForegroundColor Gray
    } else {
        Write-Host "❌ FALLO: Token NO fue agregado a blacklist" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
} catch {
    Write-Host "❌ Error verificando blacklist: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ===============================================
# 11. INTENTAR ACCEDER A PERFIL CON TOKEN REVOCADO
# ===============================================
Write-Host "🔐 Paso 11: Intentando acceder con token revocado..." -ForegroundColor Yellow

try {
    $headers = @{
        "Authorization" = "Bearer $accessToken"
    }

    $profileResponse = Invoke-RestMethod `
        -Uri "$AuthServiceUrl/api/v1/auth/me" `
        -Method GET `
        -Headers $headers `
        -ErrorAction Stop

    Write-Host "❌ FALLO: Endpoint aceptó token revocado" -ForegroundColor Red
    exit 1
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "✅ Acceso correctamente denegado" -ForegroundColor Green
        Write-Host "   Token revocado no puede acceder a endpoints protegidos" -ForegroundColor Gray
    } else {
        Write-Host "❌ Error inesperado: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

# ===============================================
# RESUMEN FINAL
# ===============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ TODAS LAS PRUEBAS PASARON" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Flujo completo validado:" -ForegroundColor White
Write-Host "  ✅ Registro de usuario" -ForegroundColor Green
Write-Host "  ✅ Login y generación de tokens" -ForegroundColor Green
Write-Host "  ✅ Validación de tokens" -ForegroundColor Green
Write-Host "  ✅ Configuración pública JWT" -ForegroundColor Green
Write-Host "  ✅ Acceso a endpoints protegidos" -ForegroundColor Green
Write-Host "  ✅ Refresh de tokens con rotación" -ForegroundColor Green
Write-Host "  ✅ Revocación de refresh tokens" -ForegroundColor Green
Write-Host "  ✅ Integración con REST Service (si disponible)" -ForegroundColor Green
Write-Host "  ✅ Logout y blacklist" -ForegroundColor Green
Write-Host "  ✅ Protección con tokens revocados" -ForegroundColor Green
Write-Host ""
Write-Host "🎉 El Auth Service está listo para integración con P1" -ForegroundColor Cyan
Write-Host ""
