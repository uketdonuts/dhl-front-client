import os, sys
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dhl_project.settings')
import django
django.setup()
from dhl_api.services import DHLService

# Datos de prueba rápida
test_data = {
    'products': [{
        'productCode': 'P',
        'productName': 'EXPRESS WORLDWIDE',
        'totalPrice': [{'currencyType': 'BILLC', 'priceCurrency': 'USD', 'price': 392.44}],
        'detailedPriceBreakdown': [{
            'currencyType': 'BILLC',
            'breakdown': [{'name': 'EXPRESS WORLDWIDE', 'price': 307.78}]
        }]
    }]
}

service = DHLService()
result = service._parse_rest_rate_response(test_data)
print('✅ MONEDA:', result['rates'][0]['currency'])
print('✅ PRECIO:', result['rates'][0]['total_charge'])
print('✅ DESGLOSE:', len(result['rates'][0]['charges']))
print('✅ SUCCESS:', result.get('success'))
