"""
Script para actualizar el constraint de message.role en PostgreSQL
Permite role='tool' para resultados de herramientas
"""
import psycopg

def fix_constraint():
    """Actualiza el constraint para permitir role='tool'"""
    
    # Conectar a PostgreSQL (credenciales del .env)
    conn_string = "host=localhost port=5432 dbname=ai_service_db user=Reservas_ULEAM password=123456"
    
    try:
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                print("Conectado a PostgreSQL")
                
                # Primero verificar el propietario de la tabla
                print("Verificando propietario de la tabla...")
                cur.execute("""
                    SELECT tableowner FROM pg_tables 
                    WHERE tablename = 'message';
                """)
                owner = cur.fetchone()
                print(f"  Propietario actual: {owner[0] if owner else 'No encontrado'}")
                
                # Cambiar propietario si es necesario
                print("Cambiando propietario de la tabla...")
                try:
                    cur.execute("""
                        ALTER TABLE message OWNER TO "Reservas_ULEAM";
                    """)
                    conn.commit()
                    print("  ✓ Propietario cambiado")
                except Exception as e:
                    print(f"  ⚠️  No se pudo cambiar propietario: {e}")
                    conn.rollback()
                
                # Eliminar constraint antiguo
                print("Eliminando constraint antiguo...")
                cur.execute("""
                    ALTER TABLE message 
                    DROP CONSTRAINT IF EXISTS message_role_check;
                """)
                
                # Crear nuevo constraint que incluye 'tool'
                print("Creando nuevo constraint...")
                cur.execute("""
                    ALTER TABLE message 
                    ADD CONSTRAINT message_role_check 
                    CHECK (role IN ('user', 'assistant', 'system', 'tool'));
                """)
                
                conn.commit()
                print("✅ Constraint actualizado exitosamente")
                print("   Roles permitidos: user, assistant, system, tool")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=== Actualizando constraint de message.role ===\n")
    success = fix_constraint()
    
    if success:
        print("\n🎉 Base de datos actualizada correctamente")
    else:
        print("\n⚠️  Hubo un error actualizando la base de datos")
