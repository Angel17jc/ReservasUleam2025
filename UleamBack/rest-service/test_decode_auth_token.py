"""
Decodificar token del auth-service para ver su estructura
"""
import sys
sys.path.insert(0, '.')

from app.utils.jwt_handler import decode_access_token

# Token de prueba - reemplazar con token real
import requests

# 1. Obtener token del auth-service
print("1️⃣ Obteniendo token del auth-service...")
response = requests.post(
    "http://localhost:9000/api/v1/auth/login",
    json={"email": "admin123@uleam.edu.ec", "password": "AdminPass123!"}
)

if response.status_code == 200:
    data = response.json()
    token = data['accessToken']
    print(f"   ✅ Token obtenido: {token[:50]}...")
    print(f"   User ID: {data['user']['id']}")
    print(f"   tipo_usuario_id: {data['user'].get('tipo_usuario_id', 'N/A')}")
    
    # 2. Decodificar token
    print("\n2️⃣ Decodificando token con REST service...")
    decoded = decode_access_token(token)
    
    if decoded:
        print("   ✅ Token decodificado exitosamente!")
        print(f"\n   📋 Payload completo:")
        import json
        print(json.dumps(decoded, indent=4))
    else:
        print("   ❌ Error al decodificar token")
else:
    print(f"   ❌ Error en login: {response.status_code}")
    print(f"   {response.text}")
