# Test Auth Service - Commit 2

Write-Host "🧪 Testing Auth Service - Commit 2" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:9000/api/v1"

# Test 1: Register a new user
Write-Host "📝 Test 1: Register new user" -ForegroundColor Yellow
$registerBody = @{
    nombre = "Carlos"
    apellido = "Ramírez"
    email = "carlos.ramirez@uleam.edu.ec"
    password = "SecurePass123!"
    tipoUsuarioId = 2
    telefono = "0987654321"
} | ConvertTo-Json

try {
    $registerResponse = Invoke-RestMethod -Uri "$baseUrl/auth/register" -Method POST -Body $registerBody -ContentType "application/json"
    Write-Host "✅ Register successful!" -ForegroundColor Green
    Write-Host "User ID: $($registerResponse.user.id)" -ForegroundColor Green
    Write-Host "Email: $($registerResponse.user.email)" -ForegroundColor Green
    Write-Host "Access Token: $($registerResponse.accessToken.Substring(0, 30))..." -ForegroundColor Green
    Write-Host "Refresh Token: $($registerResponse.refreshToken.Substring(0, 30))..." -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "❌ Register failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 2: Try to register with same email (should fail)
Write-Host "🔁 Test 2: Try duplicate registration" -ForegroundColor Yellow
try {
    $duplicateResponse = Invoke-RestMethod -Uri "$baseUrl/auth/register" -Method POST -Body $registerBody -ContentType "application/json"
    Write-Host "❌ Should have failed but didn't" -ForegroundColor Red
} catch {
    Write-Host "✅ Correctly rejected duplicate email" -ForegroundColor Green
    Write-Host ""
}

# Test 3: Login with existing user
Write-Host "🔐 Test 3: Login with existing user" -ForegroundColor Yellow
$loginBody = @{
    email = "antonio@gmail.com"
    password = "activo"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
    Write-Host "✅ Login successful!" -ForegroundColor Green
    Write-Host "User: $($loginResponse.user.nombre) $($loginResponse.user.apellido)" -ForegroundColor Green
    Write-Host "Email: $($loginResponse.user.email)" -ForegroundColor Green
    Write-Host "Tipo Usuario: $($loginResponse.user.tipoUsuarioId)" -ForegroundColor Green
    Write-Host "Access Token: $($loginResponse.accessToken.Substring(0, 30))..." -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "❌ Login failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 4: Login with invalid credentials
Write-Host "🚫 Test 4: Login with wrong password" -ForegroundColor Yellow
$wrongLoginBody = @{
    email = "antonio@gmail.com"
    password = "wrongpassword"
} | ConvertTo-Json

try {
    $wrongLoginResponse = Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method POST -Body $wrongLoginBody -ContentType "application/json"
    Write-Host "❌ Should have failed but didn't" -ForegroundColor Red
} catch {
    Write-Host "✅ Correctly rejected invalid credentials" -ForegroundColor Green
    Write-Host ""
}

# Test 5: Login with non-existent user
Write-Host "👻 Test 5: Login with non-existent user" -ForegroundColor Yellow
$nonExistentBody = @{
    email = "noexiste@uleam.edu.ec"
    password = "anypassword"
} | ConvertTo-Json

try {
    $nonExistentResponse = Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method POST -Body $nonExistentBody -ContentType "application/json"
    Write-Host "❌ Should have failed but didn't" -ForegroundColor Red
} catch {
    Write-Host "✅ Correctly rejected non-existent user" -ForegroundColor Green
    Write-Host ""
}

Write-Host "================================" -ForegroundColor Cyan
Write-Host "✅ All tests completed!" -ForegroundColor Green
