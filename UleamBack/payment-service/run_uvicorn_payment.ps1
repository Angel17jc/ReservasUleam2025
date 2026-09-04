# Start payment-service (uvicorn) ensuring correct env vars
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir
Remove-Item Env:SECRET_KEY -ErrorAction SilentlyContinue
# El secreto se toma del entorno; no se incrusta en el repositorio.
if (-not $env:SECRET_KEY) { throw "Define SECRET_KEY antes de ejecutar este script" }
$env:DATABASE_URL = 'postgresql://postgres:123456789@localhost:5432/payment_service_db'
if (Test-Path .\venv\Scripts\Activate.ps1) {
    . .\venv\Scripts\Activate.ps1
}
Start-Process -NoNewWindow -FilePath python -ArgumentList '-m','uvicorn','app.main:app','--host','0.0.0.0','--port','8001'
Write-Host "Started payment-service (uvicorn) in background."