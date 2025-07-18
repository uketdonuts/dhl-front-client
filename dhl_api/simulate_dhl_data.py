"""
Simulación de datos DHL para pruebas y desarrollo
Simula las respuestas típicas de los servicios DHL
"""

from datetime import datetime, timedelta
import json
import random

class DHLDataSimulator:
    """Simulador de datos DHL para desarrollo y pruebas"""
    
    def __init__(self):
        self.tracking_statuses = [
            'Processing',
            'In Transit',
            'Out for Delivery',
            'Delivered',
            'Exception',
            'Returned'
        ]
        
        self.event_codes = {
            'PU': 'Pickup',
            'AF': 'Arrived at Facility',
            'PL': 'Processed at Location',
            'DF': 'Departed Facility',
            'CR': 'Customs Released',
            'CC': 'Customs Cleared',
            'OC': 'On Courier',
            'OK': 'Delivered',
            'EX': 'Exception',
            'RT': 'Returned'
        }
        
        self.locations = [
            'PANAMA CITY - PANAMA',
            'MIAMI FL - USA',
            'CINCINNATI HUB - USA',
            'NEW YORK NY - USA',
            'MADRID - SPAIN',
            'COLOGNE - GERMANY',
            'HONG KONG - CHINA',
            'SINGAPORE - SINGAPORE'
        ]
        
        self.service_types = {
            'P': 'EXPRESS WORLDWIDE',
            'D': 'EXPRESS WORLDWIDE DOC',
            'U': 'EXPRESS WORLDWIDE',
            'K': 'EXPRESS 9:00',
            'L': 'EXPRESS 10:30',
            'G': 'DOMESTIC EXPRESS',
            'W': 'ECONOMY SELECT'
        }

    def simulate_tracking_response(self, tracking_number, status='In Transit'):
        """
        Simula una respuesta de tracking de DHL
        
        Args:
            tracking_number (str): Número de seguimiento
            status (str): Estado del envío
            
        Returns:
            dict: Respuesta simulada de tracking
        """
        # Generar eventos aleatorios
        events = self._generate_events()
        
        # Información básica del envío
        shipment_info = {
            'awb_number': tracking_number,
            'tracking_number': tracking_number,
            'status': status,
            'origin': 'PANAMA CITY - PANAMA',
            'destination': 'MIAMI FL - USA',
            'weight': f"{random.uniform(0.5, 10.0):.1f} K",
            'pieces': random.randint(1, 3),
            'shipment_date': (datetime.now() - timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d'),
            'service_type': 'P',
            'service_name': 'EXPRESS WORLDWIDE'
        }
        
        # Detalles de piezas
        piece_details = self._generate_piece_details(shipment_info['pieces'])
        
        return {
            "success": True,
            "tracking_info": shipment_info,
            "events": events,
            "piece_details": piece_details,
            "total_events": len(events),
            "total_pieces": len(piece_details),
            "message": "Información de seguimiento obtenida exitosamente de DHL"
        }

    def simulate_rate_response(self, origin='PA', destination='US', weight=1.0):
        """
        Simula una respuesta de cotización de DHL
        
        Args:
            origin (str): Código de país origen
            destination (str): Código de país destino
            weight (float): Peso del paquete
            
        Returns:
            dict: Respuesta simulada de cotización
        """
        rates = []
        
        # Generar tarifas para diferentes servicios
        for service_code, service_name in self.service_types.items():
            base_rate = random.uniform(25.0, 150.0)
            
            # Ajustar precio según peso
            weight_factor = max(1.0, weight)
            total_charge = base_rate * weight_factor
            
            # Generar tiempo de entrega
            delivery_days = random.randint(1, 5)
            delivery_time = (datetime.now() + timedelta(days=delivery_days)).strftime('%Y-%m-%d %H:%M')
            
            # Desglose de cargos
            charges = [
                {
                    'code': 'FREIGHT',
                    'description': 'Freight Charge',
                    'amount': round(total_charge * 0.7, 2)
                },
                {
                    'code': 'FUEL',
                    'description': 'Fuel Surcharge',
                    'amount': round(total_charge * 0.15, 2)
                },
                {
                    'code': 'HANDLING',
                    'description': 'Handling Fee',
                    'amount': round(total_charge * 0.15, 2)
                }
            ]
            
            rate = {
                'service_code': service_code,
                'service_name': service_name,
                'total_charge': round(total_charge, 2),
                'currency': 'USD',
                'delivery_time': delivery_time,
                'delivery_date': delivery_time.split(' ')[0],
                'cutoff_time': f"{datetime.now().strftime('%Y-%m-%d')} 18:00",
                'next_business_day': delivery_days == 1,
                'charges': charges,
                'content_compatibility': {
                    'documents': service_code == 'D',
                    'packages': service_code != 'D'
                }
            }
            
            rates.append(rate)
        
        return {
            "success": True,
            "rates": rates,
            "total_rates": len(rates),
            "message": f"Se encontraron {len(rates)} tarifas disponibles",
            "provider": "DHL"
        }

    def simulate_shipment_response(self, success=True):
        """
        Simula una respuesta de creación de envío
        
        Args:
            success (bool): Si la creación fue exitosa
            
        Returns:
            dict: Respuesta simulada de creación
        """
        if success:
            tracking_number = self._generate_tracking_number()
            return {
                "success": True,
                "tracking_number": tracking_number,
                "message": "Envío creado exitosamente",
                "shipment_info": {
                    "awb_number": tracking_number,
                    "service_type": "P",
                    "estimated_delivery": (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
                    "total_charge": round(random.uniform(45.0, 120.0), 2),
                    "currency": "USD"
                }
            }
        else:
            return {
                "success": False,
                "errors": [
                    {
                        'code': '998',
                        'message': 'Invalid shipment date',
                        'error_type': 'INVALID_DATE',
                        'suggestion': 'Verificar que la fecha de envío sea futura y no más de 10 días adelante'
                    }
                ],
                "message": "Error 998: Invalid shipment date",
                "error_summary": "Se encontraron 1 errores en la solicitud de envío",
                "next_steps": "Revise los datos del envío y las sugerencias para cada error"
            }

    def simulate_epod_response(self, tracking_number, has_pdf=True):
        """
        Simula una respuesta de ePOD (Proof of Delivery)
        
        Args:
            tracking_number (str): Número de seguimiento
            has_pdf (bool): Si tiene PDF disponible
            
        Returns:
            dict: Respuesta simulada de ePOD
        """
        if has_pdf:
            # Simular datos PDF en base64 (solo un ejemplo corto)
            fake_pdf_data = "JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PAovVGl0bGUgKERITCBQcm9vZiBvZiBEZWxpdmVyeSk="
            
            return {
                "success": True,
                "pdf_data": fake_pdf_data,
                "format": "base64",
                "size": len(fake_pdf_data),
                "message": "PDF obtenido exitosamente",
                "delivery_info": {
                    "tracking_number": tracking_number,
                    "delivery_date": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                    "signatory": "J. RODRIGUEZ",
                    "location": "MIAMI FL - USA"
                }
            }
        else:
            return {
                "success": False,
                "message": "No se encontró PDF en la respuesta",
                "tracking_number": tracking_number,
                "elements_found": [
                    {'tag': 'Response', 'has_text': False, 'has_attributes': True},
                    {'tag': 'Status', 'has_text': True, 'has_attributes': False}
                ]
            }

    def _generate_events(self):
        """Genera eventos de seguimiento aleatorios"""
        events = []
        current_date = datetime.now() - timedelta(days=random.randint(1, 7))
        
        # Eventos típicos de un envío
        event_sequence = ['PU', 'AF', 'DF', 'AF', 'CC', 'DF', 'AF', 'OC', 'OK']
        
        for i, event_code in enumerate(event_sequence[:random.randint(3, 8)]):
            event_date = current_date + timedelta(hours=random.randint(6, 24))
            
            event = {
                'date': event_date.strftime('%Y-%m-%d'),
                'time': event_date.strftime('%H:%M:%S'),
                'timestamp': event_date.strftime('%Y-%m-%d %H:%M:%S'),
                'code': event_code,
                'description': self.event_codes.get(event_code, 'Unknown Event'),
                'location': random.choice(self.locations)
            }
            
            # Agregar firmante para entregas
            if event_code == 'OK':
                event['signatory'] = random.choice(['J. RODRIGUEZ', 'M. GARCIA', 'A. MARTINEZ', 'L. FERNANDEZ'])
            
            events.append(event)
            current_date = event_date
        
        return events

    def _generate_piece_details(self, num_pieces):
        """Genera detalles de piezas"""
        piece_details = []
        
        for i in range(num_pieces):
            piece_detail = {
                'piece_number': str(i + 1),
                'license_plate': f"JD{random.randint(100000000, 999999999)}",
                'actual_length': str(random.randint(20, 50)),
                'actual_width': str(random.randint(15, 40)),
                'actual_height': str(random.randint(10, 30)),
                'actual_weight': f"{random.uniform(0.5, 5.0):.1f}",
                'declared_length': str(random.randint(20, 50)),
                'declared_width': str(random.randint(15, 40)),
                'declared_height': str(random.randint(10, 30)),
                'declared_weight': f"{random.uniform(0.5, 5.0):.1f}",
                'package_type': random.choice(['BOX', 'ENVELOPE', 'TUBE', 'PALLET']),
                'dim_weight': f"{random.uniform(1.0, 8.0):.1f}",
                'weight_unit': 'K'
            }
            
            piece_details.append(piece_detail)
        
        return piece_details

    def _generate_tracking_number(self):
        """Genera un número de tracking simulado"""
        return f"{random.randint(1000000000, 9999999999)}"

    def get_sample_data(self):
        """
        Retorna datos de muestra para diferentes escenarios
        
        Returns:
            dict: Conjunto de datos de muestra
        """
        return {
            'tracking_delivered': self.simulate_tracking_response('1234567890', 'Delivered'),
            'tracking_in_transit': self.simulate_tracking_response('1234567891', 'In Transit'),
            'tracking_exception': self.simulate_tracking_response('1234567892', 'Exception'),
            'rate_quote': self.simulate_rate_response('PA', 'US', 2.5),
            'shipment_success': self.simulate_shipment_response(True),
            'shipment_error': self.simulate_shipment_response(False),
            'epod_with_pdf': self.simulate_epod_response('1234567890', True),
            'epod_no_pdf': self.simulate_epod_response('1234567891', False)
        }

def main():
    """Función principal para probar el simulador"""
    simulator = DHLDataSimulator()
    
    print("=== SIMULADOR DE DATOS DHL ===\n")
    
    # Datos de muestra
    sample_data = simulator.get_sample_data()
    
    print("1. TRACKING - ENTREGADO:")
    print(json.dumps(sample_data['tracking_delivered'], indent=2, ensure_ascii=False))
    print("\n" + "="*50 + "\n")
    
    print("2. TRACKING - EN TRÁNSITO:")
    print(json.dumps(sample_data['tracking_in_transit'], indent=2, ensure_ascii=False))
    print("\n" + "="*50 + "\n")
    
    print("3. COTIZACIÓN:")
    print(json.dumps(sample_data['rate_quote'], indent=2, ensure_ascii=False))
    print("\n" + "="*50 + "\n")
    
    print("4. CREACIÓN DE ENVÍO - EXITOSO:")
    print(json.dumps(sample_data['shipment_success'], indent=2, ensure_ascii=False))
    print("\n" + "="*50 + "\n")
    
    print("5. CREACIÓN DE ENVÍO - ERROR:")
    print(json.dumps(sample_data['shipment_error'], indent=2, ensure_ascii=False))
    print("\n" + "="*50 + "\n")
    
    print("6. ePOD - CON PDF:")
    print(json.dumps(sample_data['epod_with_pdf'], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
