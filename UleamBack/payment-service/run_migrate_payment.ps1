# Run migrations for payment-service against payment_service_db
# Usage: Open PowerShell in this folder and run: .\run_migrate_payment.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

# Set DB and secret for this session
$env:DATABASE_URL = "postgresql://postgres:123456789@localhost:5432/payment_service_db"
Remove-Item Env:SECRET_KEY -ErrorAction SilentlyContinue
$env:SECRET_KEY = "mi-secreto-auth-service-super-seguro-2025"

# Activate venv if exists
if (Test-Path .\venv\Scripts\Activate.ps1) {
    Write-Host "Activating venv..."
    . .\venv\Scripts\Activate.ps1
} else {
    Write-Host "No venv found in ./venv (continuing with current Python)"
}

Write-Host "DATABASE_URL = $env:DATABASE_URL"

# Run alembic upgrade
Write-Host "Running alembic upgrade head..."
alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "alembic failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

# Show resulting tables
Write-Host "Inspecting public tables..."
$pyfile = Join-Path $PWD "show_db_temp.py"
@'
import psycopg2
from app.config import settings
conn = psycopg2.connect(settings.DATABASE_URL)
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
print('tables:', [r[0] for r in cur.fetchall()])
try:
    cur.execute("SELECT version_num FROM alembic_version;")
    print('alembic_version:', [r[0] for r in cur.fetchall()])
except Exception as e:
    print('alembic_version: error', e)
cur.close()
conn.close()
'@ | Out-File -FilePath $pyfile -Encoding utf8

python $pyfile
Remove-Item $pyfile -ErrorAction SilentlyContinue

Write-Host "Done. If tables exist, payment-service is now using payment_service_db."