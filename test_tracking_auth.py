#!/usr/bin/env python3
"""
Script de prueba completo para el tracking con autenticación
"""

import requests
import json
import time

def test_tracking_with_auth():
    # Configurar la URL del backend
    base_url = "http://backend:8000"
    
    print("🚀 Iniciando prueba completa de tracking con autenticación...")
    print("⏱️ Esperando 3 segundos para que el backend esté listo...")
    time.sleep(3)
    
    # Datos de login
    login_data = {
        "username": "admin",
        "password": "admin"
    }
    
    # Datos de tracking
    tracking_data = {
        "tracking_number": "5339266472"
    }
    
    print("=" * 60)
    print("PASO 1: LOGIN")
    print("=" * 60)
    print(f"📡 Endpoint: {base_url}/api/login/")
    print(f"👤 Usuario: {login_data['username']}")
    
    try:
        # 1. Hacer login
        login_response = requests.post(
            f"{base_url}/api/login/",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Status Code: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            access_token = login_result.get('access_token')
            
            if access_token:
                print("✅ Login exitoso!")
                print(f"🔑 Token obtenido: {access_token[:20]}...")
                print(f"👤 Usuario: {login_result.get('user', {}).get('username', 'N/A')}")
                print(f"📧 Email: {login_result.get('user', {}).get('email', 'N/A')}")
                
                print("\n" + "=" * 60)
                print("PASO 2: TRACKING")
                print("=" * 60)
                print(f"📡 Endpoint: {base_url}/api/dhl/tracking/")
                print(f"📦 Número de seguimiento: {tracking_data['tracking_number']}")
                
                # 2. Hacer tracking con el token
                tracking_response = requests.post(
                    f"{base_url}/api/dhl/tracking/",
                    json=tracking_data,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {access_token}"
                    },
                    timeout=30
                )
                
                print(f"📊 Status Code: {tracking_response.status_code}")
                
                if tracking_response.status_code == 200:
                    tracking_result = tracking_response.json()
                    print("✅ Tracking exitoso!")
                    print("\n📋 RESULTADOS DEL TRACKING:")
                    print("-" * 40)
                    print(f"📦 Número de seguimiento: {tracking_result.get('tracking_number', 'N/A')}")
                    print(f"📍 Estado: {tracking_result.get('status', 'N/A')}")
                    print(f"📊 Total eventos: {tracking_result.get('total_events', 'N/A')}")
                    print(f"📦 Total piezas: {tracking_result.get('total_pieces', 'N/A')}")
                    
                    # Mostrar información de piezas si está disponible
                    if 'piece_details' in tracking_result and tracking_result['piece_details']:
                        print(f"\n📦 DETALLES DE {len(tracking_result['piece_details'])} PIEZA(S):")
                        print("-" * 40)
                        for i, piece in enumerate(tracking_result['piece_details'], 1):
                            print(f"\n  📦 Pieza {i}:")
                            
                            # Dimensiones
                            dims = piece.get('dimensions', {})
                            if dims:
                                print(f"    📏 Dimensiones:")
                                if 'actual' in dims:
                                    actual = dims['actual']
                                    print(f"      Reales: {actual.get('length', 'N/A')} x {actual.get('width', 'N/A')} x {actual.get('height', 'N/A')} {actual.get('unit', '')}")
                                if 'declared' in dims:
                                    declared = dims['declared']
                                    print(f"      Declaradas: {declared.get('length', 'N/A')} x {declared.get('width', 'N/A')} x {declared.get('height', 'N/A')} {declared.get('unit', '')}")
                            
                            # Peso
                            weight = piece.get('weight', {})
                            if weight:
                                print(f"    ⚖️ Peso:")
                                if 'actual' in weight:
                                    actual = weight['actual']
                                    print(f"      Real: {actual.get('value', 'N/A')} {actual.get('unit', '')}")
                                if 'declared' in weight:
                                    declared = weight['declared']
                                    print(f"      Declarado: {declared.get('value', 'N/A')} {declared.get('unit', '')}")
                            
                            # Otros detalles
                            if 'package_type' in piece:
                                print(f"    📦 Tipo: {piece['package_type']}")
                            if 'license_plate' in piece:
                                print(f"    🚛 Placa: {piece['license_plate']}")
                    
                    # Mostrar eventos si están disponibles
                    if 'events' in tracking_result and tracking_result['events']:
                        print(f"\n📅 EVENTOS DE SEGUIMIENTO (Últimos 5):")
                        print("-" * 40)
                        for i, event in enumerate(tracking_result['events'][:5], 1):
                            print(f"\n  📅 Evento {i}:")
                            print(f"    Fecha: {event.get('date', 'N/A')}")
                            print(f"    Descripción: {event.get('description', 'N/A')}")
                            if 'location' in event:
                                print(f"    📍 Ubicación: {event['location']}")
                            if 'code' in event:
                                print(f"    🔢 Código: {event['code']}")
                    
                    print("\n🎉 ¡PRUEBA COMPLETADA EXITOSAMENTE!")
                    
                else:
                    print(f"❌ Error en tracking: {tracking_response.status_code}")
                    try:
                        error_data = tracking_response.json()
                        print(f"📄 Error: {error_data}")
                    except:
                        print(f"📄 Contenido: {tracking_response.text}")
            else:
                print("❌ No se obtuvo token de acceso")
                print(f"📄 Respuesta: {login_result}")
        else:
            print(f"❌ Error en login: {login_response.status_code}")
            try:
                error_data = login_response.json()
                print(f"📄 Error: {error_data}")
            except:
                print(f"📄 Contenido: {login_response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al backend")
        print("💡 Asegúrate de que el backend esté ejecutándose")
        
    except requests.exceptions.Timeout:
        print("❌ Error: Timeout al conectar con el backend")
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    test_tracking_with_auth()
