-- ============================================
-- AI SERVICE DATABASE SCHEMA
-- ============================================
-- Database: ai_service_db
-- Purpose: Almacenar conversaciones, mensajes y ejecuciones de tools del chatbot
-- Author: Tech Lead - ReservasULEAM
-- Date: 22 de enero de 2026
-- ============================================

-- Crear base de datos (ejecutar como usuario postgres)
-- CREATE DATABASE ai_service_db OWNER Reservas_ULEAM;

-- Conectar a la base de datos
\c ai_service_db;

-- ============================================
-- TABLA: conversation
-- Almacena las conversaciones de los usuarios
-- ============================================
CREATE TABLE IF NOT EXISTS conversation (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    title VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    -- FK a tabla usuario del servicio principal (sin constraint por ser multi-DB)
);

-- Índices para búsquedas eficientes
CREATE INDEX idx_conversation_usuario_id ON conversation(usuario_id);
CREATE INDEX idx_conversation_created_at ON conversation(created_at DESC);

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_conversation_timestamp
BEFORE UPDATE ON conversation
FOR EACH ROW
EXECUTE FUNCTION update_conversation_timestamp();

-- ============================================
-- TABLA: message
-- Almacena los mensajes de cada conversación
-- ============================================
CREATE TABLE IF NOT EXISTS message (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    tool_calls JSONB DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT fk_message_conversation 
        FOREIGN KEY (conversation_id) 
        REFERENCES conversation(id) 
        ON DELETE CASCADE
);

-- Índices para búsquedas eficientes
CREATE INDEX idx_message_conversation_id ON message(conversation_id);
CREATE INDEX idx_message_created_at ON message(created_at DESC);
CREATE INDEX idx_message_role ON message(role);

-- Índice GIN para búsquedas en JSONB
CREATE INDEX idx_message_tool_calls ON message USING GIN (tool_calls);

COMMENT ON TABLE message IS 'Mensajes de conversaciones del chatbot AI';
COMMENT ON COLUMN message.role IS 'Rol del mensaje: user (usuario), assistant (IA), system (sistema)';
COMMENT ON COLUMN message.tool_calls IS 'JSON con las llamadas a tools MCP que hizo el LLM';

-- ============================================
-- TABLA: tool_execution
-- Registro de ejecuciones de MCP Tools
-- ============================================
CREATE TABLE IF NOT EXISTS tool_execution (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    parameters JSONB NOT NULL,
    result JSONB DEFAULT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'success', 'failed')),
    error_message TEXT DEFAULT NULL,
    execution_time_ms INTEGER DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT fk_tool_execution_message 
        FOREIGN KEY (message_id) 
        REFERENCES message(id) 
        ON DELETE CASCADE
);

-- Índices para búsquedas y analytics
CREATE INDEX idx_tool_execution_message_id ON tool_execution(message_id);
CREATE INDEX idx_tool_execution_tool_name ON tool_execution(tool_name);
CREATE INDEX idx_tool_execution_status ON tool_execution(status);
CREATE INDEX idx_tool_execution_created_at ON tool_execution(created_at DESC);

-- Índices GIN para búsquedas en JSONB
CREATE INDEX idx_tool_execution_parameters ON tool_execution USING GIN (parameters);
CREATE INDEX idx_tool_execution_result ON tool_execution USING GIN (result);

COMMENT ON TABLE tool_execution IS 'Registro de ejecuciones de MCP Tools';
COMMENT ON COLUMN tool_execution.tool_name IS 'Nombre del tool ejecutado (ej: buscar_reservas, crear_reserva)';
COMMENT ON COLUMN tool_execution.execution_time_ms IS 'Tiempo de ejecución en milisegundos';

-- ============================================
-- VISTA: conversation_stats
-- Estadísticas de conversaciones
-- ============================================
CREATE OR REPLACE VIEW conversation_stats AS
SELECT 
    c.id AS conversation_id,
    c.usuario_id,
    c.title,
    c.created_at,
    COUNT(m.id) AS message_count,
    COUNT(CASE WHEN m.role = 'user' THEN 1 END) AS user_messages,
    COUNT(CASE WHEN m.role = 'assistant' THEN 1 END) AS assistant_messages,
    MAX(m.created_at) AS last_message_at
FROM conversation c
LEFT JOIN message m ON c.id = m.conversation_id
GROUP BY c.id, c.usuario_id, c.title, c.created_at;

COMMENT ON VIEW conversation_stats IS 'Estadísticas agregadas de conversaciones';

-- ============================================
-- VISTA: tool_usage_stats
-- Estadísticas de uso de tools
-- ============================================
CREATE OR REPLACE VIEW tool_usage_stats AS
SELECT 
    tool_name,
    COUNT(*) AS total_executions,
    COUNT(CASE WHEN status = 'success' THEN 1 END) AS successful,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) AS failed,
    ROUND(AVG(execution_time_ms)::numeric, 2) AS avg_execution_time_ms,
    MAX(execution_time_ms) AS max_execution_time_ms,
    MIN(execution_time_ms) AS min_execution_time_ms
FROM tool_execution
GROUP BY tool_name
ORDER BY total_executions DESC;

COMMENT ON VIEW tool_usage_stats IS 'Estadísticas de uso y rendimiento de MCP Tools';

-- ============================================
-- DATOS DE PRUEBA (Opcional)
-- ============================================

-- Insertar conversación de prueba (usuario_id=1 debe existir en tabla usuario del sistema principal)
-- INSERT INTO conversation (usuario_id, title) 
-- VALUES (1, 'Conversación de prueba - Bienvenida');

-- ============================================
-- PERMISOS
-- ============================================

-- Otorgar permisos al usuario Reservas_ULEAM
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "Reservas_ULEAM";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "Reservas_ULEAM";
GRANT USAGE ON SCHEMA public TO "Reservas_ULEAM";

-- ============================================
-- VERIFICACIÓN
-- ============================================

SELECT 'AI Service Database Schema creado exitosamente!' AS status;

-- Mostrar tablas creadas
\dt

-- Mostrar vistas
\dv

-- Mostrar índices
\di
