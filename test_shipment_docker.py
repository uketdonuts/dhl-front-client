#!/usr/bin/env python3
"""
Script de prueba para endpoint de crear pedidos DHL
Usando datos quemados para testing
"""

import requests
import json
from datetime import datetime

# Configuración
API_BASE_URL = "http://localhost:8001"
ENDPOINT = "/api/dhl/shipment/"

# Datos de prueba quemados
test_shipment_data = {
    "shipper": {
        "name": "Guillermo Maduro",
        "company": "SAMSUNG ELECT. LATINOAMERICA ZL",
        "phone": "507431-2600",
        "email": "shipper_test@dhl.com",
        "address": "Panama Pacifico, J. Cain",
        "city": "Panama",
        "state": "PA",
        "postalCode": "0",
        "country": "PA"
    },
    "recipient": {
        "name": "INVERSIONES ORANGE STORE, C.A.",
        "company": "INVERSIONES ORANGE STORE, C.A.",
        "phone": "58-241-8421411",
        "email": "samsung@orangestore.com.ve",
        "address": "AV.Universidad CC Freemarket L R04",
        "city": "Caracas",
        "state": "CAR",
        "postalCode": "0",
        "country": "VE"
    },
    "package": {
        "weight": 0.3,
        "length": 21,
        "width": 16,
        "height": 11,
        "description": "SVC JDM-TAPE_GLASSTIC COVER_DECO_SM-A065",
        "value": 54.87,
        "currency": "USD"
    },
    "service": "P",  # Priority
    "payment": "S"   # Shipper pays
}

def test_endpoint():
    """Probar el endpoint de creación de pedidos"""
    print("🚀 Probando endpoint de crear pedidos DHL...")
    print(f"URL: {API_BASE_URL}{ENDPOINT}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    try:
        # Hacer la petición POST
        response = requests.post(
            f"{API_BASE_URL}{ENDPOINT}",
            json=test_shipment_data,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout=30
        )
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Response Headers: {dict(response.headers)}")
        
        # Mostrar respuesta
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"✅ Response JSON:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        else:
            print(f"✅ Response Text:")
            print(response.text[:1000])  # Primeros 1000 caracteres
        
        # Evaluar resultado
        if response.status_code == 200:
            print("\n🎉 ¡Prueba EXITOSA! El endpoint está funcionando correctamente")
        elif response.status_code == 201:
            print("\n🎉 ¡Prueba EXITOSA! Pedido creado correctamente")
        elif response.status_code == 400:
            print("\n⚠️  Error de validación - Revisar datos de entrada")
        elif response.status_code == 401:
            print("\n❌ Error de autenticación - Verificar credenciales")
        elif response.status_code == 500:
            print("\n❌ Error interno del servidor")
        else:
            print(f"\n❓ Status code inesperado: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se pudo conectar al servidor")
        print("   Verifica que el contenedor backend esté corriendo en puerto 8001")
    except requests.exceptions.Timeout:
        print("❌ ERROR: Timeout - El servidor tardó mucho en responder")
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: {str(e)}")
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {str(e)}")

def test_health():
    """Probar si el servidor está vivo"""
    print("🏥 Probando salud del servidor...")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/dhl/",
            timeout=5
        )
        print(f"✅ Servidor respondió: {response.status_code}")
        return True
    except:
        print("❌ Servidor no responde")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("🧪 PRUEBA DE ENDPOINT DHL - CREAR PEDIDOS")
    print("=" * 80)
    
    # Verificar si el servidor está vivo
    if test_health():
        print()
        test_endpoint()
    else:
        print("\n❌ El servidor no está disponible. Verifica los contenedores Docker.")
        print("   Ejecuta: docker-compose ps")
    
    print("\n" + "=" * 80)
    print("🏁 Prueba completada")
    print("=" * 80)
