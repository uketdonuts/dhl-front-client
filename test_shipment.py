#!/usr/bin/env python3
"""
Script para probar el endpoint de creación de envíos DHL
Usa datos quemados para testing fácil
"""

import requests
import json
from datetime import datetime, timedelta

# Configuración del endpoint
BASE_URL = "http://localhost:8000"
SHIPMENT_ENDPOINT = f"{BASE_URL}/api/dhl/shipment/"

# Datos de prueba quemados (basados en el ejemplo real de DHL)
TEST_SHIPMENT_DATA = {
    "shipper": {
        "name": "Guillermo Maduro",
        "company": "SAMSUNG ELECT. LATINOAMERICA ZL", 
        "phone": "507431-2600",
        "email": "shipper_createshipment@dhl.com",
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

def test_shipment_endpoint():
    """Probar el endpoint de envíos"""
    print("🚀 Probando endpoint de creación de envíos DHL...")
    print(f"Endpoint: {SHIPMENT_ENDPOINT}")
    print(f"Datos de prueba: {json.dumps(TEST_SHIPMENT_DATA, indent=2)}")
    print("-" * 60)
    
    try:
        # Hacer request al endpoint
        print("📡 Enviando request...")
        response = requests.post(
            SHIPMENT_ENDPOINT,
            json=TEST_SHIPMENT_DATA,
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer fake_token_for_testing'  # Solo para testing
            },
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📊 Headers: {dict(response.headers)}")
        
        # Intentar parsear JSON
        try:
            response_data = response.json()
            print(f"📊 Response JSON:")
            print(json.dumps(response_data, indent=2))
        except json.JSONDecodeError:
            print(f"📊 Response Text:")
            print(response.text[:500])
            
        # Evaluar resultado
        if response.status_code == 200 or response.status_code == 201:
            print("✅ Request exitoso!")
            return response_data if 'response_data' in locals() else response.text
        else:
            print(f"❌ Request falló con código {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión - ¿Está corriendo el servidor Django?")
        print("💡 Ejecuta: python manage.py runserver")
        return None
    except requests.exceptions.Timeout:
        print("❌ Timeout - El servidor tardó demasiado en responder")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return None

def test_direct_dhl_service():
    """Probar DHLService directamente"""
    print("\n🔧 Probando DHLService directamente...")
    print("-" * 60)
    
    try:
        # Importar DHLService
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from dhl_api.services import DHLService
        
        # Crear instancia del servicio
        dhl_service = DHLService(
            username="apO3fS5mJ8zT7h",
            password="J^4oF@1qW!0qS!5b", 
            base_url="https://wsbexpress.dhl.com:443",
            environment="production"  # Usar producción para test real
        )
        
        print("📡 Llamando a create_shipment...")
        result = dhl_service.create_shipment(TEST_SHIPMENT_DATA)
        
        print(f"📊 Resultado:")
        print(json.dumps(result, indent=2))
        
        if result.get('success'):
            print("✅ Envío creado exitosamente!")
            if result.get('tracking_number'):
                print(f"📦 Número de tracking: {result['tracking_number']}")
        else:
            print("❌ Error creando envío")
            
        return result
        
    except ImportError as e:
        print(f"❌ Error importando DHLService: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Error en test directo: {str(e)}")
        return None

if __name__ == "__main__":
    print("🧪 SCRIPT DE PRUEBA - ENDPOINT DHL SHIPMENTS")
    print("=" * 60)
    
    # Test 1: Endpoint completo
    result1 = test_shipment_endpoint()
    
    # Test 2: Servicio directo
    result2 = test_direct_dhl_service()
    
    print("\n📋 RESUMEN DE PRUEBAS")
    print("=" * 60)
    print(f"Test Endpoint: {'✅ OK' if result1 else '❌ FAIL'}")
    print(f"Test Directo: {'✅ OK' if result2 and result2.get('success') else '❌ FAIL'}")
    
    if result2 and result2.get('tracking_number'):
        print(f"\n🎯 TRACKING NUMBER: {result2['tracking_number']}")
        print("💡 Usa este número para probar tracking en el frontend")
