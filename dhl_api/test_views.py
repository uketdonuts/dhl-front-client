"""
Vistas de prueba para el servicio DHL con el nuevo formato SOAP.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
from .services import DHLService

# Vistas anteriores que faltaban
def get_test_shipment_data(request):
    """Endpoint para obtener datos de envío de prueba (compatibilidad)"""
    return get_hardcoded_test_data(request)

@csrf_exempt
def test_shipment_direct(request):
    """Endpoint para probar envío directo (compatibilidad)"""
    return test_shipment_direct_service(request)

def get_hardcoded_test_data(request):
    """Endpoint público para obtener datos de prueba hardcodeados"""
    
    test_data = {
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
    
    return JsonResponse({
        'success': True,
        'test_data': test_data,
        'message': 'Datos de prueba para DHL con formato exacto'
    })

@csrf_exempt
@require_http_methods(["POST"])
def test_shipment_new_format(request):
    """Endpoint para probar creación de envío con el nuevo formato SOAP"""
    
    try:
        # Obtener datos del request
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        # Usar datos hardcodeados si no se proporcionan
        if not data or data.get('use_hardcoded', True):
            # Datos basados en el ejemplo que funciona
            shipment_data = {
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
                'service': 'P',
                'payment': 'S'
            }
        else:
            shipment_data = data
        
        # Determinar el entorno
        environment = data.get('environment', 'sandbox')
        
        # Crear servicio DHL
        dhl_service = DHLService(
            username="apO3fS5mJ8zT7h",
            password="J^4oF@1qW!0qS!5b",
            base_url="https://wsbexpress.dhl.com",
            environment=environment
        )
        
        # Crear envío
        result = dhl_service.create_shipment(shipment_data)
        
        # Agregar información adicional a la respuesta
        result['environment'] = environment
        result['endpoint_used'] = 'https://wsbexpress.dhl.com:443/sndpt/expressRateBook'
        result['format'] = 'nuevo_formato_exacto'
        result['test_data_used'] = shipment_data
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error en test_shipment_new_format'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])  
def test_shipment_direct_service(request):
    """Endpoint para probar el servicio DHL directamente sin usar vistas de negocio"""
    
    try:
        # Obtener parámetros
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        environment = data.get('environment', 'sandbox')
        
        # Crear servicio DHL
        dhl_service = DHLService(
            username="apO3fS5mJ8zT7h",
            password="J^4oF@1qW!0qS!5b", 
            base_url="https://wsbexpress.dhl.com",
            environment=environment
        )
        
        # Datos hardcodeados para prueba
        test_data = {
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
            'service': 'P',
            'payment': 'S'
        }
        
        # Ejecutar prueba
        result = dhl_service.create_shipment(test_data)
        
        # Información adicional
        result['test_info'] = {
            'environment': environment,
            'endpoint': 'https://wsbexpress.dhl.com:443/sndpt/expressRateBook',
            'format': 'nuevo_formato_exacto',
            'credentials': 'apO3fS5mJ8zT7h:J^4oF@1qW!0qS!5b',
            'account': '706065602'
        }
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error en test_shipment_direct_service'
        }, status=500)

def test_connection_status(request):
    """Endpoint para verificar el estado de conexión con DHL"""
    
    try:
        # Crear servicio DHL
        dhl_service = DHLService(
            username="apO3fS5mJ8zT7h",
            password="J^4oF@1qW!0qS!5b",
            base_url="https://wsbexpress.dhl.com",
            environment="production"
        )
        
        # Información del servicio
        service_info = {
            'credentials': 'apO3fS5mJ8zT7h:J^4oF@1qW!0qS!5b',
            'account_number': '706065602',
            'endpoints': {
                'shipment': 'https://wsbexpress.dhl.com:443/sndpt/expressRateBook',
                'tracking': 'https://wsbexpress.dhl.com/gbl/glDHLExpressTrack',
                'epod': 'https://wsbexpress.dhl.com/gbl/getePOD'
            },
            'soap_action': 'euExpressRateBook_providerServices_ShipmentHandlingServices_Binder_createShipmentRequest',
            'format': 'nuevo_formato_exacto'
        }
        
        return JsonResponse({
            'success': True,
            'service_info': service_info,
            'message': 'Información del servicio DHL configurado'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error obteniendo información del servicio'
        }, status=500)
