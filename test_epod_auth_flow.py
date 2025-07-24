#!/usr/bin/env python3
"""
Test completo del flujo ePOD con autenticación
"""

import requests
import json

# Configuración
BACKEND_URL = "http://localhost:8001"
LOGIN_ENDPOINT = f"{BACKEND_URL}/api/login/"
EPOD_ENDPOINT = f"{BACKEND_URL}/api/dhl/epod/"

def test_complete_epod_flow():
    """Test del flujo completo: Login -> ePOD"""
    
    print("=== Test completo de flujo ePOD ===")
    
    # Paso 1: Login
    print("\n1. Realizando login...")
    login_data = {
        "username": "admin",  # Ajustar según sea necesario
        "password": "admin123"  # Ajustar según sea necesario
    }
    
    try:
        login_response = requests.post(
            LOGIN_ENDPOINT,
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get('access_token')  # Cambiado de 'access' a 'access_token'
            
            if token:
                print("✅ Login exitoso - Token obtenido")
                
                # Paso 2: Probar ePOD con token
                print("\n2. Probando ePOD con autenticación...")
                
                epod_data = {
                    "shipment_id": "1234567890"
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                }
                
                # Probar ePOD
                epod_response = requests.post(
                    EPOD_ENDPOINT,
                    json=epod_data,
                    headers=headers
                )
                
                print(f"ePOD status: {epod_response.status_code}")
                
                if epod_response.status_code == 200:
                    epod_result = epod_response.json()
                    print("✅ ePOD endpoint funcionando correctamente")
                    print(f"Success: {epod_result.get('success')}")
                    print(f"Message: {epod_result.get('message', 'No message')}")
                    
                    if epod_result.get('success'):
                        print("🎉 ¡ePOD obtenido exitosamente!")
                    else:
                        print("⚠️ ePOD no exitoso (normal para número de prueba)")
                        
                else:
                    print(f"❌ Error en ePOD: {epod_response.status_code}")
                    try:
                        error_data = epod_response.json()
                        print(json.dumps(error_data, indent=2))
                    except:
                        print(epod_response.text[:200])

                # Paso 3: Probar Tracking con autenticación
                print("\n3. Probando Tracking con autenticación...")
                
                tracking_endpoint = f"{BACKEND_URL}/api/dhl/tracking/"
                tracking_data = {
                    "tracking_number": "1234567890"
                }
                
                tracking_response = requests.post(
                    tracking_endpoint,
                    json=tracking_data,
                    headers=headers
                )
                
                print(f"Tracking status: {tracking_response.status_code}")
                
                if tracking_response.status_code == 200:
                    tracking_result = tracking_response.json()
                    print("✅ Tracking endpoint funcionando correctamente")
                    print(f"Success: {tracking_result.get('success')}")
                    print(f"Message: {tracking_result.get('message', 'No message')}")
                    
                    if tracking_result.get('success'):
                        print("🎉 ¡Tracking obtenido exitosamente!")
                        if 'tracking_info' in tracking_result:
                            print(f"📦 Status: {tracking_result['tracking_info'].get('status', 'Unknown')}")
                            print(f"📍 Eventos: {tracking_result.get('total_events', 0)}")
                    else:
                        print("⚠️ Tracking no exitoso (normal para número de prueba)")
                        
                else:
                    print(f"❌ Error en Tracking: {tracking_response.status_code}")
                    try:
                        error_data = tracking_response.json()
                        print(json.dumps(error_data, indent=2))
                    except:
                        print(tracking_response.text[:200])
                        
            else:
                print("❌ No se pudo obtener el token")
                print(json.dumps(login_result, indent=2))
                
        else:
            print(f"❌ Error en login: {login_response.status_code}")
            try:
                error_data = login_response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(login_response.text[:200])
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def check_admin_user():
    """Verificar si existe usuario admin"""
    
    print("\n=== Verificando usuario admin ===")
    
    # Intentar con diferentes credenciales comunes
    test_credentials = [
        {"username": "admin", "password": "admin123"},
        {"username": "admin", "password": "admin"},
        {"username": "superuser", "password": "admin123"},
        {"username": "dhl_user", "password": "admin123"},
    ]
    
    for creds in test_credentials:
        try:
            response = requests.post(
                LOGIN_ENDPOINT,
                json=creds,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"✅ Credenciales válidas encontradas: {creds['username']}")
                return creds
            else:
                print(f"❌ {creds['username']}: {response.status_code}")
                
        except Exception as e:
            print(f"Error probando {creds['username']}: {str(e)}")
    
    print("\n⚠️ No se encontraron credenciales válidas")
    print("Para crear un superusuario, ejecuta:")
    print("   django-manage.bat createsuperuser")
    
    return None

if __name__ == "__main__":
    print("Test completo de autenticación y ePOD")
    print("=" * 50)
    
    # Verificar credenciales
    valid_creds = check_admin_user()
    
    if valid_creds:
        # Usar las credenciales encontradas
        test_complete_epod_flow()
    else:
        print("\n❌ No se puede proceder sin credenciales válidas")
        print("\nInstrucciones:")
        print("1. Crear superusuario: django-manage.bat createsuperuser")
        print("2. Usar esas credenciales en el frontend")
        print("3. Después el ePOD funcionará correctamente")
    
    print("\n" + "=" * 50)
    print("Test completado")
