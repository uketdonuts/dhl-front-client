#!/bin/bash
# Script para aplicar hotfix de tracking
# Copia la función corregida al contenedor Docker

# Crear la función corregida
cat > /tmp/tracking_fix.py << 'EOF'
    def _parse_rest_tracking_response(self, data):
        """Parsea la respuesta JSON de tracking de la API REST - VERSION CORREGIDA"""
        try:
            # Validar que data sea un diccionario
            if not isinstance(data, dict):
                logger.error(f"Tracking response data is not a dict: {type(data)}")
                return {
                    "success": False,
                    "tracking_info": {},
                    "shipment_info": {},
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
                    "shipment_info": {},
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
                'service_type': shipment.get('productCode', shipment.get('service', 'Unknown')),
                'description': shipment.get('description', 'Unknown'),
                'shipment_timestamp': shipment.get('shipmentTimestamp', ''),
                'origin': self._extract_location_info(shipment.get('shipperDetails', {})),
                'destination': self._extract_location_info(shipment.get('receiverDetails', {})),
                'total_weight': 0,
                'weight_unit': 'kg',
                'number_of_pieces': 0
            }

            # Eventos de tracking - COMPATIBLE CON FRONTEND
            events = []
            tracking_events = shipment.get('events', [])
            for event in tracking_events:
                event_data = {
                    'timestamp': str(event.get('timestamp', '')),
                    'date': str(event.get('timestamp', '')),
                    'location': self._extract_location_info(event.get('location', {})),
                    'status': str(event.get('description', 'Unknown')),
                    'description': str(event.get('description', 'Unknown')),
                    'next_steps': str(event.get('nextSteps', ''))
                }
                events.append(event_data)

            # Detalles de piezas
            pieces = []

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
            logger.error(f"Error parsing REST tracking response: {str(e)}")
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
EOF

echo "Fix creado exitosamente"
EOF
