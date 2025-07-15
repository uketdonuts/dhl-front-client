#!/usr/bin/env python3
"""
Script de prueba simple para el tracking del número 5339266472 con credenciales admin/admin
"""

import requests
import json
import time

def test_login_and_tracking():
    # Configurar la URL del backend
    base_url = "http://backend:8000"
    
    # Credenciales de login
    login_data = {
        "username": "admin", 
        "password": "admin"
    }
    
    # Datos de tracking
    tracking_data = {
        "tracking_number": "5339266472"
    }
    
    print(f"🚀 Prueba: Login + Tracking con número 5339266472")
    print(f"📡 Backend: {base_url}")
    print(f"👤 Usuario: {login_data['username']}")
    print("-" * 50)
    
    try:
        # PASO 1: Login
        print("🔐 Iniciando sesión...")
        login_response = requests.post(
            f"{base_url}/api/login/",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            if login_result.get('success'):
                access_token = login_result.get('access_token')
                print(f"✅ Login exitoso! Token: {access_token[:30]}...")
                
                # PASO 2: Tracking
                print(f"\n📦 Buscando tracking para: {tracking_data['tracking_number']}")
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                
                tracking_response = requests.post(
                    f"{base_url}/api/dhl/tracking/",
                    json=tracking_data,
                    headers=headers,
                    timeout=30
                )
                
                print(f"Status: {tracking_response.status_code}")
                
                if tracking_response.status_code == 200:
                    result = tracking_response.json()
                    print("✅ Tracking completado!")
                    print(f"📦 Número: {result.get('tracking_number')}")
                    print(f"✅ Éxito: {result.get('success')}")
                    print(f"📊 Eventos: {result.get('total_events', 0)}")
                    print(f"📦 Piezas: {result.get('total_pieces', 0)}")
                    
                    # Mostrar eventos si existen
                    events = result.get('events', [])
                    if events:
                        print(f"\n📅 Eventos encontrados:")
                        for i, event in enumerate(events[:3], 1):
                            print(f"  {i}. {event.get('date', 'N/A')} - {event.get('description', 'N/A')}")
                    
                    # Mostrar detalles de piezas si existen
                    pieces = result.get('piece_details', [])
                    if pieces:
                        print(f"\n📦 Detalles de piezas:")
                        for i, piece in enumerate(pieces[:2], 1):
                            print(f"  Pieza {i}: {piece}")
                    
                    print(f"\n💬 Mensaje: {result.get('message', 'Sin mensaje')}")
                    
                else:
                    print(f"❌ Error tracking: {tracking_response.status_code}")
                    print(f"Respuesta: {tracking_response.text[:200]}...")
                    
            else:
                print(f"❌ Login falló: {login_result.get('message')}")
        else:
            print(f"❌ Error login: {login_response.status_code}")
            print(f"Respuesta: {login_response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_login_and_tracking()
