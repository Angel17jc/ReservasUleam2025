# Script para ejecutar la inicializacion de la base de datos
# Asegurate de que PostgreSQL este corriendo y la base de datos reservasuleam exista

$pgPath = "C:\Program Files\PostgreSQL\17\bin\psql.exe"

# Verificar si psql existe en la ruta por defecto
if (Test-Path $pgPath) {
    Write-Host "[OK] PostgreSQL encontrado en: $pgPath" -ForegroundColor Green
    
    # Pedir la contraseña de forma segura
    Write-Host ""
    Write-Host "[INFO] Ingrese la contrasena de PostgreSQL (usuario: postgres):" -ForegroundColor Yellow
    $password = Read-Host -AsSecureString
    $env:PGPASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($password))
    
    Write-Host "[...] Ejecutando script de inicializacion..." -ForegroundColor Yellow
    Write-Host ""
    
    # Ejecutar el script
    & $pgPath -h localhost -U postgres -d reservasuleam -f "init.sql"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Base de datos inicializada correctamente!" -ForegroundColor Green
        Write-Host ""
        Write-Host "[INFO] Tablas creadas:" -ForegroundColor Cyan
        Write-Host "   - tipo_usuario" -ForegroundColor White
        Write-Host "   - usuario" -ForegroundColor White
        Write-Host "   - categoria_espacio" -ForegroundColor White
        Write-Host "   - referencia" -ForegroundColor White
        Write-Host "   - espacio" -ForegroundColor White
        Write-Host "   - caracteristica_espacio" -ForegroundColor White
        Write-Host "   - disponibilidad_espacio" -ForegroundColor White
        Write-Host "   - tipo_evento" -ForegroundColor White
        Write-Host "   - estado_reserva" -ForegroundColor White
        Write-Host "   - reserva" -ForegroundColor White
        Write-Host "   - notificacion" -ForegroundColor White
        Write-Host ""
        Write-Host "[INFO] Usuarios de prueba (password: password123):" -ForegroundColor Cyan
        Write-Host "   - admin@uleam.edu.ec (Administrador)" -ForegroundColor White
        Write-Host "   - profesor1@uleam.edu.ec (Profesor)" -ForegroundColor White
        Write-Host "   - estudiante1@uleam.edu.ec (Estudiante)" -ForegroundColor White
        Write-Host "   - admin2@uleam.edu.ec (Personal Administrativo)" -ForegroundColor White
    } else {
        Write-Host "[ERROR] Error al ejecutar el script" -ForegroundColor Red
    }
    
    # Limpiar variable de entorno
    Remove-Item Env:\PGPASSWORD
} else {
    Write-Host "[ERROR] PostgreSQL no encontrado en: $pgPath" -ForegroundColor Red
    Write-Host "[INFO] Por favor, ejecuta el script manualmente en pgAdmin:" -ForegroundColor Yellow
    Write-Host "1. Abre pgAdmin 4" -ForegroundColor White
    Write-Host "2. Conecta a la base de datos reservasuleam" -ForegroundColor White
    Write-Host "3. Abre el Query Tool (Tools > Query Tool)" -ForegroundColor White
    Write-Host "4. Carga y ejecuta el archivo init.sql" -ForegroundColor White
}
