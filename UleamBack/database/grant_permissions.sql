-- Otorgar permisos al usuario Reservas_ULEAM
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "Reservas_ULEAM";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "Reservas_ULEAM";
GRANT USAGE ON SCHEMA public TO "Reservas_ULEAM";

-- Verificación
SELECT 'Permisos otorgados exitosamente a Reservas_ULEAM' AS status;
