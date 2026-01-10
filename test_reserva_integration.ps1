# Test de creación de reserva con token del auth-service
Write-Host "🔍 Probando creación de reserva con token real..." -ForegroundColor Yellow

# 1. Login en auth-service
Write-Host "`n1️⃣ Haciendo login en auth-service..." -ForegroundColor Cyan
$loginBody = @{
    email = "admin123@uleam.edu.ec"
    password = "admin123"
} | ConvertTo-Json

try {
    $authResponse = Invoke-RestMethod -Uri "http://localhost:9000/api/v1/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body $loginBody
    
    $token = $authResponse.accessToken
    Write-Host "   ✅ Login exitoso! Token obtenido." -ForegroundColor Green
    Write-Host "   User ID: $($authResponse.user.id)" -ForegroundColor Gray
    Write-Host "   Email: $($authResponse.user.email)" -ForegroundColor Gray
    
    # 2. Crear reserva en REST service
    Write-Host "`n2️⃣ Creando reserva en REST service..." -ForegroundColor Cyan
    
    $reservaBody = @{
        espacio_id = 1
        tipo_evento_id = 1
        fecha = (Get-Date).AddDays(1).ToString("yyyy-MM-dd")
        hora_inicio = "09:00"
        hora_fin = "11:00"
        titulo = "Prueba de integración REST"
        descripcion = "Reserva desde frontend"
    } | ConvertTo-Json
    
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    $reservaResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/reservas" `
        -Method POST `
        -Headers $headers `
        -Body $reservaBody
    
    Write-Host "   ✅ Reserva creada exitosamente!" -ForegroundColor Green
    Write-Host "`n📋 Respuesta:" -ForegroundColor Cyan
    $reservaResponse | ConvertTo-Json -Depth 5
}
catch {
    Write-Host "`n❌ Error:" -ForegroundColor Red
    Write-Host "StatusCode: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    
    if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
        Write-Host "`nDetalle:" -ForegroundColor Yellow
        $_.ErrorDetails.Message
    }
}
