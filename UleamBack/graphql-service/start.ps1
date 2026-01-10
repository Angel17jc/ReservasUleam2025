# Script para iniciar el servicio GraphQL con variables de entorno
Write-Host "[INFO] Iniciando GraphQL Service..." -ForegroundColor Cyan

# Configurar variables de entorno
$env:DATABASE_URL = "postgresql://postgres:admin@localhost:5432/reservasuleam?sslmode=disable"
$env:SECRET_KEY = "tu_clave_secreta_muy_segura_cambiar_en_produccion_12345"
$env:JWT_SECRET = "tu_clave_secreta_muy_segura_cambiar_en_produccion_12345"
$env:WEBSOCKET_SERVICE_URL = "http://localhost:3001"
$env:PORT = "8080"

Write-Host "[OK] Variables de entorno configuradas" -ForegroundColor Green
Write-Host ""
Write-Host "[...] Ejecutando: go run ./cmd/server" -ForegroundColor Yellow
Write-Host "[INFO] Servicio escuchando en: http://localhost:8080/graphql" -ForegroundColor Cyan
Write-Host ""

# Ejecutar el servidor
go run ./cmd/server
