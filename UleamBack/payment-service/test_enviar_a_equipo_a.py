import os
#!/usr/bin/env python3
"""
TESTS: Enviar webhooks desde Equipo B (ULEAM) a Equipo A
=========================================================

Este script prueba el envío de webhooks desde nuestro sistema (ULEAM)
hacia el Equipo A (Recomendaciones Turísticas).

CONFIGURACIÓN:
- Usamos el endpoint local: http://localhost:8001/api/v1/equipo-a/test-send
- El endpoint interno hace POST a Equipo A con HMAC correcto
- URL de Equipo A: <url-publica-de-equipo-a>/api/reservas
"""

import requests
import json
from datetime import datetime

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
BASE_URL = "http://localhost:8001/api/v1"
TEST_SEND_ENDPOINT = f"{BASE_URL}/equipo-a/test-send"

# ============================================================================
# TEST 1: Enviar booking.confirmed usando el endpoint de test
# ============================================================================
def test_send_booking_confirmed():
    """
    Usa el endpoint /test-send que envía un webhook de prueba a Equipo A
    """
    print("\n" + "="*70)
    print("🧪 TEST 1: Enviar booking.confirmed a Equipo A")
    print("="*70)
    
    print(f"\n📤 Endpoint local: {TEST_SEND_ENDPOINT}")
    print("   (Este endpoint enviará internamente a Equipo A con HMAC correcto)")
    
    try:
        response = requests.post(TEST_SEND_ENDPOINT, timeout=15)
        
        print(f"\n📥 Respuesta del endpoint local: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ ¡ÉXITO! Webhook enviado a Equipo A")
            print(f"\n📊 Resultado:")
            print(json.dumps(data, indent=2))
            
            if data.get("status") == "success":
                print("\n🎉 Equipo A recibió y procesó el webhook correctamente")
                if data.get("equipo_a_response"):
                    print(f"📦 Respuesta de Equipo A:")
                    print(json.dumps(data["equipo_a_response"], indent=2))
                return True
            else:
                print(f"\n⚠️ Equipo A respondió con error:")
                print(f"   Status Code: {data.get('status_code')}")
                print(f"   Response: {data.get('equipo_a_response')}")
                return False
        else:
            print(f"\n❌ Error al llamar al endpoint local")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ TIMEOUT: El servidor no respondió en 15 segundos")
        print("💡 Verificar:")
        print("   1. payment-service está corriendo en puerto 8001")
        print("   2. ngrok de Equipo A está activo")
        return False
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR: No se puede conectar")
        print("💡 Verificar que payment-service esté corriendo:")
        print("   cd C:\\ReservasUleam2025\\UleamBack\\payment-service")
        print("   uvicorn app.main:app --port 8001 --reload")
        return False
    except Exception as e:
        print(f"\n❌ EXCEPCIÓN: {str(e)}")
        return False

# ============================================================================
# TEST 2: Verificar health de Equipo A directamente
# ============================================================================
def test_equipo_a_health():
    """
    Verifica que Equipo A esté online
    """
    print("\n" + "="*70)
    print("🧪 TEST 2: Verificar health de Equipo A")
    print("="*70)
    
    health_url = os.environ["EQUIPO_A_HEALTH_URL"]
    
    print(f"\n📤 Consultando: {health_url}")
    
    try:
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Equipo A está ONLINE")
            try:
                print(f"📦 Response: {json.dumps(response.json(), indent=2)}")
            except:
                print(f"📦 Response: {response.text}")
            return True
        else:
            print(f"⚠️ Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Equipo A NO disponible: {str(e)}")
        print("💡 Verificar que su ngrok esté corriendo")
        return False

# ============================================================================
# TEST 3: Verificar status de integración local
# ============================================================================
def test_integration_status():
    """
    Consulta el status de integración de nuestro lado
    """
    print("\n" + "="*70)
    print("🧪 TEST 3: Status de integración (nuestro lado)")
    print("="*70)
    
    status_url = f"{BASE_URL}/equipo-a/status"
    
    print(f"\n📤 Consultando: {status_url}")
    
    try:
        response = requests.get(status_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Estado de integración:")
            print(json.dumps(data, indent=2))
            
            stats = data.get("statistics", {})
            print(f"\n📈 Estadísticas:")
            print(f"   Partner activo: {stats.get('is_active')}")
            print(f"   Webhooks enviados: {stats.get('webhooks_sent')}")
            print(f"   Exitosos: {stats.get('webhooks_succeeded')}")
            print(f"   Fallidos: {stats.get('webhooks_failed')}")
            
            return True
        else:
            print(f"❌ Error {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

# ============================================================================
# TEST 4: Verificar que payment-service esté corriendo
# ============================================================================
def test_payment_service_health():
    """
    Verifica que nuestro payment-service esté online
    """
    print("\n" + "="*70)
    print("🧪 TEST 4: Verificar payment-service (nuestro)")
    print("="*70)
    
    health_url = f"{BASE_URL}/health"
    
    print(f"\n📤 Consultando: {health_url}")
    
    try:
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Payment-service ONLINE")
            print(f"   Service: {data.get('service')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Payment-service NO está corriendo")
        print("\n💡 Iniciar payment-service:")
        print("   cd C:\\ReservasUleam2025\\UleamBack\\payment-service")
        print("   uvicorn app.main:app --port 8001 --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

# ============================================================================
# EJECUTAR TODOS LOS TESTS
# ============================================================================
def ejecutar_todos_los_tests():
    """Ejecuta la suite completa de tests de envío"""
    print("\n" + "="*70)
    print("🚀 SUITE DE TESTS: EQUIPO B (ULEAM) → EQUIPO A")
    print("="*70)
    print(f"\n📅 Fecha: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"🎯 Objetivo: Verificar envío de webhooks a Equipo A")
    
    # Lista de tests
    tests = [
        ("TEST 1: Payment-service health (nuestro)", test_payment_service_health),
        ("TEST 2: Equipo A health", test_equipo_a_health),
        ("TEST 3: Integration status", test_integration_status),
        ("TEST 4: Enviar webhook a Equipo A", test_send_booking_confirmed),
    ]
    
    # Ejecutar tests
    resultados = []
    for nombre, test_func in tests:
        try:
            resultado = test_func()
            resultados.append((nombre, resultado))
            
            # Si payment-service no está corriendo, no seguir
            if "Payment-service" in nombre and not resultado:
                print("\n⚠️ Payment-service no está corriendo. Deteniendo tests.")
                break
                
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
        print("✅ Pueden enviar webhooks a Equipo A correctamente")
    else:
        print("\n⚠️ Algunos tests fallaron")
        print("📞 Revisar mensajes de error arriba")

# ============================================================================
# MENÚ INTERACTIVO
# ============================================================================
def menu_interactivo():
    """Permite elegir qué test ejecutar"""
    while True:
        print("\n" + "="*70)
        print("📋 MENÚ DE TESTS - ENVÍO A EQUIPO A")
        print("="*70)
        print("\n1. Verificar payment-service (nuestro)")
        print("2. Verificar health de Equipo A")
        print("3. Ver status de integración")
        print("4. 📤 ENVIAR webhook a Equipo A (booking.confirmed)")
        print("5. 🚀 EJECUTAR TODOS LOS TESTS")
        print("0. Salir")
        
        opcion = input("\nElige una opción: ").strip()
        
        if opcion == "0":
            print("\n👋 ¡Hasta luego!")
            break
        elif opcion == "1":
            test_payment_service_health()
        elif opcion == "2":
            test_equipo_a_health()
        elif opcion == "3":
            test_integration_status()
        elif opcion == "4":
            test_send_booking_confirmed()
        elif opcion == "5":
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
