# Script para ejecutar n8n localmente en Windows (PowerShell)
# Navega a la carpeta del proyecto y ejecuta n8n con datos persistentes

$n8nDataPath = "$PSScriptRoot\n8n-data"
$workflowsPath = "$PSScriptRoot\n8n-workflows"

Write-Host "=== n8n Local - ReservasULEAM ===" -ForegroundColor Cyan
Write-Host "Data folder: $n8nDataPath" -ForegroundColor Green
Write-Host "Workflows folder: $workflowsPath" -ForegroundColor Green
Write-Host ""
Write-Host "Starting n8n on http://localhost:5678..." -ForegroundColor Yellow
Write-Host ""

$env:N8N_USER_FOLDER = $n8nDataPath
$env:N8N_HOST = "localhost"
$env:N8N_PORT = "5678"
$env:NODE_ENV = "development"

n8n start
