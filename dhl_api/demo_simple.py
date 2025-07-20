#!/usr/bin/env python3
"""
Script simplificado para demostrar cotización DHL sin interacción
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dhl_project.settings')
django.setup()

from dhl_api.services import DHLService

def format_currency(amount, currency="USD"):
    """Formatea moneda con separadores de miles"""
    return f"{currency} {amount:,.2f}"

def main():
    print("=== COTIZADOR DHL - DEMO FUNCIONAL ===")
    print()
    
    try:
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
        
        print(f"📍 Cotización: {origin['city']} → {destination['city']}")
        print(f"📦 Peso: {weight} kg, Dimensiones: {dimensions['length']}x{dimensions['width']}x{dimensions['height']} cm")
        print()
        print("🔍 Solicitando cotización a DHL API...")
        
        # Realizar cotización
        result = dhl_service.get_rate(
            origin=origin,
            destination=destination,
            weight=weight,
            dimensions=dimensions,
            content_type="P",
            account_number="706014493"
        )
        
        print(f"📊 Estado: {'✅ Exitoso' if result.get('success') else '❌ Error'}")
        
        if result.get('success'):
            rates = result.get('rates', [])
            print(f"🎯 Servicios encontrados: {len(rates)}")
            print()
            print("="*60)
            print("📋 RESUMEN DE SERVICIOS Y PRECIOS")
            print("="*60)
            
            for i, rate in enumerate(rates, 1):
                service_name = rate.get('service_name', 'Servicio desconocido')
                service_code = rate.get('service_code', 'N/A')
                total_charge = rate.get('total_charge', 0)
                currency = rate.get('currency', 'USD')
                delivery_date = rate.get('delivery_date', '')
                
                print(f"\n📦 Servicio {i}: {service_name} ({service_code})")
                print(f"   💰 Precio: {format_currency(total_charge, currency)}")
                
                if delivery_date:
                    print(f"   📅 Entrega estimada: {delivery_date}")
                
                # Mostrar desglose de precios si está disponible
                charges = rate.get('charges', [])
                if charges:
                    print(f"   💡 Desglose de precios ({len(charges)} conceptos):")
                    subtotal = 0
                    for charge in charges:
                        description = charge.get('description', charge.get('code', 'Concepto'))
                        amount = charge.get('amount', 0)
                        print(f"      • {description}: {format_currency(amount, currency)}")
                        subtotal += amount
                    
                    print(f"      {'-'*30}")
                    print(f"      Total: {format_currency(total_charge, currency)}")
                    
                    # Verificar cálculos
                    if abs(subtotal - total_charge) > 0.01:
                        print(f"      ⚠️  Diferencia: {format_currency(abs(subtotal - total_charge), currency)}")
                
                # Información de entrega
                if rate.get('next_business_day'):
                    print(f"   ⚡ Entrega próximo día hábil")
                
                if rate.get('cutoff_time'):
                    print(f"   ⏰ Hora límite: {rate['cutoff_time']}")
            
            # Información adicional del envío
            print()
            print("="*60)
            print("📊 INFORMACIÓN ADICIONAL DEL ENVÍO")
            print("="*60)
            
            weight_breakdown = result.get('weight_breakdown', {})
            if weight_breakdown:
                print("⚖️  Análisis de peso:")
                print(f"   • Peso real: {weight_breakdown.get('actual_weight', 0):.2f} kg")
                print(f"   • Peso dimensional: {weight_breakdown.get('dimensional_weight', 0):.2f} kg")
                print(f"   • Peso facturable: {weight_breakdown.get('chargeable_weight', 0):.2f} kg ⭐")
            
            content_info = result.get('content_info', {})
            if content_info:
                content_type = content_info.get('content_type', 'P')
                is_customs = content_info.get('is_customs_declarable', False)
                account = content_info.get('account_number', 'N/A')
                
                print("\n📄 Configuración del envío:")
                print(f"   • Tipo de contenido: {'Paquetes/Mercancía' if content_type == 'P' else 'Documentos'}")
                print(f"   • Requiere declaración aduanera: {'Sí' if is_customs else 'No'}")
                print(f"   • Cuenta DHL utilizada: {account}")
            
            print()
            print("="*60)
            print("✅ COTIZACIÓN COMPLETADA EXITOSAMENTE")
            print("💡 En la interfaz web, cada servicio tendría un botón")
            print("   'Ver detalles' para expandir toda esta información.")
            print("="*60)
            
        else:
            print()
            print("❌ ERROR EN LA COTIZACIÓN")
            print(f"Mensaje: {result.get('message', 'Error desconocido')}")
            
            error_data = result.get('error_data', {})
            if error_data:
                print(f"Código de error: {result.get('error_code', 'N/A')}")
                print(f"HTTP Status: {result.get('http_status', 'N/A')}")
                
                if isinstance(error_data, dict):
                    detail = error_data.get('detail', error_data.get('message', ''))
                    if detail:
                        print(f"Detalle: {detail}")
    
    except Exception as e:
        print(f"💥 Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
