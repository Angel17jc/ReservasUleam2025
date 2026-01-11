import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Conectar como postgres
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",
    password="123456789",
    database="reservasuleam"
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cursor = conn.cursor()

print("📦 Creando tabla refresh_token...")

# Crear tabla refresh_token
cursor.execute("""
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
""")

print("✅ Tabla refresh_token creada")

# Crear índices
print("📊 Creando índices...")
cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_refresh_token_token ON refresh_token(token);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_refresh_token_user_revoked ON refresh_token(usuario_id, revocado);")
print("✅ Índices creados")

# Agregar columnas de seguridad a usuario
print("🔐 Agregando columnas de seguridad a tabla usuario...")

cursor.execute("""
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'usuario' AND column_name = 'ultimo_login') THEN
        ALTER TABLE usuario ADD COLUMN ultimo_login TIMESTAMP WITH TIME ZONE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'usuario' AND column_name = 'intentos_fallidos_login') THEN
        ALTER TABLE usuario ADD COLUMN intentos_fallidos_login INTEGER DEFAULT 0;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'usuario' AND column_name = 'bloqueado_hasta') THEN
        ALTER TABLE usuario ADD COLUMN bloqueado_hasta TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;
""")

print("✅ Columnas de seguridad agregadas")

# Dar permisos
print("🔑 Otorgando permisos a Reservas_ULEAM...")
cursor.execute('GRANT ALL PRIVILEGES ON TABLE refresh_token TO "Reservas_ULEAM";')
cursor.execute('GRANT USAGE, SELECT ON SEQUENCE refresh_token_id_seq TO "Reservas_ULEAM";')
print("✅ Permisos otorgados")

# Verificar
cursor.execute("SELECT COUNT(*) FROM refresh_token;")
count = cursor.fetchone()[0]
print(f"\n✅ Tabla refresh_token: {count} registros")

cursor.execute("""
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'usuario' 
AND column_name IN ('ultimo_login', 'intentos_fallidos_login', 'bloqueado_hasta')
ORDER BY column_name;
""")
columns = cursor.fetchall()
print(f"✅ Columnas agregadas a usuario: {', '.join([c[0] for c in columns])}")

cursor.close()
conn.close()

print("\n🎉 Migración completada exitosamente!")
