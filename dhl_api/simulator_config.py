"""
Configuración simple para el simulador DHL
"""
import os

# Configurar variables de entorno para el simulador
os.environ.setdefault('DHL_SIMULATE_MODE', 'true')
os.environ.setdefault('DHL_ENVIRONMENT', 'development')

# Función para verificar si el simulador está activo
def is_simulator_active():
    return os.getenv('DHL_SIMULATE_MODE', 'false').lower() == 'true'

# Función para obtener datos de prueba rápidos
def get_quick_test_data():
    return {
        "success": True,
        "tracking_info": {
            "awb_number": "TEST123",
            "tracking_number": "TEST123",
            "status": "Delivered",
            "origin": "PANAMA CITY - PANAMA",
            "destination": "MIAMI FL - USA",
            "weight": "2.5 K",
            "pieces": 1,
            "shipment_date": "2025-07-14",
            "service_type": "P",
            "service_name": "EXPRESS WORLDWIDE"
        },
        "events": [
            {
                "date": "2025-07-14",
                "time": "09:30:00",
                "timestamp": "2025-07-14 09:30:00",
                "code": "PU",
                "description": "Pickup",
                "location": "PANAMA CITY - PANAMA"
            },
            {
                "date": "2025-07-15",
                "time": "15:30:00",
                "timestamp": "2025-07-15 15:30:00",
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
                "actual_weight": "2.5",
                "package_type": "BOX",
                "weight_unit": "K"
            }
        ],
        "total_events": 2,
        "total_pieces": 1,
        "message": "Información de seguimiento obtenida exitosamente (simulado)",
        "is_simulated": True,
        "simulation_reason": "Usando datos simulados en modo desarrollo"
    }
