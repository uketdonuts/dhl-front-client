#!/usr/bin/env python3
"""
Test simple para el tracking
"""
import os
import sys
import django
import logging
import traceback

# Configurar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from dhl_api.services import DHLService
from django.conf import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def simple_tracking_test():
    """Test básico del tracking"""
    print("=== TEST SIMPLE TRACKING ===")
    
    try:
        # Crear servicio
        print("1. Creando servicio DHL...")
        dhl_service = DHLService(
            username=settings.DHL_USERNAME,
            password=settings.DHL_PASSWORD,
            base_url=settings.DHL_BASE_URL,
            environment=settings.DHL_ENVIRONMENT
        )
        print("   ✅ Servicio creado")
        
        # Probar tracking
        print("2. Probando tracking...")
        tracking_number = "5339266472"
        result = dhl_service.get_tracking(tracking_number)
        
        print(f"   ✅ Resultado obtenido: {result}")
        
        if result.get('success'):
            print("   🎉 ¡Tracking exitoso!")
        else:
            print(f"   ❌ Error: {result.get('message', 'Sin mensaje')}")
            
    except Exception as e:
        print(f"❌ Error en el test: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    simple_tracking_test()
