-- Script SQL para crear tabla refresh_token y agregar columnas de seguridad a usuario
-- Se ejecuta directamente con el usuario postgres

-- Crear tabla refresh_token
CREATE TABLE IF NOT EXISTS refresh_token (
    id SERIAL PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    usuario_id INTEGER NOT NULL,
    expira_en TIMESTAMP WITH TIME ZONE NOT NULL,
    revocado BOOLEAN DEFAULT FALSE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_refresh_token_usuario 
        FOREIGN KEY (usuario_id) 
        REFERENCES usuario(id) 
        ON DELETE CASCADE
);

-- Crear índices
CREATE UNIQUE INDEX IF NOT EXISTS idx_refresh_token_token ON refresh_token(token);
CREATE INDEX IF NOT EXISTS idx_refresh_token_user_revoked ON refresh_token(usuario_id, revocado);

-- Agregar columnas de seguridad a tabla usuario si no existen
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'usuario' 
                   AND column_name = 'ultimo_login') THEN
        ALTER TABLE usuario ADD COLUMN ultimo_login TIMESTAMP WITH TIME ZONE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'usuario' 
                   AND column_name = 'intentos_fallidos_login') THEN
        ALTER TABLE usuario ADD COLUMN intentos_fallidos_login INTEGER DEFAULT 0;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'usuario' 
                   AND column_name = 'bloqueado_hasta') THEN
        ALTER TABLE usuario ADD COLUMN bloqueado_hasta TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- Dar permisos al usuario Reservas_ULEAM
GRANT ALL PRIVILEGES ON TABLE refresh_token TO "Reservas_ULEAM";
GRANT USAGE, SELECT ON SEQUENCE refresh_token_id_seq TO "Reservas_ULEAM";

-- Verificación
SELECT 'Tabla refresh_token creada exitosamente' AS status;
SELECT COUNT(*) as total_refresh_tokens FROM refresh_token;
