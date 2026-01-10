# Script para probar REST login con detalle de errores
Write-Host "Probando REST Login con detalle..." -ForegroundColor Yellow

$loginBody = @{
    email = "admin@uleam.edu.ec"
    password = "password123"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body $loginBody
    
    Write-Host "`n✅ Login exitoso!" -ForegroundColor Green
    $responseObj = $response.Content | ConvertFrom-Json
    $responseObj | ConvertTo-Json -Depth 10
    
} catch {
    Write-Host "`n❌ Error:" -ForegroundColor Red
    Write-Host "StatusCode:" $_.Exception.Response.StatusCode.value__
    Write-Host "StatusDescription:" $_.Exception.Response.StatusDescription
    
    if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
        Write-Host "`nDetalle del error:"
        $_.ErrorDetails.Message
    }
    
    # Try to read response body
    try {
        $result = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($result)
        $responseBody = $reader.ReadToEnd()
        Write-Host "`nRespuesta del servidor:"
        $responseBody
    } catch {}
}
