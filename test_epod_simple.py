#!/usr/bin/env python3
"""
Test simplificado del endpoint ePOD para verificar la implementación del fix
"""

import requests
import json


def test_epod_locally():
    """Prueba el endpoint ePOD localmente"""
    
    print("🧪 Test del endpoint ePOD - Verificación del fix")
    print("=" * 60)
    
    # URL del endpoint
    url = "http://localhost:8001/api/dhl/epod/"
    
    # Test 1: Con account_number específico
    print("\n📋 Test 1: Con account_number específico")
    data1 = {
        "shipment_id": "5339266472",
        "account_number": "706065602"
    }
    
    print(f"Payload: {json.dumps(data1, indent=2)}")
    print("Expected: Debería usar account_number=706065602 en la URL de DHL")
    
    # Test 2: Sin account_number (debe usar default)
    print("\n📋 Test 2: Sin account_number (debe usar default)")
    data2 = {
        "shipment_id": "5339266472"
    }
    
    print(f"Payload: {json.dumps(data2, indent=2)}")
    print("Expected: Debería usar account_number=706014493 en la URL de DHL")
    
    print("\n" + "=" * 60)
    print("📝 VERIFICACIÓN MANUAL NECESARIA:")
    print("1. Iniciar el servidor Django: docker-dev.bat up")
    print("2. Hacer login en http://localhost:8001/admin")
    print("3. Probar el endpoint desde el frontend en la pestaña ePOD")
    print("4. Verificar los logs del backend para confirmar que se usa la cuenta correcta")
    print("\nComando para ver logs:")
    print("docker logs dhl-django-backend --tail=20")
    
    print("\n🔍 PUNTOS A VERIFICAR:")
    print("✅ El campo account_number se acepta en el serializer")
    print("✅ El account_number se pasa correctamente al servicio")
    print("✅ Los logs muestran: 'ePOD: Using account_number=X, final account_to_use=Y'")
    print("✅ La URL de error contiene el account_number correcto")
    print("✅ El frontend muestra información clara sobre qué cuenta se utilizó")


if __name__ == "__main__":
    test_epod_locally()
