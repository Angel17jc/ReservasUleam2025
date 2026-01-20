"""
Script para actualizar el constraint check_message_role en la BD.
Permite el role='tool' para resultados de herramientas.
"""
import sys
sys.path.insert(0, 'C:\\ReservasUleam2025\\UleamBack\\ai-service')

from sqlalchemy import text
from app.database import engine

def update_role_constraint():
    """Actualiza el constraint para permitir role='tool'"""
    try:
        with engine.connect() as conn:
            # Iniciar transacción
            trans = conn.begin()
            
            try:
                # 1. Eliminar constraint antiguo
                print("Eliminando constraint antiguo...")
                conn.execute(text("""
                    ALTER TABLE message 
                    DROP CONSTRAINT IF EXISTS check_message_role
                """))
                
                conn.execute(text("""
                    ALTER TABLE message 
                    DROP CONSTRAINT IF EXISTS message_role_check
                """))
                
                # 2. Agregar constraint nuevo con 'tool'
                print("Agregando constraint nuevo con 'tool'...")
                conn.execute(text("""
                    ALTER TABLE message 
                    ADD CONSTRAINT check_message_role 
                    CHECK (role IN ('user', 'assistant', 'system', 'tool'))
                """))
                
                # Commit
                trans.commit()
                print("\n✅ Constraint actualizado exitosamente!")
                print("   Roles permitidos: user, assistant, system, tool")
                
            except Exception as e:
                trans.rollback()
                print(f"\n❌ Error durante la actualización: {e}")
                raise
                
    except Exception as e:
        print(f"\n❌ Error conectando a la BD: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("="*60)
    print("ACTUALIZACIÓN DE CONSTRAINT: check_message_role")
    print("="*60)
    print()
    
    update_role_constraint()
    
    print()
    print("="*60)
    print("ACTUALIZACIÓN COMPLETADA")
    print("="*60)
