# Script para consultar webhooks en la base de datos
# Muestra los últimos webhooks enviados y recibidos

# Configuración
$env:PGPASSWORD = "postgres123"
$PGUSER = "postgres"
$PGDATABASE = "uleam_payment"

Write-Host "`n================================================================"
Write-Host "📊 CONSULTA DE WEBHOOKS - INTEGRACIÓN EQUIPO A ↔ EQUIPO B"
Write-Host "================================================================`n"

# 1. Webhooks recibidos de Equipo A
Write-Host "📥 WEBHOOKS RECIBIDOS (de Equipo A):`n"
$query1 = @"
SELECT 
    id,
    event_type,
    status,
    LEFT(payload::text, 100) as payload_preview,
    created_at
FROM webhook_event 
WHERE partner_id = 1 
ORDER BY created_at DESC 
LIMIT 5;
"@

psql -U $PGUSER -d $PGDATABASE -c $query1

# 2. Logs de webhooks (enviados y recibidos)
Write-Host "`n`n📤 LOGS DE WEBHOOKS (enviados a Equipo A):`n"
$query2 = @"
SELECT 
    id,
    direction,
    event_type,
    status_code,
    success,
    LEFT(request_payload::text, 80) as request_preview,
    created_at
FROM partner_webhook_log 
WHERE partner_id = 1 
ORDER BY created_at DESC 
LIMIT 5;
"@

psql -U $PGUSER -d $PGDATABASE -c $query2

# 3. Estadísticas generales
Write-Host "`n`n📊 ESTADÍSTICAS GENERALES:`n"
$query3 = @"
SELECT 
    (SELECT COUNT(*) FROM webhook_event WHERE partner_id = 1) as total_recibidos,
    (SELECT COUNT(*) FROM webhook_event WHERE partner_id = 1 AND status = 'processed') as recibidos_exitosos,
    (SELECT COUNT(*) FROM partner_webhook_log WHERE partner_id = 1 AND direction = 'outbound') as total_enviados,
    (SELECT COUNT(*) FROM partner_webhook_log WHERE partner_id = 1 AND direction = 'outbound' AND success = true) as enviados_exitosos;
"@

psql -U $PGUSER -d $PGDATABASE -c $query3

Write-Host "`n================================================================"
Write-Host "✅ Consulta completada"
Write-Host "================================================================`n"
