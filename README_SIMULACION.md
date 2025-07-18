# 🚀 Sistema de Simulación de Datos DHL

Este sistema permite simular las respuestas de DHL para desarrollo y pruebas, manteniendo la misma interfaz que el servicio real.

## 📁 Archivos Incluidos

- **`simulate_dhl_data.py`**: Simulador principal que genera datos dinámicos
- **`test_data.py`**: Datos de prueba predefinidos para casos específicos
- **`examples_dhl_data.py`**: Ejemplos de cómo usar los datos simulados
- **`dhl_integration.py`**: Integración con el sistema existente

## 🔧 Configuración

### Modo Desarrollo
```bash
# En tu archivo .env
DHL_SIMULATE_MODE=true
```

### Modo Producción
```bash
# En tu archivo .env
DHL_SIMULATE_MODE=false
DHL_USERNAME=tu_usuario_real
DHL_PASSWORD=tu_password_real
DHL_BASE_URL=https://wsbexpress.dhl.com
```

## 🚀 Uso Básico

### 1. Importar el Simulador
```python
from dhl_integration import get_dhl_service

# Obtener servicio (automáticamente usa simulador en desarrollo)
dhl_service = get_dhl_service()
```

### 2. Tracking de Envíos
```python
# Usar números de tracking predefinidos
tracking_data = dhl_service.get_tracking('1234567890')  # Entregado
tracking_data = dhl_service.get_tracking('1234567891')  # En tránsito
tracking_data = dhl_service.get_tracking('1234567892')  # Excepción

# O usar números aleatorios para datos dinámicos
tracking_data = dhl_service.get_tracking('9876543210')

print(f"Estado: {tracking_data['tracking_info']['status']}")
print(f"Eventos: {tracking_data['total_events']}")
```

### 3. Cotizaciones
```python
rate_data = dhl_service.get_rate(
    origin={'country': 'PA'},
    destination={'country': 'US'},
    weight=2.5,
    dimensions={'length': 25, 'width': 20, 'height': 15}
)

for rate in rate_data['rates']:
    print(f"{rate['service_name']}: ${rate['total_charge']:.2f}")
```

### 4. Creación de Envíos
```python
from test_data import get_test_data

# Usar datos de formulario predefinidos
shipment_data = get_test_data('form', 'shipment_basic')

# Crear envío
result = dhl_service.create_shipment(shipment_data, 'P')

if result['success']:
    print(f"Tracking: {result['tracking_number']}")
else:
    print(f"Error: {result['message']}")
```

### 5. Validación de Cuentas
```python
is_valid = dhl_service.validate_account('706065602')
print(f"Cuenta válida: {is_valid}")
```

## 📊 Datos de Prueba Predefinidos

### Números de Tracking
```python
TRACKING_NUMBERS = {
    'delivered': '1234567890',
    'in_transit': '1234567891',
    'exception': '1234567892',
    'returned': '1234567893',
    'processing': '1234567894'
}
```

### Cuentas de Prueba
```python
TEST_ACCOUNTS = {
    'principal': {
        'account_number': '706065602',
        'status': 'active',
        'services': ['P', 'D', 'K', 'L', 'G', 'W']
    },
    'secundaria': {
        'account_number': '706065603',
        'status': 'active',
        'services': ['P', 'D']
    }
}
```

## 🔄 Integración con Views.py

### Antes (usando servicio real)
```python
from dhl_api.services import DHLService

def tracking_view(request):
    dhl_service = DHLService(username, password, base_url)
    tracking_data = dhl_service.get_tracking(tracking_number)
    return render(request, 'tracking.html', {'data': tracking_data})
```

### Después (con simulador)
```python
from dhl_integration import get_dhl_service

def tracking_view(request):
    dhl_service = get_dhl_service()  # Automáticamente usa simulador en desarrollo
    tracking_data = dhl_service.get_tracking(tracking_number)
    return render(request, 'tracking.html', {'data': tracking_data})
```

## 🧪 Ejecutar Ejemplos

```bash
# Ver todos los ejemplos
python examples_dhl_data.py

# Probar la integración
python dhl_integration.py

# Generar datos dinámicos
python simulate_dhl_data.py
```

## 📝 Casos de Uso Comunes

### 1. Desarrollo Frontend
```python
# Simular diferentes estados de envío
statuses = ['Processing', 'In Transit', 'Delivered', 'Exception']
for status in statuses:
    tracking_data = simulator.simulate_tracking_response(f"TEST{status}", status)
    # Usar tracking_data en tu frontend
```

### 2. Testing
```python
import unittest
from test_data import get_test_data

class TestTrackingView(unittest.TestCase):
    def test_delivered_package(self):
        mock_data = get_test_data('tracking', 'delivered')
        response = self.client.post('/api/tracking/', {
            'tracking_number': '1234567890'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'Delivered')
```

### 3. Simulación de Errores
```python
# Simular errores específicos
error_data = get_test_data('shipment', 'error_invalid_date')
print(f"Error: {error_data['message']}")

# Simular error de autenticación
error_data = get_test_data('errors', 'authentication')
print(f"Código: {error_data['code']}, Solución: {error_data['solution']}")
```

## 🚦 Estados de Envío Simulados

| Estado | Descripción | Eventos Típicos |
|--------|-------------|-----------------|
| `Processing` | Envío en procesamiento | PU (Pickup) |
| `In Transit` | En tránsito | PU, AF, DF, AF |
| `Delivered` | Entregado | PU, AF, DF, AF, CC, OC, OK |
| `Exception` | Excepción | PU, AF, EX |
| `Returned` | Devuelto | PU, AF, DF, RT |

## 🔧 Personalización

### Crear Nuevos Datos de Prueba
```python
# Agregar en test_data.py
NEW_TRACKING_DATA = {
    'custom_scenario': {
        "success": True,
        "tracking_info": {
            "awb_number": "CUSTOM123",
            "status": "Custom Status",
            # ... más datos
        }
    }
}
```

### Modificar Simulador
```python
# Extender DHLDataSimulator
class CustomDHLSimulator(DHLDataSimulator):
    def simulate_custom_scenario(self, tracking_number):
        # Tu lógica personalizada
        return custom_data
```

## 🐛 Debugging

### Activar Logs de Simulación
```python
# El simulador automáticamente imprime logs
🔍 Simulando tracking para: 1234567890
💰 Simulando cotización: PA -> US, 2.5kg
📦 Simulando creación de envío: P
```

### Verificar Modo Activo
```python
from dhl_integration import DHLServiceSimulator

simulator = DHLServiceSimulator()
print(f"Modo simulación: {simulator.simulate_mode}")
```

## 📈 Ventajas del Sistema

1. **🚀 Desarrollo más rápido**: No depende de API externa
2. **💰 Sin costos**: No consume calls reales de DHL
3. **🔧 Datos consistentes**: Mismos datos para todos los desarrolladores
4. **🧪 Testing fácil**: Datos predecibles para pruebas
5. **🔄 Fácil cambio**: Un toggle para activar/desactivar
6. **📊 Casos completos**: Cubre success, errors, y edge cases

## 🚨 Importante

- **Nunca** hacer commit de credenciales reales
- **Siempre** usar `DHL_SIMULATE_MODE=false` en producción
- **Verificar** que los datos simulados coincidan con la estructura real
- **Actualizar** los datos de prueba cuando cambie la API de DHL

## 🤝 Contribuir

Para agregar nuevos datos o casos de uso:

1. Agregar datos en `test_data.py`
2. Crear ejemplos en `examples_dhl_data.py`
3. Extender el simulador en `simulate_dhl_data.py`
4. Actualizar este README

---

**✨ ¡Listo para simular todos los datos DHL que necesites!**
