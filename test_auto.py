#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test automatizado - Ejecutar con: python test_auto.py USERNAME PASSWORD
"""
import requests
import json
from datetime import datetime, timedelta
import sys

BASE_URL = "http://localhost:8000"

def calculate_business_days(days):
    """Calcula N dias laborales en el futuro"""
    current = datetime.now()
    days_ahead = 1
    business_days_found = 0

    while business_days_found < days:
        next_date = current + timedelta(days=days_ahead)
        if next_date.weekday() < 5:
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
        json={"username": username, "password": password},
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        print("Autenticacion exitosa!")
        return data.get('access')
    else:
        print(f"Error de autenticacion: {response.status_code}")
        print(response.text)
        return None

def test_rate(token, test_name, payload, description):
    """Ejecuta un test de rate"""
    print("\n" + "=" * 80)
    print(f"TEST: {test_name}")
    print("=" * 80)
    print(f"{description}\n")

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

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"RESULTADO: SUCCESS")
                if 'rates' in result and result['rates']:
                    print(f"Servicios: {len(result['rates'])}")
                    for rate in result['rates']:
                        service_name = rate.get('service_name', rate.get('serviceName', 'Unknown'))
                        total_price = rate.get('total_price', rate.get('totalPrice', 0))
                        print(f"  - {service_name}: ${total_price}")
                return True
            else:
                print(f"RESULTADO: ERROR")
                print(f"Mensaje: {result.get('message')}")
                return False
        else:
            print(f"RESULTADO: HTTP ERROR {response.status_code}")
            try:
                error_data = response.json()
                print(f"Mensaje: {error_data.get('message', 'Unknown')}")
            except:
                print(response.text[:200])
            return False

    except Exception as e:
        print(f"RESULTADO: EXCEPTION - {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("Uso: python test_auto.py USERNAME PASSWORD")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    print("=" * 80)
    print("TESTS AUTOMATIZADOS - DHL RATES")
    print("=" * 80)

    token = login(username, password)
    if not token:
        print("\nNo se pudo autenticar. Abortando.")
        sys.exit(1)

    date_5_days = calculate_business_days(5)
    print(f"\nFecha minima: {date_5_days.strftime('%Y-%m-%d')}")

    results = []

    # TEST 1: CR -> NI con auto-reemplazo de CP
    results.append((
        "Test 1: CR->NI (CP auto)",
        test_rate(token, "CR -> NI con CP '0'", {
            "origin": {"city": "San Jose", "country": "CR", "postal_code": "0"},
            "destination": {"city": "Managua", "country": "NI", "postal_code": "0"},
            "weight": 5,
            "dimensions": {"length": 30, "width": 20, "height": 10},
            "service": "P",
            "account_number": "959390223",
            "shippingDate": date_5_days.strftime('%Y-%m-%d')
        }, "Auto-reemplazo: CR 0->10101, NI 0->11001")
    ))

    # TEST 2: PA -> CO valido
    results.append((
        "Test 2: PA->CO (valido)",
        test_rate(token, "PA -> CO valido", {
            "origin": {"city": "Panama", "country": "PA", "postal_code": "0000"},
            "destination": {"city": "Bogota", "country": "CO", "postal_code": "110111"},
            "weight": 5,
            "dimensions": {"length": 30, "width": 20, "height": 10},
            "service": "P",
            "account_number": "706014493",
            "shippingDate": date_5_days.strftime('%Y-%m-%d')
        }, "Deberia funcionar correctamente")
    ))

    # TEST 3: Fecha festiva
    results.append((
        "Test 3: Fecha festiva",
        test_rate(token, "Fecha festiva (10-nov)", {
            "origin": {"city": "Panama", "country": "PA", "postal_code": "0000"},
            "destination": {"city": "Bogota", "country": "CO", "postal_code": "110111"},
            "weight": 5,
            "dimensions": {"length": 30, "width": 20, "height": 10},
            "service": "P",
            "account_number": "706014493",
            "shippingDate": "2025-11-10"
        }, "Validar fecha festiva Panama")
    ))

    # TEST 4: Fecha valida
    results.append((
        "Test 4: Fecha valida",
        test_rate(token, "Fecha valida (17-nov)", {
            "origin": {"city": "Panama", "country": "PA", "postal_code": "0000"},
            "destination": {"city": "Bogota", "country": "CO", "postal_code": "110111"},
            "weight": 5,
            "dimensions": {"length": 30, "width": 20, "height": 10},
            "service": "P",
            "account_number": "706014493",
            "shippingDate": "2025-11-17"
        }, "Deberia funcionar")
    ))

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    passed = sum(1 for _, r in results if r)
    for name, result in results:
        print(f"{'PASS' if result else 'FAIL'} - {name}")
    print(f"\nTotal: {passed}/{len(results)} exitosos")
    print("=" * 80)

if __name__ == "__main__":
    main()
