# Script para probar REST login
Write-Host "Probando REST Login..." -ForegroundColor Yellow

$loginBody = @{
    email = "admin@uleam.edu.ec"
    password = "password123"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body $loginBody
    
    Write-Host "`n✅ Login exitoso!" -ForegroundColor Green
    Write-Host "`n📋 Respuesta completa:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10
    
    Write-Host "`n🔍 Datos específicos del usuario:" -ForegroundColor Cyan
    Write-Host "  - ID: $($response.user.id)"
    Write-Host "  - Email: $($response.user.email)"
    Write-Host "  - Nombre: $($response.user.nombre)"
    Write-Host "  - tipo_usuario_id: $($response.user.tipo_usuario_id)"
    Write-Host "  - tipo_usuario: $($response.user.tipo_usuario | ConvertTo-Json -Compress)"
    
} catch {
    Write-Host "`n❌ Error:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    if ($_.ErrorDetails) {
        Write-Host $_.ErrorDetails.Message
    }
}
