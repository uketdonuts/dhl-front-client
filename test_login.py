#!/usr/bin/env python3
"""
Script de prueba para verificar el login después de arreglar el LoginSerializer
"""

import requests
import json
import time

def test_login():
    # Configurar la URL del backend
    base_url = "http://backend:8000"
    
    # Datos de login de prueba
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print(f"🔐 Probando login en: {base_url}/api/login/")
    print(f"📋 Datos: {login_data}")
    print("-" * 50)
    
    try:
        # Realizar la petición POST al endpoint de login
        response = requests.post(
            f"{base_url}/api/login/",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        print("-" * 50)
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Login exitoso!")
                print(f"🎯 Success: {result.get('success', 'N/A')}")
                if 'access_token' in result:
                    print(f"🔑 Access Token: {result['access_token'][:50]}...")
                if 'user' in result:
                    print(f"👤 Usuario: {result['user'].get('username', 'N/A')}")
                    print(f"📧 Email: {result['user'].get('email', 'N/A')}")
                
            except json.JSONDecodeError:
                print("❌ Error: Respuesta no es JSON válido")
                print(f"📄 Contenido: {response.text}")
                
        elif response.status_code == 401:
            print("❌ Error 401: Credenciales inválidas")
            print(f"📄 Contenido: {response.text}")
        elif response.status_code == 400:
            print("❌ Error 400: Datos inválidos")
            print(f"📄 Contenido: {response.text}")
        else:
            print(f"❌ Error {response.status_code}")
            print(f"📄 Contenido: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al backend")
        print("💡 Asegúrate de que el backend esté ejecutándose")
        
    except requests.exceptions.Timeout:
        print("❌ Error: Timeout al conectar con el backend")
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando prueba de login...")
    print("⏱️ Esperando 2 segundos para que el backend esté listo...")
    time.sleep(2)
    test_login()
