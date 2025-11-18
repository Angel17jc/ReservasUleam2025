# Script para probar GraphQL directamente
$headers = @{
    "Content-Type" = "application/json"
    # Token de admin - necesitas obtener uno válido primero
}

$query = @{
    query = "query { reservas(limit: 3) { id codigo usuario_id espacio_id tipo_evento estado fecha hora_inicio hora_fin titulo } }"
} | ConvertTo-Json

Write-Host "Probando GraphQL sin autenticación:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8080/graphql" -Method Post -Body $query -Headers $headers
    Write-Host "Respuesta:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "StatusCode:" $_.Exception.Response.StatusCode.value__
}
