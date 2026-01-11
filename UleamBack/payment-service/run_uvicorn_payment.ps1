# Start payment-service (uvicorn) ensuring correct env vars
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir
Remove-Item Env:SECRET_KEY -ErrorAction SilentlyContinue
$env:SECRET_KEY = 'mi-secreto-auth-service-super-seguro-2025'
$env:DATABASE_URL = 'postgresql://postgres:123456789@localhost:5432/payment_service_db'
if (Test-Path .\venv\Scripts\Activate.ps1) {
    . .\venv\Scripts\Activate.ps1
}
Start-Process -NoNewWindow -FilePath python -ArgumentList '-m','uvicorn','app.main:app','--host','0.0.0.0','--port','8001'
Write-Host "Started payment-service (uvicorn) in background."