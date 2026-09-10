"""
Script para registrar al Equipo A como Partner B2B

Este script:
1. Registra al Equipo A en el payment-service
2. Genera API key y secret para autenticación
3. Configura los eventos suscritos
4. Muestra las credenciales para compartir

IMPORTANTE: Ejecutar una sola vez. Las credenciales solo se muestran una vez.
"""
import os

import requests
import json

# Configuración del payment-service (local)
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8024")  # Puerto del payment-service

# Datos del Equipo A (Recomendaciones Turísticas ULEAM)
EQUIPO_A_DATA = {
    "name": "Equipo A - Recomendaciones Turísticas ULEAM",
    "email": "equipo-a@uleam.edu.ec",
    "webhook_url": os.environ["EQUIPO_A_WEBHOOK_URL"],
    "events_subscribed": [
        "payment.success",      # Cuando un pago es exitoso
        "payment.failed",       # Cuando un pago falla
        "booking.confirmed",    # Cuando confirmamos una reserva (nosotros → ellos)
        "service.activated"     # Cuando activamos un servicio
    ]
}


def register_partner():
    """
    Registra al Equipo A como partner en payment-service.
    """
    print("=" * 70)
    print("REGISTRO DE PARTNER B2B: EQUIPO A")
    print("=" * 70)
    print("\nRegistrando Equipo A como partner...")
    print(f"URL: {PAYMENT_SERVICE_URL}/api/v1/partners")
    print(f"\nDatos del partner:")
    print(json.dumps(EQUIPO_A_DATA, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            f"{PAYMENT_SERVICE_URL}/api/v1/partners",
            json=EQUIPO_A_DATA,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            partner = response.json()
            
            print("\n" + "=" * 70)
            print("[EXITO] Partner registrado correctamente")
            print("=" * 70)
            
            print(f"\nPartner ID: {partner['id']}")
            print(f"Nombre: {partner['name']}")
            print(f"Email: {partner['email']}")
            print(f"Webhook URL: {partner['webhook_url']}")
            print(f"Estado: {'Activo' if partner['is_active'] else 'Inactivo'}")
            
            print("\n" + "=" * 70)
            print("CREDENCIALES (GUARDAR DE FORMA SEGURA)")
            print("=" * 70)
            print(f"\nAPI Key: {partner['api_key']}")
            print(f"Secret Key: {partner['secret_key']}")
            
            print("\n" + "=" * 70)
            print("COMPARTIR CON EQUIPO A")
            print("=" * 70)
            print("""
Para que el Equipo A nos envíe webhooks, deben usar:

Endpoint: https://TU_NGROK_URL/api/v1/partners/webhook

Headers:
  X-Api-Key: {api_key}
  X-Webhook-Signature: <HMAC-SHA256 del payload>
  X-Webhook-Timestamp: <Unix timestamp>

Secret para HMAC: {secret_key}

Eventos que pueden enviarnos:
  - booking.confirmed: Cuando confirman una reserva/tour
  - tour.purchased: Cuando compran un tour
  - service.activated: Cuando activan un servicio
  - booking.cancelled: Cuando cancelan una reserva

Ejemplo de payload:
{{
  "event_type": "tour.purchased",
  "event_id": "evt_123",
  "timestamp": 1737336000,
  "booking_id": "tour_456",
  "amount": 120.00,
  "currency": "USD",
  "metadata": {{
    "tour_name": "Tour Manta City",
    "user_email": "user@example.com"
  }}
}}
""".format(api_key=partner['api_key'], secret_key=partner['secret_key']))
            
            # Guardar en archivo para referencia
            with open("equipo_a_credentials.json", "w") as f:
                json.dump(partner, f, indent=2, ensure_ascii=False)
            
            print("\n[INFO] Credenciales guardadas en: equipo_a_credentials.json")
            print("[IMPORTANTE] Este archivo contiene información sensible. NO subir a Git.")
            
            return partner
        
        else:
            print(f"\n[ERROR] Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] No se pudo conectar con payment-service")
        print(f"Verificar que esté corriendo en {PAYMENT_SERVICE_URL}")
        print("\nPara iniciar payment-service:")
        print("  cd UleamBack/payment-service")
        print("  uvicorn app.main:app --port 8001 --reload")
        return None
    
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        return None


def verify_partner(partner_id: int):
    """
    Verifica que el partner esté correctamente registrado.
    """
    print(f"\n\nVerificando partner ID {partner_id}...")
    
    try:
        response = requests.get(f"{PAYMENT_SERVICE_URL}/api/v1/partners/{partner_id}")
        
        if response.status_code == 200:
            partner = response.json()
            print("[OK] Partner verificado correctamente")
            print(f"Nombre: {partner['name']}")
            print(f"Estado: {'Activo' if partner['is_active'] else 'Inactivo'}")
            print(f"Eventos suscritos: {', '.join(partner['events_subscribed'])}")
            return True
        else:
            print(f"[ERROR] No se pudo verificar partner: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return False


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "REGISTRO DE PARTNER B2B - EQUIPO A" + " " * 19 + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n")
    
    # Registrar partner
    partner = register_partner()
    
    if partner:
        # Verificar registro
        verify_partner(partner['id'])
        
        print("\n" + "=" * 70)
        print("[SIGUIENTE PASO]")
        print("=" * 70)
        print("""
1. Compartir credenciales con Equipo A (ver arriba)
2. Recibir las credenciales del Equipo A
3. Configurar el envío de webhooks a su URL
4. Probar la integración bidireccional

Ver: B2B_INTEGRATION_GUIDE.md para más detalles
""")
    else:
        print("\n[FALLO] No se pudo registrar el partner")
        exit(1)
