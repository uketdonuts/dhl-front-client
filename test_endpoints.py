#!/usr/bin/env python3
"""
Script para probar los nuevos endpoints DHL desde fuera del contenedor Docker.
Este script hace requests HTTP a los endpoints de prueba.
"""

import requests
import json
import time

def test_dhl_endpoints():
    """Probar los nuevos endpoints DHL"""
    
    # Base URL del API
    base_url = "http://localhost:8000/api"
    
    print("=== PRUEBAS DE ENDPOINTS DHL - FORMATO NUEVO ===")
    print(f"Base URL: {base_url}")
    print()
    
    # 1. Probar endpoint de estado de conexión
    print("1. Probando endpoint de estado de conexión...")
    try:
        response = requests.get(f"{base_url}/test/connection-status/", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Conexión OK")
            print(f"   Credenciales: {data.get('service_info', {}).get('credentials', 'No disponible')}")
            print(f"   Account: {data.get('service_info', {}).get('account_number', 'No disponible')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print()
    
    # 2. Probar endpoint de datos hardcodeados
    print("2. Probando endpoint de datos hardcodeados...")
    try:
        response = requests.get(f"{base_url}/test/hardcoded-data/", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Datos obtenidos")
            test_data = data.get('test_data', {})
            print(f"   Remitente: {test_data.get('shipper', {}).get('name', 'No disponible')}")
            print(f"   Destinatario: {test_data.get('recipient', {}).get('name', 'No disponible')}")
            print(f"   Servicio: {test_data.get('service', 'No disponible')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print()
    
    # 3. Probar endpoint de envío con formato nuevo (modo sandbox)
    print("3. Probando creación de envío - modo SANDBOX...")
    try:
        payload = {
            "environment": "sandbox",
            "use_hardcoded": True
        }
        
        response = requests.post(
            f"{base_url}/test/shipment-new-format/",
            json=payload,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Envío procesado")
            print(f"   Éxito: {data.get('success', False)}")
            print(f"   Mensaje: {data.get('message', 'No disponible')}")
            if data.get('tracking_number'):
                print(f"   Tracking: {data.get('tracking_number')}")
            if data.get('environment'):
                print(f"   Entorno: {data.get('environment')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print()
    
    # 4. Probar endpoint de envío directo (modo sandbox)
    print("4. Probando servicio directo - modo SANDBOX...")
    try:
        payload = {
            "environment": "sandbox"
        }
        
        response = requests.post(
            f"{base_url}/test/shipment-direct-service/",
            json=payload,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Servicio directo procesado")
            print(f"   Éxito: {data.get('success', False)}")
            print(f"   Mensaje: {data.get('message', 'No disponible')}")
            if data.get('tracking_number'):
                print(f"   Tracking: {data.get('tracking_number')}")
            test_info = data.get('test_info', {})
            if test_info:
                print(f"   Endpoint: {test_info.get('endpoint', 'No disponible')}")
                print(f"   Formato: {test_info.get('format', 'No disponible')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print()
    
    # 5. Probar endpoint de envío con formato nuevo (modo producción)
    print("5. Probando creación de envío - modo PRODUCCIÓN...")
    response_input = input("   ¿Desea probar con el API real de DHL? (y/N): ")
    
    if response_input.lower() == 'y':
        try:
            payload = {
                "environment": "production",
                "use_hardcoded": True
            }
            
            print("   ⚠️  ADVERTENCIA: Esto hará una llamada real al API de DHL")
            print("   Enviando request...")
            
            response = requests.post(
                f"{base_url}/test/shipment-new-format/",
                json=payload,
                timeout=60
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Envío procesado")
                print(f"   Éxito: {data.get('success', False)}")
                print(f"   Mensaje: {data.get('message', 'No disponible')}")
                if data.get('tracking_number'):
                    print(f"   🎉 ¡TRACKING REAL!: {data.get('tracking_number')}")
                if data.get('error_code'):
                    print(f"   Error code: {data.get('error_code')}")
                if data.get('fault_string'):
                    print(f"   Fault string: {data.get('fault_string')}")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    else:
        print("   ⏭️  Saltando prueba de producción")
    
    print()
    print("=== PRUEBAS COMPLETADAS ===")

if __name__ == "__main__":
    test_dhl_endpoints()
