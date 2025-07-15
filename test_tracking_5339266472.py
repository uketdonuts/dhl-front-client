#!/usr/bin/env python3
"""
Script de prueba para el tracking del número 5339266472
"""

import requests
import json
import time

def test_tracking():
    # Configurar la URL del backend
    base_url = "http://backend:8000"
    
    # Datos de prueba
    tracking_data = {
        "tracking_number": "5339266472"
    }
    
    print(f"🔍 Probando tracking para: {tracking_data['tracking_number']}")
    print(f"📡 Endpoint: {base_url}/api/dhl/tracking/")
    print("-" * 50)
    
    try:
        # Realizar la petición POST
        response = requests.post(
            f"{base_url}/api/dhl/tracking/",
            json=tracking_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        print("-" * 50)
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Respuesta exitosa!")
                print(f"📦 Tracking Number: {result.get('tracking_number', 'N/A')}")
                print(f"📍 Status: {result.get('status', 'N/A')}")
                print(f"📊 Total Events: {result.get('total_events', 'N/A')}")
                print(f"📦 Total Pieces: {result.get('total_pieces', 'N/A')}")
                
                # Mostrar información de piezas si está disponible
                if 'piece_details' in result:
                    print(f"\n📦 Detalles de {len(result['piece_details'])} pieza(s):")
                    for i, piece in enumerate(result['piece_details'], 1):
                        print(f"  Pieza {i}:")
                        print(f"    📏 Dimensiones: {piece.get('dimensions', {})}")
                        print(f"    ⚖️ Peso: {piece.get('weight', {})}")
                        print(f"    📦 Tipo: {piece.get('package_type', 'N/A')}")
                        if 'license_plate' in piece:
                            print(f"    🚛 Placa: {piece['license_plate']}")
                
                # Mostrar eventos si están disponibles
                if 'events' in result and result['events']:
                    print(f"\n📅 Últimos eventos:")
                    for event in result['events'][:3]:  # Mostrar solo los primeros 3
                        print(f"  • {event.get('date', 'N/A')} - {event.get('description', 'N/A')}")
                        if 'location' in event:
                            print(f"    📍 {event['location']}")
                
            except json.JSONDecodeError:
                print("❌ Error: Respuesta no es JSON válido")
                print(f"📄 Contenido: {response.text}")
                
        else:
            print(f"❌ Error {response.status_code}")
            print(f"📄 Contenido: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al backend")
        print("💡 Asegúrate de que el backend esté ejecutándose en el puerto 8001")
        
    except requests.exceptions.Timeout:
        print("❌ Error: Timeout al conectar con el backend")
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando prueba de tracking...")
    print("⏱️ Esperando 3 segundos para que el backend esté listo...")
    time.sleep(3)
    test_tracking()
