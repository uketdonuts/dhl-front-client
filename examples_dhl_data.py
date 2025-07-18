"""
Ejemplos de uso de los datos simulados de DHL
Demuestra cómo integrar los datos de prueba en el desarrollo
"""

import json
from simulate_dhl_data import DHLDataSimulator
from test_data import get_test_data, TRACKING_NUMBERS

def example_tracking_integration():
    """
    Ejemplo de cómo integrar los datos simulados en el tracking
    """
    print("=== EJEMPLO: INTEGRACIÓN DE TRACKING ===\n")
    
    # Usar datos predefinidos
    tracking_data = get_test_data('tracking', 'delivered')
    
    print("📦 INFORMACIÓN DEL ENVÍO:")
    info = tracking_data['tracking_info']
    print(f"   Número de tracking: {info['tracking_number']}")
    print(f"   Estado: {info['status']}")
    print(f"   Origen: {info['origin']}")
    print(f"   Destino: {info['destination']}")
    print(f"   Peso: {info['weight']}")
    print(f"   Piezas: {info['pieces']}")
    print(f"   Fecha de envío: {info['shipment_date']}")
    
    print("\n📋 EVENTOS DE SEGUIMIENTO:")
    for i, event in enumerate(tracking_data['events'], 1):
        print(f"   {i}. {event['timestamp']} - {event['code']}: {event['description']}")
        print(f"      Ubicación: {event['location']}")
        if event.get('signatory'):
            print(f"      Firmante: {event['signatory']}")
        print()
    
    print(f"📊 RESUMEN: {tracking_data['total_events']} eventos, {tracking_data['total_pieces']} piezas")

def example_rate_integration():
    """
    Ejemplo de cómo integrar los datos simulados en las cotizaciones
    """
    print("\n=== EJEMPLO: INTEGRACIÓN DE COTIZACIONES ===\n")
    
    # Usar datos predefinidos
    rate_data = get_test_data('rate', 'panama_to_usa')
    
    print("💰 TARIFAS DISPONIBLES:")
    for i, rate in enumerate(rate_data['rates'], 1):
        print(f"   {i}. {rate['service_name']} ({rate['service_code']})")
        print(f"      Precio: ${rate['total_charge']:.2f} {rate['currency']}")
        print(f"      Entrega: {rate['delivery_date']}")
        print(f"      Tiempo de corte: {rate['cutoff_time']}")
        
        print("      Desglose de cargos:")
        for charge in rate['charges']:
            print(f"        • {charge['description']}: ${charge['amount']:.2f}")
        
        print("      Compatibilidad de contenido:")
        compat = rate['content_compatibility']
        print(f"        • Documentos: {'✓' if compat['documents'] else '✗'}")
        print(f"        • Paquetes: {'✓' if compat['packages'] else '✗'}")
        print()

def example_shipment_integration():
    """
    Ejemplo de cómo integrar los datos simulados en la creación de envíos
    """
    print("\n=== EJEMPLO: INTEGRACIÓN DE CREACIÓN DE ENVÍOS ===\n")
    
    # Ejemplo exitoso
    success_data = get_test_data('shipment', 'success')
    print("✅ ENVÍO CREADO EXITOSAMENTE:")
    print(f"   Número de tracking: {success_data['tracking_number']}")
    print(f"   Servicio: {success_data['shipment_info']['service_type']}")
    print(f"   Entrega estimada: {success_data['shipment_info']['estimated_delivery']}")
    print(f"   Costo total: ${success_data['shipment_info']['total_charge']:.2f}")
    print(f"   Tipo de contenido: {success_data['content_info']['description']}")
    
    # Ejemplo con error
    error_data = get_test_data('shipment', 'error_invalid_date')
    print("\n❌ ERROR EN CREACIÓN DE ENVÍO:")
    print(f"   Mensaje: {error_data['message']}")
    print(f"   Resumen: {error_data['error_summary']}")
    print("   Errores específicos:")
    for error in error_data['errors']:
        print(f"     • Código {error['code']}: {error['message']}")
        print(f"       Sugerencia: {error['suggestion']}")

def example_dynamic_simulation():
    """
    Ejemplo de cómo usar el simulador dinámico
    """
    print("\n=== EJEMPLO: SIMULADOR DINÁMICO ===\n")
    
    simulator = DHLDataSimulator()
    
    # Simular tracking con diferentes estados
    print("🔄 SIMULACIONES DINÁMICAS:")
    
    states = ['Processing', 'In Transit', 'Delivered', 'Exception']
    for state in states:
        tracking_data = simulator.simulate_tracking_response(f"SIM{state[:3].upper()}", state)
        print(f"   {state}: {tracking_data['tracking_info']['tracking_number']} - {tracking_data['total_events']} eventos")
    
    # Simular cotización
    rate_data = simulator.simulate_rate_response('PA', 'US', 3.5)
    print(f"\n💰 COTIZACIÓN SIMULADA:")
    print(f"   Servicios disponibles: {rate_data['total_rates']}")
    print(f"   Precio más bajo: ${min(rate['total_charge'] for rate in rate_data['rates']):.2f}")
    print(f"   Precio más alto: ${max(rate['total_charge'] for rate in rate_data['rates']):.2f}")

def example_error_handling():
    """
    Ejemplo de manejo de errores comunes
    """
    print("\n=== EJEMPLO: MANEJO DE ERRORES ===\n")
    
    from test_data import COMMON_ERRORS
    
    print("⚠️ ERRORES COMUNES Y SOLUCIONES:")
    for error_type, error_info in COMMON_ERRORS.items():
        print(f"   {error_type.upper().replace('_', ' ')}:")
        print(f"     Código: {error_info['code']}")
        print(f"     Mensaje: {error_info['message']}")
        print(f"     Solución: {error_info['solution']}")
        print()

def example_form_data():
    """
    Ejemplo de datos de formulario para pruebas
    """
    print("\n=== EJEMPLO: DATOS DE FORMULARIO ===\n")
    
    # Datos para envío de paquetes
    package_form = get_test_data('form', 'shipment_basic')
    print("📦 FORMULARIO PARA PAQUETES:")
    print(f"   Remitente: {package_form['shipper']['name']} ({package_form['shipper']['company']})")
    print(f"   Destinatario: {package_form['recipient']['name']} ({package_form['recipient']['company']})")
    print(f"   Paquete: {package_form['package']['weight']} kg, {package_form['package']['description']}")
    print(f"   Servicio: {package_form['service']}")
    print(f"   Cuenta: {package_form['account_number']}")
    
    # Datos para envío de documentos
    doc_form = get_test_data('form', 'shipment_documents')
    print("\n📄 FORMULARIO PARA DOCUMENTOS:")
    print(f"   Remitente: {doc_form['shipper']['name']} ({doc_form['shipper']['company']})")
    print(f"   Destinatario: {doc_form['recipient']['name']} ({doc_form['recipient']['company']})")
    print(f"   Documento: {doc_form['package']['weight']} kg, {doc_form['package']['description']}")
    print(f"   Servicio: {doc_form['service']}")

def example_accounts_management():
    """
    Ejemplo de manejo de cuentas DHL
    """
    print("\n=== EJEMPLO: MANEJO DE CUENTAS ===\n")
    
    from test_data import TEST_ACCOUNTS
    
    print("🏢 CUENTAS DISPONIBLES:")
    for account_id, account_info in TEST_ACCOUNTS.items():
        status_icon = "✅" if account_info['status'] == 'active' else "❌"
        print(f"   {status_icon} {account_info['name']} ({account_info['account_number']})")
        print(f"      Estado: {account_info['status']}")
        print(f"      Servicios: {', '.join(account_info['services']) if account_info['services'] else 'Ninguno'}")
        print()

def main():
    """
    Función principal que ejecuta todos los ejemplos
    """
    print("🚀 EJEMPLOS DE USO DE DATOS SIMULADOS DHL")
    print("=" * 50)
    
    example_tracking_integration()
    example_rate_integration()
    example_shipment_integration()
    example_dynamic_simulation()
    example_error_handling()
    example_form_data()
    example_accounts_management()
    
    print("\n✨ CÓMO USAR EN TU CÓDIGO:")
    print("""
    # Importar en tu archivo Python
    from simulate_dhl_data import DHLDataSimulator
    from test_data import get_test_data
    
    # Usar datos predefinidos
    tracking_data = get_test_data('tracking', 'delivered')
    
    # Usar simulador dinámico
    simulator = DHLDataSimulator()
    rate_data = simulator.simulate_rate_response('PA', 'US', 2.5)
    
    # En tus tests o desarrollo
    def test_tracking_view():
        mock_data = get_test_data('tracking', 'in_transit')
        # Usar mock_data en lugar de llamada real a DHL
        response = process_tracking_data(mock_data)
        assert response['success'] == True
    """)

if __name__ == "__main__":
    main()
