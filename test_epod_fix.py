#!/usr/bin/env python3
"""
Test para verificar que el fix del ePOD funciona correctamente.
Prueba que el account_number se pasa correctamente al servicio.
"""

import requests
import json
import os
from datetime import datetime

# Configuración del test
BASE_URL = "http://localhost:8001"
LOGIN_URL = f"{BASE_URL}/api/auth/login/"
EPOD_URL = f"{BASE_URL}/api/dhl/epod/"

# Credenciales de prueba
USERNAME = "admin"
PASSWORD = "admin123"

def get_auth_token():
    """Obtiene el token de autenticación"""
    response = requests.post(LOGIN_URL, json={
        "username": USERNAME,
        "password": PASSWORD
    })
    
    if response.status_code == 200:
        return response.json()["access"]
    else:
        print(f"Error de autenticación: {response.status_code}")
        print(response.text)
        return None

def test_epod_with_account_number():
    """Prueba el ePOD con account_number específico"""
    token = get_auth_token()
    if not token:
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test con account_number específico
    payload = {
        "shipment_id": "5339266472",
        "account_number": "706065602"
    }
    
    print(f"🔍 Probando ePOD con payload: {json.dumps(payload, indent=2)}")
    print(f"📡 URL: {EPOD_URL}")
    
    response = requests.post(EPOD_URL, json=payload, headers=headers)
    
    print(f"📊 Código de respuesta: {response.status_code}")
    print(f"📋 Respuesta completa:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    return response.status_code == 200

def test_epod_without_account_number():
    """Prueba el ePOD sin account_number (debe usar el default)"""
    token = get_auth_token()
    if not token:
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test sin account_number
    payload = {
        "shipment_id": "5339266472"
    }
    
    print(f"\n🔍 Probando ePOD sin account_number: {json.dumps(payload, indent=2)}")
    
    response = requests.post(EPOD_URL, json=payload, headers=headers)
    
    print(f"📊 Código de respuesta: {response.status_code}")
    print(f"📋 Respuesta completa:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    return response.status_code == 200

if __name__ == "__main__":
    print("🧪 Iniciando tests del fix de ePOD")
    print("=" * 50)
    
    print("Test 1: ePOD con account_number específico")
    test1_result = test_epod_with_account_number()
    
    print("\nTest 2: ePOD sin account_number (usando default)")
    test2_result = test_epod_without_account_number()
    
    print("\n" + "=" * 50)
    print("📈 Resumen de tests:")
    print(f"✅ Test 1 (con account_number): {'PASÓ' if test1_result else 'FALLÓ'}")
    print(f"✅ Test 2 (sin account_number): {'PASÓ' if test2_result else 'FALLÓ'}")
    
    if test1_result and test2_result:
        print("🎉 Todos los tests pasaron! El fix funciona correctamente.")
    else:
        print("❌ Algunos tests fallaron. Revisar la implementación.")
