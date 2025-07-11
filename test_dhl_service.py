#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del servicio DHL
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dhl_api.services import DHLService
from datetime import datetime, timedelta
import json

def test_dhl_service():
    """Prueba completa del servicio DHL"""
    
    print("🚀 Iniciando pruebas del servicio DHL...")
    print("=" * 50)
    
    # Configurar el servicio DHL
    dhl_service = DHLService(
        username="apO3fS5mJ8zT7h",
        password="J^4oF@1qW!0qS!5b",
        base_url="https://wsbexpress.dhl.com",
        environment="production"  # Usar producción para pruebas reales
    )
    
    # 1. Probar validación de fecha
    print("\n1. ✅ Probando validación de fecha de envío...")
    
    # Fecha válida (mañana)
    valid_date = dhl_service._get_valid_ship_timestamp()
    print(f"   Fecha válida generada: {valid_date}")
    
    # Fecha en el pasado (debería corregirse)
    past_date = datetime.now() - timedelta(days=1)
    corrected_date = dhl_service._get_valid_ship_timestamp(past_date)
    print(f"   Fecha pasada corregida: {corrected_date}")
    
    # Fecha muy futura (debería limitarse)
    future_date = datetime.now() + timedelta(days=15)
    limited_date = dhl_service._get_valid_ship_timestamp(future_date)
    print(f"   Fecha futura limitada: {limited_date}")
    
    # 2. Probar generación de XML para múltiples paquetes
    print("\n2. ✅ Probando generación de XML para múltiples paquetes...")
    
    packages = [
        {"weight": 0.3, "length": 21, "width": 16, "height": 11, "reference": "PKG001"},
        {"weight": 0.5, "length": 25, "width": 20, "height": 15, "reference": "PKG002"},
        {"weight": 0.4, "length": 22, "width": 18, "height": 12, "reference": "PKG003"}
    ]
    
    packages_xml = dhl_service._generate_packages_xml(packages, "TEST123")
    print(f"   XML generado para {len(packages)} paquetes:")
    print(f"   {packages_xml[:200]}...")
    
    # 3. Probar creación de envío en modo sandbox
    print("\n3. ✅ Probando creación de envío (modo sandbox)...")
    
    # Cambiar a sandbox para pruebas seguras
    dhl_service.environment = "sandbox"
    
    shipment_data = {
        "shipper": {
            "name": "Juan Pérez",
            "company": "Empresa Test",
            "address": "Calle Test 123",
            "city": "Madrid",
            "state": "MD",
            "postalCode": "28001",
            "country": "ES",
            "phone": "912345678",
            "email": "test@empresa.com"
        },
        "recipient": {
            "name": "María González",
            "company": "Destino Test",
            "address": "Avenida Destino 456",
            "city": "Barcelona",
            "postalCode": "08001",
            "country": "ES",
            "phone": "934567890",
            "email": "destino@test.com"
        },
        "packages": [
            {"weight": 0.3, "length": 21, "width": 16, "height": 11, "reference": "PKG001"},
            {"weight": 0.5, "length": 25, "width": 20, "height": 15, "reference": "PKG002"}
        ],
        "service": "P",
        "payment": "S"
    }
    
    result = dhl_service.create_shipment(shipment_data)
    print(f"   Resultado: {result['success']}")
    print(f"   Mensaje: {result['message']}")
    if result['success']:
        print(f"   Tracking: {result.get('tracking_number', 'N/A')}")
    
    # 4. Probar cotización de tarifas
    print("\n4. ✅ Probando cotización de tarifas...")
    
    origin = {
        "address": "Calle Origen 123",
        "city": "Madrid",
        "state": "MD",
        "postal_code": "28001",
        "country": "ES"
    }
    
    destination = {
        "address": "Calle Destino 456",
        "city": "Barcelona",
        "postal_code": "08001",
        "country": "ES"
    }
    
    dimensions = {"length": 21, "width": 16, "height": 11}
    
    rates_result = dhl_service.get_rate(origin, destination, 0.5, dimensions)
    print(f"   Resultado: {rates_result['success']}")
    print(f"   Mensaje: {rates_result['message']}")
    if rates_result['success']:
        print(f"   Tarifas encontradas: {len(rates_result.get('rates', []))}")
        for rate in rates_result.get('rates', [])[:3]:  # Mostrar primeras 3
            print(f"     - {rate['service_name']}: ${rate['total_charge']} {rate['currency']}")
    
    # 5. Probar seguimiento
    print("\n5. ✅ Probando seguimiento...")
    
    tracking_result = dhl_service.get_tracking("1234567890")
    print(f"   Resultado: {tracking_result['success']}")
    print(f"   Mensaje: {tracking_result['message']}")
    if tracking_result['success']:
        info = tracking_result.get('tracking_info', {})
        print(f"   Estado: {info.get('status', 'N/A')}")
        print(f"   Eventos: {len(tracking_result.get('events', []))}")
    
    # 6. Probar con datos reales (solo si se especifica)
    if len(sys.argv) > 1 and sys.argv[1] == "--real":
        print("\n6. ⚠️  Probando con API real de DHL...")
        
        # Volver a producción
        dhl_service.environment = "production"
        
        # Datos mínimos para prueba real
        real_shipment_data = {
            "shipper": {
                "name": "Test Shipper",
                "company": "Test Company",
                "address": "Test Address",
                "city": "Test City",
                "state": "XX",
                "postalCode": "00000",
                "country": "US",
                "phone": "1234567890",
                "email": "test@test.com"
            },
            "recipient": {
                "name": "Test Recipient",
                "company": "Test Company",
                "address": "Test Address",
                "city": "Test City",
                "postalCode": "00000",
                "country": "US",
                "phone": "1234567890",
                "email": "test@test.com"
            },
            "package": {
                "weight": 0.3,
                "length": 21,
                "width": 16,
                "height": 11,
                "description": "Test Package",
                "value": 100,
                "currency": "USD"
            },
            "service": "P",
            "payment": "S"
        }
        
        real_result = dhl_service.create_shipment(real_shipment_data)
        print(f"   Resultado real: {real_result['success']}")
        print(f"   Mensaje: {real_result['message']}")
        if not real_result['success']:
            print(f"   Errores: {real_result.get('errors', [])}")
    
    print("\n" + "=" * 50)
    print("🎉 Pruebas completadas!")
    print("\nPara probar con la API real de DHL, ejecuta:")
    print("python test_dhl_service.py --real")
    print("\n⚠️  ADVERTENCIA: Las pruebas reales pueden generar cargos en DHL")

if __name__ == "__main__":
    test_dhl_service()
