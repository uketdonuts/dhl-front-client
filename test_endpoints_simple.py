#!/usr/bin/env python3
"""
Script simple para verificar el estado de los endpoints DHL usando solo librerías estándar.
"""

import urllib.request
import urllib.parse
import json
import sys

def make_request(url, method='GET', data=None, headers=None):
    """Hacer request HTTP usando urllib"""
    try:
        if headers is None:
            headers = {}
        
        if method == 'POST' and data:
            if isinstance(data, dict):
                data = json.dumps(data).encode('utf-8')
                headers['Content-Type'] = 'application/json'
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
        else:
            req = urllib.request.Request(url, headers=headers, method=method)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.getcode(), response.read().decode('utf-8')
    
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return 0, str(e)

def test_endpoints():
    """Probar los endpoints DHL"""
    
    base_url = "http://localhost:8000/api"
    
    print("=== VERIFICACIÓN DE ENDPOINTS DHL ===")
    print(f"Base URL: {base_url}")
    print()
    
    # 1. Probar endpoint de estado
    print("1. Verificando estado de conexión...")
    status_code, response_text = make_request(f"{base_url}/test/connection-status/")
    print(f"   Status: {status_code}")
    
    if status_code == 200:
        try:
            data = json.loads(response_text)
            print(f"   ✅ Endpoint funcional")
            service_info = data.get('service_info', {})
            print(f"   Credenciales: {service_info.get('credentials', 'No disponible')}")
            print(f"   Account: {service_info.get('account_number', 'No disponible')}")
        except:
            print(f"   ⚠️  Respuesta no es JSON válido")
    else:
        print(f"   ❌ Error: {response_text[:200]}")
    
    print()
    
    # 2. Probar datos hardcodeados
    print("2. Verificando datos hardcodeados...")
    status_code, response_text = make_request(f"{base_url}/test/hardcoded-data/")
    print(f"   Status: {status_code}")
    
    if status_code == 200:
        try:
            data = json.loads(response_text)
            print(f"   ✅ Datos disponibles")
            test_data = data.get('test_data', {})
            print(f"   Remitente: {test_data.get('shipper', {}).get('name', 'No disponible')}")
            print(f"   Destinatario: {test_data.get('recipient', {}).get('name', 'No disponible')}")
        except:
            print(f"   ⚠️  Respuesta no es JSON válido")
    else:
        print(f"   ❌ Error: {response_text[:200]}")
    
    print()
    
    # 3. Probar creación de envío en sandbox
    print("3. Probando creación de envío (sandbox)...")
    payload = {
        "environment": "sandbox",
        "use_hardcoded": True
    }
    
    status_code, response_text = make_request(
        f"{base_url}/test/shipment-new-format/",
        method='POST',
        data=payload
    )
    
    print(f"   Status: {status_code}")
    
    if status_code == 200:
        try:
            data = json.loads(response_text)
            print(f"   ✅ Envío procesado")
            print(f"   Éxito: {data.get('success', False)}")
            print(f"   Mensaje: {data.get('message', 'No disponible')}")
            if data.get('tracking_number'):
                print(f"   Tracking: {data.get('tracking_number')}")
            print(f"   Entorno: {data.get('environment', 'No disponible')}")
        except:
            print(f"   ⚠️  Respuesta no es JSON válido")
            print(f"   Respuesta: {response_text[:300]}")
    else:
        print(f"   ❌ Error: {response_text[:200]}")
    
    print()
    
    # 4. Mostrar información del formato
    print("4. Información del formato nuevo:")
    print("   URL: https://wsbexpress.dhl.com:443/sndpt/expressRateBook")
    print("   Credentials: apO3fS5mJ8zT7h:J^4oF@1qW!0qS!5b")
    print("   Account: 706065602")
    print("   Format: Formato exacto del ejemplo que funciona")
    
    print()
    
    # 5. Preguntar si probar producción
    print("5. ¿Desea probar el endpoint de producción? (y/N):")
    try:
        response = input().strip().lower()
        if response == 'y':
            print("   Probando con API real de DHL...")
            payload = {
                "environment": "production",
                "use_hardcoded": True
            }
            
            status_code, response_text = make_request(
                f"{base_url}/test/shipment-new-format/",
                method='POST',
                data=payload
            )
            
            print(f"   Status: {status_code}")
            
            if status_code == 200:
                try:
                    data = json.loads(response_text)
                    print(f"   ✅ Respuesta del API real")
                    print(f"   Éxito: {data.get('success', False)}")
                    print(f"   Mensaje: {data.get('message', 'No disponible')}")
                    
                    if data.get('tracking_number'):
                        print(f"   🎉 ¡TRACKING REAL!: {data.get('tracking_number')}")
                    
                    if data.get('error_code'):
                        print(f"   Error code: {data.get('error_code')}")
                    if data.get('fault_string'):
                        print(f"   Fault string: {data.get('fault_string')}")
                    
                except:
                    print(f"   ⚠️  Respuesta no es JSON válido")
                    print(f"   Respuesta: {response_text[:500]}")
            else:
                print(f"   ❌ Error: {response_text[:200]}")
        else:
            print("   ⏭️  Saltando prueba de producción")
    except KeyboardInterrupt:
        print("   ⏭️  Saltando prueba de producción")
    
    print()
    print("=== VERIFICACIÓN COMPLETADA ===")

if __name__ == "__main__":
    test_endpoints()
