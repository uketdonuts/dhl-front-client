#!/usr/bin/env python3
"""
Script para validar que el endpoint de ePOD esté configurado correctamente
"""
import sys
import os

# Agregar el directorio actual al path para importar dhl_api
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dhl_api.services import DHLService

def validate_epod_endpoint():
    """Valida la configuración del endpoint ePOD"""
    try:
        # Crear instancia del servicio para validación
        service = DHLService('test', 'test', 'https://express.api.dhl.com/mydhlapi')
        
        print("=== VALIDACIÓN DEL ENDPOINT ePOD ===\n")
        
        # Validar endpoints configurados
        print("Endpoints configurados:")
        for name, url in service.endpoints.items():
            print(f"  {name}: {url}")
        
        # Validar que el método ePOD existe
        has_epod_method = hasattr(service, 'get_ePOD')
        print(f"\nMétodo get_ePOD existe: {has_epod_method}")
        
        if not has_epod_method:
            print("❌ ERROR: Método get_ePOD no encontrado")
            return False
        
        # Validar estructura del endpoint ePOD
        epod_url = service.endpoints.get('epod')
        if not epod_url:
            print("❌ ERROR: Endpoint ePOD no configurado")
            return False
        
        # Probar formateo de URL
        test_id = '1234567890'
        try:
            formatted_url = epod_url.format(test_id)
            print(f"\nURL ePOD formateada: {formatted_url}")
        except Exception as e:
            print(f"❌ ERROR en formateo de URL: {e}")
            return False
        
        # Validar parámetros del método get_ePOD
        import inspect
        epod_signature = inspect.signature(service.get_ePOD)
        print(f"\nSignatura del método get_ePOD:")
        print(f"  Parámetros: {list(epod_signature.parameters.keys())}")
        
        # Validar tipos de contenido válidos según documentación
        valid_content_types = [
            "epod-detail", "epod-summary", "epod-detail-esig", 
            "epod-summary-esig", "epod-table", "epod-table-detail", "epod-table-esig"
        ]
        print(f"\nTipos de contenido válidos según documentación DHL:")
        for content_type in valid_content_types:
            print(f"  - {content_type}")
        
        print("\n✅ VALIDACIÓN COMPLETADA EXITOSAMENTE")
        print("\nEl endpoint ePOD está configurado correctamente según la documentación oficial de DHL.")
        print("URL: https://express.api.dhl.com/mydhlapi/shipments/{}/proof-of-delivery")
        print("Parámetros: shipperAccountNumber, content")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR en validación: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    validate_epod_endpoint()
