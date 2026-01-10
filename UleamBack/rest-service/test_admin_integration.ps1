# Test de integración completo con admin123@uleam.edu.ec
Write-Host "====== PRUEBA DE INTEGRACION ADMIN ======" -ForegroundColor Cyan

# 1. Login en auth-service
Write-Host "`n1️⃣ Autenticando en auth-service..." -ForegroundColor Yellow
$loginBody = @{
    email = "admin123@uleam.edu.ec"
    password = "AdminPass123!"
} | ConvertTo-Json

try {
    $authResponse = Invoke-RestMethod -Uri "http://localhost:9000/api/v1/auth/login" `
        -Method POST `
        -Body $loginBody `
        -ContentType "application/json"
    
    Write-Host "   ✅ Login exitoso" -ForegroundColor Green
    Write-Host "   User ID: $($authResponse.user.id)"
    Write-Host "   Tipo Usuario ID: $($authResponse.user.tipo_usuario_id)"
    Write-Host "   Email: $($authResponse.user.email)"
    
    $token = $authResponse.accessToken
    Write-Host "   Token: $($token.Substring(0, 50))..." -ForegroundColor Gray
    
} catch {
    Write-Host "   ❌ Error en login: $_" -ForegroundColor Red
    exit 1
}

# 2. Test /api/auth/me en REST service
Write-Host "`n2️⃣ Probando /api/auth/me en REST service..." -ForegroundColor Yellow
try {
    $meResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/me" `
        -Method GET `
        -Headers @{ Authorization = "Bearer $token" }
    
    Write-Host "   ✅ Endpoint /api/auth/me funciona" -ForegroundColor Green
    Write-Host "   User ID: $($meResponse.id)"
    Write-Host "   Email: $($meResponse.email)"
    Write-Host "   Tipo Usuario ID: $($meResponse.tipo_usuario_id)"
    Write-Host "   Tipo Usuario Nombre: $($meResponse.tipo_usuario.nombre)" -ForegroundColor Cyan
    
} catch {
    Write-Host "   ❌ Error en /api/auth/me: $_" -ForegroundColor Red
    Write-Host "   Status: $($_.Exception.Response.StatusCode.Value__)"
}

# 3. Crear una reserva
Write-Host "`n3️⃣ Creando reserva de prueba..." -ForegroundColor Yellow
$reservaBody = @{
    espacio_id = 1
    fecha = (Get-Date).AddDays(7).ToString("yyyy-MM-dd")
    hora_inicio = "10:00"
    hora_fin = "12:00"
    proposito = "Prueba de integración desde PowerShell"
} | ConvertTo-Json

try {
    $reservaResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/reservas" `
        -Method POST `
        -Body $reservaBody `
        -ContentType "application/json" `
        -Headers @{ Authorization = "Bearer $token" }
    
    Write-Host "   ✅ Reserva creada exitosamente" -ForegroundColor Green
    Write-Host "   Reserva ID: $($reservaResponse.id)"
    Write-Host "   Espacio ID: $($reservaResponse.espacio_id)"
    Write-Host "   Estado: $($reservaResponse.estado)"
    Write-Host "   Propósito: $($reservaResponse.proposito)"
    
} catch {
    Write-Host "   ❌ Error al crear reserva: $_" -ForegroundColor Red
    Write-Host "   Status: $($_.Exception.Response.StatusCode.Value__)"
    if ($_.ErrorDetails.Message) {
        Write-Host "   Detalle: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}

Write-Host "`n====== FIN DE PRUEBA ======" -ForegroundColor Cyan
