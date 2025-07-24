"""
Script para aplicar hotfix directo en el contenedor Docker
"""

# Simular el tracking con parsing corregido
test_data = {
    'shipments': [{
        'shipmentTrackingNumber': '1222598506',
        'status': 'Success',
        'shipmentTimestamp': '2025-07-24T13:00:00',
        'productCode': 'Q',
        'description': 'General Merchandise',
        'shipperDetails': {
            'name': '',
            'postalAddress': {
                'cityName': '', 
                'postalCode': '', 
                'countryCode': 'PA'
            },
            'serviceArea': [{'code': 'PTY', 'description': 'Panama City-PA'}]
        },
        'receiverDetails': {
            'name': '',
            'postalAddress': {
                'cityName': '', 
                'postalCode': '', 
                'countryCode': 'CO'
            },
            'serviceArea': [{'code': 'BOG', 'description': 'Bogotá-CO'}]
        }
    }]
}

def extract_location_info(location_details):
    """Extrae información de ubicación de diferentes formatos"""
    try:
        if not location_details:
            return "Unknown"
        
        # Para shipperDetails/receiverDetails
        if 'postalAddress' in location_details:
            postal = location_details['postalAddress']
            city = postal.get('cityName', '')
            country = postal.get('countryCode', '')
            service_areas = location_details.get('serviceArea', [])
            
            if service_areas and len(service_areas) > 0:
                return service_areas[0].get('description', f"{city}, {country}".strip(', '))
            return f"{city}, {country}".strip(', ') or "Unknown"
        
        # Para eventos de tracking con location/address
        elif 'address' in location_details:
            address = location_details['address']
            return address.get('addressLocality', 'Unknown')
        
        # Otros formatos
        else:
            return str(location_details) if location_details else "Unknown"
            
    except Exception as e:
        return "Unknown"

def parse_tracking_response_safe(data):
    """Función de parsing ultra-segura para tracking"""
    try:
        shipments = data.get('shipments', [])
        if not shipments:
            return {"success": False, "message": "No shipments found"}
        
        shipment = shipments[0]
        
        # Crear respuesta básica con datos seguros
        result = {
            "success": True,
            "shipment_info": {
                "tracking_number": str(shipment.get('shipmentTrackingNumber', '')),
                "status": str(shipment.get('status', 'Unknown')),
                "status_description": str(shipment.get('status', 'Unknown')),
                "service": str(shipment.get('productCode', 'Unknown')),
                "service_type": str(shipment.get('productCode', 'Unknown')),
                "description": str(shipment.get('description', 'Unknown')),
                "shipment_timestamp": str(shipment.get('shipmentTimestamp', '')),
                "origin": extract_location_info(shipment.get('shipperDetails', {})),
                "destination": extract_location_info(shipment.get('receiverDetails', {})),
                "total_weight": 0,
                "weight_unit": "kg",
                "number_of_pieces": 0
            },
            "tracking_info": {},
            "events": [],
            "piece_details": [],
            "total_events": 0,
            "total_pieces": 0,
            "message": "Tracking encontrado: datos básicos disponibles",
            "raw_data": data
        }
        
        # Copiar shipment_info a tracking_info para compatibilidad
        result["tracking_info"] = result["shipment_info"].copy()
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error en parsing seguro: {str(e)}",
            "shipment_info": {},
            "tracking_info": {},
            "events": [],
            "piece_details": [],
            "total_events": 0,
            "total_pieces": 0
        }

# Probar la función
result = parse_tracking_response_safe(test_data)
print("=== RESULTADO PARSING SEGURO ===")
print(f"Success: {result['success']}")
if result['success']:
    print(f"Tracking Number: {result['shipment_info']['tracking_number']}")
    print(f"Status: {result['shipment_info']['status']}")
    print(f"Service: {result['shipment_info']['service_type']}")
    print(f"Origin: {result['shipment_info']['origin']}")
    print(f"Destination: {result['shipment_info']['destination']}")
    print(f"Timestamp: {result['shipment_info']['shipment_timestamp']}")
print(f"Message: {result['message']}")
