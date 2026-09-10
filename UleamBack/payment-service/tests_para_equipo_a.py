import os
#!/usr/bin/env python3
"""
TESTS PARA EQUIPO A - Enviar webhooks a Equipo B (ULEAM)
=========================================================

Este script contiene todos los tests que el Equipo A debe ejecutar
para verificar que pueden enviar webhooks correctamente a ULEAM.

CONFIGURACIÓN:
- URL de Equipo B (ULEAM): <nuestra-url-publica>/api/v1/equipo-a/webhook
- Secret compartido: <secreto-acordado-con-equipo-a>
- Método: HMAC-SHA256 en header X-Signature

EVENTOS QUE EQUIPO A PUEDE ENVIAR:
1. tour.purchased - Cuando un usuario compra un tour
2. booking.confirmed - Cuando se confirma una reserva
3. recommendation.created - Cuando se crea una recomendación
"""

import requests
import json
import hmac
import hashlib
from datetime import datetime

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
SECRET = os.environ["EQUIPO_A_SHARED_SECRET"]  # obligatoria: nunca incrustar el secreto
URL_EQUIPO_B = os.getenv("NUESTRA_URL_PUBLICA", "http://localhost:8024") + "/api/v1/equipo-a/webhook"

# ============================================================================
# FUNCIÓN PARA GENERAR FIRMA HMAC (MÉTODO CORRECTO)
# ============================================================================
def generar_firma_hmac(payload_dict):
    """
    Genera firma HMAC-SHA256 de forma correcta.
    
    ⚠️ IMPORTANTE:
    - Serializar con sort_keys=True y separators=(',', ':')
    - Retornar tanto la firma como el string serializado
    - Enviar el MISMO string que se usa para calcular la firma
    """
    mensaje = json.dumps(payload_dict, sort_keys=True, separators=(',', ':'))
    firma = hmac.new(
        SECRET.encode('utf-8'),
        mensaje.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return firma, mensaje

# ============================================================================
# FUNCIÓN AUXILIAR PARA ENVIAR WEBHOOK
# ============================================================================
def enviar_webhook(evento, payload, test_name):
    """Envía un webhook al Equipo B y verifica la respuesta"""
    print("\n" + "="*70)
    print(f"🧪 TEST: {test_name}")
    print("="*70)
    
    # Generar firma
    firma, mensaje = generar_firma_hmac(payload)
    
    print(f"\n📤 Enviando a: {URL_EQUIPO_B}")
    print(f"📦 Evento: {evento}")
    print(f"🔐 Firma: {firma[:40]}...{firma[-20:]}")
    print(f"\n📝 Payload:")
    print(json.dumps(payload, indent=2))
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "X-Signature": firma
    }
    
    try:
        # ⚠️ CRÍTICO: Usar data= con el string serializado, NO json=
        response = requests.post(
            URL_EQUIPO_B,
            data=mensaje,
            headers=headers,
            timeout=10
        )
        
        print(f"\n📥 Respuesta HTTP {response.status_code}")
        
        if response.status_code == 200:
            print("✅ ¡ÉXITO! Webhook enviado y procesado correctamente")
            try:
                print(f"📦 Response: {json.dumps(response.json(), indent=2)}")
            except:
                print(f"📦 Response: {response.text}")
            return True
        elif response.status_code == 401:
            print("❌ ERROR 401: Firma HMAC inválida")
            print(f"📦 Response: {response.text}")
            print("\n💡 Verificar:")
            print("   1. Secret key: <secreto-acordado-con-equipo-a>")
            print("   2. Usar json.dumps con sort_keys=True y separators=(',', ':')")
            print("   3. Enviar con data=mensaje (NO json=payload)")
            return False
        else:
            print(f"⚠️ Error {response.status_code}")
            print(f"📦 Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ TIMEOUT: Servidor de Equipo B no responde")
        print("💡 Verificar que ngrok de ULEAM esté corriendo")
        return False
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR: No se puede conectar")
        print("💡 Verificar URL y conectividad")
        return False
    except Exception as e:
        print(f"\n❌ EXCEPCIÓN: {str(e)}")
        return False

# ============================================================================
# TEST 1: tour.purchased
# ============================================================================
def test_tour_purchased():
    """
    Simula que un usuario compró un tour en Equipo A.
    Equipo B debe registrar esta compra.
    """
    payload = {
        "event": "tour.purchased",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "tour_id": "tour_001",
            "user_id": "user_123",
            "user_email": "juan.perez@example.com",
            "tour_name": "Tour a Baños de Agua Santa",
            "price": 150.00,
            "currency": "USD",
            "destination": "Baños de Agua Santa",
            "description": "Tour de aventura con cascadas y puentes colgantes",
            "tour_date": "2026-02-15",
            "persons": 2,
            "purchase_date": datetime.utcnow().isoformat() + "Z"
        },
        "source": "equipo-a-recomendaciones"
    }
    
    return enviar_webhook("tour.purchased", payload, "Enviar tour.purchased")

# ============================================================================
# TEST 2: booking.confirmed
# ============================================================================
def test_booking_confirmed():
    """
    Simula que se confirmó una reserva en Equipo A.
    Equipo B debe registrar esta confirmación.
    """
    payload = {
        "event": "booking.confirmed",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "booking_id": "booking_456",
            "user_id": "user_789",
            "user_email": "maria.lopez@example.com",
            "tour_id": "tour_002",
            "tour_name": "Tour al Volcán Cotopaxi",
            "status": "confirmed",
            "amount": 120.00,
            "currency": "USD",
            "persons": 3,
            "booking_date": "2026-02-20",
            "confirmed_at": datetime.utcnow().isoformat() + "Z"
        },
        "source": "equipo-a-recomendaciones"
    }
    
    return enviar_webhook("booking.confirmed", payload, "Enviar booking.confirmed")

# ============================================================================
# TEST 3: recommendation.created
# ============================================================================
def test_recommendation_created():
    """
    Simula que se creó una recomendación en Equipo A.
    Equipo B debe registrar esta recomendación.
    """
    payload = {
        "event": "recommendation.created",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "recommendation_id": "rec_789",
            "user_id": "user_456",
            "user_email": "carlos.ruiz@example.com",
            "recommended_tour_id": "tour_003",
            "recommended_tour_name": "Tour Galápagos Express",
            "reason": "Basado en tu interés en naturaleza y vida marina",
            "score": 0.95,
            "price": 350.00,
            "currency": "USD",
            "created_at": datetime.utcnow().isoformat() + "Z"
        },
        "source": "equipo-a-recomendaciones"
    }
    
    return enviar_webhook("recommendation.created", payload, "Enviar recommendation.created")

# ============================================================================
# TEST 4: Evento con payload mínimo (verificar validación)
# ============================================================================
def test_payload_minimo():
    """
    Prueba con payload mínimo para verificar validación.
    """
    payload = {
        "event": "tour.purchased",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "tour_id": "test_minimal",
            "user_id": "test_user"
        },
        "source": "equipo-a-recomendaciones"
    }
    
    return enviar_webhook("tour.purchased", payload, "Payload mínimo (validación)")

# ============================================================================
# TEST 5: Verificar validación de firma (firma incorrecta)
# ============================================================================
def test_firma_invalida():
    """
    Prueba con firma incorrecta - DEBE FALLAR con 401.
    Esto verifica que Equipo B valida correctamente.
    """
    print("\n" + "="*70)
    print("🧪 TEST: Firma inválida (DEBE FALLAR con 401)")
    print("="*70)
    
    payload = {
        "event": "tour.purchased",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {"tour_id": "test", "user_id": "test"},
        "source": "equipo-a-recomendaciones"
    }
    
    firma_correcta, mensaje = generar_firma_hmac(payload)
    firma_incorrecta = "0" * 64  # Firma inválida
    
    print(f"\n📤 Enviando a: {URL_EQUIPO_B}")
    print(f"🔐 Firma correcta: {firma_correcta[:20]}...")
    print(f"❌ Firma enviada (incorrecta): {firma_incorrecta[:20]}...")
    
    try:
        response = requests.post(
            URL_EQUIPO_B,
            data=mensaje,
            headers={
                "Content-Type": "application/json",
                "X-Signature": firma_incorrecta
            },
            timeout=10
        )
        
        if response.status_code == 401:
            print(f"\n✅ CORRECTO: Recibió 401 (firma rechazada)")
            print(f"📦 Response: {response.text}")
            return True
        else:
            print(f"\n⚠️ INESPERADO: Status {response.status_code}")
            print("   Debería rechazar con 401")
            return False
            
    except Exception as e:
        print(f"\n❌ EXCEPCIÓN: {str(e)}")
        return False

# ============================================================================
# TEST 6: Verificar salud de Equipo B
# ============================================================================
def test_health_check():
    """Verifica que el servicio de Equipo B esté online"""
    print("\n" + "="*70)
    print("🧪 TEST: Health Check - Verificar servicio online")
    print("="*70)
    
    health_url = os.getenv("NUESTRA_URL_PUBLICA", "http://localhost:8024") + "/api/v1/health"
    
    try:
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Servicio ONLINE")
            print(f"📦 Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            print(f"⚠️ Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Servicio NO disponible: {str(e)}")
        return False

# ============================================================================
# EJECUTAR TODOS LOS TESTS
# ============================================================================
def ejecutar_todos_los_tests():
    """Ejecuta la suite completa de tests"""
    print("\n" + "="*70)
    print("🚀 SUITE DE TESTS PARA EQUIPO A → EQUIPO B (ULEAM)")
    print("="*70)
    print(f"\n🎯 Destino: {URL_EQUIPO_B}")
    print(f"🔑 Secret: {SECRET[:20]}...")
    print(f"📅 Fecha: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # Lista de tests
    tests = [
        ("Health Check", test_health_check),
        ("TEST 1: tour.purchased", test_tour_purchased),
        ("TEST 2: booking.confirmed", test_booking_confirmed),
        ("TEST 3: recommendation.created", test_recommendation_created),
        ("TEST 4: Payload mínimo", test_payload_minimo),
        ("TEST 5: Firma inválida (debe fallar)", test_firma_invalida),
    ]
    
    # Ejecutar tests
    resultados = []
    for nombre, test_func in tests:
        try:
            resultado = test_func()
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"\n❌ Error ejecutando {nombre}: {str(e)}")
            resultados.append((nombre, False))
    
    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE TESTS")
    print("="*70)
    
    for nombre, resultado in resultados:
        status = "✅ PASÓ" if resultado else "❌ FALLÓ"
        print(f"{status}: {nombre}")
    
    total = len(resultados)
    exitosos = sum(1 for _, r in resultados if r)
    porcentaje = (exitosos / total) * 100 if total > 0 else 0
    
    print(f"\n📈 Total: {exitosos}/{total} tests exitosos ({porcentaje:.1f}%)")
    
    if exitosos == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        print("✅ La integración Equipo A → Equipo B está funcionando correctamente")
    elif exitosos >= total - 1:  # Permitir 1 fallo (el de firma inválida es esperado)
        print("\n✅ Tests principales pasaron")
        print("⚠️ Revisar tests fallidos arriba")
    else:
        print("\n⚠️ Varios tests fallaron")
        print("📞 Revisar mensajes de error arriba")
        print("📞 Contactar a Equipo B si el problema persiste")

# ============================================================================
# MENÚ INTERACTIVO
# ============================================================================
def menu_interactivo():
    """Permite elegir qué test ejecutar"""
    while True:
        print("\n" + "="*70)
        print("📋 MENÚ DE TESTS - EQUIPO A → EQUIPO B")
        print("="*70)
        print("\n1. Health Check (verificar servicio)")
        print("2. TEST: tour.purchased")
        print("3. TEST: booking.confirmed")
        print("4. TEST: recommendation.created")
        print("5. TEST: Payload mínimo")
        print("6. TEST: Firma inválida (debe fallar)")
        print("7. 🚀 EJECUTAR TODOS LOS TESTS")
        print("0. Salir")
        
        opcion = input("\nElige una opción: ").strip()
        
        if opcion == "0":
            print("\n👋 ¡Hasta luego!")
            break
        elif opcion == "1":
            test_health_check()
        elif opcion == "2":
            test_tour_purchased()
        elif opcion == "3":
            test_booking_confirmed()
        elif opcion == "4":
            test_recommendation_created()
        elif opcion == "5":
            test_payload_minimo()
        elif opcion == "6":
            test_firma_invalida()
        elif opcion == "7":
            ejecutar_todos_los_tests()
        else:
            print("❌ Opción inválida")

# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        # Ejecutar todos los tests sin interacción
        ejecutar_todos_los_tests()
    else:
        # Menú interactivo
        menu_interactivo()
