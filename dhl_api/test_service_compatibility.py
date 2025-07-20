#!/usr/bin/env python3
"""
Script de prueba para verificar la información de compatibilidad de servicios DHL
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dhl_project.settings')
django.setup()

from dhl_api.services import DHLService

def test_service_compatibility():
    print("=== PRUEBA DE COMPATIBILIDAD DE SERVICIOS DHL ===")
    print()
    
    # Instanciar el servicio
    dhl_service = DHLService("user", "pass", "url", "sandbox")
    
    # Códigos de servicio comunes de DHL
    test_codes = ['N', 'P', 'T', 'Y', 'U', 'K', 'L', 'Q', 'D', 'W', 'X', 'Z']
    
    for code in test_codes:
        compatibility = dhl_service.get_service_content_compatibility(code)
        
        print(f"📦 Servicio {code}:")
        print(f"   Descripción: {compatibility['restrictions']}")
        print(f"   Documentos: {'✅' if compatibility.get('documents') else '❌'}")
        print(f"   Paquetes: {'✅' if compatibility.get('packages') else '❌'}")
        print(f"   Pallets: {'✅' if compatibility.get('pallets') else '❌'}")
        print()

if __name__ == "__main__":
    test_service_compatibility()
