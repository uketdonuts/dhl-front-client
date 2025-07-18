"""
Integración de datos simulados con el sistema DHL existente
Permite usar datos simulados en modo desarrollo
"""

import os
from datetime import datetime, timedelta
from simulate_dhl_data import DHLDataSimulator
from test_data import get_test_data, TRACKING_NUMBERS, TEST_ACCOUNTS

class DHLServiceSimulator:
    """
    Clase que simula el comportamiento de DHLService para desarrollo
    Mantiene la misma interfaz pero devuelve datos simulados
    """
    
    def __init__(self, username=None, password=None, base_url=None, environment="development"):
        self.username = username or "test_user"
        self.password = password or "test_password"
        self.base_url = base_url or "https://test.dhl.com"
        self.environment = environment
        self.simulator = DHLDataSimulator()
        
        # Configurar modo simulado
        self.simulate_mode = os.getenv('DHL_SIMULATE_MODE', 'true').lower() == 'true'
        
        print(f"🔧 DHLServiceSimulator inicializado en modo: {environment}")
        print(f"📊 Simulación activa: {'Sí' if self.simulate_mode else 'No'}")
    
    def get_tracking(self, tracking_number):
        """
        Simula la obtención de información de seguimiento
        
        Args:
            tracking_number (str): Número de seguimiento
            
        Returns:
            dict: Respuesta simulada de tracking
        """
        if not self.simulate_mode:
            # En modo real, llamar al servicio real
            # from dhl_api.services import DHLService
            # real_service = DHLService(self.username, self.password, self.base_url)
            # return real_service.get_tracking(tracking_number)
            pass
        
        print(f"🔍 Simulando tracking para: {tracking_number}")
        
        # Determinar estado basado en el número de tracking
        if tracking_number in TRACKING_NUMBERS.values():
            # Usar datos predefinidos
            for status, number in TRACKING_NUMBERS.items():
                if number == tracking_number:
                    return get_test_data('tracking', status)
        
        # Generar datos aleatorios para números no predefinidos
        statuses = ['Processing', 'In Transit', 'Delivered', 'Exception']
        # Usar el último dígito para determinar el estado
        status_index = int(tracking_number[-1]) % len(statuses)
        status = statuses[status_index]
        
        return self.simulator.simulate_tracking_response(tracking_number, status)
    
    def get_rate(self, origin, destination, weight, dimensions, declared_weight=None, content_type="P"):
        """
        Simula la obtención de cotizaciones
        
        Args:
            origin: Información del origen
            destination: Información del destino
            weight: Peso del paquete
            dimensions: Dimensiones del paquete
            declared_weight: Peso declarado
            content_type: Tipo de contenido
            
        Returns:
            dict: Respuesta simulada de cotización
        """
        if not self.simulate_mode:
            # En modo real, llamar al servicio real
            pass
        
        print(f"💰 Simulando cotización: {origin} -> {destination}, {weight}kg")
        
        # Usar datos predefinidos si coincide con el patrón
        if origin.get('country') == 'PA' and destination.get('country') == 'US':
            rate_data = get_test_data('rate', 'panama_to_usa')
            
            # Ajustar precios basado en peso real
            weight_factor = max(1.0, float(weight))
            for rate in rate_data['rates']:
                base_price = rate['total_charge']
                rate['total_charge'] = round(base_price * weight_factor, 2)
                
                # Ajustar cargos individuales
                for charge in rate['charges']:
                    charge['amount'] = round(charge['amount'] * weight_factor, 2)
            
            return rate_data
        
        # Generar cotización dinámica
        origin_code = origin.get('country', 'PA')
        destination_code = destination.get('country', 'US')
        
        return self.simulator.simulate_rate_response(origin_code, destination_code, weight, dimensions)
    
    def create_shipment(self, shipment_data, content_type="P"):
        """
        Simula la creación de envíos
        
        Args:
            shipment_data: Datos del envío
            content_type: Tipo de contenido
            
        Returns:
            dict: Respuesta simulada de creación
        """
        if not self.simulate_mode:
            # En modo real, llamar al servicio real
            pass
        
        print(f"📦 Simulando creación de envío: {content_type}")
        
        # Validar datos básicos
        if not shipment_data.get('shipper') or not shipment_data.get('recipient'):
            return get_test_data('shipment', 'error_validation')
        
        # Simular fecha inválida ocasionalmente
        if 'invalid_date' in str(shipment_data):
            return get_test_data('shipment', 'error_invalid_date')
        
        # Simular éxito
        success_data = get_test_data('shipment', 'success')
        
        # Personalizar respuesta
        if content_type == "D":
            success_data['content_info'] = {
                'content_type': 'D',
                'content_xml': 'DOCUMENTS',
                'description': 'Solo documentos'
            }
        
        # Generar número de tracking único
        timestamp = int(datetime.now().timestamp())
        success_data['tracking_number'] = f"SIM{timestamp}"
        success_data['shipment_info']['awb_number'] = success_data['tracking_number']
        
        return success_data
    
    def get_ePOD(self, shipment_id):
        """
        Simula la obtención de ePOD
        
        Args:
            shipment_id (str): ID del envío
            
        Returns:
            dict: Respuesta simulada de ePOD
        """
        if not self.simulate_mode:
            # En modo real, llamar al servicio real
            pass
        
        print(f"📋 Simulando ePOD para: {shipment_id}")
        
        # Simular que algunos envíos no tienen PDF
        if shipment_id.endswith('1') or shipment_id.endswith('3'):
            return get_test_data('epod', 'no_pdf')
        
        return get_test_data('epod', 'with_pdf')
    
    def validate_account(self, account_number):
        """
        Simula la validación de cuentas
        
        Args:
            account_number (str): Número de cuenta
            
        Returns:
            bool: True si es válida
        """
        if not self.simulate_mode:
            # En modo real, llamar al servicio real
            pass
        
        print(f"🏢 Simulando validación de cuenta: {account_number}")
        
        # Verificar en cuentas de prueba
        for account_data in TEST_ACCOUNTS.values():
            if account_data['account_number'] == account_number:
                return account_data['status'] == 'active'
        
        # Simular validación para cuentas desconocidas
        return account_number.startswith('7060')
    
    def get_content_types(self):
        """
        Obtiene tipos de contenido disponibles
        
        Returns:
            list: Lista de tipos de contenido
        """
        return [
            {
                'code': 'P',
                'name': 'NON_DOCUMENTS',
                'description': 'Paquetes con productos',
                'xml_value': 'NON_DOCUMENTS',
                'restrictions': [
                    'Productos con valor comercial',
                    'Requiere declaración de valor',
                    'Sujeto a aranceles e impuestos'
                ],
                'typical_services': ['P', 'U', 'K', 'L', 'G', 'W', 'I', 'N', 'O']
            },
            {
                'code': 'D',
                'name': 'DOCUMENTS',
                'description': 'Solo documentos',
                'xml_value': 'DOCUMENTS',
                'restrictions': [
                    'Solo documentos sin valor comercial',
                    'Peso máximo típico: 2 kg',
                    'Sin declaración de valor'
                ],
                'typical_services': ['D']
            }
        ]
    
    def get_service_content_compatibility(self, service_code):
        """
        Obtiene compatibilidad de contenido para un servicio
        
        Args:
            service_code (str): Código del servicio
            
        Returns:
            dict: Información de compatibilidad
        """
        if service_code == 'D':
            return {
                'documents': True,
                'packages': False,
                'description': 'Solo documentos'
            }
        else:
            return {
                'documents': False,
                'packages': True,
                'description': 'Paquetes con productos'
            }

def get_dhl_service(environment="development", simulate=None):
    """
    Factory function para obtener el servicio DHL apropiado
    
    Args:
        environment (str): Entorno de ejecución
        simulate (bool): Forzar modo simulación (opcional)
        
    Returns:
        DHLService o DHLServiceSimulator: Instancia del servicio
    """
    # Determinar si usar simulación
    should_simulate = simulate if simulate is not None else (
        environment == "development" or 
        os.getenv('DHL_SIMULATE_MODE', 'true').lower() == 'true'
    )
    
    if should_simulate:
        return DHLServiceSimulator(environment=environment)
    else:
        # En producción, usar el servicio real
        from dhl_api.services import DHLService
        return DHLService(
            username=os.getenv('DHL_USERNAME'),
            password=os.getenv('DHL_PASSWORD'),
            base_url=os.getenv('DHL_BASE_URL', 'https://wsbexpress.dhl.com')
        )

# Ejemplo de uso en views.py
def example_view_integration():
    """
    Ejemplo de cómo usar el simulador en las vistas
    """
    print("\n=== EJEMPLO: INTEGRACIÓN EN VIEWS.PY ===")
    
    # En lugar de importar directamente DHLService
    # from dhl_api.services import DHLService
    
    # Usar la factory function
    dhl_service = get_dhl_service()
    
    # El resto del código permanece igual
    tracking_data = dhl_service.get_tracking('1234567890')
    print(f"✅ Tracking obtenido: {tracking_data['tracking_info']['status']}")
    
    rate_data = dhl_service.get_rate(
        origin={'country': 'PA'},
        destination={'country': 'US'},
        weight=2.5,
        dimensions={'length': 25, 'width': 20, 'height': 15}
    )
    print(f"💰 Cotizaciones obtenidas: {rate_data['total_rates']} servicios")
    
    return {
        'tracking': tracking_data,
        'rates': rate_data
    }

if __name__ == "__main__":
    print("🔧 SIMULADOR DE SERVICIOS DHL")
    print("=" * 40)
    
    # Crear instancia del simulador
    simulator = DHLServiceSimulator()
    
    # Probar diferentes funciones
    print("\n1. TRACKING:")
    tracking_result = simulator.get_tracking('1234567890')
    print(f"   Status: {tracking_result['tracking_info']['status']}")
    print(f"   Eventos: {tracking_result['total_events']}")
    
    print("\n2. COTIZACIÓN:")
    rate_result = simulator.get_rate(
        origin={'country': 'PA'},
        destination={'country': 'US'},
        weight=2.5,
        dimensions={'length': 25, 'width': 20, 'height': 15}
    )
    print(f"   Servicios: {rate_result['total_rates']}")
    print(f"   Precio más bajo: ${min(rate['total_charge'] for rate in rate_result['rates']):.2f}")
    
    print("\n3. CREACIÓN DE ENVÍO:")
    shipment_data = get_test_data('form', 'shipment_basic')
    shipment_result = simulator.create_shipment(shipment_data, 'P')
    print(f"   Éxito: {shipment_result['success']}")
    if shipment_result['success']:
        print(f"   Tracking: {shipment_result['tracking_number']}")
    
    print("\n4. VALIDACIÓN DE CUENTA:")
    account_valid = simulator.validate_account('706065602')
    print(f"   Cuenta válida: {account_valid}")
    
    print("\n📝 CÓMO USAR EN TU PROYECTO:")
    print("   1. Importar: from dhl_integration import get_dhl_service")
    print("   2. Usar: dhl_service = get_dhl_service()")
    print("   3. Llamar métodos normalmente")
    print("   4. Configurar: DHL_SIMULATE_MODE=true en .env para desarrollo")
    
    example_view_integration()
