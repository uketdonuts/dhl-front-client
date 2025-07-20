#!/usr/bin/env python3
"""
Demo simplificado para mostrar el funcionamiento del cotizador DHL con detalles
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dhl_project.settings')
django.setup()

from dhl_api.services import DHLService
import json

def main():
    print("=== DEMO COTIZADOR DHL CON DETALLES EXPANDIBLES ===")
    print("📦 Simulando una cotización de Panamá a Miami")
    print("="*50)
    
    # Configuración del servicio
    username = "apO3fS5mJ8zT7h"
    password = "J^4oF@1qW!0qS!5b"
    base_url = "https://express.api.dhl.com"
    environment = "sandbox"
    
    print("🔧 Inicializando servicio DHL...")
    dhl_service = DHLService(username, password, base_url, environment)
    
    # Datos de prueba
    origin = {
        'city': 'Panama City',
        'postal_code': '0000',
        'country': 'PA'
    }
    
    destination = {
        'city': 'Miami',
        'postal_code': '33101',
        'country': 'US'
    }
    
    weight = 2.5
    dimensions = {
        'length': 20,
        'width': 15,
        'height': 10
    }
    
    print(f"📍 Origen: {origin['city']}, {origin['country']}")
    print(f"📍 Destino: {destination['city']}, {destination['country']}")
    print(f"📦 Peso: {weight} kg")
    print(f"📏 Dimensiones: {dimensions['length']}x{dimensions['width']}x{dimensions['height']} cm")
    print("\n🔍 Solicitando cotización...")
    
    # Realizar cotización
    result = dhl_service.get_rate(
        origin=origin,
        destination=destination,
        weight=weight,
        dimensions=dimensions,
        content_type="P",
        account_number="706014493"
    )
    
    print(f"\n📊 Resultado de la API: {'✅ Exitoso' if result.get('success') else '❌ Error'}")
    
    if result.get('success'):
        rates = result.get('rates', [])
        print(f"🎯 Tarifas encontradas: {len(rates)}")
        
        # Mostrar resumen de tarifas
        print(f"\n" + "="*60)
        print("📋 RESUMEN DE COTIZACIONES")
        print("="*60)
        
        for i, rate in enumerate(rates, 1):
            service_name = rate.get('service_name', 'Servicio desconocido')
            total_charge = rate.get('total_charge', 0)
            currency = rate.get('currency', 'USD')
            delivery_date = rate.get('delivery_date', '')
            
            print(f"\n📦 Tarifa {i}: {service_name}")
            print(f"   💰 Precio: {currency} {total_charge:,.2f}")
            
            if delivery_date:
                print(f"   📅 Entrega: {delivery_date}")
            
            # Mostrar desglose si está disponible
            charges = rate.get('charges', [])
            if charges:
                print(f"   📋 Desglose disponible ({len(charges)} conceptos):")
                for charge in charges[:3]:  # Mostrar solo los primeros 3
                    description = charge.get('description', charge.get('code', 'Concepto'))
                    amount = charge.get('amount', 0)
                    print(f"      • {description}: {currency} {amount:.2f}")
                if len(charges) > 3:
                    print(f"      • ... y {len(charges) - 3} más")
        
        # Mostrar información de peso
        weight_breakdown = result.get('weight_breakdown', {})
        if weight_breakdown:
            print(f"\n⚖️  Información de Peso:")
            print(f"   • Peso real: {weight_breakdown.get('actual_weight', 0):.2f} kg")
            print(f"   • Peso dimensional: {weight_breakdown.get('dimensional_weight', 0):.2f} kg")
            print(f"   • Peso facturable: {weight_breakdown.get('chargeable_weight', 0):.2f} kg ⭐")
        
        # Mostrar información del envío
        content_info = result.get('content_info', {})
        if content_info:
            content_type = content_info.get('content_type', 'P')
            is_customs = content_info.get('is_customs_declarable', False)
            account = content_info.get('account_number', 'N/A')
            
            print(f"\n📄 Información del Envío:")
            print(f"   • Tipo: {'Paquetes' if content_type == 'P' else 'Documentos'}")
            print(f"   • Declarable a aduana: {'Sí' if is_customs else 'No'}")
            print(f"   • Cuenta DHL: {account}")
        
        print(f"\n" + "="*60)
        print("✅ COTIZACIÓN COMPLETADA EXITOSAMENTE")
        print("💡 En la aplicación web, esto se mostraría con botones")
        print("   para expandir detalles de cada tarifa.")
        print("="*60)
        
    else:
        print(f"\n❌ Error en la cotización: {result.get('message', 'Error desconocido')}")
        
        # Mostrar detalles del error
        error_data = result.get('error_data', {})
        if error_data:
            print(f"\n🔍 Detalles del error:")
            print(f"   • Código: {result.get('error_code', 'N/A')}")
            print(f"   • HTTP Status: {result.get('http_status', 'N/A')}")
            
            if isinstance(error_data, dict):
                detail = error_data.get('detail', error_data.get('message', ''))
                if detail:
                    print(f"   • Detalle: {detail}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n💥 Error inesperado: {str(e)}")
        sys.exit(1)
