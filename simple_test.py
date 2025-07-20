import json
import sys
import os

# Simular las variables de entorno y configuración que necesita Django
os.environ['DHL_API_KEY'] = 'demo-key'  
os.environ['DHL_API_SECRET'] = 'demo-secret'
os.environ['DHL_API_URL'] = 'https://express.api.dhl.com'

# Importar directamente el servicio DHL
sys.path.append('/app')
sys.path.append('/app/dhl_api')

# Simular la configuración básica de Django si es necesaria
class MockSettings:
    DHL_API_KEY = 'demo-key'
    DHL_API_SECRET = 'demo-secret'
    DHL_API_URL = 'https://express.api.dhl.com'

# Mock de Django si es necesario
class MockDjango:
    def setup(self):
        pass

# Simular sys.modules['django'] 
sys.modules['django'] = MockDjango()

try:
    # Ahora importar el servicio
    from dhl_api.services import DHLService
    
    # Datos del frontend
    frontend_data = {
        "origin": {
            "postal_code": "0000",
            "city": "Panama",
            "country": "PA",
            "state": "PA"
        },
        "destination": {
            "postal_code": "110111",
            "city": "BOG", 
            "country": "CO"
        },
        "weight": 45,
        "dimensions": {
            "length": 20,
            "width": 15,
            "height": 10
        },
        "declared_weight": 45,
        "service": "P",
        "account_number": "706014493"
    }
    
    print("🔍 RESPUESTA DE DHL CON DATOS DEL FRONTEND")
    print("=" * 60)
    print()
    
    # Crear instancia del servicio
    dhl_service = DHLService()
    
    # Hacer cotización
    result = dhl_service.get_rate(
        origin_country=frontend_data["origin"]["country"],
        origin_postal_code=frontend_data["origin"]["postal_code"],
        origin_city=frontend_data["origin"]["city"],
        destination_country=frontend_data["destination"]["country"],
        destination_postal_code=frontend_data["destination"]["postal_code"],
        destination_city=frontend_data["destination"]["city"],
        weight=frontend_data["weight"],
        length=frontend_data["dimensions"]["length"],
        width=frontend_data["dimensions"]["width"],
        height=frontend_data["dimensions"]["height"],
        declared_weight=frontend_data["declared_weight"],
        content_type=frontend_data["service"],
        account_number=frontend_data["account_number"]
    )
    
    print("📋 DATOS DE ENTRADA:")
    print(json.dumps(frontend_data, indent=2, ensure_ascii=False))
    print()
    
    print("✅ RESPUESTA COMPLETA:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
