# Obtener token de admin
$loginBody = @{
    email = "admin@gmail.com"
    password = "123456"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
    $token = $loginResponse.access_token
    Write-Host "Token obtenido exitosamente" -ForegroundColor Green
    
    # Probar GraphQL con el token
    $headers = @{
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $token"
    }
    
    $query = @{
        query = "query { reservas(limit: 3) { id codigo usuario_id espacio_id tipo_evento estado fecha hora_inicio hora_fin titulo } }"
    } | ConvertTo-Json
    
    Write-Host "`nProbando GraphQL con autenticación:" -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri "http://localhost:8080/graphql" -Method Post -Body $query -Headers $headers -ContentType "application/json"
    Write-Host "`nReservas obtenidas:" -ForegroundColor Green
    $response.data.reservas | ForEach-Object {
        Write-Host "  ID: $($_.id) | Usuario: $($_.usuario_id) | Espacio: $($_.espacio_id) | Fecha: $($_.fecha) | Horas: $($_.hora_inicio)-$($_.hora_fin)" -ForegroundColor Cyan
    }
    
    Write-Host "`nJSON completo:" -ForegroundColor Yellow
    $response | ConvertTo-Json -Depth 5
    
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        Write-Host "Detalles: $($reader.ReadToEnd())" -ForegroundColor Red
    }
}
