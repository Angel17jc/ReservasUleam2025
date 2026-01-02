# Script SQL para verificar la tabla payments
# Ejecutar: psql -U postgres -d reservasuleam -f verify_database.sql

\echo '🔍 Verificando tabla payments...'
\echo ''

-- Verificar que existe la tabla
SELECT 
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'public'
    AND table_name = 'payments';

\echo ''
\echo '📊 Estructura de la tabla:'
\echo ''

-- Mostrar columnas
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'payments'
ORDER BY ordinal_position;

\echo ''
\echo '📑 Índices:'
\echo ''

-- Mostrar índices
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'payments';

\echo ''
\echo '📈 Datos actuales:'
\echo ''

-- Mostrar registros
SELECT 
    id,
    reserva_id,
    usuario_id,
    provider,
    LEFT(transaction_id, 20) || '...' as transaction_id,
    amount,
    currency,
    status,
    created_at
FROM payments
ORDER BY created_at DESC
LIMIT 10;

\echo ''
\echo '✅ Verificación completada'
