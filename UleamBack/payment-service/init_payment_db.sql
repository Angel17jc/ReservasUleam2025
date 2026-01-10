-- Migraciones para Payment Service
-- Base de datos: payment_service_db

-- Tabla: payment_provider_config
CREATE TABLE IF NOT EXISTS payment_provider_config (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    config_json JSONB DEFAULT '{}',
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: payment
CREATE TABLE IF NOT EXISTS payment (
    id SERIAL PRIMARY KEY,
    external_payment_id VARCHAR(255) UNIQUE,
    reserva_id INTEGER,
    usuario_id INTEGER,
    provider_name VARCHAR(50) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    metadata_json JSONB DEFAULT '{}',
    error_message TEXT,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_payment_status CHECK (status IN ('pending', 'completed', 'failed', 'refunded', 'cancelled'))
);

-- Tabla: partner
CREATE TABLE IF NOT EXISTS partner (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    webhook_url VARCHAR(500) NOT NULL,
    shared_secret VARCHAR(255) NOT NULL,
    eventos_suscritos JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    descripcion TEXT,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: partner_webhook_log
CREATE TABLE IF NOT EXISTS partner_webhook_log (
    id SERIAL PRIMARY KEY,
    partner_id INTEGER REFERENCES partner(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    payload_json JSONB NOT NULL,
    response_status INTEGER,
    response_body TEXT,
    signature_valid BOOLEAN,
    error_message TEXT,
    direction VARCHAR(20) NOT NULL DEFAULT 'outgoing',
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_direction CHECK (direction IN ('outgoing', 'incoming'))
);

-- Tabla: webhook_event
CREATE TABLE IF NOT EXISTS webhook_event (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(100) NOT NULL,
    payload_json JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: alembic_version (para compatibilidad con Alembic)
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) PRIMARY KEY
);

-- Insertar versión inicial
INSERT INTO alembic_version (version_num) VALUES ('initial') ON CONFLICT DO NOTHING;

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_payment_reserva ON payment(reserva_id);
CREATE INDEX IF NOT EXISTS idx_payment_usuario ON payment(usuario_id);
CREATE INDEX IF NOT EXISTS idx_payment_status ON payment(status);
CREATE INDEX IF NOT EXISTS idx_payment_provider ON payment(provider_name);
CREATE INDEX IF NOT EXISTS idx_payment_external_id ON payment(external_payment_id);

CREATE INDEX IF NOT EXISTS idx_partner_webhook_log_partner ON partner_webhook_log(partner_id);
CREATE INDEX IF NOT EXISTS idx_partner_webhook_log_event ON partner_webhook_log(event_type);
CREATE INDEX IF NOT EXISTS idx_partner_webhook_log_direction ON partner_webhook_log(direction);

CREATE INDEX IF NOT EXISTS idx_webhook_event_type ON webhook_event(event_type);
CREATE INDEX IF NOT EXISTS idx_webhook_event_source ON webhook_event(source);
CREATE INDEX IF NOT EXISTS idx_webhook_event_processed ON webhook_event(processed);

-- Triggers para actualización automática de timestamps
CREATE OR REPLACE FUNCTION update_timestamp_payment()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_en = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_payment_provider_config_timestamp 
BEFORE UPDATE ON payment_provider_config 
FOR EACH ROW EXECUTE FUNCTION update_timestamp_payment();

CREATE TRIGGER update_payment_timestamp 
BEFORE UPDATE ON payment 
FOR EACH ROW EXECUTE FUNCTION update_timestamp_payment();

CREATE TRIGGER update_partner_timestamp 
BEFORE UPDATE ON partner 
FOR EACH ROW EXECUTE FUNCTION update_timestamp_payment();

CREATE TRIGGER update_webhook_event_timestamp 
BEFORE UPDATE ON webhook_event 
FOR EACH ROW EXECUTE FUNCTION update_timestamp_payment();

-- Datos iniciales: Payment Providers
INSERT INTO payment_provider_config (name, is_active, config_json) VALUES
('mock', TRUE, '{"description": "Mock provider for testing"}'),
('stripe', FALSE, '{"description": "Stripe payment provider"}'),
('mercadopago', FALSE, '{"description": "MercadoPago payment provider"}')
ON CONFLICT (name) DO NOTHING;

-- Verificación
SELECT 'Payment Service database initialized successfully' AS status;
SELECT COUNT(*) as total_tables FROM information_schema.tables WHERE table_schema = 'public';
SELECT name, is_active FROM payment_provider_config;
