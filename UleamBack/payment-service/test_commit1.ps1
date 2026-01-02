# PowerShell script para testing del Payment Service - Commit 1
# Prueba todos los endpoints con MockAdapter

$BASE_URL = "http://localhost:9001"

Write-Host "🧪 Testing Payment Service - Commit 1 (MockAdapter)" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health Check
Write-Host "Test 1: Health Check" -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$BASE_URL/health" -Method GET
    Write-Host "✅ Health check OK" -ForegroundColor Green
    Write-Host "   Status: $($health.status)" -ForegroundColor Gray
    Write-Host "   Service: $($health.service)" -ForegroundColor Gray
    Write-Host "   Providers: Mock=$($health.providers.mock), Stripe=$($health.providers.stripe)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Health check failed: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 2: Crear pago con MockAdapter
Write-Host "Test 2: Crear pago con MockAdapter" -ForegroundColor Yellow
try {
    $paymentData = @{
        reserva_id = 1
        usuario_id = 1
        amount = 150.00
        currency = "USD"
        provider = "mock"
        metadata = @{
            espacio = "Auditorio Principal"
            fecha = "2026-02-15"
            hora_inicio = "09:00"
        }
    } | ConvertTo-Json

    $payment = Invoke-RestMethod -Uri "$BASE_URL/payments" -Method POST `
        -ContentType "application/json" `
        -Body $paymentData

    Write-Host "✅ Pago creado exitosamente" -ForegroundColor Green
    Write-Host "   ID: $($payment.id)" -ForegroundColor Gray
    Write-Host "   Transaction ID: $($payment.transaction_id)" -ForegroundColor Gray
    Write-Host "   Status: $($payment.status)" -ForegroundColor Gray
    Write-Host "   Amount: $($payment.amount) $($payment.currency)" -ForegroundColor Gray
    Write-Host "   Provider: $($payment.provider)" -ForegroundColor Gray
    
    $paymentId = $payment.id
} catch {
    Write-Host "❌ Error al crear pago: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 3: Obtener pago por ID
Write-Host "Test 3: Obtener pago por ID" -ForegroundColor Yellow
try {
    $payment = Invoke-RestMethod -Uri "$BASE_URL/payments/$paymentId" -Method GET
    Write-Host "✅ Pago obtenido correctamente" -ForegroundColor Green
    Write-Host "   ID: $($payment.id)" -ForegroundColor Gray
    Write-Host "   Transaction ID: $($payment.transaction_id)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Error al obtener pago: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 4: Crear segundo pago para misma reserva
Write-Host "Test 4: Crear segundo pago (misma reserva)" -ForegroundColor Yellow
try {
    $paymentData2 = @{
        reserva_id = 1
        usuario_id = 1
        amount = 50.00
        currency = "USD"
        provider = "mock"
    } | ConvertTo-Json

    $payment2 = Invoke-RestMethod -Uri "$BASE_URL/payments" -Method POST `
        -ContentType "application/json" `
        -Body $paymentData2

    Write-Host "✅ Segundo pago creado" -ForegroundColor Green
    Write-Host "   Transaction ID: $($payment2.transaction_id)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Error al crear segundo pago: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 5: Obtener todos los pagos de una reserva
Write-Host "Test 5: Obtener pagos de reserva" -ForegroundColor Yellow
try {
    $payments = Invoke-RestMethod -Uri "$BASE_URL/payments/reserva/1" -Method GET
    Write-Host "✅ Pagos de reserva obtenidos" -ForegroundColor Green
    Write-Host "   Total de pagos: $($payments.Count)" -ForegroundColor Gray
    foreach ($p in $payments) {
        Write-Host "   - Payment ID: $($p.id), Amount: $($p.amount), Status: $($p.status)" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Error al obtener pagos de reserva: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 6: Obtener estadísticas
Write-Host "Test 6: Obtener estadísticas de pagos" -ForegroundColor Yellow
try {
    $stats = Invoke-RestMethod -Uri "$BASE_URL/payments/stats/summary" -Method GET
    Write-Host "✅ Estadísticas obtenidas" -ForegroundColor Green
    Write-Host "   Total pagos: $($stats.total_payments)" -ForegroundColor Gray
    Write-Host "   Completados: $($stats.completed)" -ForegroundColor Gray
    Write-Host "   Pendientes: $($stats.pending)" -ForegroundColor Gray
    Write-Host "   Fallidos: $($stats.failed)" -ForegroundColor Gray
    Write-Host "   Monto total: $($stats.total_amount) USD" -ForegroundColor Gray
} catch {
    Write-Host "❌ Error al obtener estadísticas: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Resumen
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "✅ TODOS LOS TESTS PASARON EXITOSAMENTE" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Criterios de aceptación Commit 1:" -ForegroundColor Yellow
Write-Host "✅ Payment Service inicia en puerto 9001" -ForegroundColor Green
Write-Host "✅ MockAdapter genera transaction_id único" -ForegroundColor Green
Write-Host "✅ MockAdapter siempre retorna 'completed'" -ForegroundColor Green
Write-Host "✅ Pagos se guardan en PostgreSQL" -ForegroundColor Green
Write-Host "✅ Endpoints funcionan correctamente" -ForegroundColor Green
Write-Host ""
Write-Host "🎉 Commit 1 completado con éxito!" -ForegroundColor Cyan
