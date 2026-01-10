-- Script para crear rol y base de datos para Reservas ULEAM
-- Ejecutar como superusuario (por ejemplo, usuario "postgres").

-- Crear rol/usuario (ajusta la contraseña si quieres otra)
CREATE ROLE "Reservas_ULEAM" WITH LOGIN PASSWORD '123456';

-- Crear base de datos con propietario
CREATE DATABASE reservasuleam
    OWNER "Reservas_ULEAM"
    ENCODING 'UTF8'
    LC_COLLATE = 'C'
    LC_CTYPE = 'C'
    TEMPLATE template0;

-- Otorgar privilegios adicionales (por si acaso)
GRANT ALL PRIVILEGES ON DATABASE reservasuleam TO "Reservas_ULEAM";

-- Nota: después de crear la base, ejecutar el script de tablas de autenticación:
-- psql -U postgres -d reservasuleam -f UleamBack/auth-service/create_auth_tables.sql

-- Fin del script
