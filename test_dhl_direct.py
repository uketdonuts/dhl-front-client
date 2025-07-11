#!/usr/bin/env python3
"""
Script para probar directamente el DHLService sin Django
"""

import sys
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dhl_project.settings')
django.setup()

# Ahora importar los modelos de Django
from dhl_api.services import DHLService
import json

# Datos de prueba quemados (basados en el ejemplo real de DHL)
TEST_SHIPMENT_DATA = {
    "shipper": {
        "name": "Guillermo Maduro",
        "company": "SAMSUNG ELECT. LATINOAMERICA ZL", 
        "phone": "507431-2600",
        "email": "shipper_createshipment@dhl.com",
        "address": "Panama Pacifico, J. Cain",
        "city": "Panama",
        "state": "PA",
        "postalCode": "0",
        "country": "PA"
    },
    "recipient": {
        "name": "INVERSIONES ORANGE STORE, C.A.",
        "company": "INVERSIONES ORANGE STORE, C.A.",
        "phone": "58-241-8421411", 
        "email": "samsung@orangestore.com.ve",
        "address": "AV.Universidad CC Freemarket L R04",
        "city": "Caracas",
        "state": "CAR",
        "postalCode": "0",
        "country": "VE"
    },
    "package": {
        "weight": 0.3,
        "length": 21,
        "width": 16,
        "height": 11,
        "description": "SVC JDM-TAPE_GLASSTIC COVER_DECO_SM-A065",
        "value": 54.87,
        "currency": "USD"
    },
    "service": "P",  # Priority
    "payment": "S"   # Shipper pays
}

def test_dhl_service():
    """Probar DHLService directamente"""
    print("🔧 Probando DHLService con datos reales...")
    print("-" * 60)
    
    try:
        # Crear instancia del servicio
        dhl_service = DHLService(
            username="apO3fS5mJ8zT7h",
            password="J^4oF@1qW!0qS!5b", 
            base_url="https://wsbexpress.dhl.com:443",
            environment="production"  # Usar producción para test real
        )
        
        print("📡 Llamando a create_shipment...")
        print(f"📦 Datos de envío:")
        print(json.dumps(TEST_SHIPMENT_DATA, indent=2))
        print("-" * 40)
        
        result = dhl_service.create_shipment(TEST_SHIPMENT_DATA)
        
        print(f"📊 Resultado:")
        print(json.dumps(result, indent=2))
        
        if result.get('success'):
            print("✅ Envío creado exitosamente!")
            if result.get('tracking_number'):
                print(f"📦 Número de tracking: {result['tracking_number']}")
        else:
            print("❌ Error creando envío")
            
        return result
        
    except Exception as e:
        print(f"❌ Error en test: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🧪 SCRIPT DE PRUEBA - DHLService DIRECTO")
    print("=" * 60)
    
    result = test_dhl_service()
    
    print("\n📋 RESUMEN DE PRUEBAS")
    print("=" * 60)
    print(f"Test DHLService: {'✅ OK' if result and result.get('success') else '❌ FAIL'}")
    
    if result and result.get('tracking_number'):
        print(f"\n🎯 TRACKING NUMBER: {result['tracking_number']}")
        print("💡 Usa este número para probar tracking en el frontend")
    
    # Imprimir datos para el frontend
    print("\n📱 DATOS PARA FRONTEND (JSON):")
    print("=" * 60)
    print("Copia estos datos en tu formulario de frontend:")
    print(json.dumps(TEST_SHIPMENT_DATA, indent=2))
