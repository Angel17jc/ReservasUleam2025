-- Añade la columna asistentes_estimada a la tabla reserva si no existe
ALTER TABLE reserva
ADD COLUMN IF NOT EXISTS asistentes_estimada INTEGER;

-- Opcional: si quieres llenar con 0 para filas existentes (descomenta):
-- UPDATE reserva SET asistentes_estimada = 0 WHERE asistentes_estimada IS NULL;

-- Para ejecutar:
-- psql -U postgres -d reservasuleam -f database/patches/001_add_asistentes_estimada.sql
