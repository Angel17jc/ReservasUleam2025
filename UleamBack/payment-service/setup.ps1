# ================================================
# Payment Service - Setup Script
# Automatiza la instalación y configuración inicial
# ================================================

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  ULEAM Payment Service - Setup Script" -ForegroundColor Cyan
Write-Host "  Pilar 2 - Commit 1: Setup Inicial" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Variables
$VENV_DIR = "venv"
$DB_NAME = "payment_service_db"
$DB_USER = "postgres"
$SERVICE_PORT = 8001

# Función para verificar si un comando existe
function Test-Command {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Verificar Python
Write-Host "[->] Verificando Python..." -ForegroundColor Yellow
if (Test-Command python) {
    $pythonVersion = python --version
    Write-Host "  [OK] Python encontrado: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Python no encontrado. Instala Python 3.9+" -ForegroundColor Red
    exit 1
}

# Verificar PostgreSQL
Write-Host ""
Write-Host "[->] Verificando PostgreSQL..." -ForegroundColor Yellow
if (Test-Command psql) {
    Write-Host "  [OK] PostgreSQL encontrado" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] PostgreSQL no encontrado. Instala PostgreSQL 13+" -ForegroundColor Red
    exit 1
}

# Crear entorno virtual
Write-Host ""
Write-Host "[->] Creando entorno virtual..." -ForegroundColor Yellow
if (Test-Path $VENV_DIR) {
    Write-Host "  [INFO] El entorno virtual ya existe. Saltando..." -ForegroundColor Yellow
} else {
    python -m venv $VENV_DIR
    if ($?) {
        Write-Host "  [OK] Entorno virtual creado" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Error al crear entorno virtual" -ForegroundColor Red
        exit 1
    }
}

# Activar entorno virtual
Write-Host ""
Write-Host "[->] Activando entorno virtual..." -ForegroundColor Yellow
& ".\$VENV_DIR\Scripts\Activate.ps1"

# Instalar dependencias
Write-Host ""
Write-Host "[->] Instalando dependencias..." -ForegroundColor Yellow
pip install --upgrade pip | Out-Null
pip install -r requirements.txt
if ($?) {
    Write-Host "  [OK] Dependencias instaladas" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Error al instalar dependencias" -ForegroundColor Red
    exit 1
}

# Crear archivo .env si no existe
Write-Host ""
Write-Host "[->] Configurando archivo .env..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  [INFO] .env ya existe. Saltando..." -ForegroundColor Yellow
} else {
    Copy-Item ".env.example" ".env"
    Write-Host "  [OK] .env creado desde .env.example" -ForegroundColor Green
    Write-Host "  [INFO] Edita .env con tus configuraciones" -ForegroundColor Cyan
}

# Crear base de datos
Write-Host ""
Write-Host "[->] Creando base de datos '$DB_NAME'..." -ForegroundColor Yellow
$dbExists = psql -U $DB_USER -lqt | Select-String -Pattern $DB_NAME -Quiet
if ($dbExists) {
    Write-Host "  [INFO] La base de datos ya existe. Saltando..." -ForegroundColor Yellow
} else {
    $createDbCmd = "CREATE DATABASE $DB_NAME;"
    $result = psql -U $DB_USER -c $createDbCmd 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Base de datos creada" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Error al crear base de datos" -ForegroundColor Red
        Write-Host "  [INFO] Crea manualmente: psql -U $DB_USER -c '$createDbCmd'" -ForegroundColor Cyan
    }
}

# Ejecutar migraciones
Write-Host ""
Write-Host "[->] Ejecutando migraciones de Alembic..." -ForegroundColor Yellow
alembic upgrade head
if ($?) {
    Write-Host "  [OK] Migraciones aplicadas" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Error al aplicar migraciones" -ForegroundColor Red
    exit 1
}

# Verificar tablas
Write-Host ""
Write-Host "[->] Verificando tablas creadas..." -ForegroundColor Yellow
$tables = psql -U $DB_USER -d $DB_NAME -c "\dt" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Tablas verificadas:" -ForegroundColor Green
    $tables | Select-String -Pattern "payment|partner|webhook" | ForEach-Object {
        Write-Host "    - $_" -ForegroundColor Gray
    }
} else {
    Write-Host "  [INFO] No se pudieron verificar las tablas" -ForegroundColor Yellow
}

# Resumen final
Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  [OK] Setup completado exitosamente!" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para iniciar el servicio:" -ForegroundColor White
Write-Host "  1. Asegurate de que el entorno virtual este activo:" -ForegroundColor Gray
Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. Ejecuta el servidor:" -ForegroundColor Gray
Write-Host "     uvicorn app.main:app --reload --port $SERVICE_PORT" -ForegroundColor Yellow
Write-Host ""
Write-Host "Documentacion API:" -ForegroundColor White
Write-Host "  http://localhost:$SERVICE_PORT/api/v1/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Health Check:" -ForegroundColor White
Write-Host "  http://localhost:$SERVICE_PORT/api/v1/health" -ForegroundColor Cyan
Write-Host ""
