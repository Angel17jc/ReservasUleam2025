-- Crea las bases de datos por dominio.
-- La base core (reservasuleam) ya la crea el entrypoint via POSTGRES_DB.
CREATE DATABASE ai_service_db OWNER "Reservas_ULEAM" ENCODING 'UTF8' TEMPLATE template0;
CREATE DATABASE payment_service_db OWNER "Reservas_ULEAM" ENCODING 'UTF8' TEMPLATE template0;
