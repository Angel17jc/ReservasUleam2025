"""
Test de compatibilidad de tokens entre auth-service y rest-service
"""
import sys
sys.path.insert(0, '.')

from app.utils.jwt_handler import decode_access_token, create_access_token

# Token ejemplo del auth-service (con sub como número)
auth_service_token_payload = {
    "sub": 6,
    "email": "admin123@uleam.edu.ec",
    "tipo_usuario_id": 1,
    "type": "access"
}

print("🔍 Probando compatibilidad de tokens...\n")

# 1. Crear token tipo auth-service (sub como número)
print("1️⃣ Creando token con sub como número (estilo auth-service):")
test_token = create_access_token(auth_service_token_payload)
print(f"   Token generado: {test_token[:50]}...")

# 2. Decodificar token
print("\n2️⃣ Decodificando token:")
decoded = decode_access_token(test_token)
if decoded:
    print(f"   ✅ Decodificación exitosa!")
    print(f"   - sub: {decoded.get('sub')} (tipo: {type(decoded.get('sub')).__name__})")
    print(f"   - email: {decoded.get('email')}")
    print(f"   - tipo_usuario_id: {decoded.get('tipo_usuario_id')}")
else:
    print(f"   ❌ Error al decodificar")

# 3. Probar conversión a int
print("\n3️⃣ Probando conversión a int para buscar usuario:")
if decoded and decoded.get('sub'):
    try:
        user_id = int(decoded['sub'])
        print(f"   ✅ Conversión exitosa: {user_id}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n✅ Test completo")
