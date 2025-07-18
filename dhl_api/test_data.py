"""
Datos de prueba específicos para el desarrollo del sistema DHL
Incluye casos de uso comunes y ejemplos de respuestas
"""

# Números de tracking de prueba
TRACKING_NUMBERS = {
    'delivered': '1234567890',
    'in_transit': '1234567891',
    'exception': '1234567892',
    'returned': '1234567893',
    'processing': '1234567894'
}

# Respuestas de tracking simuladas
TRACKING_RESPONSES = {
    'delivered': {
        "success": True,
        "tracking_info": {
            "awb_number": "1234567890",
            "tracking_number": "1234567890",
            "status": "Delivered",
            "origin": "PANAMA CITY - PANAMA",
            "destination": "MIAMI FL - USA",
            "weight": "2.5 K",
            "pieces": 1,
            "shipment_date": "2025-07-10",
            "service_type": "P",
            "service_name": "EXPRESS WORLDWIDE"
        },
        "events": [
            {
                "date": "2025-07-10",
                "time": "09:30:00",
                "timestamp": "2025-07-10 09:30:00",
                "code": "PU",
                "description": "Pickup",
                "location": "PANAMA CITY - PANAMA"
            },
            {
                "date": "2025-07-10",
                "time": "14:45:00",
                "timestamp": "2025-07-10 14:45:00",
                "code": "AF",
                "description": "Arrived at Facility",
                "location": "PANAMA CITY - PANAMA"
            },
            {
                "date": "2025-07-10",
                "time": "18:20:00",
                "timestamp": "2025-07-10 18:20:00",
                "code": "DF",
                "description": "Departed Facility",
                "location": "PANAMA CITY - PANAMA"
            },
            {
                "date": "2025-07-11",
                "time": "06:15:00",
                "timestamp": "2025-07-11 06:15:00",
                "code": "AF",
                "description": "Arrived at Facility",
                "location": "MIAMI FL - USA"
            },
            {
                "date": "2025-07-11",
                "time": "08:30:00",
                "timestamp": "2025-07-11 08:30:00",
                "code": "CC",
                "description": "Customs Cleared",
                "location": "MIAMI FL - USA"
            },
            {
                "date": "2025-07-11",
                "time": "10:45:00",
                "timestamp": "2025-07-11 10:45:00",
                "code": "OC",
                "description": "On Courier",
                "location": "MIAMI FL - USA"
            },
            {
                "date": "2025-07-11",
                "time": "15:30:00",
                "timestamp": "2025-07-11 15:30:00",
                "code": "OK",
                "description": "Delivered",
                "location": "MIAMI FL - USA",
                "signatory": "J. RODRIGUEZ"
            }
        ],
        "piece_details": [
            {
                "piece_number": "1",
                "license_plate": "JD123456789",
                "actual_length": "25",
                "actual_width": "20",
                "actual_height": "15",
                "actual_weight": "2.5",
                "declared_length": "25",
                "declared_width": "20",
                "declared_height": "15",
                "declared_weight": "2.5",
                "package_type": "BOX",
                "dim_weight": "3.1",
                "weight_unit": "K"
            }
        ],
        "total_events": 7,
        "total_pieces": 1,
        "message": "Información de seguimiento obtenida exitosamente de DHL"
    },
    
    'in_transit': {
        "success": True,
        "tracking_info": {
            "awb_number": "1234567891",
            "tracking_number": "1234567891",
            "status": "In Transit",
            "origin": "PANAMA CITY - PANAMA",
            "destination": "NEW YORK NY - USA",
            "weight": "1.2 K",
            "pieces": 1,
            "shipment_date": "2025-07-14",
            "service_type": "P",
            "service_name": "EXPRESS WORLDWIDE"
        },
        "events": [
            {
                "date": "2025-07-14",
                "time": "11:00:00",
                "timestamp": "2025-07-14 11:00:00",
                "code": "PU",
                "description": "Pickup",
                "location": "PANAMA CITY - PANAMA"
            },
            {
                "date": "2025-07-14",
                "time": "16:30:00",
                "timestamp": "2025-07-14 16:30:00",
                "code": "AF",
                "description": "Arrived at Facility",
                "location": "PANAMA CITY - PANAMA"
            },
            {
                "date": "2025-07-14",
                "time": "20:15:00",
                "timestamp": "2025-07-14 20:15:00",
                "code": "DF",
                "description": "Departed Facility",
                "location": "PANAMA CITY - PANAMA"
            },
            {
                "date": "2025-07-15",
                "time": "05:45:00",
                "timestamp": "2025-07-15 05:45:00",
                "code": "AF",
                "description": "Arrived at Facility",
                "location": "CINCINNATI HUB - USA"
            }
        ],
        "piece_details": [
            {
                "piece_number": "1",
                "license_plate": "JD123456790",
                "actual_length": "21",
                "actual_width": "16",
                "actual_height": "11",
                "actual_weight": "1.2",
                "declared_length": "21",
                "declared_width": "16",
                "declared_height": "11",
                "declared_weight": "1.2",
                "package_type": "ENVELOPE",
                "dim_weight": "1.5",
                "weight_unit": "K"
            }
        ],
        "total_events": 4,
        "total_pieces": 1,
        "message": "Información de seguimiento obtenida exitosamente de DHL"
    }
}

# Respuestas de cotización simuladas
RATE_RESPONSES = {
    'panama_to_usa': {
        "success": True,
        "rates": [
            {
                "service_code": "P",
                "service_name": "EXPRESS WORLDWIDE",
                "total_charge": 75.50,
                "currency": "USD",
                "delivery_time": "2025-07-17 12:00",
                "delivery_date": "2025-07-17",
                "cutoff_time": "2025-07-15 18:00",
                "next_business_day": False,
                "charges": [
                    {
                        "code": "FREIGHT",
                        "description": "Freight Charge",
                        "amount": 52.85
                    },
                    {
                        "code": "FUEL",
                        "description": "Fuel Surcharge",
                        "amount": 11.33
                    },
                    {
                        "code": "HANDLING",
                        "description": "Handling Fee",
                        "amount": 11.32
                    }
                ],
                "content_compatibility": {
                    "documents": False,
                    "packages": True
                }
            },
            {
                "service_code": "D",
                "service_name": "EXPRESS WORLDWIDE DOC",
                "total_charge": 45.25,
                "currency": "USD",
                "delivery_time": "2025-07-17 12:00",
                "delivery_date": "2025-07-17",
                "cutoff_time": "2025-07-15 18:00",
                "next_business_day": False,
                "charges": [
                    {
                        "code": "FREIGHT",
                        "description": "Freight Charge",
                        "amount": 31.68
                    },
                    {
                        "code": "FUEL",
                        "description": "Fuel Surcharge",
                        "amount": 6.79
                    },
                    {
                        "code": "HANDLING",
                        "description": "Handling Fee",
                        "amount": 6.78
                    }
                ],
                "content_compatibility": {
                    "documents": True,
                    "packages": False
                }
            },
            {
                "service_code": "K",
                "service_name": "EXPRESS 9:00",
                "total_charge": 125.75,
                "currency": "USD",
                "delivery_time": "2025-07-17 09:00",
                "delivery_date": "2025-07-17",
                "cutoff_time": "2025-07-15 18:00",
                "next_business_day": False,
                "charges": [
                    {
                        "code": "FREIGHT",
                        "description": "Freight Charge",
                        "amount": 88.03
                    },
                    {
                        "code": "FUEL",
                        "description": "Fuel Surcharge",
                        "amount": 18.86
                    },
                    {
                        "code": "HANDLING",
                        "description": "Handling Fee",
                        "amount": 18.86
                    }
                ],
                "content_compatibility": {
                    "documents": False,
                    "packages": True
                }
            }
        ],
        "total_rates": 3,
        "message": "Se encontraron 3 tarifas disponibles",
        "provider": "DHL"
    }
}

# Respuestas de creación de envío
SHIPMENT_RESPONSES = {
    'success': {
        "success": True,
        "tracking_number": "5678901234",
        "message": "Envío creado exitosamente",
        "shipment_info": {
            "awb_number": "5678901234",
            "service_type": "P",
            "estimated_delivery": "2025-07-18",
            "total_charge": 75.50,
            "currency": "USD"
        },
        "content_info": {
            "content_type": "P",
            "content_xml": "NON_DOCUMENTS",
            "description": "Paquetes con productos"
        }
    },
    
    'error_invalid_date': {
        "success": False,
        "errors": [
            {
                "code": "998",
                "message": "Invalid shipment date",
                "error_type": "INVALID_DATE",
                "suggestion": "Verificar que la fecha de envío sea futura y no más de 10 días adelante"
            }
        ],
        "message": "Error 998: Invalid shipment date",
        "error_summary": "Se encontraron 1 errores en la solicitud de envío",
        "next_steps": "Revise los datos del envío y las sugerencias para cada error"
    },
    
    'error_validation': {
        "success": False,
        "errors": [
            {
                "code": "400",
                "message": "Invalid recipient address",
                "error_type": "VALIDATION_ERROR",
                "suggestion": "Verificar datos del envío (direcciones, pesos, dimensiones)"
            }
        ],
        "message": "Error 400: Invalid recipient address",
        "error_summary": "Se encontraron 1 errores en la solicitud de envío",
        "next_steps": "Revise los datos del envío y las sugerencias para cada error"
    }
}

# Respuestas de ePOD
EPOD_RESPONSES = {
    'with_pdf': {
        "success": True,
        "pdf_data": "JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PAovVGl0bGUgKERITCBQcm9vZiBvZiBEZWxpdmVyeSk=",
        "format": "base64",
        "size": 76,
        "message": "PDF obtenido exitosamente",
        "delivery_info": {
            "tracking_number": "1234567890",
            "delivery_date": "2025-07-11",
            "signatory": "J. RODRIGUEZ",
            "location": "MIAMI FL - USA"
        }
    },
    
    'no_pdf': {
        "success": False,
        "message": "No se encontró PDF en la respuesta",
        "tracking_number": "1234567891",
        "elements_found": [
            {
                "tag": "Response",
                "has_text": False,
                "has_attributes": True,
                "attributes": ["xmlns"]
            },
            {
                "tag": "Status",
                "has_text": True,
                "has_attributes": False,
                "attributes": []
            }
        ]
    }
}

# Datos de formulario de prueba
FORM_DATA = {
    'shipment_basic': {
        'shipper': {
            'name': 'Juan Pérez',
            'company': 'Empresa Ejemplo S.A.',
            'phone': '507-431-2600',
            'email': 'juan.perez@ejemplo.com',
            'address': 'Calle 50, Torre Global Bank, Piso 10',
            'address2': 'Oficina 1001',
            'address3': 'Bella Vista',
            'city': 'Panama City',
            'state': 'PA',
            'postalCode': '0801',
            'country': 'PA'
        },
        'recipient': {
            'name': 'María García',
            'company': 'Receptora Corp.',
            'phone': '305-555-0123',
            'email': 'maria.garcia@receptora.com',
            'address': '1234 Main Street',
            'address2': 'Suite 456',
            'city': 'Miami',
            'state': 'FL',
            'postalCode': '33101',
            'country': 'US',
            'vat': '123456789'
        },
        'package': {
            'weight': 2.5,
            'length': 25,
            'width': 20,
            'height': 15,
            'description': 'Productos electrónicos',
            'value': 250.00,
            'currency': 'USD'
        },
        'service': 'P',
        'payment': 'S',
        'account_number': '706065602'
    },
    
    'shipment_documents': {
        'shipper': {
            'name': 'Carlos Rodríguez',
            'company': 'Consultora Legal',
            'phone': '507-264-8000',
            'email': 'carlos@consultora.com',
            'address': 'Vía España, Edificio Torres del Prado',
            'city': 'Panama City',
            'state': 'PA',
            'postalCode': '0832',
            'country': 'PA'
        },
        'recipient': {
            'name': 'Ana Martínez',
            'company': 'Legal Services Inc.',
            'phone': '212-555-0198',
            'email': 'ana.martinez@legalservices.com',
            'address': '789 Broadway',
            'city': 'New York',
            'state': 'NY',
            'postalCode': '10003',
            'country': 'US'
        },
        'package': {
            'weight': 0.5,
            'length': 30,
            'width': 21,
            'height': 2,
            'description': 'Documentos legales',
            'value': 0,
            'currency': 'USD'
        },
        'service': 'D',
        'payment': 'S',
        'account_number': '706065602'
    }
}

# Errores comunes y sus soluciones
COMMON_ERRORS = {
    'authentication': {
        'code': 401,
        'message': 'Credenciales inválidas',
        'solution': 'Verificar username y password en la configuración'
    },
    'invalid_account': {
        'code': 1001,
        'message': 'Número de cuenta inválido',
        'solution': 'Verificar el número de cuenta DHL'
    },
    'service_unavailable': {
        'code': 503,
        'message': 'Servicio no disponible',
        'solution': 'Reintentar más tarde o contactar soporte DHL'
    },
    'invalid_destination': {
        'code': 300,
        'message': 'Destino no válido',
        'solution': 'Verificar el código de país y ciudad de destino'
    },
    'weight_exceeded': {
        'code': 350,
        'message': 'Peso excede el límite permitido',
        'solution': 'Dividir el envío en paquetes más pequeños'
    }
}

# Configuración de cuentas de prueba
TEST_ACCOUNTS = {
    'principal': {
        'account_number': '706065602',
        'name': 'Cuenta Principal',
        'status': 'active',
        'services': ['P', 'D', 'K', 'L', 'G', 'W']
    },
    'secundaria': {
        'account_number': '706065603',
        'name': 'Cuenta Secundaria',
        'status': 'active',
        'services': ['P', 'D']
    },
    'inactiva': {
        'account_number': '706065604',
        'name': 'Cuenta Inactiva',
        'status': 'inactive',
        'services': []
    }
}

def get_test_data(data_type, scenario='default'):
    """
    Obtiene datos de prueba específicos
    
    Args:
        data_type (str): Tipo de datos (tracking, rate, shipment, epod)
        scenario (str): Escenario específico
        
    Returns:
        dict: Datos de prueba
    """
    data_maps = {
        'tracking': TRACKING_RESPONSES,
        'rate': RATE_RESPONSES,
        'shipment': SHIPMENT_RESPONSES,
        'epod': EPOD_RESPONSES,
        'form': FORM_DATA,
        'errors': COMMON_ERRORS,
        'accounts': TEST_ACCOUNTS
    }
    
    if data_type in data_maps:
        data = data_maps[data_type]
        if scenario in data:
            return data[scenario]
        else:
            # Devolver el primer elemento si no se encuentra el escenario
            return list(data.values())[0] if data else {}
    
    return {}

def print_test_scenarios():
    """Imprime todos los escenarios de prueba disponibles"""
    print("=== ESCENARIOS DE PRUEBA DISPONIBLES ===\n")
    
    print("1. TRACKING:")
    for key in TRACKING_RESPONSES.keys():
        print(f"   - {key}")
    
    print("\n2. RATE:")
    for key in RATE_RESPONSES.keys():
        print(f"   - {key}")
    
    print("\n3. SHIPMENT:")
    for key in SHIPMENT_RESPONSES.keys():
        print(f"   - {key}")
    
    print("\n4. EPOD:")
    for key in EPOD_RESPONSES.keys():
        print(f"   - {key}")
    
    print("\n5. FORM DATA:")
    for key in FORM_DATA.keys():
        print(f"   - {key}")
    
    print("\n6. COMMON ERRORS:")
    for key in COMMON_ERRORS.keys():
        print(f"   - {key}")
    
    print("\n7. TEST ACCOUNTS:")
    for key in TEST_ACCOUNTS.keys():
        print(f"   - {key}")

if __name__ == "__main__":
    print_test_scenarios()
    
    print("\n=== EJEMPLO DE USO ===")
    print("from test_data import get_test_data")
    print("tracking_data = get_test_data('tracking', 'delivered')")
    print("rate_data = get_test_data('rate', 'panama_to_usa')")
    print("shipment_data = get_test_data('shipment', 'success')")
