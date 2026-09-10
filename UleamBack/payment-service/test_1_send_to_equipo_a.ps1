# TEST 1: NOSOTROS → EQUIPO A
# Probamos enviar un webhook a Equipo A

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  TEST 1: ENVIAR WEBHOOK A EQUIPO A (Nosotros → Ellos)  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "🚀 Enviando webhook de prueba a Equipo A..." -ForegroundColor Yellow
Write-Host "   URL destino: <url-publica-de-equipo-a>/api/reservas`n" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/v1/equipo-a/test-send" -Method POST
    
    Write-Host "✅ ÉXITO - Webhook enviado" -ForegroundColor Green
    Write-Host "`n📋 Respuesta de Equipo A:" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    $response | ConvertTo-Json -Depth 5 | Write-Host -ForegroundColor White
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Gray
    
    if ($response.status -eq "success") {
        Write-Host "🎉 Equipo A recibió el webhook correctamente!" -ForegroundColor Green
        Write-Host "   Status Code: $($response.status_code)" -ForegroundColor White
        
        if ($response.equipo_a_response) {
            Write-Host "`n📥 Respuesta de Equipo A:" -ForegroundColor Cyan
            $response.equipo_a_response | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor White
        }
    } else {
        Write-Host "⚠️  Webhook enviado pero con errores" -ForegroundColor Yellow
        Write-Host "   Status Code: $($response.status_code)" -ForegroundColor White
        Write-Host "   Mensaje: $($response.message)" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "❌ ERROR al enviar webhook" -ForegroundColor Red
    Write-Host "   Detalles: $($_.Exception.Message)" -ForegroundColor Yellow
    
    if ($_.Exception.Message -like "*504*") {
        Write-Host "`n💡 Timeout - Posibles causas:" -ForegroundColor Cyan
        Write-Host "   • Equipo A no tiene ngrok activo" -ForegroundColor Gray
        Write-Host "   • Su servidor no está respondiendo" -ForegroundColor Gray
        Write-Host "   • Firewall bloqueando la conexión" -ForegroundColor Gray
    }
}

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Gray
