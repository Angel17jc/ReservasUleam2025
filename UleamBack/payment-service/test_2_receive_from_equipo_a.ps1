# TEST 2: EQUIPO A → NOSOTROS
# Simulamos recibir un webhook de Equipo A

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  TEST 2: RECIBIR WEBHOOK DE EQUIPO A (Ellos → Nosotros) ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "📥 Simulando webhook de Equipo A..." -ForegroundColor Yellow
Write-Host "   Nuestro endpoint: https://heuristically-farraginous-marquitta.ngrok-free.dev/api/v1/equipo-a/webhook`n" -ForegroundColor Gray

# Payload de prueba (formato Equipo A)
$payload = @{
    event = "tour.purchased"
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    data = @{
        booking_id = "test_booking_$(Get-Random -Minimum 1000 -Maximum 9999)"
        user_email = "test@uleam.edu.ec"
        tour_name = "Tour de Prueba - Manta City"
        amount = 150.00
        persons = 2
        destination = "Manta"
    }
    source = "equipo-a-recomendaciones"
} | ConvertTo-Json -Compress

Write-Host "📦 Payload a enviar:" -ForegroundColor Cyan
$payload | ConvertFrom-Json | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor White

# Generar firma HMAC-SHA256
$secret = "integracion-turismo-2026-uleam"
$hmac = New-Object System.Security.Cryptography.HMACSHA256
$hmac.Key = [Text.Encoding]::UTF8.GetBytes($secret)
$signature = [BitConverter]::ToString($hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($payload))).Replace("-", "").ToLower()

Write-Host "`n🔐 Firma HMAC generada: $($signature.Substring(0, 16))..." -ForegroundColor Magenta

try {
    $response = Invoke-RestMethod `
        -Uri "http://localhost:8001/api/v1/equipo-a/webhook" `
        -Method POST `
        -Body $payload `
        -ContentType "application/json" `
        -Headers @{
            "X-Signature" = $signature
        }
    
    Write-Host "`n✅ ÉXITO - Webhook recibido y procesado" -ForegroundColor Green
    Write-Host "`n📋 Respuesta de nuestro servidor:" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    $response | ConvertTo-Json -Depth 5 | Write-Host -ForegroundColor White
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Gray
    
    if ($response.status -eq "ok") {
        Write-Host "🎉 Webhook procesado correctamente!" -ForegroundColor Green
        Write-Host "   Evento: $($response.event)" -ForegroundColor White
        Write-Host "   Procesado: $($response.processed_at)" -ForegroundColor Gray
        
        if ($response.result) {
            Write-Host "`n📊 Resultado del procesamiento:" -ForegroundColor Cyan
            $response.result | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor White
        }
    }
    
} catch {
    Write-Host "`n❌ ERROR al procesar webhook" -ForegroundColor Red
    Write-Host "   Detalles: $($_.Exception.Message)" -ForegroundColor Yellow
    
    if ($_.ErrorDetails) {
        Write-Host "`n📄 Detalles del error:" -ForegroundColor Yellow
        $_.ErrorDetails.Message | Write-Host -ForegroundColor Red
    }
    
    if ($_.Exception.Message -like "*401*") {
        Write-Host "`n💡 Error de autenticación - Posibles causas:" -ForegroundColor Cyan
        Write-Host "   • Firma HMAC incorrecta" -ForegroundColor Gray
        Write-Host "   • Clave secreta no coincide" -ForegroundColor Gray
        Write-Host "   • Formato de payload incorrecto" -ForegroundColor Gray
    }
}

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Gray
