"""
Hotfix temporal para el parsing de tracking mientras se reconstruye Docker
Este archivo contiene la función corregida para parsing de tracking DHL
"""

def parse_tracking_response_fixed(data):
    """Versión corregida del parsing de tracking de DHL"""
    try:
        # Validar que data sea un diccionario
        if not isinstance(data, dict):
            return {
                "success": False,
                "tracking_info": {},
                "events": [],
                "piece_details": [],
                "total_events": 0,
                "total_pieces": 0,
                "message": "Error DHL API: Formato de respuesta inválido",
                "error_code": "INVALID_FORMAT",
                "suggestion": "Reintentar más tarde",
                "raw_response": str(data)[:500]
            }
        
        # Estructura de respuesta de tracking de DHL REST API
        shipments = data.get('shipments', [])
        if not shipments:
            return {
                "success": False,
                "tracking_info": {},
                "events": [],
                "piece_details": [],
                "total_events": 0,
                "total_pieces": 0,
                "message": "Error DHL API: No se encontró información de tracking",
                "error_code": "NO_DATA",
                "suggestion": "Verificar número de tracking",
                "raw_response": str(data)[:500]
            }
        
        # Usar el primer envío
        shipment = shipments[0]
        
        # Función auxiliar para extraer ubicación
        def extract_location_info(location_details):
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
                    
            except Exception:
                return "Unknown"
        
        # Manejar status como string o como objeto
        status = shipment.get('status', 'Unknown')
        if isinstance(status, dict):
            status_code = status.get('statusCode', 'Unknown')
            status_desc = status.get('description', 'Unknown')
        else:
            status_code = str(status)
            status_desc = str(status)
        
        # Información básica del envío - COMPATIBLE CON FRONTEND
        tracking_info = {
            'tracking_number': shipment.get('shipmentTrackingNumber', shipment.get('id', '')),
            'status': status_code,
            'status_description': status_desc,
            'service': shipment.get('productCode', shipment.get('service', 'Unknown')),
            'service_type': shipment.get('productCode', shipment.get('service', 'Unknown')),  # Para frontend
            'description': shipment.get('description', 'Unknown'),
            'shipment_timestamp': shipment.get('shipmentTimestamp', ''),
            'origin': extract_location_info(shipment.get('shipperDetails', {})),
            'destination': extract_location_info(shipment.get('receiverDetails', {})),
            'total_weight': shipment.get('details', {}).get('totalWeight', {}).get('value', 0),
            'weight_unit': shipment.get('details', {}).get('totalWeight', {}).get('unitText', 'kg'),
            'number_of_pieces': shipment.get('details', {}).get('numberOfPieces', 0)
        }
        
        # Eventos de tracking - COMPATIBLE CON FRONTEND
        events = []
        tracking_events = shipment.get('events', [])
        for event in tracking_events:
            event_data = {
                'timestamp': event.get('timestamp', ''),
                'date': event.get('timestamp', ''),  # Para frontend
                'location': extract_location_info(event.get('location', {})),
                'status': event.get('description', 'Unknown'),
                'description': event.get('description', 'Unknown'),  # Para frontend
                'next_steps': event.get('nextSteps', '')
            }
            events.append(event_data)
        
        # Detalles de piezas
        pieces = []
        piece_details = shipment.get('pieces', [])
        for piece in piece_details:
            piece_data = {
                'piece_id': piece.get('id', ''),
                'description': piece.get('description', ''),
                'weight': piece.get('weight', {}).get('value', 0),
                'weight_unit': piece.get('weight', {}).get('unitText', 'kg'),
                'dimensions': piece.get('dimensions', {})
            }
            pieces.append(piece_data)
        
        # ESTRUCTURA COMPATIBLE CON FRONTEND
        return {
            "success": True,
            "shipment_info": tracking_info,  # Para compatibilidad con frontend
            "tracking_info": tracking_info,  # Para nueva estructura
            "events": events,
            "piece_details": pieces,
            "total_events": len(events),
            "total_pieces": len(pieces),
            "message": f"Tracking encontrado: {len(events)} eventos, {len(pieces)} piezas",
            "raw_data": data
        }
        
    except Exception as e:
        return {
            "success": False,
            "tracking_info": {},
            "shipment_info": {},
            "events": [],
            "piece_details": [],
            "total_events": 0,
            "total_pieces": 0,
            "message": f"Error procesando respuesta de tracking: {str(e)}",
            "error_code": "PARSE_ERROR",
            "suggestion": "Reintentar más tarde",
            "raw_response": str(data)[:500] if data else "No data"
        }


# Test con datos reales de DHL
if __name__ == "__main__":
    # Simular datos reales que recibimos de DHL
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
    
    result = parse_tracking_response_fixed(test_data)
    print("RESULTADO DEL PARSING CORREGIDO:")
    print(f"Success: {result['success']}")
    print(f"Tracking Number: {result['tracking_info']['tracking_number']}")
    print(f"Status: {result['tracking_info']['status']}")
    print(f"Service: {result['tracking_info']['service_type']}")
    print(f"Origin: {result['tracking_info']['origin']}")
    print(f"Destination: {result['tracking_info']['destination']}")
    print(f"Message: {result['message']}")
