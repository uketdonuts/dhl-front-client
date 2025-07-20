#!/usr/bin/env python3
"""
Script para probar la cotización con los datos exactos del frontend
y ver la respuesta completa de DHL
"""

import json
import sys
import os

# Agregar el directorio raíz al path para importar los módulos de Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dhl_project.settings')

import django
django.setup()

from dhl_api.services import DHLService

def test_frontend_rate_data():
    """Prueba la cotización con los datos exactos del frontend"""
    
    # Datos exactos del frontend Dashboard.js
    test_data = {
        "origin": {
            "postal_code": "0000",
            "city": "Panama",
            "country": "PA",
            "state": "PA"
        },
        "destination": {
            "postal_code": "110111",
            "city": "BOG", 
            "country": "CO"
        },
        "weight": 45,
        "dimensions": {
            "length": 20,
            "width": 15,
            "height": 10
        },
        "declared_weight": 45,
        "service": "P",
        "account_number": "706014493"
    }
    
    print("🔍 PRUEBA DE COTIZACIÓN CON DATOS DEL FRONTEND")
    print("=" * 60)
    print()
    
    print("📋 DATOS DE ENTRADA:")
    print(json.dumps(test_data, indent=2, ensure_ascii=False))
    print()
    
    # Crear instancia del servicio DHL
    dhl_service = DHLService()
    
    try:
        print("📡 Realizando cotización...")
        print()
        
        # Hacer la cotización
        result = dhl_service.get_rate(
            origin_country=test_data["origin"]["country"],
            origin_postal_code=test_data["origin"]["postal_code"],
            origin_city=test_data["origin"]["city"],
            destination_country=test_data["destination"]["country"],
            destination_postal_code=test_data["destination"]["postal_code"],
            destination_city=test_data["destination"]["city"],
            weight=test_data["weight"],
            length=test_data["dimensions"]["length"],
            width=test_data["dimensions"]["width"],
            height=test_data["dimensions"]["height"],
            declared_weight=test_data["declared_weight"],
            content_type=test_data["service"],
            account_number=test_data["account_number"]
        )
        
        print("✅ RESPUESTA COMPLETA:")
        print("=" * 60)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()
        
        if result.get('success'):
            print("📊 ANÁLISIS DE LA RESPUESTA:")
            print("-" * 40)
            
            rates = result.get('rates', [])
            print(f"• Número de servicios: {len(rates)}")
            
            for i, rate in enumerate(rates, 1):
                print(f"\n🚚 SERVICIO {i}:")
                print(f"  - Nombre: {rate.get('service_name', 'N/A')}")
                print(f"  - Código: {rate.get('service_code', 'N/A')}")
                print(f"  - Precio: {rate.get('currency', 'USD')} {rate.get('total_charge', 0)}")
                print(f"  - Fecha entrega: {rate.get('delivery_date', 'N/A')}")
                
                # Mostrar compatibilidad de contenido
                if 'content_compatibility' in rate:
                    comp = rate['content_compatibility']
                    print(f"  - Compatibilidad:")
                    print(f"    * Restricciones: {comp.get('restrictions', 'N/A')}")
                    print(f"    * Documentos: {'✅' if comp.get('documents') else '❌'}")
                    print(f"    * Paquetes: {'✅' if comp.get('packages') else '❌'}")
                    print(f"    * Pallets: {'✅' if comp.get('pallets') else '❌'}")
                
                # Mostrar desglose de precios si existe
                if 'charges' in rate and rate['charges']:
                    print(f"  - Desglose ({len(rate['charges'])} conceptos):")
                    for charge in rate['charges']:
                        desc = charge.get('description', charge.get('code', 'Concepto'))
                        amount = charge.get('amount', 0)
                        print(f"    * {desc}: {rate.get('currency', 'USD')} {amount}")
            
            # Mostrar información adicional
            if 'weight_breakdown' in result:
                wb = result['weight_breakdown']
                print(f"\n⚖️ PESO:")
                print(f"  - Real: {wb.get('actual_weight', 0)} kg")
                print(f"  - Dimensional: {wb.get('dimensional_weight', 0)} kg")
                print(f"  - Facturable: {wb.get('chargeable_weight', 0)} kg")
                
        else:
            print("❌ ERROR EN LA COTIZACIÓN:")
            print(f"  Mensaje: {result.get('error', 'Error desconocido')}")
            
    except Exception as e:
        print(f"💥 EXCEPCIÓN: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_frontend_rate_data()
