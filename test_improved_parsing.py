#!/usr/bin/env python3
"""
Script para probar el parsing mejorado de respuestas DHL
"""

import json
import sys
import os

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dhl_project.settings')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import django
django.setup()

from dhl_api.services import DHLService

def test_improved_parsing():
    """Prueba el parsing mejorado con los datos reales"""
    
    # Datos reales de la respuesta anterior (simplificado para la prueba)
    sample_data = {
        "products": [
            {
                "productName": "EXPRESS WORLDWIDE",
                "productCode": "P",
                "weight": {
                    "volumetric": 0.6,
                    "provided": 45,
                    "unitOfMeasurement": "metric"
                },
                "totalPrice": [
                    {
                        "currencyType": "BILLC",
                        "priceCurrency": "USD",
                        "price": 392.44
                    }
                ],
                "detailedPriceBreakdown": [
                    {
                        "currencyType": "BILLC",
                        "priceCurrency": "USD",
                        "breakdown": [
                            {
                                "name": "EXPRESS WORLDWIDE",
                                "price": 307.78
                            },
                            {
                                "name": "NON-CONVEYABLE PIECE",
                                "serviceCode": "YO",
                                "price": 22
                            },
                            {
                                "name": "FUEL SURCHARGE",
                                "serviceCode": "FF",
                                "price": 62.66
                            }
                        ]
                    }
                ],
                "pickupCapabilities": {
                    "nextBusinessDay": False,
                    "localCutoffDateAndTime": "2025-07-21T18:30:00",
                    "GMTCutoffTime": "19:00:00"
                },
                "deliveryCapabilities": {
                    "estimatedDeliveryDateAndTime": "2025-07-22T23:59:00",
                    "totalTransitDays": 1
                }
            }
        ]
    }
    
    print("🔧 PRUEBA DE PARSING MEJORADO")
    print("=" * 50)
    print()
    
    # Crear instancia del servicio y probar el parsing
    dhl_service = DHLService()
    result = dhl_service._parse_rest_rate_response(sample_data)
    
    print("✅ RESULTADO DEL PARSING:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()
    
    if result.get('success') and result.get('rates'):
        rate = result['rates'][0]
        print("📊 INFORMACIÓN EXTRAÍDA:")
        print(f"  💰 Precio: {rate.get('currency', 'USD')} {rate.get('total_charge', 0)}")
        print(f"  📅 Entrega: {rate.get('delivery_date', 'No disponible')}")
        print(f"  ⏰ Hora: {rate.get('delivery_time', 'No disponible')}")
        print(f"  🕐 Límite: {rate.get('cutoff_time', 'No disponible')}")
        print(f"  📋 Desglose: {len(rate.get('charges', []))} conceptos")
        
        if rate.get('charges'):
            print("  💸 Conceptos:")
            for charge in rate['charges']:
                print(f"    • {charge.get('description', 'N/A')}: {rate.get('currency', 'USD')} {charge.get('amount', 0)}")
                
        # Información de peso
        if 'weight_breakdown' in result:
            wb = result['weight_breakdown']
            print(f"  ⚖️ Peso real: {wb.get('actual_weight', 0)} kg")
            print(f"  📦 Peso dimensional: {wb.get('dimensional_weight', 0)} kg")
            print(f"  💰 Peso facturable: {wb.get('chargeable_weight', 0)} kg")

if __name__ == "__main__":
    test_improved_parsing()
