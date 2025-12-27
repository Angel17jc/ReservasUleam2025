@echo off
cd /d C:\ReservasUleam2025\UleamBack\auth-service
echo Iniciando Auth Service...
start "Auth Service" cmd /k "npm run start:dev"
timeout /t 10
echo.
echo Probando registro...
curl.exe -X POST http://localhost:9000/api/v1/auth/register -H "Content-Type: application/json" -d "{\"nombre\":\"Carlos\",\"apellido\":\"Ramirez\",\"email\":\"carlos.ramirez@uleam.edu.ec\",\"password\":\"SecurePass123!\",\"tipoUsuarioId\":2,\"telefono\":\"0987654321\"}"
echo.
echo.
echo Probando login con usuario existente...
curl.exe -X POST http://localhost:9000/api/v1/auth/login -H "Content-Type: application/json" -d "{\"email\":\"antonio@gmail.com\",\"password\":\"activo\"}"
echo.
pause
