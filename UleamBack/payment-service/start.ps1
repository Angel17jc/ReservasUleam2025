# PowerShell script para iniciar el Payment Service
# Uso: .\start.ps1

Write-Host "🚀 Iniciando Payment Service..." -ForegroundColor Cyan

# Verificar que existe el archivo .env
if (-Not (Test-Path ".env")) {
    Write-Host "⚠️  Archivo .env no encontrado. Copiando desde .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Archivo .env creado. Por favor, configúralo con tus credenciales." -ForegroundColor Green
    Write-Host ""
}

# Verificar node_modules
if (-Not (Test-Path "node_modules")) {
    Write-Host "📦 Instalando dependencias..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error al instalar dependencias" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Dependencias instaladas" -ForegroundColor Green
}

# Iniciar en modo desarrollo
Write-Host "🔥 Iniciando en modo desarrollo..." -ForegroundColor Cyan
npm run start:dev
