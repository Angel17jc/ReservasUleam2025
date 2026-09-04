-- Permisos sobre el esquema core una vez creadas las tablas.
GRANT USAGE ON SCHEMA public TO "Reservas_ULEAM";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "Reservas_ULEAM";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "Reservas_ULEAM";

\connect ai_service_db
GRANT ALL ON SCHEMA public TO "Reservas_ULEAM";

\connect payment_service_db
GRANT ALL ON SCHEMA public TO "Reservas_ULEAM";
