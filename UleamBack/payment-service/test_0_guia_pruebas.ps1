# GUÍA RÁPIDA DE PRUEBAS - INTEGRACIÓN B2B CON EQUIPO A

Write-Host "`n╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  GUÍA DE PRUEBAS - INTEGRACIÓN BIDIRECCIONAL CON EQUIPO A        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "📋 SERVICIOS ACTIVOS:" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

# Verificar payment-service
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8001/api/v1/health" -TimeoutSec 2
    Write-Host "✅ payment-service: ONLINE (puerto 8001)" -ForegroundColor Green
} catch {
    Write-Host "❌ payment-service: OFFLINE (puerto 8001)" -ForegroundColor Red
    Write-Host "   → Ejecutar: uvicorn app.main:app --port 8001" -ForegroundColor Yellow
}

# Verificar ngrok
$ngrokRunning = Get-Process -Name ngrok -ErrorAction SilentlyContinue
if ($ngrokRunning) {
    Write-Host "✅ ngrok: ONLINE" -ForegroundColor Green
    Write-Host "   URL: <nuestra-url-publica>" -ForegroundColor Gray
} else {
    Write-Host "❌ ngrok: OFFLINE" -ForegroundColor Red
    Write-Host "   → Ejecutar: ngrok http 8001" -ForegroundColor Yellow
}

Write-Host "`n🌐 ENDPOINTS CONFIGURADOS:" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

Write-Host "`n📤 EQUIPO A (Ellos):" -ForegroundColor Cyan
Write-Host "   Webhook:      <url-publica-de-equipo-a>/api/reservas" -ForegroundColor White
Write-Host "   Health:       <url-publica-de-equipo-a>/health" -ForegroundColor White
Write-Host "   Status:       <url-publica-de-equipo-a>/api/integracion/status" -ForegroundColor White

Write-Host "`n📥 EQUIPO B (Nosotros):" -ForegroundColor Cyan
Write-Host "   Webhook:      <nuestra-url-publica>/api/v1/equipo-a/webhook" -ForegroundColor White
Write-Host "   Status:       <nuestra-url-publica>/api/v1/equipo-a/status" -ForegroundColor White
Write-Host "   Health:       <nuestra-url-publica>/api/v1/health" -ForegroundColor White
Write-Host "   Docs:         <nuestra-url-publica>/api/v1/docs" -ForegroundColor White

Write-Host "`n🧪 SCRIPTS DE PRUEBA DISPONIBLES:" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

Write-Host "`n1️⃣  TEST 1: Enviar a Equipo A (Nosotros → Ellos)" -ForegroundColor Cyan
Write-Host "   Archivo: test_1_send_to_equipo_a.ps1" -ForegroundColor Gray
Write-Host "   Comando: .\test_1_send_to_equipo_a.ps1" -ForegroundColor White
Write-Host "   Descripción: Envía webhook de prueba 'booking.confirmed' a Equipo A" -ForegroundColor Gray

Write-Host "`n2️⃣  TEST 2: Recibir de Equipo A (Ellos → Nosotros)" -ForegroundColor Cyan
Write-Host "   Archivo: test_2_receive_from_equipo_a.ps1" -ForegroundColor Gray
Write-Host "   Comando: .\test_2_receive_from_equipo_a.ps1" -ForegroundColor White
Write-Host "   Descripción: Simula recepción de webhook 'tour.purchased' de Equipo A" -ForegroundColor Gray

Write-Host "`n🔐 AUTENTICACIÓN:" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "   Método: HMAC-SHA256" -ForegroundColor White
Write-Host "   Header: X-Signature" -ForegroundColor White
Write-Host "   Secret: (definido en la variable de entorno EQUIPO_A_SHARED_SECRET)" -ForegroundColor Magenta

Write-Host "`n📊 EVENTOS CONFIGURADOS:" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

Write-Host "`n📥 Recibimos (de Equipo A):" -ForegroundColor Cyan
Write-Host "   • tour.purchased" -ForegroundColor White
Write-Host "   • booking.confirmed" -ForegroundColor White
Write-Host "   • recommendation.created" -ForegroundColor White

Write-Host "`n📤 Enviamos (a Equipo A):" -ForegroundColor Cyan
Write-Host "   • booking.confirmed" -ForegroundColor White
Write-Host "   • payment.success" -ForegroundColor White
Write-Host "   • service.activated" -ForegroundColor White

Write-Host "`n🚀 ORDEN RECOMENDADO DE EJECUCIÓN:" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

Write-Host "`n1. Verificar servicios:" -ForegroundColor Cyan
Write-Host "   .\test_0_verify_services.ps1" -ForegroundColor White

Write-Host "`n2. Probar envío (Nosotros → Equipo A):" -ForegroundColor Cyan
Write-Host "   .\test_1_send_to_equipo_a.ps1" -ForegroundColor White
Write-Host "   👉 Coordinar con Equipo A para verificar recepción" -ForegroundColor Yellow

Write-Host "`n3. Probar recepción (Equipo A → Nosotros):" -ForegroundColor Cyan
Write-Host "   .\test_2_receive_from_equipo_a.ps1" -ForegroundColor White
Write-Host "   👉 También pueden usar: <nuestra-url-publica>/api/v1/docs" -ForegroundColor Yellow

Write-Host "`n4. Prueba completa bidireccional:" -ForegroundColor Cyan
Write-Host "   Ejecutar ambos tests y verificar logs en ambos lados" -ForegroundColor White

Write-Host "`n💡 TIPS:" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "   • Ver logs del servidor payment-service para debugging" -ForegroundColor White
Write-Host "   • Usar Swagger UI para probar endpoints manualmente" -ForegroundColor White
Write-Host "   • Si hay timeout, verificar que ngrok de Equipo A esté activo" -ForegroundColor White
Write-Host "   • Si hay error 401, verificar firma HMAC" -ForegroundColor White

Write-Host "`n📞 CONTACTO EQUIPO A:" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "   Email: equipoa@uleam.edu.ec" -ForegroundColor White
Write-Host "   Coordinar pruebas en simultáneo para mejor debugging" -ForegroundColor Gray

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Gray

Write-Host "🎯 ¿Listo para empezar? Ejecuta: .\test_1_send_to_equipo_a.ps1`n" -ForegroundColor Green
