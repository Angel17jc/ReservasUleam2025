# 🧪 Script de prueba: Simular webhook desde Equipo B
# Este script simula que Equipo B nos envía un webhook con HMAC correcto

import json
import hmac
import hashlib
import requests
from datetime import datetime

# Configuración
SECRET = "integracion-turismo-2026-uleam"
URL_NUESTRO_WEBHOOK = "http://localhost:8001/api/v1/equipo-a/webhook"

def generar_firma_correcta(payload_dict):
    """
    Genera firma HMAC-SHA256 correcta.
    IMPORTANTE: Retorna tanto la firma como el mensaje serializado
    """
    mensaje = json.dumps(payload_dict, separators=(',', ':'), sort_keys=True)
    firma = hmac.new(
        SECRET.encode('utf-8'),
        mensaje.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return firma, mensaje

def test_recibir_webhook_equipo_b():
    """
    Simula que Equipo B nos envía un webhook con un tour comprado.
    """
    print("=" * 70)
    print("🧪 TEST: Simular webhook desde Equipo B → Equipo A")
    print("=" * 70)
    
    # Payload de prueba (como si viniera de Equipo B)
    payload = {
        "event": "tour.purchased",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "tour_id": "tour_test_123",
            "user_id": "user_test_456",
            "tour_name": "Volcán Cotopaxi",
            "price": 120.00,
            "destination": "Latacunga",
            "description": "Tour de un día al volcán Cotopaxi"
        },
        "source": "equipo-b-sistema-prueba"
    }
    
    # Calcular firma SOBRE EL MISMO STRING QUE SE ENVIARÁ
    firma, mensaje_serializado = generar_firma_correcta(payload)
    
    print(f"📤 URL: {URL_NUESTRO_WEBHOOK}")
    print(f"📦 Event: {payload['event']}")
    print(f"🔐 Firma: {firma}")
    print(f"📝 Mensaje serializado (para HMAC):")
    print(mensaje_serializado)
    print(f"\n📝 Payload formateado:")
    print(json.dumps(payload, indent=2))
    print("=" * 70)
    
    try:
        # CRÍTICO: Enviar el MISMO string usado para calcular la firma
        # Usar data= en vez de json= para enviar el string exacto
        response = requests.post(
            URL_NUESTRO_WEBHOOK,
            data=mensaje_serializado,  # ⚠️ Enviar string, no dict
            headers={
                "Content-Type": "application/json",
                "X-Signature": firma
            },
            timeout=10
        )
        
        print(f"\n✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"📥 Response: {response.json()}")
            print("\n🎉 ¡ÉXITO! Webhook recibido correctamente")
            print("✅ La validación HMAC funcionó")
            print("✅ El endpoint está procesando eventos correctamente")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📥 Response: {response.text}")
            print("\n⚠️  El webhook fue rechazado")
            return False
            
    except Exception as e:
        print(f"\n❌ EXCEPCIÓN: {str(e)}")
        return False

if __name__ == "__main__":
    test_recibir_webhook_equipo_b()
