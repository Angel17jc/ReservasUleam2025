"""
Test JWT compatibility between auth-service and rest-service
"""
import sys
sys.path.insert(0, 'C:\\ReservasUleam2025\\UleamBack\\rest-service')

from app.config import settings
from app.utils.jwt_handler import decode_access_token, create_access_token
import jwt

print("="*60)
print("JWT COMPATIBILITY TEST")
print("="*60)

# Test 1: Verify configuration
print(f"\n1️⃣  Configuration Check:")
print(f"   SECRET_KEY: {settings.SECRET_KEY[:30]}...")
print(f"   ALGORITHM: {settings.ALGORITHM}")
print(f"   DB_HOST: {settings.DB_HOST}")
print(f"   DB_NAME: {settings.DB_NAME}")

# Test 2: Create a token with REST service
print(f"\n2️⃣  Creating token with REST service...")
test_payload = {
    "sub": 6,  # Numeric (like auth-service)
    "email": "admin123@uleam.edu.ec",
    "tipo_usuario_id": 1
}
rest_token = create_access_token(test_payload)
print(f"   ✅ Token created: {rest_token[:50]}...")

# Test 3: Decode the token
print(f"\n3️⃣  Decoding token with REST service...")
decoded = decode_access_token(rest_token)
if decoded:
    print(f"   ✅ Token decoded successfully")
    print(f"   sub: {decoded.get('sub')} (type: {type(decoded.get('sub')).__name__})")
    print(f"   email: {decoded.get('email')}")
    print(f"   tipo_usuario_id: {decoded.get('tipo_usuario_id')}")
else:
    print(f"   ❌ Failed to decode token")
    sys.exit(1)

# Test 4: Simulate auth-service token (numeric sub)
print(f"\n4️⃣  Simulating auth-service token (numeric sub)...")
auth_service_token = jwt.encode(
    {
        "sub": 6,  # Numeric
        "email": "admin123@uleam.edu.ec",
        "tipo_usuario_id": 1,
        "type": "access"
    },
    settings.SECRET_KEY,
    algorithm=settings.ALGORITHM
)
print(f"   Token: {auth_service_token[:50]}...")

# Test 5: Decode auth-service style token
print(f"\n5️⃣  Decoding auth-service token with REST service...")
decoded_auth = decode_access_token(auth_service_token)
if decoded_auth:
    print(f"   ✅ Auth-service token decoded successfully")
    print(f"   sub: {decoded_auth.get('sub')} (type: {type(decoded_auth.get('sub')).__name__})")
    print(f"   email: {decoded_auth.get('email')}")
else:
    print(f"   ❌ Failed to decode auth-service token")
    sys.exit(1)

print(f"\n{'='*60}")
print(f"✅ ALL TESTS PASSED - JWT COMPATIBILITY CONFIRMED")
print(f"{'='*60}\n")
