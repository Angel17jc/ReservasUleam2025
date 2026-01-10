"""
Regenerar password hash del admin
"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.usuario import Usuario
from app.utils.password_handler import get_password_hash

db = SessionLocal()

try:
    admin = db.query(Usuario).filter(Usuario.email == "admin@uleam.edu.ec").first()
    
    if admin:
        print(f"✓ Admin encontrado: {admin.nombre} ({admin.email})")
        print(f"  Hash actual: {admin.password_hash[:50]}...")
        
        # Regenerar hash
        new_hash = get_password_hash("password123")
        print(f"  Nuevo hash: {new_hash[:50]}...")
        
        admin.password_hash = new_hash
        db.commit()
        
        print("\n✅ Password hash actualizado correctamente")
    else:
        print("❌ Admin no encontrado")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
