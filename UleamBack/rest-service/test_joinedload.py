"""
Script para probar joinedload directamente
"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.usuario import Usuario
from sqlalchemy.orm import joinedload

db = SessionLocal()

try:
    print("🔍 Probando query SIN joinedload...")
    user1 = db.query(Usuario).filter(Usuario.email == "admin@uleam.edu.ec").first()
    print(f"  ✓ Usuario encontrado: {user1.nombre}")
    print(f"  - tipo_usuario_id: {user1.tipo_usuario_id}")
    print(f"  - tipo_usuario object: {user1.tipo_usuario}")
    if user1.tipo_usuario:
        print(f"  - tipo_usuario.nombre: {user1.tipo_usuario.nombre}")
    
    print("\n🔍 Probando query CON joinedload...")
    user2 = db.query(Usuario).options(joinedload(Usuario.tipo_usuario)).filter(Usuario.email == "admin@uleam.edu.ec").first()
    print(f"  ✓ Usuario encontrado: {user2.nombre}")
    print(f"  - tipo_usuario_id: {user2.tipo_usuario_id}")
    print(f"  - tipo_usuario object: {user2.tipo_usuario}")
    if user2.tipo_usuario:
        print(f"  - tipo_usuario.id: {user2.tipo_usuario.id}")
        print(f"  - tipo_usuario.nombre: {user2.tipo_usuario.nombre}")
    
    print("\n✅ Ambas queries funcionaron correctamente")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
