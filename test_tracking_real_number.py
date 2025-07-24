#!/usr/bin/env python3
"""
Test de tracking con número real 1222598506
"""
import requests
import json

def test_tracking_real_number():
    base_url = "http://localhost:8001/api"  # Cambiar puerto a 8001
    
    print("=== PROBANDO TRACKING CON NÚMERO REAL: 1222598506 ===")
    
    # Login
    print("1. Realizando login...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    login_response = requests.post(f"{base_url}/login/", json=login_data)
    if login_response.status_code != 200:
        print(f"❌ Error en login: {login_response.status_code}")
        return
    
    login_result = login_response.json()
    token = login_result.get("access_token", login_result.get("access"))  # Probar ambos campos
    print("✅ Login exitoso")
    
    # Test tracking con número real
    print("2. Probando tracking con número real...")
    tracking_data = {
        "tracking_number": "1222598506"  # El número que se generó en el shipment anterior
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    tracking_response = requests.post(
        f"{base_url}/dhl/tracking/", 
        json=tracking_data, 
        headers=headers
    )
    
    print(f"Status HTTP: {tracking_response.status_code}")
    response_data = tracking_response.json()
    
    print(f"Success: {response_data.get('success', False)}")
    print(f"Message: {response_data.get('message', 'No message')}")
    
    if response_data.get('success'):
        print("🎉 ¡TRACKING EXITOSO!")
        print(f"Eventos encontrados: {response_data.get('total_events', 0)}")
        print(f"Piezas encontradas: {response_data.get('total_pieces', 0)}")
        
        # Mostrar información básica del envío
        tracking_info = response_data.get('tracking_info', {})
        if tracking_info:
            print("\n=== INFORMACIÓN DEL ENVÍO ===")
            print(f"Tracking Number: {tracking_info.get('tracking_number', 'N/A')}")
            print(f"Status: {tracking_info.get('status', 'N/A')}")
            print(f"Descripción: {tracking_info.get('status_description', 'N/A')}")
            print(f"Origen: {tracking_info.get('origin', 'N/A')}")
            print(f"Destino: {tracking_info.get('destination', 'N/A')}")
            print(f"Servicio: {tracking_info.get('service', 'N/A')}")
            print(f"Peso total: {tracking_info.get('total_weight', 'N/A')} {tracking_info.get('weight_unit', '')}")
            print(f"Número de piezas: {tracking_info.get('number_of_pieces', 'N/A')}")
        
        # Mostrar eventos
        events = response_data.get('events', [])
        if events:
            print("\n=== EVENTOS DE TRACKING ===")
            for i, event in enumerate(events):
                print(f"{i+1}. {event.get('timestamp', 'N/A')} - {event.get('status', 'N/A')} en {event.get('location', 'N/A')}")
                if event.get('next_steps'):
                    print(f"   Próximos pasos: {event.get('next_steps')}")
        
        # Mostrar detalles de piezas
        pieces = response_data.get('piece_details', [])
        if pieces:
            print("\n=== DETALLES DE PIEZAS ===")
            for i, piece in enumerate(pieces):
                print(f"Pieza {i+1}:")
                print(f"  ID: {piece.get('piece_id', 'N/A')}")
                print(f"  Descripción: {piece.get('description', 'N/A')}")
                print(f"  Peso: {piece.get('weight', 'N/A')} {piece.get('weight_unit', '')}")
                print(f"  Dimensiones: {piece.get('dimensions', 'N/A')}")
    else:
        print("❌ Tracking no exitoso")
        print(f"Error Code: {response_data.get('error_code', 'N/A')}")
        print(f"Sugerencia: {response_data.get('suggestion', 'N/A')}")
    
    print("\n=== RESPUESTA COMPLETA ===")
    print(json.dumps(response_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_tracking_real_number()
