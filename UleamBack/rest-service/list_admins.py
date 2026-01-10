"""
Verificar usuarios admin en la base de datos
"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.usuario import Usuario
from sqlalchemy.orm import joinedload

db = SessionLocal()

try:
    print("🔍 Buscando usuarios con tipo_usuario_id = 1 (Administrador)...\n")
    
    admins = db.query(Usuario).options(joinedload(Usuario.tipo_usuario)).filter(Usuario.tipo_usuario_id == 1).all()
    
    if admins:
        print(f"✅ Encontrados {len(admins)} administradores:\n")
        for admin in admins:
            print(f"   📧 Email: {admin.email}")
            print(f"      - ID: {admin.id}")
            print(f"      - Nombre: {admin.nombre} {admin.apellido}")
            print(f"      - Estado: {admin.estado}")
            if admin.tipo_usuario:
                print(f"      - Rol: {admin.tipo_usuario.nombre}")
            print()
    else:
        print("❌ No se encontraron administradores")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
