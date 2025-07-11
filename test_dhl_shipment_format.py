#!/usr/bin/env python3
"""
Script para probar el nuevo formato del SOAP request de DHL
que usa el formato exacto del ejemplo que funciona.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dhl_project.settings')
django.setup()

from dhl_api.services import DHLService

def test_dhl_shipment_format():
    """Probar el nuevo formato de envío DHL"""
    
    print("=== PRUEBA DE ENVÍO DHL - FORMATO EXACTO ===")
    print()
    
    # Configurar el servicio DHL para producción
    dhl_service = DHLService(
        username="apO3fS5mJ8zT7h",
        password="J^4oF@1qW!0qS!5b",
        base_url="https://wsbexpress.dhl.com",
        environment="production"  # Usar producción para probar el formato real
    )
    
    # Datos de prueba basados en el ejemplo que funciona
    test_shipment_data = {
        'shipper': {
            'name': 'Test Shipper',
            'company': 'Test Company LATINOAMERICA',
            'phone': '507431-2600',
            'email': 'shipper_test@dhl.com',
            'address': 'Test Address, Building 1',
            'address2': 'Building 1',
            'address3': 'Floor 1',
            'city': 'Test City',
            'state': 'XX',
            'postalCode': '0',
            'country': 'US'
        },
        'recipient': {
            'name': 'Test Recipient Company',
            'company': 'Test Recipient Company',
            'phone': '1234567890',
            'email': 'recipient_test@example.com',
            'address': 'Test Recipient Address',
            'address2': 'Apt 1',
            'city': 'Test City',
            'postalCode': '0',
            'country': 'US',
            'vat': '123456789'
        },
        'package': {
            'weight': 0.3,
            'length': 21,
            'width': 16,
            'height': 11,
            'description': 'Test Package - Electronic Components',
            'value': 54.87,
            'currency': 'USD'
        },
        'service': 'P',  # Priority
        'payment': 'S'   # Shipper pays
    }
    
    print("Datos de prueba:")
    print(f"  Remitente: {test_shipment_data['shipper']['name']} ({test_shipment_data['shipper']['company']})")
    print(f"  Destinatario: {test_shipment_data['recipient']['name']} ({test_shipment_data['recipient']['company']})")
    print(f"  Paquete: {test_shipment_data['package']['weight']} kg, {test_shipment_data['package']['description']}")
    print(f"  Servicio: {test_shipment_data['service']}")
    print()
    
    print("Creando envío...")
    try:
        result = dhl_service.create_shipment(test_shipment_data)
        
        print("=== RESULTADO ===")
        print(f"Éxito: {result.get('success', False)}")
        print(f"Mensaje: {result.get('message', 'Sin mensaje')}")
        
        if result.get('success'):
            print(f"Número de tracking: {result.get('tracking_number', 'No disponible')}")
            print("¡Envío creado exitosamente!")
        else:
            print("Error en la creación del envío:")
            print(f"  Código de error: {result.get('error_code', 'No especificado')}")
            print(f"  Tipo de error: {result.get('error_type', 'No especificado')}")
            if result.get('fault_code'):
                print(f"  Fault Code: {result.get('fault_code')}")
            if result.get('fault_string'):
                print(f"  Fault String: {result.get('fault_string')}")
            if result.get('raw_response'):
                print(f"  Respuesta (primeros 500 chars): {result.get('raw_response')[:500]}")
        
        print()
        print("=== RESPUESTA COMPLETA ===")
        for key, value in result.items():
            if key != 'raw_response':
                print(f"{key}: {value}")
        
    except Exception as e:
        print(f"Error en la prueba: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dhl_shipment_format()
