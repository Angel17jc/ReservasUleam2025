-- ============================================
-- ULEAM SPACE RESERVATION SYSTEM - DATABASE SCHEMA
-- Universidad Laica Eloy Alfaro de Manabí
-- ============================================

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS notificacion CASCADE;
DROP TABLE IF EXISTS reserva CASCADE;
DROP TABLE IF EXISTS estado_reserva CASCADE;
DROP TABLE IF EXISTS disponibilidad_espacio CASCADE;
DROP TABLE IF EXISTS caracteristica_espacio CASCADE;
DROP TABLE IF EXISTS espacio CASCADE;
DROP TABLE IF EXISTS categoria_espacio CASCADE;
DROP TABLE IF EXISTS tipo_evento CASCADE;
DROP TABLE IF EXISTS usuario CASCADE;
DROP TABLE IF EXISTS tipo_usuario CASCADE;
DROP TABLE IF EXISTS referencia CASCADE;

-- ============================================
-- TABLA: tipo_usuario (DEC1 - REST API)
-- ============================================
CREATE TABLE tipo_usuario (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT,
    nivel_prioridad INTEGER NOT NULL DEFAULT 1,
    permisos JSONB DEFAULT '{}',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA: usuario (DEC1 - REST API)
-- ============================================
CREATE TABLE usuario (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    tipo_usuario_id INTEGER NOT NULL REFERENCES tipo_usuario(id) ON DELETE RESTRICT,
    estado VARCHAR(20) NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'bloqueado')),
    avatar_url VARCHAR(500),
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA: categoria_espacio (DEC1 - REST API)
-- ============================================
CREATE TABLE categoria_espacio (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT,
    requiere_aprobacion BOOLEAN DEFAULT FALSE,
    capacidad_maxima INTEGER,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA: referencia (DEC2 - GraphQL)
-- ============================================
CREATE TABLE referencia (
    id SERIAL PRIMARY KEY,
    descripcion_general TEXT NOT NULL,
    color_referencia VARCHAR(50),
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA: espacio (DEC1 - REST API)
-- ============================================
CREATE TABLE espacio (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    categoria_id INTEGER NOT NULL REFERENCES categoria_espacio(id) ON DELETE RESTRICT,
    capacidad_maxima INTEGER NOT NULL,
    imagen_url VARCHAR(500),
    estado VARCHAR(20) NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'mantenimiento')),
    referencia_id INTEGER REFERENCES referencia(id) ON DELETE SET NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA: caracteristica_espacio (DEC1 - REST API)
-- ============================================
CREATE TABLE caracteristica_espacio (
    id SERIAL PRIMARY KEY,
    espacio_id INTEGER NOT NULL REFERENCES espacio(id) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    disponible BOOLEAN DEFAULT TRUE,
    descripcion TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA: disponibilidad_espacio (DEC2 - GraphQL)
-- ============================================
CREATE TABLE disponibilidad_espacio (
    id SERIAL PRIMARY KEY,
    espacio_id INTEGER NOT NULL REFERENCES espacio(id) ON DELETE CASCADE,
    dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 6),
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_horario CHECK (hora_fin > hora_inicio)
);

-- ============================================
-- TABLA: tipo_evento (DEC1 - REST API)
-- ============================================
CREATE TABLE tipo_evento (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT,
    requiere_aprobacion BOOLEAN DEFAULT FALSE,
    color_hex VARCHAR(7) DEFAULT '#3B82F6',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA: estado_reserva (DEC2 - GraphQL)
-- ============================================
CREATE TABLE estado_reserva (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    color_hex VARCHAR(7) NOT NULL,
    permite_edicion BOOLEAN DEFAULT TRUE,
    es_final BOOLEAN DEFAULT FALSE,
    orden INTEGER NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA: reserva (DEC2 - GraphQL)
-- ============================================
CREATE TABLE reserva (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    usuario_id INTEGER NOT NULL REFERENCES usuario(id) ON DELETE RESTRICT,
    espacio_id INTEGER NOT NULL REFERENCES espacio(id) ON DELETE RESTRICT,
    tipo_evento_id INTEGER NOT NULL REFERENCES tipo_evento(id) ON DELETE RESTRICT,
    estado_id INTEGER NOT NULL REFERENCES estado_reserva(id) ON DELETE RESTRICT,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    es_bloqueo BOOLEAN DEFAULT FALSE,
    motivo_bloqueo TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_hora_reserva CHECK (hora_fin > hora_inicio),
    CONSTRAINT chk_bloqueo CHECK (
        (es_bloqueo = TRUE AND motivo_bloqueo IS NOT NULL) OR 
        (es_bloqueo = FALSE)
    )
);

-- ============================================
-- TABLA: notificacion (DEC3 - WebSocket)
-- ============================================
CREATE TABLE notificacion (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    titulo VARCHAR(200) NOT NULL,
    mensaje TEXT NOT NULL,
    leida BOOLEAN DEFAULT FALSE,
    reserva_id INTEGER REFERENCES reserva(id) ON DELETE SET NULL,
    espacio_id INTEGER REFERENCES espacio(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    leida_at TIMESTAMP,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Usuario indexes
CREATE INDEX idx_usuario_email ON usuario(email);
CREATE INDEX idx_usuario_tipo ON usuario(tipo_usuario_id);
CREATE INDEX idx_usuario_estado ON usuario(estado);

-- Espacio indexes
CREATE INDEX idx_espacio_codigo ON espacio(codigo);
CREATE INDEX idx_espacio_categoria ON espacio(categoria_id);
CREATE INDEX idx_espacio_estado ON espacio(estado);

-- Reserva indexes
CREATE INDEX idx_reserva_codigo ON reserva(codigo);
CREATE INDEX idx_reserva_usuario ON reserva(usuario_id);
CREATE INDEX idx_reserva_espacio ON reserva(espacio_id);
CREATE INDEX idx_reserva_estado ON reserva(estado_id);
CREATE INDEX idx_reserva_fecha ON reserva(fecha);
CREATE INDEX idx_reserva_fecha_espacio ON reserva(fecha, espacio_id);

-- Notificacion indexes
CREATE INDEX idx_notificacion_usuario ON notificacion(usuario_id);
CREATE INDEX idx_notificacion_leida ON notificacion(leida);
CREATE INDEX idx_notificacion_reserva ON notificacion(reserva_id);

-- Disponibilidad indexes
CREATE INDEX idx_disponibilidad_espacio ON disponibilidad_espacio(espacio_id);
CREATE INDEX idx_disponibilidad_dia ON disponibilidad_espacio(dia_semana);

-- ============================================
-- SEED DATA - INITIAL DATA
-- ============================================

-- Insert TipoUsuario
INSERT INTO tipo_usuario (nombre, descripcion, nivel_prioridad, permisos) VALUES
('Administrador', 'Usuario con acceso total al sistema', 1, '{"admin": true, "crear_reservas": true, "aprobar_reservas": true, "gestionar_usuarios": true}'),
('Profesor', 'Docente universitario', 2, '{"crear_reservas": true, "ver_reportes": true}'),
('Estudiante', 'Estudiante de la universidad', 3, '{"crear_reservas": true}'),
('Personal Administrativo', 'Personal de administración', 2, '{"crear_reservas": true, "aprobar_reservas": true}');

-- Insert Usuarios (password: "password123" hashed with bcrypt)
INSERT INTO usuario (email, password_hash, nombre, apellido, telefono, tipo_usuario_id, estado) VALUES
('admin@uleam.edu.ec', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lXz9p3hWHb4G', 'Juan', 'Pérez', '0998765432', 1, 'activo'),
('profesor1@uleam.edu.ec', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lXz9p3hWHb4G', 'María', 'González', '0987654321', 2, 'activo'),
('estudiante1@uleam.edu.ec', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lXz9p3hWHb4G', 'Carlos', 'Rodríguez', '0976543210', 3, 'activo'),
('admin2@uleam.edu.ec', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lXz9p3hWHb4G', 'Ana', 'Martínez', '0965432109', 4, 'activo');

-- Insert CategoriaEspacio
INSERT INTO categoria_espacio (nombre, descripcion, requiere_aprobacion, capacidad_maxima) VALUES
('Auditorio', 'Espacios para conferencias y eventos académicos', TRUE, 500),
('Paraninfo', 'Paraninfo principal de la universidad', TRUE, 1000),
('Cancha Deportiva', 'Espacios deportivos y recreativos', FALSE, 50),
('Sala de Reuniones', 'Salas para reuniones y trabajo grupal', FALSE, 20),
('Laboratorio', 'Laboratorios de cómputo y ciencias', FALSE, 30);

-- Insert Referencias
INSERT INTO referencia (descripcion_general, color_referencia) VALUES
('Espacios académicos principales', '#3B82F6'),
('Espacios deportivos y recreativos', '#10B981'),
('Espacios administrativos', '#F59E0B');

-- Insert Espacios
INSERT INTO espacio (codigo, nombre, categoria_id, capacidad_maxima, estado, referencia_id) VALUES
('AUD-001', 'Auditorio Central', 1, 300, 'activo', 1),
('PAR-001', 'Paraninfo Eloy Alfaro', 2, 1000, 'activo', 1),
('CAN-001', 'Cancha de Fútbol Principal', 3, 22, 'activo', 2),
('CAN-002', 'Cancha de Básquet', 3, 10, 'activo', 2),
('SAL-001', 'Sala de Reuniones A', 4, 15, 'activo', 3),
('LAB-001', 'Laboratorio de Cómputo 1', 5, 30, 'activo', 1);

-- Insert CaracteristicaEspacio
INSERT INTO caracteristica_espacio (espacio_id, nombre, disponible, descripcion) VALUES
(1, 'Proyector', TRUE, 'Proyector HD de alta calidad'),
(1, 'Sistema de Audio', TRUE, 'Sistema de sonido profesional'),
(1, 'Aire Acondicionado', TRUE, 'Climatización completa'),
(2, 'Proyector', TRUE, 'Proyector 4K'),
(2, 'Sistema de Audio', TRUE, 'Sistema de sonido envolvente'),
(2, 'Escenario', TRUE, 'Escenario principal con iluminación'),
(3, 'Arcos de Fútbol', TRUE, 'Arcos reglamentarios'),
(3, 'Iluminación', TRUE, 'Iluminación nocturna'),
(4, 'Aros de Básquet', TRUE, 'Aros reglamentarios'),
(5, 'Pizarra', TRUE, 'Pizarra inteligente'),
(6, 'Computadoras', TRUE, '30 computadoras de última generación');

-- Insert DisponibilidadEspacio (Lunes a Viernes, 8:00-18:00)
INSERT INTO disponibilidad_espacio (espacio_id, dia_semana, hora_inicio, hora_fin, activo) VALUES
-- Auditorio Central
(1, 1, '08:00', '18:00', TRUE),
(1, 2, '08:00', '18:00', TRUE),
(1, 3, '08:00', '18:00', TRUE),
(1, 4, '08:00', '18:00', TRUE),
(1, 5, '08:00', '18:00', TRUE),
-- Paraninfo
(2, 1, '08:00', '20:00', TRUE),
(2, 2, '08:00', '20:00', TRUE),
(2, 3, '08:00', '20:00', TRUE),
(2, 4, '08:00', '20:00', TRUE),
(2, 5, '08:00', '20:00', TRUE),
-- Cancha de Fútbol
(3, 1, '06:00', '22:00', TRUE),
(3, 2, '06:00', '22:00', TRUE),
(3, 3, '06:00', '22:00', TRUE),
(3, 4, '06:00', '22:00', TRUE),
(3, 5, '06:00', '22:00', TRUE),
(3, 6, '08:00', '18:00', TRUE);

-- Insert TipoEvento
INSERT INTO tipo_evento (nombre, descripcion, requiere_aprobacion, color_hex) VALUES
('Conferencia', 'Evento académico o científico', TRUE, '#3B82F6'),
('Clase', 'Clase regular o taller', FALSE, '#10B981'),
('Evento Deportivo', 'Competencia o práctica deportiva', FALSE, '#F59E0B'),
('Reunión', 'Reunión administrativa o académica', FALSE, '#8B5CF6'),
('Ceremonia', 'Graduación, inauguración u otros eventos formales', TRUE, '#EF4444');

-- Insert EstadoReserva
INSERT INTO estado_reserva (nombre, color_hex, permite_edicion, es_final, orden) VALUES
('Pendiente', '#F59E0B', TRUE, FALSE, 1),
('Aprobada', '#10B981', FALSE, FALSE, 2),
('Rechazada', '#EF4444', FALSE, TRUE, 3),
('Completada', '#6B7280', FALSE, TRUE, 4),
('Cancelada', '#DC2626', FALSE, TRUE, 5);

-- Insert Reservas de ejemplo
INSERT INTO reserva (codigo, usuario_id, espacio_id, tipo_evento_id, estado_id, fecha, hora_inicio, hora_fin, titulo, descripcion, es_bloqueo, motivo_bloqueo) VALUES
('RES-2025-001', 2, 1, 1, 2, '2025-11-15', '09:00', '12:00', 'Conferencia de Ingeniería de Software', 'Conferencia anual sobre nuevas tecnologías', FALSE, NULL),
('RES-2025-002', 3, 3, 3, 2, '2025-11-16', '15:00', '17:00', 'Torneo de Fútbol Inter-Facultades', 'Fase eliminatoria del torneo', FALSE, NULL),
('RES-2025-003', 2, 2, 5, 1, '2025-12-20', '10:00', '13:00', 'Ceremonia de Graduación', 'Graduación promoción 2025', FALSE, NULL),
('BLK-2025-001', 1, 1, 1, 2, '2025-11-10', '08:00', '18:00', 'Mantenimiento Programado', 'Mantenimiento del sistema de audio', TRUE, 'Mantenimiento del sistema de audio');

-- Insert Notificaciones de ejemplo
INSERT INTO notificacion (usuario_id, titulo, mensaje, leida, reserva_id, metadata) VALUES
(2, 'Reserva Aprobada', 'Su reserva RES-2025-001 ha sido aprobada', FALSE, 1, '{"tipo": "aprobacion", "prioridad": "alta"}'),
(3, 'Reserva Confirmada', 'Su reserva RES-2025-002 ha sido confirmada', TRUE, 2, '{"tipo": "confirmacion", "prioridad": "media"}'),
(2, 'Recordatorio', 'Su evento es mañana a las 09:00', FALSE, 1, '{"tipo": "recordatorio", "prioridad": "alta"}');

-- ============================================
-- UPDATE TIMESTAMP TRIGGER
-- ============================================

CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_en = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to all tables
CREATE TRIGGER update_tipo_usuario_timestamp BEFORE UPDATE ON tipo_usuario FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_usuario_timestamp BEFORE UPDATE ON usuario FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_categoria_espacio_timestamp BEFORE UPDATE ON categoria_espacio FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_referencia_timestamp BEFORE UPDATE ON referencia FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_espacio_timestamp BEFORE UPDATE ON espacio FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_caracteristica_espacio_timestamp BEFORE UPDATE ON caracteristica_espacio FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_disponibilidad_espacio_timestamp BEFORE UPDATE ON disponibilidad_espacio FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_tipo_evento_timestamp BEFORE UPDATE ON tipo_evento FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_estado_reserva_timestamp BEFORE UPDATE ON estado_reserva FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_reserva_timestamp BEFORE UPDATE ON reserva FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_notificacion_timestamp BEFORE UPDATE ON notificacion FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ============================================
-- VIEWS FOR REPORTING
-- ============================================

-- View: Complete reservation information
CREATE OR REPLACE VIEW vista_reservas_completa AS
SELECT 
    r.id,
    r.codigo,
    r.titulo,
    r.descripcion,
    r.fecha,
    r.hora_inicio,
    r.hora_fin,
    r.es_bloqueo,
    u.nombre || ' ' || u.apellido AS usuario_nombre,
    u.email AS usuario_email,
    e.nombre AS espacio_nombre,
    e.codigo AS espacio_codigo,
    te.nombre AS tipo_evento_nombre,
    er.nombre AS estado_nombre,
    er.color_hex AS estado_color,
    r.creado_en
FROM reserva r
JOIN usuario u ON r.usuario_id = u.id
JOIN espacio e ON r.espacio_id = e.id
JOIN tipo_evento te ON r.tipo_evento_id = te.id
JOIN estado_reserva er ON r.estado_id = er.id;

-- ============================================
-- SUCCESS MESSAGE
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '✅ Database schema created successfully!';
    RAISE NOTICE '✅ All 11 entities created';
    RAISE NOTICE '✅ Indexes created for performance';
    RAISE NOTICE '✅ Seed data inserted';
    RAISE NOTICE '✅ Triggers configured';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Sample data summary:';
    RAISE NOTICE '   - 4 User types';
    RAISE NOTICE '   - 4 Users (password: password123)';
    RAISE NOTICE '   - 5 Space categories';
    RAISE NOTICE '   - 6 Spaces';
    RAISE NOTICE '   - 5 Event types';
    RAISE NOTICE '   - 5 Reservation states';
    RAISE NOTICE '   - 4 Sample reservations';
    RAISE NOTICE '   - 3 Sample notifications';
END $$;
