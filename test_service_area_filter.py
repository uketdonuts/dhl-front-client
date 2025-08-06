#!/usr/bin/env python3
"""
Script para probar el nuevo endpoint con service_area
"""

import requests
import time

def test_service_area_filter():
    """Prueba filtros de service_area"""
    base_url = 'http://localhost:8000/api'
    
    print("=== PRUEBA FILTROS DE SERVICE AREA ===\n")
    
    # Test 1: Verificar áreas de servicio disponibles para Canadá
    print("📍 Test 1: Canadá sin filtros (debería mostrar service_areas)")
    start_time = time.time()
    try:
        response = requests.get(f'{base_url}/service-zones/postal-codes/CA/')
        elapsed = time.time() - start_time
        print(f"   ⏱️  Tiempo de respuesta: {elapsed:.2f} segundos")
        
        if response.status_code == 400:
            data = response.json()
            print(f"   ✅ Filtros requeridos correctamente:")
            print(f"   📝 Mensaje: {data.get('message', 'N/A')}")
            print(f"   🔢 Total registros: {data.get('total_count', 'N/A'):,}")
            print(f"   🏛️  Estados disponibles: {len(data.get('available_filters', {}).get('states', []))}")
            print(f"   🏙️  Ciudades disponibles: {len(data.get('available_filters', {}).get('cities', []))}")
            print(f"   🏢 Áreas de servicio disponibles: {len(data.get('available_filters', {}).get('service_areas', []))}")
            
            # Mostrar las primeras service areas
            service_areas = data.get('available_filters', {}).get('service_areas', [])
            if service_areas:
                print(f"   🔍 Primeras áreas de servicio: {service_areas[:8]}")
        else:
            print(f"   ❌ Error inesperado: {response.status_code}")
            print(f"   📄 Respuesta: {response.text[:300]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 2: Probar con una service area específica que sabemos que existe
    print("📍 Test 2: Canadá con service_area=YVR (Vancouver)")
    start_time = time.time()
    try:
        response = requests.get(f'{base_url}/service-zones/postal-codes/CA/?service_area=YVR')
        elapsed = time.time() - start_time
        print(f"   ⏱️  Tiempo de respuesta: {elapsed:.2f} segundos")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Éxito con filtro de service area:")
            print(f"   📊 Registros en página: {data.get('pagination', {}).get('count', 'N/A')}")
            print(f"   🔢 Total registros: {data.get('pagination', {}).get('total_count', 'N/A'):,}")
            
            # Mostrar algunos códigos postales
            codes = data.get('data', [])[:3]
            if codes:
                print(f"   📮 Ejemplos de códigos postales:")
                for code in codes:
                    print(f"     {code.get('postal_code_from', '')} - {code.get('postal_code_to', '')} (Area: {code.get('service_area', '')})")
            else:
                print(f"   ℹ️  No se encontraron códigos postales para YVR")
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   📄 Respuesta: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 3: Probar con otra service area
    print("📍 Test 3: Canadá con service_area=YYC (Calgary)")
    start_time = time.time()
    try:
        response = requests.get(f'{base_url}/service-zones/postal-codes/CA/?service_area=YYC')
        elapsed = time.time() - start_time
        print(f"   ⏱️  Tiempo de respuesta: {elapsed:.2f} segundos")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Éxito con filtro de service area:")
            print(f"   📊 Registros en página: {data.get('pagination', {}).get('count', 'N/A')}")
            print(f"   🔢 Total registros: {data.get('pagination', {}).get('total_count', 'N/A'):,}")
            
            # Mostrar algunos códigos postales
            codes = data.get('data', [])[:3]
            if codes:
                print(f"   📮 Ejemplos de códigos postales:")
                for code in codes:
                    print(f"     {code.get('postal_code_from', '')} - {code.get('postal_code_to', '')} (Area: {code.get('service_area', '')})")
            else:
                print(f"   ℹ️  No se encontraron códigos postales para YYC")
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   📄 Respuesta: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == '__main__':
    test_service_area_filter()
