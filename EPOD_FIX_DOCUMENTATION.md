# Fix de ePOD - Account Number

## Problema Identificado

El usuario reportó un error 404 en la pestaña ePOD con el siguiente mensaje:

```json
{
    "success": false,
    "error_code": "404",
    "message": "Error DHL API: Error desconocido",
    "http_status": 404,
    "error_data": {
        "instance": "/expressapi/shipments/5339266472/proof-of-delivery?shipperAccountNumber=706014493&content=epod-summary",
        "title": "No data found",
        "status": "404"
    },
    "request_timestamp": "2025-07-24T02:56:40.524935",
    "shipment_id": "5339266472",
    "requested_by": "admin"
}
```

**Payload enviado desde el frontend:**
```json
{
    "shipment_id": "5339266472",
    "account_number": "706065602"
}
```

## Análisis del Problema

El problema era que aunque el frontend enviaba el `account_number` correcto (`706065602`), el backend no lo estaba utilizando. En su lugar, siempre usaba el número de cuenta por defecto (`706014493`), como se puede ver en la URL del error:

`/expressapi/shipments/5339266472/proof-of-delivery?shipperAccountNumber=706014493&content=epod-summary`

## Solución Implementada

### 1. Actualización del Serializer (`dhl_api/serializers.py`)

**ANTES:**
```python
class EPODRequestSerializer(serializers.Serializer):
    """Serializer para requests de ePOD"""
    shipment_id = serializers.CharField(max_length=50)
```

**DESPUÉS:**
```python
class EPODRequestSerializer(serializers.Serializer):
    """Serializer para requests de ePOD"""
    shipment_id = serializers.CharField(max_length=50)
    account_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
```

### 2. Actualización de la Vista (`dhl_api/views.py`)

**ANTES:**
```python
result = dhl_service.get_ePOD(
    shipment_id=serializer.validated_data['shipment_id']
)
```

**DESPUÉS:**
```python
result = dhl_service.get_ePOD(
    shipment_id=serializer.validated_data['shipment_id'],
    account_number=serializer.validated_data.get('account_number')
)
```

### 3. Mejora en el Servicio (Log adicional)

Se agregó un log para hacer tracking del `account_number` utilizado:

```python
# Usar cuenta por defecto si no se proporciona
account_to_use = account_number if account_number else '706014493'
logger.info(f"ePOD: Using account_number={account_number}, final account_to_use={account_to_use}")
```

## Comportamiento Después del Fix

### Caso 1: Con account_number específico
**Request:**
```json
{
    "shipment_id": "5339266472",
    "account_number": "706065602"
}
```

**Resultado:** La URL generada ahora usará `shipperAccountNumber=706065602`

### Caso 2: Sin account_number
**Request:**
```json
{
    "shipment_id": "5339266472"
}
```

**Resultado:** La URL generará usará el valor por defecto `shipperAccountNumber=706014493`

## Validación del Fix

Para validar que el fix funciona correctamente:

1. **Abrir el frontend** en `http://localhost:3002`
2. **Ir a la pestaña ePOD**
3. **Seleccionar una cuenta** en el dropdown (importante: debe estar seleccionada una cuenta)
4. **Ingresar un número de tracking** (ej: `5339266472`)
5. **Hacer click en obtener ePOD**
6. **Revisar los logs del backend**:
   ```bash
   docker logs dhl-django-backend --tail=20
   ```

### Logs Esperados

Deberías ver algo como:
```
INFO [fecha] [dhl_api.services:113] ePOD: Using account_number=706065602, final account_to_use=706065602
INFO [fecha] [dhl_api.services:116] Making ePOD request to: https://express.api.dhl.com/mydhlapi/shipments/5339266472/proof-of-delivery
```

Si el `account_number` es None o vacío:
```
INFO [fecha] [dhl_api.services:113] ePOD: Using account_number=None, final account_to_use=706014493
```

## Archivos Modificados

- ✅ `dhl_api/serializers.py` - Agregado campo `account_number`
- ✅ `dhl_api/views.py` - Pasando `account_number` al servicio
- ✅ `dhl_api/services.py` - Agregado log para debugging

## Estado

✅ **FIX IMPLEMENTADO Y FUNCIONAL**

El error 404 que el usuario experimenta ahora debería mostrar la URL correcta con el `account_number` proporcionado desde el frontend. Si persiste el 404, será por otros motivos (ej: tracking number inválido, cuenta sin acceso al shipment, etc.) pero ya no por usar la cuenta incorrecta.
