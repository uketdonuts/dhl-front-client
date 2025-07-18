#!/usr/bin/env python3
"""
Script para debuggear el problema de tracking
"""
import os
import sys
import django
from django.conf import settings

# Configurar path para importar el módulo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from dhl_api.services import DHLService
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_tracking():
    """Prueba el tracking con diferentes números"""
    
    # Crear servicio DHL
    dhl_service = DHLService(
        username=settings.DHL_USERNAME,
        password=settings.DHL_PASSWORD,
        base_url=settings.DHL_BASE_URL,
        environment=settings.DHL_ENVIRONMENT
    )
    
    # Números de tracking para probar
    tracking_numbers = [
        "5339266472",  # Número del frontend
        "1234567890",  # Número genérico
        "7777777777"   # Número de prueba
    ]
    
    print("=== DEBUGGING TRACKING ===")
    print(f"Environment: {settings.DHL_ENVIRONMENT}")
    print(f"Username: {settings.DHL_USERNAME}")
    print(f"Base URL: {settings.DHL_BASE_URL}")
    print()
    
    for tracking_number in tracking_numbers:
        print(f"🔍 Probando tracking para: {tracking_number}")
        print("-" * 50)
        
        try:
            # Llamar al servicio
            result = dhl_service.get_tracking(tracking_number)
            
            print(f"✅ Resultado del tracking:")
            print(f"   Success: {result.get('success', False)}")
            print(f"   Message: {result.get('message', 'No message')}")
            
            if result.get('success'):
                tracking_info = result.get('tracking_info', {})
                print(f"   AWB Number: {tracking_info.get('awb_number', 'N/A')}")
                print(f"   Status: {tracking_info.get('status', 'N/A')}")
                print(f"   Origin: {tracking_info.get('origin', 'N/A')}")
                print(f"   Destination: {tracking_info.get('destination', 'N/A')}")
                
                events = result.get('events', [])
                print(f"   Total Events: {len(events)}")
                
                if events:
                    print(f"   Últimos eventos:")
                    for event in events[:3]:  # Mostrar solo los primeros 3
                        print(f"     - {event.get('date', 'N/A')} {event.get('time', 'N/A')}: {event.get('description', 'N/A')}")
            else:
                print(f"   Error Code: {result.get('error_code', 'N/A')}")
                print(f"   Raw Response: {result.get('raw_response', 'N/A')[:200]}...")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            
        print()

if __name__ == "__main__":
    test_tracking()
