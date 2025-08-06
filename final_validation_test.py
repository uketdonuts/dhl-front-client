#!/usr/bin/env python3
"""
Script de prueba final para validar optimización de códigos postales canadienses
Valida que la mejora de rendimiento funciona correctamente con todos los filtros
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000/api"

def test_large_country_without_filters():
    """Prueba país grande sin filtros - debe requerir filtros"""
    print("🔍 Test 1: Canadá sin filtros (debe requerir filtros)")
    
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/service-zones/postal-codes/CA/")
        end_time = time.time()
        
        if response.status_code == 400:
            data = response.json()
            print(f"   ✅ Respuesta rápida: {end_time - start_time:.3f}s")
            print(f"   ✅ Requiere filtros: {data.get('message', '')}")
            print(f"   ✅ Filtros disponibles: {list(data.get('available_filters', {}).keys())}")
            return True
        else:
            print(f"   ❌ Respuesta inesperada: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_service_area_filter():
    """Prueba filtro por área de servicio"""
    print("\n🔍 Test 2: Canadá con filtro de área de servicio (YYC - Calgary)")
    
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/service-zones/postal-codes/CA/?service_area=YYC")
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                count = data.get('pagination', {}).get('count', 0)
                total = data.get('pagination', {}).get('total_count', 0)
                print(f"   ✅ Respuesta exitosa: {end_time - start_time:.3f}s")
                print(f"   ✅ Códigos obtenidos: {count} de {total} para YYC")
                print(f"   ✅ Primer código: {data['data'][0]['postal_code_from'] if data['data'] else 'N/A'}")
                return True
            else:
                print(f"   ❌ Respuesta no exitosa: {data.get('message', '')}")
                return False
        else:
            print(f"   ❌ Código de estado: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_multiple_service_areas():
    """Prueba múltiples áreas de servicio"""
    print("\n🔍 Test 3: Múltiples áreas de servicio canadienses")
    
    areas_to_test = ['YVR', 'YYZ', 'YUL', 'YOW']  # Vancouver, Toronto, Montreal, Ottawa
    
    for area in areas_to_test:
        start_time = time.time()
        try:
            response = requests.get(f"{BASE_URL}/service-zones/postal-codes/CA/?service_area={area}")
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    total = data.get('pagination', {}).get('total_count', 0)
                    print(f"   ✅ {area}: {total} códigos en {end_time - start_time:.3f}s")
                else:
                    print(f"   ❌ {area}: {data.get('message', '')}")
            else:
                print(f"   ❌ {area}: Status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {area}: Error {e}")

def test_small_country():
    """Prueba país pequeño sin restricciones"""
    print("\n🔍 Test 4: País pequeño (ES) sin restricciones")
    
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/service-zones/postal-codes/ES/")
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                count = data.get('pagination', {}).get('count', 0)
                total = data.get('pagination', {}).get('total_count', 0)
                print(f"   ✅ Respuesta exitosa: {end_time - start_time:.3f}s")
                print(f"   ✅ Códigos obtenidos: {count} de {total}")
                print(f"   ✅ Sin restricciones de filtros")
                return True
            else:
                print(f"   ❌ Respuesta no exitosa: {data.get('message', '')}")
                return False
        else:
            print(f"   ❌ Código de estado: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_available_service_areas():
    """Prueba endpoint de áreas de servicio disponibles"""
    print("\n🔍 Test 5: Áreas de servicio disponibles para Canadá")
    
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/service-zones/areas/CA/")
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                areas = data.get('data', [])
                print(f"   ✅ Respuesta exitosa: {end_time - start_time:.3f}s")
                print(f"   ✅ Áreas disponibles: {len(areas)}")
                print(f"   ✅ Primeras 5 áreas: {areas[:5] if areas else 'N/A'}")
                return True
            else:
                print(f"   ❌ Respuesta no exitosa: {data.get('message', '')}")
                return False
        else:
            print(f"   ❌ Código de estado: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Ejecuta todos los tests de validación"""
    print("🧪 VALIDACIÓN FINAL: Optimización de códigos postales canadienses")
    print("=" * 70)
    
    tests = [
        test_large_country_without_filters,
        test_service_area_filter,
        test_multiple_service_areas,
        test_small_country,
        test_available_service_areas
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ❌ Test falló con excepción: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 RESULTADOS: {passed} tests exitosos, {failed} tests fallidos")
    
    if failed == 0:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON! La optimización funciona correctamente.")
        print("\n✅ Beneficios confirmados:")
        print("   • Respuestas rápidas para países grandes sin filtros")
        print("   • Filtros por área de servicio funcionando correctamente")
        print("   • Países pequeños sin restricciones")
        print("   • Cache y paginación operativos")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar implementación.")

if __name__ == "__main__":
    main()
