#!/usr/bin/env python3
"""
Test simple para verificar funcionalidad ePOD desde el frontend
"""

import requests
import json
import os
import sys

# Configuración
BACKEND_URL = "http://localhost:8001"  # Ajustar según tu configuración
API_ENDPOINT = f"{BACKEND_URL}/api/dhl/epod/"

def test_epod_functionality():
    """Test de funcionalidad ePOD"""
    
    print("=== Test de funcionalidad ePOD ===")
    print(f"URL del API: {API_ENDPOINT}")
    
    # Datos de prueba
    test_data = {
        "shipment_id": "1234567890"  # Número de prueba
    }
    
    # Headers básicos
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    print(f"Datos de prueba: {json.dumps(test_data, indent=2)}")
    
    try:
        # Hacer la petición
        print("\n--- Enviando petición ePOD ---")
        response = requests.post(
            API_ENDPOINT,
            json=test_data,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers de respuesta: {dict(response.headers)}")
        
        # Analizar respuesta
        if response.status_code == 200:
            try:
                result = response.json()
                print("\n--- Respuesta exitosa ---")
                print(json.dumps(result, indent=2))
                
                # Verificar estructura de respuesta
                if result.get('success'):
                    print("\n✅ ePOD obtenido exitosamente")
                    if 'pdf_data' in result:
                        print(f"📄 PDF disponible: {len(result['pdf_data'])} caracteres")
                    if 'epod_data' in result:
                        print(f"📋 Datos ePOD disponibles")
                else:
                    print(f"\n⚠️ ePOD no exitoso: {result.get('message', 'Sin mensaje')}")
                    
            except json.JSONDecodeError:
                print(f"\n❌ Error decodificando JSON:")
                print(response.text[:500])
        
        elif response.status_code == 401:
            print("\n🔒 Error de autenticación - Token requerido")
            print("Respuesta:", response.text[:200])
        
        elif response.status_code == 400:
            print("\n❌ Error de validación")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(response.text[:200])
        
        else:
            print(f"\n❌ Error HTTP {response.status_code}")
            print(response.text[:200])
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error de conexión - ¿Está el backend ejecutándose en {BACKEND_URL}?")
    
    except requests.exceptions.Timeout:
        print("\n❌ Timeout - El backend tardó demasiado en responder")
    
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")

def test_backend_health():
    """Verificar que el backend esté funcionando"""
    
    print("\n=== Test de salud del backend ===")
    
    try:
        health_url = f"{BACKEND_URL}/api/"
        response = requests.get(health_url, timeout=10)
        print(f"Backend status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Backend está funcionando")
            return True
        else:
            print(f"⚠️ Backend responde con código {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ No se puede conectar al backend en {BACKEND_URL}")
        return False
    except Exception as e:
        print(f"❌ Error verificando backend: {str(e)}")
        return False

if __name__ == "__main__":
    print("Test de funcionalidad ePOD Frontend")
    print("=" * 50)
    
    # Test 1: Verificar backend
    backend_ok = test_backend_health()
    
    # Test 2: Probar ePOD
    if backend_ok:
        test_epod_functionality()
    else:
        print("\n❌ No se puede proceder - Backend no disponible")
        print("\nPasos para solucionar:")
        print("1. Asegúrate de que Docker esté ejecutándose")
        print("2. Ejecuta: docker-dev.bat up")
        print("3. Verifica que el backend esté en puerto 8001")
    
    print("\n" + "=" * 50)
    print("Test completado")
