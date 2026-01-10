"""
Test directo del endpoint de login para ver errores
"""
import sys
sys.path.insert(0, '.')

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

print("🔍 Probando endpoint /api/auth/login...")

try:
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@uleam.edu.ec", "password": "password123"}
    )
    
    print(f"\n✅ Response Status: {response.status_code}")
    print(f"✅ Response Headers: {dict(response.headers)}")
    print(f"\n📋 Response Body:")
    print(response.json())
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
