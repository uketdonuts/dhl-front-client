#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test automatizado con autenticacion para validar rates
"""
import requests
import json
from datetime import datetime, timedelta
import getpass

BASE_URL = "http://localhost:8000"

def calculate_business_days(days):
    """Calcula N dias laborales en el futuro"""
    current = datetime.now()
    days_ahead = 1
    business_days_found = 0

    while business_days_found < days:
        next_date = current + timedelta(days=days_ahead)
        if next_date.weekday() < 5:  # Lunes-Viernes
            business_days_found += 1
            if business_days_found >= days:
                return next_date
        days_ahead += 1

    return current

def login(username, password):
    """Autenticarse y obtener token JWT"""
    print(f"\nAutenticando como {username}...")

    response = requests.post(
        f"{BASE_URL}/api/auth/login/",
        json={
            "username": username,
            "password": password
        },
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        access_token = data.get('access')
        print("Autenticacion exitosa!")
        return access_token
    else:
        print(f"Error de autenticacion: {response.status_code}")
        print(response.text)
        return None

def test_rate(token, test_name, payload, description):
    """Ejecuta un test de rate con autenticacion"""
    print("\n" + "=" * 80)
    print(f"TEST: {test_name}")
    print("=" * 80)
    print(f"Descripcion: {description}")
    print(f"\nPayload:")
    print(json.dumps(payload, indent=2))

    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{BASE_URL}/api/dhl/rate/",
            json=payload,
            headers=headers,
            timeout=45
        )

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("\nRESPUESTA:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            if result.get('success'):
                print(f"\n✓ SUCCESS - DHL acepto el request")
                if 'rates' in result and result['rates']:
                    print(f"\nServicios disponibles: {len(result['rates'])}")
                    for rate in result['rates']:
                        service_name = rate.get('service_name', rate.get('serviceName', 'Unknown'))
                        total_price = rate.get('total_price', rate.get('totalPrice', 0))
                        print(f"  - {service_name}: ${total_price}")
                return True
            else:
                print(f"\n✗ ERROR - DHL rechazo el request")
                print(f"Mensaje: {result.get('message')}")
                if result.get('error_detail'):
                    print(f"Detalle: {result.get('error_detail')}")
                return False
        else:
            print(f"\n✗ ERROR HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(response.text)
            return False

    except requests.exceptions.Timeout:
        print("\n✗ ERROR: Timeout (request tardo mas de 45 segundos)")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False

def main():
    print("=" * 80)
    print("SUITE DE TESTS AUTOMATIZADOS - DHL RATES")
    print("=" * 80)

    # Solicitar credenciales
    print("\nPor favor ingresa tus credenciales para autenticarte:")
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")

    # Autenticarse
    token = login(username, password)
    if not token:
        print("\n✗ No se pudo autenticar. Abortando tests.")
        return

    # Calcular fechas
    date_5_days = calculate_business_days(5)

    print(f"\nFecha minima (5 dias laborales): {date_5_days.strftime('%Y-%m-%d')}")

    results = []

    # TEST 1: Costa Rica -> Nicaragua con CP "0" (auto-reemplazo)
    print("\n" + "=" * 80)
    print("EJECUTANDO TESTS...")
    print("=" * 80)

    result = test_rate(
        token,
        "Test 1: CR -> NI con CP '0' (auto-reemplazo)",
        {
            "origin": {
                "city": "San Jose",
                "country": "CR",
                "postal_code": "0"
            },
            "destination": {
                "city": "Managua",
                "country": "NI",
                "postal_code": "0"
            },
            "weight": 5,
            "dimensions": {
                "length": 30,
                "width": 20,
                "height": 10
            },
            "service": "P",
            "account_number": "959390223",
            "shippingDate": date_5_days.strftime('%Y-%m-%d')
        },
        "El backend deberia reemplazar CP '0' con '10101' (CR) y '11001' (NI)"
    )
    results.append(("Test 1: CR -> NI (auto-reemplazo)", result))

    # TEST 2: Panama -> Colombia (deberia funcionar)
    result = test_rate(
        token,
        "Test 2: PA -> CO con CP validos",
        {
            "origin": {
                "city": "Panama",
                "country": "PA",
                "postal_code": "0000"
            },
            "destination": {
                "city": "Bogota",
                "country": "CO",
                "postal_code": "110111"
            },
            "weight": 5,
            "dimensions": {
                "length": 30,
                "width": 20,
                "height": 10
            },
            "service": "P",
            "account_number": "706014493",
            "shippingDate": date_5_days.strftime('%Y-%m-%d')
        },
        "Deberia funcionar correctamente y devolver rates"
    )
    results.append(("Test 2: PA -> CO (valido)", result))

    # TEST 3: Fecha festiva - 10 de noviembre
    result = test_rate(
        token,
        "Test 3: PA -> CO con fecha festiva (10-nov-2025)",
        {
            "origin": {
                "city": "Panama",
                "country": "PA",
                "postal_code": "0000"
            },
            "destination": {
                "city": "Bogota",
                "country": "CO",
                "postal_code": "110111"
            },
            "weight": 5,
            "dimensions": {
                "length": 30,
                "width": 20,
                "height": 10
            },
            "service": "P",
            "account_number": "706014493",
            "shippingDate": "2025-11-10"
        },
        "Validar comportamiento con fecha festiva en Panama"
    )
    results.append(("Test 3: Fecha festiva (10-nov)", result))

    # TEST 4: Fecha valida - 17 de noviembre
    result = test_rate(
        token,
        "Test 4: PA -> CO con fecha valida (17-nov-2025)",
        {
            "origin": {
                "city": "Panama",
                "country": "PA",
                "postal_code": "0000"
            },
            "destination": {
                "city": "Bogota",
                "country": "CO",
                "postal_code": "110111"
            },
            "weight": 5,
            "dimensions": {
                "length": 30,
                "width": 20,
                "height": 10
            },
            "service": "P",
            "account_number": "706014493",
            "shippingDate": "2025-11-17"
        },
        "Deberia funcionar correctamente (fecha laboral)"
    )
    results.append(("Test 4: Fecha valida (17-nov)", result))

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN DE RESULTADOS")
    print("=" * 80)

    passed = sum(1 for _, r in results if r)
    failed = len(results) - passed

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed} exitosos, {failed} fallidos de {len(results)} tests")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTests interrumpidos por el usuario.")
    except Exception as e:
        print(f"\n\nError inesperado: {e}")
