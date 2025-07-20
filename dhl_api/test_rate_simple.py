#!/usr/bin/env python3
"""
Script simple para probar cotizaciones DHL con detalles expandibles
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dhl_project.settings')
django.setup()

from dhl_api.services import DHLService
import logging
import json
from datetime import datetime

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def format_currency(amount, currency="USD"):
    """Formatea moneda con separadores de miles"""
    return f"{currency} {amount:,.2f}"

def format_datetime(date_str):
    """Formatea fecha/hora de manera legible"""
    if not date_str:
        return "No disponible"
    try:
        # Intentar parsear diferentes formatos de fecha
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y %H:%M')
    except:
        return date_str

def print_rate_summary(rate, index):
    """Imprime resumen básico de una tarifa"""
    service_name = rate.get('service_name', 'Servicio desconocido')
    total_charge = rate.get('total_charge', 0)
    currency = rate.get('currency', 'USD')
    delivery_date = rate.get('delivery_date', '')
    
    print(f"\n📦 Tarifa {index}: {service_name}")
    print(f"   💰 Precio: {format_currency(total_charge, currency)}")
    
    if delivery_date:
        print(f"   📅 Entrega: {format_datetime(delivery_date)}")
    
    # Indicar si hay detalles disponibles
    charges = rate.get('charges', [])
    if charges:
        print(f"   ℹ️  Desglose disponible: {len(charges)} conceptos")
    
    print(f"   🔍 Para más detalles, presiona [D{index}]")

def print_rate_details(rate, index):
    """Imprime detalles completos de una tarifa"""
    service_name = rate.get('service_name', 'Servicio desconocido')
    service_code = rate.get('service_code', 'N/A')
    total_charge = rate.get('total_charge', 0)
    currency = rate.get('currency', 'USD')
    
    print(f"\n" + "="*60)
    print(f"📦 DETALLES COMPLETOS - Tarifa {index}")
    print(f"="*60)
    print(f"Servicio: {service_name} ({service_code})")
    print(f"Precio Total: {format_currency(total_charge, currency)}")
    
    # Información de tiempo de entrega
    delivery_info = []
    if rate.get('delivery_date'):
        delivery_info.append(f"Fecha: {format_datetime(rate['delivery_date'])}")
    if rate.get('delivery_time'):
        delivery_info.append(f"Hora: {rate['delivery_time']}")
    if rate.get('cutoff_time'):
        delivery_info.append(f"Hora límite: {rate['cutoff_time']}")
    if rate.get('next_business_day'):
        delivery_info.append("✅ Entrega próximo día hábil")
    
    if delivery_info:
        print(f"\n📅 Información de Entrega:")
        for info in delivery_info:
            print(f"   • {info}")
    
    # Desglose de precios
    charges = rate.get('charges', [])
    if charges:
        print(f"\n💰 Desglose de Precios:")
        subtotal = 0
        for charge in charges:
            amount = charge.get('amount', 0)
            description = charge.get('description', charge.get('code', 'Concepto'))
            print(f"   • {description}: {format_currency(amount, currency)}")
            subtotal += amount
        
        print(f"   {'-'*40}")
        print(f"   Total: {format_currency(total_charge, currency)}")
        
        # Verificar si el total coincide
        if abs(subtotal - total_charge) > 0.01:
            print(f"   ⚠️  Diferencia detectada en cálculo: {format_currency(abs(subtotal - total_charge), currency)}")
    
    # Compatibilidad de contenido
    content_compat = rate.get('content_compatibility', {})
    if content_compat:
        print(f"\n📋 Compatibilidad de Contenido:")
        if content_compat.get('documents'):
            print(f"   ✅ Documentos")
        if content_compat.get('packages'):
            print(f"   ✅ Paquetes")
        if content_compat.get('pallets'):
            print(f"   ✅ Pallets")
    
    print(f"="*60)

def print_weight_breakdown(weight_breakdown):
    """Imprime información detallada del peso"""
    if not weight_breakdown:
        return
    
    print(f"\n⚖️  Información de Peso:")
    print(f"   • Peso real: {weight_breakdown.get('actual_weight', 0):.2f} kg")
    print(f"   • Peso dimensional: {weight_breakdown.get('dimensional_weight', 0):.2f} kg")
    
    declared_weight = weight_breakdown.get('declared_weight', 0)
    if declared_weight > 0:
        print(f"   • Peso declarado: {declared_weight:.2f} kg")
    
    chargeable_weight = weight_breakdown.get('chargeable_weight', 0)
    print(f"   • Peso facturable: {chargeable_weight:.2f} kg ⭐")

def print_content_info(content_info):
    """Imprime información del tipo de contenido"""
    if not content_info:
        return
    
    content_type = content_info.get('content_type', 'P')
    is_customs = content_info.get('is_customs_declarable', False)
    account = content_info.get('account_number', 'N/A')
    
    print(f"\n📄 Información del Envío:")
    print(f"   • Tipo: {'Paquetes' if content_type == 'P' else 'Documentos'}")
    print(f"   • Declarable a aduana: {'Sí' if is_customs else 'No'}")
    print(f"   • Cuenta DHL: {account}")

def interactive_details(rates):
    """Permite al usuario ver detalles interactivamente"""
    print(f"\n" + "="*60)
    print("🔍 EXPLORAR DETALLES")
    print("="*60)
    print("Comandos disponibles:")
    for i in range(len(rates)):
        print(f"   D{i+1} - Ver detalles completos de la Tarifa {i+1}")
    print("   Q - Salir")
    print("="*60)
    
    while True:
        try:
            choice = input("\nIngresa tu opción: ").strip().upper()
            
            if choice == 'Q':
                break
            elif choice.startswith('D') and choice[1:].isdigit():
                rate_index = int(choice[1:]) - 1
                if 0 <= rate_index < len(rates):
                    print_rate_details(rates[rate_index], rate_index + 1)
                else:
                    print(f"❌ Tarifa {choice[1:]} no existe. Opciones válidas: 1-{len(rates)}")
            else:
                print("❌ Opción inválida. Usa D1, D2, etc. o Q para salir")
                
        except KeyboardInterrupt:
            print("\n\n👋 Saliendo...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def test_rate_simple():
    """Prueba simple de cotización con detalles expandibles"""
    
    try:
        # Configuración del servicio
        username = "apO3fS5mJ8zT7h"
        password = "J^4oF@1qW!0qS!5b"
        base_url = "https://express.api.dhl.com"
        environment = "sandbox"
        
        logger.info("Inicializando servicio DHL...")
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
        
        logger.info(f"Solicitando cotización de {origin['city']} a {destination['city']}...")
        
        # Probar con paquetes (NON_DOCUMENTS)
        result = dhl_service.get_rate(
            origin=origin,
            destination=destination,
            weight=weight,
            dimensions=dimensions,
            content_type="P",
            account_number="706014493"
        )
        
        logger.info(f"Resultado: {result.get('success', False)}")
        
        if result.get('success'):
            rates = result.get('rates', [])
            logger.info(f"Tarifas encontradas: {len(rates)}")
            
            # Mostrar resumen de todas las tarifas
            print(f"\n" + "="*60)
            print("📋 RESUMEN DE COTIZACIONES")
            print("="*60)
            
            for i, rate in enumerate(rates, 1):
                print_rate_summary(rate, i)
            
            # Mostrar información adicional
            weight_breakdown = result.get('weight_breakdown', {})
            if weight_breakdown:
                print_weight_breakdown(weight_breakdown)
            
            content_info = result.get('content_info', {})
            if content_info:
                print_content_info(content_info)
            
            # Ofrecer exploración interactiva
            if rates:
                try:
                    interactive_details(rates)
                except KeyboardInterrupt:
                    print("\n\n👋 Saliendo del modo interactivo...")
            
            return True
        else:
            logger.error(f"Error: {result.get('message', 'Error desconocido')}")
            
            # Mostrar información adicional del error si está disponible
            error_data = result.get('error_data', {})
            if error_data:
                print(f"\n❌ Detalles del error:")
                print(f"   Código: {result.get('error_code', 'N/A')}")
                print(f"   HTTP Status: {result.get('http_status', 'N/A')}")
                
                # Si hay información estructurada del error
                if isinstance(error_data, dict):
                    detail = error_data.get('detail', error_data.get('message', ''))
                    if detail:
                        print(f"   Detalle: {detail}")
            
            return False
            
    except Exception as e:
        logger.exception(f"Error en prueba: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== COTIZADOR DHL CON DETALLES EXPANDIBLES ===")
    print("📦 Este script muestra un resumen de tarifas y permite")
    print("   explorar detalles completos de cada servicio.")
    print("="*50)
    
    success = test_rate_simple()
    
    if success:
        print("\n✅ Cotización completada exitosamente")
    else:
        print("\n❌ Error en la cotización")
        sys.exit(1)
