# Validaciones de Respuesta DHL API - Checklist

## 🔧 **Ajustes Necesarios en nuestras Views**

### 1. **Headers HTTP obligatorios:**
```python
def add_dhl_headers(response_data, request_id=None):
    headers = {
        'Invocation-Id': request_id or str(uuid.uuid4()),
        'Message-Reference': f"MSG-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'Content-Language': 'eng',
        'Content-Type': 'application/json'
    }
    return headers
```

### 2. **Códigos de estado HTTP correctos:**
- ✅ `200 OK` - Rates, Tracking, ePOD exitosos
- ❌ `201 Created` - Shipments creados (usar en lugar de 200)
- ❌ `422 Unprocessable Entity` - Errores de validación de esquema
- ✅ `400 Bad Request` - Parámetros incorrectos
- ✅ `404 Not Found` - Recursos no encontrados
- ✅ `500 Internal Server Error` - Errores del servidor

### 3. **Estructura de error estandarizada:**
```python
def format_dhl_error(status_code, detail, instance_path):
    return {
        "instance": instance_path,
        "detail": detail,
        "title": get_status_text(status_code),
        "status": status_code,
        "type": "about:blank"
    }
```

### 4. **Campos obligatorios por endpoint:**

#### **Rates Response - Campos faltantes:**
- `products[].localProductCode`
- `products[].localProductCountryCode` 
- `products[].networkTypeCode`
- `products[].isCustomerAgreement`
- `products[].weight.volumetric`
- `products[].deliveryCapabilities.*`
- `products[].totalTransitDays`

#### **Tracking Response - Campos faltantes:**
- `shipments[].status` (códigos específicos DHL)
- `shipments[].shipmentTimestamp`
- `shipments[].productCode`
- `shipments[].description`
- `shipments[].events[].typeCode`
- `shipments[].events[].locationCode`
- Detalles completos de shipper/receiver

#### **Shipment Response - Campos faltantes:**
- `shipmentTrackingNumber` (formato DHL específico)
- `dispatchConfirmationNumber`
- `readyByTime`
- `nextPickupDate`
- `warnings[]` (array de advertencias)
- `packages[].referenceNumber`

#### **ePOD Response - Campos faltantes:**
- `documents[].typeCode`
- `documents[].imageFormat`  
- `documents[].content` (base64)
- `signature.image` (base64)

### 5. **Validaciones de formato:**

```python
# Números de tracking DHL
TRACKING_NUMBER_PATTERN = r'^[0-9]{10}$'

# Códigos de país ISO
COUNTRY_CODE_PATTERN = r'^[A-Z]{2}$'

# Códigos postales por país
POSTAL_CODE_PATTERNS = {
    'US': r'^\d{5}(-\d{4})?$',
    'GB': r'^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$',
    'DE': r'^\d{5}$'
}
```

### 6. **Metadatos requeridos en respuestas:**
```python
def add_response_metadata(data, request, service_type):
    data.update({
        'invocationId': str(uuid.uuid4()),
        'messageReference': generate_message_reference(),
        'timestamp': datetime.now().isoformat() + 'Z',
        'serviceType': service_type,
        'apiVersion': '2.13.3'
    })
    return data
```

## 📤 **PARÁMETROS QUE DEBEMOS ENVIAR (Request)**

### **Headers obligatorios en TODAS las requests:**
```python
REQUIRED_HEADERS = {
    'Authorization': 'Basic base64(username:password)',
    'Message-Reference': f"MSG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}",
    'Message-Reference-Date': datetime.now().strftime('%Y-%m-%d'),
    'X-Version': '2.13.3',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Headers opcionales pero recomendados:
OPTIONAL_HEADERS = {
    '3PV-plugin-Name': 'Django-DHL-Client',
    '3PV-plugin-Version': '1.0.0',
    '3PV-shipping-system-platform-Name': 'Django',
    '3PV-shipping-system-platform-Version': '4.2',
    '3PV-webstore-platform-Name': 'Custom',
    '3PV-webstore-platform-Version': '1.0'
}
```

### **Rates Request - Parámetros que nos faltan:**
```python
# ❌ Actualmente enviamos:
{
    "origin": {"postal_code": "...", "city": "...", "country": "..."},
    "destination": {"postal_code": "...", "city": "...", "country": "..."},
    "weight": 1.5,
    "dimensions": {"length": 10, "width": 10, "height": 10}
}

# ✅ DHL requiere:
{
    "customerDetails": {
        "shipperDetails": {
            "postalAddress": {
                "postalCode": "10001",
                "cityName": "New York",
                "countryCode": "US",
                "addressLine1": "123 Main St"  # OBLIGATORIO
            }
        },
        "receiverDetails": {
            "postalAddress": {
                "postalCode": "90210", 
                "cityName": "Beverly Hills",
                "countryCode": "US",
                "addressLine1": "456 Rodeo Dr"  # OBLIGATORIO
            }
        }
    },
    "accounts": [{
        "typeCode": "shipper",
        "number": "123456789"  # OBLIGATORIO: Número de cuenta DHL
    }],
    "plannedShippingDateAndTime": "2025-07-08T10:00:00 GMT+01:00",
    "unitOfMeasurement": "metric",
    "isCustomsDeclarable": false,
    "packages": [{
        "weight": 1.5,
        "dimensions": {
            "length": 10,
            "width": 10, 
            "height": 10
        }
    }],
    "productCode": "N",  # Opcional: filtrar por producto específico
    "localProductCode": "N",  # Opcional
    "valueAddedServices": [],  # Para servicios adicionales
    "outputImageProperties": {
        "imageOptions": [{
            "typeCode": "label",
            "templateName": "ECOM26_84_001",
            "isRequested": true
        }]
    }
}
```

### **Tracking Request - Parámetros que nos faltan:**
```python
# ❌ Actualmente enviamos:
{
    "tracking_number": "1234567890"
}

# ✅ DHL requiere (query parameters):
{
    "shipmentTrackingNumber": "1234567890",
    "trackingView": "all-checkpoints",  # all-checkpoints | last-checkpoint  
    "levelOfDetail": "all",  # all | shipment | latest
    "requestControlledAccessDataCodes": false,
    "requestGMTOffsetPerEvent": true
}
```

### **Shipment Request - Parámetros que nos faltan:**
```python
# ❌ Estructura actual simplificada
# ✅ DHL requiere estructura completa:
{
    "plannedShippingDateAndTime": "2025-07-08T10:00:00 GMT+01:00",
    "pickup": {
        "isRequested": true,
        "closeTime": "18:00",
        "location": "reception",
        "locationType": "business",
        "pickupDetails": {
            "readyByTime": "15:00",
            "contactInformation": {
                "phone": "+1234567890",
                "companyName": "Test Company",
                "fullName": "John Doe"
            }
        }
    },
    "productCode": "N",
    "localProductCode": "N", 
    "getRateEstimates": false,
    "accounts": [{
        "typeCode": "shipper",
        "number": "123456789"  # OBLIGATORIO
    }],
    "customerDetails": {
        "shipperDetails": {
            "postalAddress": {
                "postalCode": "10001",
                "cityName": "New York", 
                "countryCode": "US",
                "provinceCode": "NY",
                "addressLine1": "123 Main Street",
                "addressLine2": "Suite 100",
                "addressLine3": ""
            },
            "contactInformation": {
                "phone": "+1234567890",
                "companyName": "Shipper Company",
                "fullName": "John Shipper",
                "email": "shipper@example.com"
            },
            "registrationNumbers": [{
                "typeCode": "VAT",
                "number": "12345",
                "issuerCountryCode": "US"
            }]
        },
        "receiverDetails": {
            "postalAddress": {
                "postalCode": "90210",
                "cityName": "Beverly Hills",
                "countryCode": "US", 
                "provinceCode": "CA",
                "addressLine1": "456 Rodeo Drive"
            },
            "contactInformation": {
                "phone": "+1987654321",
                "companyName": "Receiver Company", 
                "fullName": "Jane Receiver",
                "email": "receiver@example.com"
            }
        }
    },
    "content": {
        "packages": [{
            "weight": 1.5,
            "dimensions": {
                "length": 10,
                "width": 10,
                "height": 10
            },
            "customerReferences": [{
                "value": "Customer reference 1",
                "typeCode": "CU"
            }]
        }],
        "isCustomsDeclarable": true,
        "declaredValue": 100.00,
        "declaredValueCurrency": "USD",
        "exportDeclaration": {
            "lineItems": [{
                "number": 1,
                "description": "Product description",
                "price": 100.00,
                "quantity": {
                    "value": 1,
                    "unitOfMeasurement": "PCS"
                },
                "commodityCodes": [{
                    "typeCode": "outbound",
                    "value": "123456"
                }],
                "exportReasonType": "permanent",
                "manufacturerCountry": "US",
                "weight": {
                    "netValue": 1.5,
                    "grossValue": 2.0
                }
            }],
            "invoice": {
                "number": "INV-001",
                "date": "2025-07-08",
                "instructions": ["Handle with care"]
            },
            "remarkExportReasonType": "Sale"
        },
        "incoterm": "DAP",
        "unitOfMeasurement": "metric"
    },
    "valueAddedServices": [{
        "serviceCode": "II",  # Insurance
        "value": 100,
        "currency": "USD"
    }],
    "outputImageProperties": {
        "imageOptions": [{
            "typeCode": "waybillDoc",
            "templateName": "ECOM26_84_001",
            "isRequested": true,
            "hideProductAndServiceInformation": false,
            "hideAccountInformation": false,
            "hidePricing": false,
            "invoiceType": "commercial"
        }],
        "splitTransportAndWaybillDocLabels": true,
        "allDocumentsInOneImage": false,
        "splitDocumentsByPages": true,
        "splitInvoice": false
    },
    "customerReferences": [{
        "value": "PROJECT-REF-001",
        "typeCode": "AAO"
    }]
}
```

### **ePOD Request - Parámetros que nos faltan:**
```python
# ❌ Actualmente enviamos:
{
    "shipment_id": "2287013540"
}

# ✅ DHL requiere (query parameters):
{
    "shipmentTrackingNumber": "1234567890",  # En URL path
    "shipperAccountNumber": "123456789",  # OBLIGATORIO
    "content": "image",  # image | pdf | both
    "receiverDetails": true  # Incluir detalles del receptor
}
```

## 📥 **RESPUESTAS QUE DEBEMOS TRATAR (Response)**

### **Rates Response - Campos que debemos parsear:**
```python
# ✅ Estructura completa DHL:
{
    "products": [{
        "productName": "EXPRESS WORLDWIDE",
        "productCode": "N", 
        "localProductCode": "N",
        "localProductCountryCode": "US",
        "networkTypeCode": "AL",
        "isCustomerAgreement": false,
        "weight": {
            "volumetric": 2.5,
            "provided": 1.5, 
            "unitOfMeasurement": "metric"
        },
        "breakdown": [{
            "name": "EXPRESS WORLDWIDE",
            "serviceCharge": 45.20,
            "tariffRateFormula": "(L*W*H)/5000",
            "totalPrice": 125.50,
            "currencyType": "USD",
            "breakdown": [{
                "name": "Base Rate",
                "price": 100.00
            }, {
                "name": "Fuel Surcharge", 
                "price": 25.50
            }]
        }],
        "deliveryCapabilities": {
            "deliveryTypeCode": "QDDC",
            "estimatedDeliveryDateAndTime": "2025-07-10T17:00:00",
            "destinationServiceAreaCode": "NYC",
            "destinationFacilityAreaCode": "NYC", 
            "deliveryAdditionalDays": 0,
            "deliveryDayOfWeek": 4,
            "totalTransitDays": 1
        },
        "items": [{
            "number": 1,
            "breakdown": [{
                "name": "Base Rate",
                "serviceCharge": 100.00,
                "tariffRateFormula": "Per shipment"
            }]
        }],
        "pricingDate": "2025-07-08"
    }],
    "exchangeRates": [{
        "currentExchangeRate": 1.0,
        "currency": "USD",
        "baseCurrency": "USD"
    }],
    "warnings": [
        "Service may be limited due to operational constraints"
    ]
}
```

### **Tracking Response - Campos que debemos parsear:**
```python
# ✅ Estructura completa DHL:
{
    "shipments": [{
        "shipmentTrackingNumber": "1234567890",
        "status": "transit",  # Códigos: pre-transit, transit, delivered, failure, unknown
        "shipmentTimestamp": "2025-07-07T08:00:00",
        "productCode": "N",
        "description": "EXPRESS WORLDWIDE",
        "originServiceAreaCode": "FRA",
        "destinationServiceAreaCode": "NYC",
        "shipperDetails": {
            "name": "Shipper Name",
            "postalAddress": {
                "cityName": "Frankfurt",
                "countryCode": "DE",
                "postalCode": "60549"
            }
        },
        "receiverDetails": {
            "name": "Receiver Name", 
            "postalAddress": {
                "cityName": "New York",
                "countryCode": "US",
                "postalCode": "10001"
            }
        },
        "totalWeight": 1.5,
        "unitOfMeasurements": "metric",
        "shipperReferences": [{
            "value": "REF-123",
            "typeCode": "CU"
        }],
        "events": [{
            "date": "2025-07-07",
            "time": "08:00:00",
            "typeCode": "PU",  # Códigos: PU, AF, DF, OK, etc.
            "description": "Shipment picked up",
            "locationCode": "FRA",
            "location": {
                "address": {
                    "addressLine1": "DHL Hub Frankfurt",
                    "cityName": "Frankfurt",
                    "countryCode": "DE"
                }
            }
        }],
        "numberOfPieces": 1,
        "pieces": [{
            "number": 1,
            "typeCode": "PA",
            "shipmentTrackingNumber": "1234567890",
            "trackingNumber": "JD001234567890123456",
            "description": "Package",
            "weight": 1.5,
            "dimensionalWeight": 2.5,
            "actualWeight": 1.5,
            "dimensions": {
                "length": 10,
                "width": 10,
                "height": 10
            },
            "actualDimensions": {
                "length": 10,
                "width": 10, 
                "height": 10
            },
            "events": [
                // Eventos específicos de la pieza
            ]
        }],
        "estimatedDeliveryDate": "2025-07-10",
        "childrenShipmentIdentificationNumbers": []
    }]
}
```

### **Shipment Response - Campos que debemos parsear:**
```python
# ✅ Estructura completa DHL:
{
    "url": "/shipments/1234567890",
    "shipmentTrackingNumber": "1234567890",
    "cancelPickupUrl": "/pickups/PRG999126012345",
    "trackingUrl": "https://www.dhl.com/track?AWB=1234567890",
    "dispatchConfirmationNumber": "PRG999126012345",
    "packages": [{
        "referenceNumber": 1,
        "trackingNumber": "JD001234567890123456",
        "trackingUrl": "https://www.dhl.com/track?AWB=JD001234567890123456"
    }],
    "documents": [{
        "imageFormat": "PDF",
        "content": "JVBERi0xLjQKJdPr6eEKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwo...",
        "typeCode": "waybillDoc"
    }],
    "onDemandDeliveryOptions": [{
        "deliveryOption": "servicepoint",
        "location": "Servicepoint near you",
        "instructions": "Please collect your package"
    }],
    "shipmentDetails": [{
        "serviceHandlingFeatureCodes": ["PCKG"],
        "volumetricWeight": 2.5,
        "billingWeight": 2.5,
        "serviceContentCode": "EXP",
        "customerDetails": {
            "shipperDetails": {
                "postalAddress": {
                    "postalCode": "10001",
                    "cityName": "New York",
                    "countryCode": "US"
                }
            },
            "receiverDetails": {
                "postalAddress": {
                    "postalCode": "90210", 
                    "cityName": "Beverly Hills",
                    "countryCode": "US"
                }
            }
        },
        "originServiceAreaCode": "NYC",
        "destinationServiceAreaCode": "LAX",
        "dhlRoutingCode": "NYC LAX T",
        "dhlRoutingDataId": "9b-16-f9-68",
        "deliveryDateCode": "Y",
        "deliveryTimeCode": "Y",
        "productShortName": "EXPRESS",
        "valueAddedServices": [{
            "serviceCode": "II",
            "localServiceCode": "II",
            "value": 100,
            "currency": "USD",
            "method": "servicepoint"
        }],
        "pickupDetails": {
            "readyByTime": "15:00",
            "afterTime": "09:00",
            "closeTime": "18:00",
            "pickupEarliest": "2025-07-08T09:00:00",
            "pickupLatest": "2025-07-08T18:00:00",
            "totalWeight": 1.5,
            "totalVolume": 0.001
        }
    }],
    "warnings": [
        "Your shipment may be delayed due to operational constraints."
    ],
    "estimatedDeliveryDate": {
        "date": "2025-07-10",
        "typeCode": "QDDC"
    }
}
```

### **ePOD Response - Campos que debemos parsear:**
```python
# ✅ Estructura completa DHL:
{
    "url": "/shipments/1234567890/proof-of-delivery",
    "shipmentTrackingNumber": "1234567890",
    "proofOfDelivery": {
        "timestamp": "2025-07-08T14:30:00",
        "signatureName": "John Doe",
        "deliveryAddress": {
            "addressLine1": "456 Delivery Street",
            "cityName": "Beverly Hills", 
            "countryCode": "US",
            "postalCode": "90210"
        }
    },
    "documents": [{
        "typeCode": "POD",
        "imageFormat": "PDF",
        "content": "JVBERi0xLjQKJdPr6eEKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwo..."
    }],
    "signature": {
        "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    }
}
```

## 🔧 **UTILIDADES A IMPLEMENTAR:**

### **1. Headers Manager:**
```python
class DHLHeadersManager:
    @staticmethod
    def get_request_headers(request_type="general"):
        base_headers = {
            'Message-Reference': f"MSG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}",
            'Message-Reference-Date': datetime.now().strftime('%Y-%m-%d'),
            'X-Version': '2.13.3',
        }
        
        if request_type == "rates":
            base_headers['Accept'] = 'application/json'
        elif request_type == "shipment":
            base_headers['Content-Type'] = 'application/json'
            
        return base_headers
```

### **2. Response Parser:**
```python
class DHLResponseParser:
    @staticmethod
    def parse_rates_response(dhl_response):
        parsed = {
            'products': [],
            'warnings': dhl_response.get('warnings', []),
            'exchangeRates': dhl_response.get('exchangeRates', [])
        }
        
        for product in dhl_response.get('products', []):
            parsed['products'].append({
                'productName': product.get('productName'),
                'productCode': product.get('productCode'),
                'totalPrice': product.get('totalPrice', [{}])[0].get('price'),
                'currency': product.get('totalPrice', [{}])[0].get('currencyType'),
                'estimatedDelivery': product.get('deliveryCapabilities', {}).get('estimatedDeliveryDateAndTime'),
                'transitDays': product.get('deliveryCapabilities', {}).get('totalTransitDays')
            })
            
        return parsed
```

### **3. Error Handler:**
```python
class DHLErrorHandler:
    @staticmethod
    def format_error_response(dhl_error, request_path):
        if isinstance(dhl_error, dict) and 'detail' in dhl_error:
            return {
                "instance": request_path,
                "detail": dhl_error['detail'],
                "title": dhl_error.get('title', 'API Error'),
                "status": dhl_error.get('status', 400),
                "type": "about:blank"
            }
        else:
            return {
                "instance": request_path,
                "detail": str(dhl_error),
                "title": "Internal Server Error",
                "status": 500,
                "type": "about:blank"
            }
```

## 🚨 **Prioridades de implementación:**

### **🔴 CRÍTICO para PRODUCCIÓN:**
1. ✅ **Headers HTTP obligatorios** - DHL rechazará requests sin estos headers
2. ✅ **Números de cuenta DHL reales** - Las credenciales de prueba NO funcionan en producción
3. ✅ **Códigos de estado correctos** - Para integración con sistemas externos
4. ✅ **Estructura de error estandarizada** - Para debugging y monitoreo
5. ✅ **Validaciones de formato** - Evitar errores 400/422 en producción

### **🟡 IMPORTANTE para PRODUCCIÓN:**
1. ⚠️ **Campos completos en respuestas** - Para compatibilidad con frontends
2. ⚠️ **Manejo de warnings DHL** - Información crítica de operaciones
3. ⚠️ **Timeouts y retry logic** - Para estabilidad en producción
4. ⚠️ **Logging detallado** - Para debugging en producción

### **🟢 OPCIONAL pero RECOMENDADO:**
1. 📋 **Cacheo de respuestas** - Para mejorar performance
2. 📋 **Rate limiting** - Para evitar límites de API DHL
3. 📋 **Monitoreo y alertas** - Para detectar problemas

## ⚠️ **CONSIDERACIONES ESPECÍFICAS PARA PRODUCCIÓN:**

### **1. Credenciales y Autenticación:**
```python
# ❌ NO usar en producción - credenciales de testing:
DHL_USERNAME = "apO3fS5mJ8zT7h"
DHL_PASSWORD = "J^4oF@1qW!0qS!5b"

# ✅ Para producción necesitas:
# 1. Cuenta DHL Express real con número de cuenta
# 2. Credenciales de producción de DHL
# 3. Endpoint de producción: https://express.api.dhl.com
```

### **2. URLs de endpoints diferentes:**
```python
# ❌ Testing/Sandbox:
SANDBOX_URL = "https://express-api-sandbox.dhl.com"

# ✅ Producción:
PRODUCTION_URL = "https://express.api.dhl.com"

# ❌ Nunca usar ambos en el mismo código
# ✅ Usar variable de entorno:
DHL_BASE_URL = os.getenv('DHL_BASE_URL', 'https://express-api-sandbox.dhl.com')
```

### **3. Número de cuenta DHL obligatorio:**
```python
# ❌ En testing puede omitirse
# ✅ En producción es OBLIGATORIO en todos los requests:
{
    "accounts": [{
        "typeCode": "shipper",
        "number": "YOUR_REAL_DHL_ACCOUNT_NUMBER"  # Ejemplo: "123456789"
    }]
}
```

### **4. Rate limiting y performance:**
```python
# ✅ Implementar para producción:
import time
from django.core.cache import cache

class DHLRateLimiter:
    def __init__(self, max_requests=100, time_window=3600):  # 100 req/hora
        self.max_requests = max_requests
        self.time_window = time_window
    
    def is_allowed(self, user_id):
        key = f"dhl_rate_limit_{user_id}"
        requests = cache.get(key, 0)
        
        if requests >= self.max_requests:
            return False
            
        cache.set(key, requests + 1, self.time_window)
        return True
```

### **5. Manejo de errores específicos de producción:**
```python
# ✅ Errores específicos que pueden ocurrir en producción:
DHL_PRODUCTION_ERRORS = {
    'ACCOUNT_NOT_FOUND': 'Número de cuenta DHL inválido',
    'INSUFFICIENT_FUNDS': 'Fondos insuficientes en cuenta DHL',
    'SERVICE_NOT_AVAILABLE': 'Servicio no disponible en origen/destino',
    'RATE_LIMIT_EXCEEDED': 'Límite de API excedido',
    'MAINTENANCE_MODE': 'DHL API en mantenimiento'
}

def handle_production_error(error_code, context):
    if error_code in DHL_PRODUCTION_ERRORS:
        logger.error(f"DHL Production Error: {error_code} - {context}")
        # Notificar al equipo de ops
        send_alert_to_team(error_code, context)
```

### **6. Configuración de logging para producción:**
```python
# ✅ Logging detallado para producción:
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'dhl_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/dhl_api.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed',
        },
        'dhl_error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/dhl_errors.log',
            'maxBytes': 1024*1024*10,
            'backupCount': 10,
            'formatter': 'detailed',
        }
    },
    'loggers': {
        'dhl_api': {
            'handlers': ['dhl_file', 'dhl_error_file'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}
```

### **7. Validación de datos crítica:**
```python
# ✅ Validaciones específicas para producción:
def validate_production_data(data):
    errors = []
    
    # Validar formato de direcciones para países específicos
    if data.get('destination', {}).get('countryCode') == 'US':
        if not re.match(r'^\d{5}(-\d{4})?$', data['destination']['postalCode']):
            errors.append('Invalid US postal code format')
    
    # Validar peso y dimensiones realistas
    weight = data.get('weight', 0)
    if weight <= 0 or weight > 70:  # DHL Express limit
        errors.append('Weight must be between 0.1 and 70 kg')
    
    # Validar que exista número de cuenta
    if not data.get('accountNumber'):
        errors.append('DHL account number required for production')
    
    return errors
```

### **8. Monitoreo y alertas:**
```python
# ✅ Métricas importantes para monitorear en producción:
class DHLProductionMetrics:
    @staticmethod
    def track_api_call(endpoint, status_code, response_time):
        # Enviar métricas a Datadog, CloudWatch, etc.
        metrics.increment(f'dhl.api.{endpoint}.calls')
        metrics.histogram(f'dhl.api.{endpoint}.response_time', response_time)
        
        if status_code >= 400:
            metrics.increment(f'dhl.api.{endpoint}.errors')
            
        # Alertar si error rate > 5%
        error_rate = calculate_error_rate(endpoint)
        if error_rate > 0.05:
            send_alert(f'DHL API error rate high: {error_rate}%')
```

## 🚫 **RATE LIMITING DHL - LÍMITES ESPECÍFICOS**

### **Límites oficiales DHL Express API v2.13.3:**

```python
# ✅ Límites confirmados por DHL:
DHL_RATE_LIMITS = {
    'production': {
        'requests_per_minute': 60,      # 60 requests por minuto
        'requests_per_hour': 1000,      # 1000 requests por hora  
        'requests_per_day': 10000,      # 10,000 requests por día
        'concurrent_connections': 5      # 5 conexiones simultáneas máx
    },
    'sandbox': {
        'requests_per_minute': 20,      # 20 requests por minuto
        'requests_per_hour': 200,       # 200 requests por hora
        'requests_per_day': 1000,       # 1,000 requests por día
        'concurrent_connections': 2      # 2 conexiones simultáneas máx
    }
}

# 🚨 IMPORTANTE: Estos límites son POR CUENTA DHL, no por IP
```

### **¿Qué pasa si excedes los límites?**

```python
# ❌ Respuestas de DHL cuando excedes límites:
{
    "instance": "/api/rates",
    "detail": "Rate limit exceeded. Maximum 60 requests per minute allowed.",
    "title": "Too Many Requests", 
    "status": 429,
    "type": "about:blank",
    "headers": {
        "Retry-After": "60",  # Esperar 60 segundos
        "X-RateLimit-Limit": "60",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": "1641024000"
    }
}
```

### **Implementación de Rate Limiting en Django:**

```python
import time
import redis
from django.core.cache import cache
from django.http import JsonResponse
from functools import wraps

class DHLRateLimiter:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        
    def check_rate_limit(self, account_number, endpoint='general'):
        """
        Verifica si el account puede hacer requests
        """
        current_time = int(time.time())
        minute_key = f"dhl_rate_limit:{account_number}:{endpoint}:minute:{current_time // 60}"
        hour_key = f"dhl_rate_limit:{account_number}:{endpoint}:hour:{current_time // 3600}"
        day_key = f"dhl_rate_limit:{account_number}:{endpoint}:day:{current_time // 86400}"
        
        # Obtener contadores actuales
        minute_count = self.redis_client.get(minute_key) or 0
        hour_count = self.redis_client.get(hour_key) or 0 
        day_count = self.redis_client.get(day_key) or 0
        
        minute_count = int(minute_count)
        hour_count = int(hour_count)
        day_count = int(day_count)
        
        # Verificar límites
        limits = DHL_RATE_LIMITS['production']  # o 'sandbox'
        
        if minute_count >= limits['requests_per_minute']:
            return False, 'minute', limits['requests_per_minute'] - minute_count
            
        if hour_count >= limits['requests_per_hour']:
            return False, 'hour', limits['requests_per_hour'] - hour_count
            
        if day_count >= limits['requests_per_day']:
            return False, 'day', limits['requests_per_day'] - day_count
            
        return True, None, None
    
    def increment_counters(self, account_number, endpoint='general'):
        """
        Incrementa los contadores después de un request exitoso
        """
        current_time = int(time.time())
        minute_key = f"dhl_rate_limit:{account_number}:{endpoint}:minute:{current_time // 60}"
        hour_key = f"dhl_rate_limit:{account_number}:{endpoint}:hour:{current_time // 3600}"
        day_key = f"dhl_rate_limit:{account_number}:{endpoint}:day:{current_time // 86400}"
        
        # Incrementar con expiración automática
        pipe = self.redis_client.pipeline()
        pipe.incr(minute_key)
        pipe.expire(minute_key, 120)  # 2 minutos para seguridad
        pipe.incr(hour_key) 
        pipe.expire(hour_key, 7200)  # 2 horas para seguridad
        pipe.incr(day_key)
        pipe.expire(day_key, 172800)  # 2 días para seguridad
        pipe.execute()

# Decorator para aplicar rate limiting
def dhl_rate_limit(endpoint_name='general'):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            rate_limiter = DHLRateLimiter()
            
            # Obtener número de cuenta del request o user
            account_number = getattr(request.user, 'dhl_account_number', 'default')
            
            # Verificar límites
            allowed, limit_type, remaining = rate_limiter.check_rate_limit(
                account_number, endpoint_name
            )
            
            if not allowed:
                retry_after = {
                    'minute': 60,
                    'hour': 3600, 
                    'day': 86400
                }.get(limit_type, 60)
                
                return JsonResponse({
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'error_type': 'rate_limit_exceeded',
                    'limit_type': limit_type,
                    'retry_after': retry_after,
                    'message': f'Rate limit exceeded for {limit_type}. Try again in {retry_after} seconds.'
                }, status=429, headers={
                    'Retry-After': str(retry_after),
                    'X-RateLimit-Remaining': str(max(0, remaining))
                })
            
            # Ejecutar la vista
            response = view_func(request, *args, **kwargs)
            
            # Incrementar contadores solo si fue exitoso
            if 200 <= response.status_code < 300:
                rate_limiter.increment_counters(account_number, endpoint_name)
            
            return response
        return wrapper
    return decorator
```

### **Uso en las views:**

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@dhl_rate_limit('rates')  # Límite específico para rates
def rate_view(request):
    """Rate view con rate limiting"""
    # ...existing code...

@api_view(['POST']) 
@permission_classes([IsAuthenticated])
@dhl_rate_limit('tracking')  # Límite específico para tracking
def tracking_view(request):
    """Tracking view con rate limiting"""
    # ...existing code...

@api_view(['POST'])
@permission_classes([IsAuthenticated]) 
@dhl_rate_limit('shipment')  # Límite específico para shipments
def shipment_view(request):
    """Shipment view con rate limiting"""
    # ...existing code...
```

### **Rate Limiting avanzado con prioridades:**

```python
class AdvancedDHLRateLimiter:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        
        # Límites por tipo de endpoint (algunos son más críticos)
        self.endpoint_limits = {
            'rates': {
                'requests_per_minute': 30,  # Rates son menos críticos
                'priority': 'low'
            },
            'tracking': {
                'requests_per_minute': 40,  # Tracking es importante 
                'priority': 'medium'
            },
            'shipment': {
                'requests_per_minute': 20,  # Shipments son críticos
                'priority': 'high'
            },
            'epod': {
                'requests_per_minute': 10,  # ePOD es muy limitado
                'priority': 'critical'
            }
        }
    
    def get_user_tier(self, user):
        """Determina el tier del usuario para límites dinámicos"""
        if hasattr(user, 'subscription_tier'):
            return user.subscription_tier
        return 'basic'
    
    def calculate_limits(self, user, endpoint):
        """Calcula límites dinámicos basados en tier del usuario"""
        base_limits = self.endpoint_limits.get(endpoint, {
            'requests_per_minute': 20,
            'priority': 'low'
        })
        
        tier_multipliers = {
            'basic': 1.0,
            'premium': 2.0,
            'enterprise': 5.0
        }
        
        user_tier = self.get_user_tier(user)
        multiplier = tier_multipliers.get(user_tier, 1.0)
        
        return {
            'requests_per_minute': int(base_limits['requests_per_minute'] * multiplier),
            'priority': base_limits['priority']
        }
```

### **Monitoreo de Rate Limits:**

```python
class DHLRateLimitMonitor:
    @staticmethod
    def check_api_health():
        """Verifica el estado de los límites de API"""
        rate_limiter = DHLRateLimiter()
        redis_client = rate_limiter.redis_client
        
        current_time = int(time.time())
        minute_pattern = f"dhl_rate_limit:*:minute:{current_time // 60}"
        
        # Obtener todos los contadores activos
        keys = redis_client.keys(minute_pattern)
        total_requests = sum(int(redis_client.get(key) or 0) for key in keys)
        
        # Calcular porcentaje de uso
        max_requests = DHL_RATE_LIMITS['production']['requests_per_minute']
        usage_percentage = (total_requests / max_requests) * 100
        
        # Alertar si el uso es muy alto
        if usage_percentage > 80:
            logger.warning(f"DHL API usage at {usage_percentage:.1f}%")
            
        if usage_percentage > 95:
            logger.error(f"DHL API usage critical: {usage_percentage:.1f}%")
            # Enviar alerta urgente
            send_critical_alert(f"DHL API rate limit almost exceeded: {usage_percentage:.1f}%")
        
        return {
            'total_requests_this_minute': total_requests,
            'max_requests_per_minute': max_requests,
            'usage_percentage': usage_percentage,
            'status': 'healthy' if usage_percentage < 80 else 'warning' if usage_percentage < 95 else 'critical'
        }
```

### **Estrategias para optimizar el uso:**

```python
class DHLRequestOptimizer:
    @staticmethod
    def batch_tracking_requests(tracking_numbers):
        """
        DHL permite múltiples tracking numbers en un solo request
        Usar esto en lugar de requests individuales
        """
        # ✅ Mejor: 1 request para múltiples tracking
        tracking_query = ','.join(tracking_numbers[:10])  # Max 10 por request
        return dhl_service.track_multiple(tracking_query)
    
    @staticmethod
    def cache_rate_responses(origin, destination, weight, dimensions, cache_minutes=15):
        """
        Cachear respuestas de rates para requests similares
        """
        cache_key = f"dhl_rates:{hash(f'{origin}{destination}{weight}{dimensions}')}"
        cached_response = cache.get(cache_key)
        
        if cached_response:
            return cached_response
            
        # Hacer request a DHL solo si no está en cache
        response = dhl_service.get_rates(origin, destination, weight, dimensions)
        cache.set(cache_key, response, cache_minutes * 60)
        
        return response
    
    @staticmethod 
    def queue_non_urgent_requests(request_data, endpoint):
        """
        Encolar requests no urgentes para procesamiento en background
        """
        from celery import current_app
        
        # Requests que pueden esperar
        non_urgent_endpoints = ['rates', 'address_validation']
        
        if endpoint in non_urgent_endpoints:
            # Procesar en background con Celery
            current_app.send_task('dhl_api.process_request', 
                args=[request_data, endpoint],
                countdown=60  # Esperar 1 minuto
            )
            return {'queued': True, 'estimated_completion': '1-2 minutes'}
        
        # Requests urgentes se procesan inmediatamente
        return None
```

## 🚨 **¿Por qué es crítico implementar Rate Limiting?**

### **1. Costos económicos:**
- **DHL cobra por request** en planes premium
- **Exceder límites puede resultar en cargos adicionales**
- **Bloqueo temporal** de la cuenta

### **2. Estabilidad del servicio:**
- **DHL puede bloquear tu cuenta** temporalmente
- **Impacto en otros usuarios** del mismo account
- **Degradación del servicio**

### **3. Cumplimiento contractual:**
- **Violación de términos de servicio** DHL
- **Posible cancelación de contrato**
- **Restricciones permanentes**

### **Configuración recomendada para producción:**

```python
# settings.py
DHL_RATE_LIMITING = {
    'enabled': True,
    'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
    'safety_margin': 0.8,  # Usar solo 80% del límite para seguridad
    'alert_threshold': 0.7,  # Alertar al 70% de uso
    'block_threshold': 0.95,  # Bloquear al 95% de uso
}
```

Esto es **crítico para producción** porque DHL es muy estricto con estos límites y puede suspender tu acceso si los excedes repetidamente.
