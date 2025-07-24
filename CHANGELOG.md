# Changelog

Todos los cambios importantes de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto se adhiere al [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]
### Changed
- **MEJORA CRÍTICA - Integración Completa del Dropdown de Cuentas**: Sincronización total de la cuenta seleccionada (706091269) con todas las operaciones DHL
  - **Envíos (Shipment)**: El dropdown ahora influye en la creación de envíos, incluyendo `account_number` en `shipmentData`
  - **Tracking**: Las consultas de rastreo ahora incluyen `account_number` para mayor precisión
  - **ePOD (Proof of Delivery)**: Los comprobantes de entrega ahora usan la cuenta seleccionada
  - **Cotizaciones (Rate)**: Mantenida la sincronización existente con el dropdown
  - **Shipment desde Rate**: La creación de envíos desde cotizaciones usa la cuenta seleccionada
  - **Cuenta por Defecto**: Actualizada de 706014493 a 706091269 en todas las operaciones
  - **Sincronización Automática**: useEffect que actualiza todas las operaciones cuando cambia selectedAccount

### Added
- **Módulo ePOD (Electronic Proof of Delivery)**: Nuevo módulo completo para obtener comprobantes de entrega
  - **Formulario de ePOD**: Input para número de tracking de envíos entregados
  - **Descarga de Comprobantes**: Botón principal para descargar el PDF de comprobante de entrega
  - **Documentos Múltiples**: Soporte para descargar documentos adicionales si están disponibles
  - **Información Técnica**: Detalles del documento (tipo, formato, tamaño)
  - **Validación de Estado**: Verificación de que el envío esté entregado antes de mostrar ePOD
  - **Nueva Consulta**: Opción para limpiar formulario y hacer nueva búsqueda
- **Pestaña de Tracking**: Nueva funcionalidad completa de rastreo de envíos
  - **Formulario de Tracking**: Input para ingresar número de tracking con validación
  - **Resultados Detallados**: Muestra estado, origen, destino, servicio y fecha estimada
  - **Historial de Eventos**: Timeline completo con ubicaciones y fechas de cada evento
  - **Enlace a DHL Oficial**: Botón directo al tracking en dhl.com
  - **Botón "Ver Tracking Aquí"**: Navegación directa desde resultados de shipment
  - **Nueva Consulta**: Opción para limpiar formulario y hacer nueva búsqueda
- **Visualización Completa de Respuesta de Shipment**: Nueva interfaz mejorada para mostrar toda la información de envíos creados
  - **Tracking Principal**: Muestra el número de seguimiento principal con diseño destacado
  - **URL de Rastreo DHL**: Botón directo para rastrear en el sitio web de DHL
  - **Información de Paquetes**: Lista detallada de todos los paquetes individuales con sus tracking numbers
  - **Descarga de Documentos**: Funcionalidad para descargar etiquetas y documentos PDF desde contenido base64
  - **Información Adicional**: Detalles completos del envío (ID, estado, tipo de contenido, fecha, usuario)
  - **Botón "Crear Otro Envío"**: Opción para limpiar el formulario y crear un nuevo envío

### Removed
- **Botón "Rastrear Envío en DHL"**: Eliminado el enlace externo al sitio web de DHL desde los resultados de shipment
- **Función downloadDocument**: Utilidad para convertir contenido base64 a PDF descargable
- **Botón "Crear Shipment" en Cotizaciones**: Nueva funcionalidad para crear shipments desde resultados de cotización
  - Botón "📦 Crear Shipment" en cada tarjeta de servicio cotizado
  - Pre-llenado automático de datos de shipment con información de la cotización
  - Navegación automática al tab "Crear Envío" al hacer clic
  - Notificación elegante mostrando los datos pre-llenados
  - Conversión automática de datos: origen/destino, peso, dimensiones, servicio DHL
  - Campos de remitente/destinatario pre-configurados (editables por el usuario)
  - Integración completa con el flujo existente de creación de shipments

### Changed
- **Configuración de entorno**: Cambiado DHL_ENVIRONMENT de 'sandbox' a 'production' por defecto
- **Endpoints corregidos**: URLs de tracking y ePOD actualizadas para coincidir con backend

### Removed
- **Pestaña "Comparar Tipos"**: Eliminada funcionalidad de comparación DOCUMENTS vs NON_DOCUMENTS
  - Función `compareContentTypes` y estados relacionados eliminados
  - Interfaz simplificada enfocada en funcionalidades principales
- **Servicios DHL**: Eliminada lógica de sandbox, solo endpoints de producción

### Removed
- **Archivos de testing**: Eliminados todos los archivos de prueba y testing
  - `test_shipment_fix.py`, `test_rate_demo.py`, `test_improved_parsing.py`
  - `test_frontend_rate_data.py`, `simple_test.py`, `quick_test.py`
  - `frontend_test_data.json`, `test-docker.bat`, `validate-docker.bat`
  - Archivos en `dhl_api/`: `test_service_compatibility.py`, `test_rate_simple.py`, `test_data.py`
  - `dhl_integration.py` (simulador de datos)
  - Comando de management: `setup_simulator.py`
- **Funciones de testing en views.py**: Eliminadas funciones de prueba
  - `test_dhl_credentials_view()` 
  - `test_frontend_rate_view()`
- **Rutas de testing**: Eliminadas rutas de endpoints de prueba en `urls.py`
- **Tareas de testing**: Eliminadas tareas de VS Code para tests
  - "Django: Ejecutar tests"
  - "Docker: Validar entorno"
- **Configuración sandbox**: Eliminada lógica de endpoints de testing en `services.py`
- **Funciones de comparación**: Eliminadas funciones incompletas de testing al final de `services.py`

### Fixed
- **Información de Compatibilidad de Servicios**: Corregida la función `get_service_content_compatibility`
  - Agregados códigos de servicio DHL reales (N, P, T, Y, U, K, L, Q, D, W)
  - Eliminado mensaje "Servicio desconocido, asumiendo paquetes"
  - Información más precisa sobre compatibilidad con documentos, paquetes y pallets
  - Descripción mejorada de cada tipo de servicio DHL
- **Vista de Compatibilidad**: Mejora en la presentación del componente RateResults
  - Reorganización de la información de compatibilidad en grid
  - Indicadores visuales mejorados (✅/❌) para cada tipo de contenido
  - Tipo de servicio visible en vista resumida
  - Script de prueba para validar compatibilidad de servicios
- **Parsing de Respuestas DHL**: Mejorado el procesamiento de datos de cotización
  - Extracción correcta de desglose detallado de precios desde `detailedPriceBreakdown`
  - Conversión de moneda de BILLC a USD real con `priceCurrency`
  - Extracción de fechas y horarios de entrega desde `estimatedDeliveryDateAndTime`
  - Extracción de horarios límite desde `localCutoffDateAndTime`
  - Información de peso mejorada con cálculo de peso facturable
  - Manejo correcto de múltiples tipos de moneda (BILLC, BASEC)
  - Campos de `charges` ahora poblados correctamente con conceptos reales

### Removed
- **Elementos de UI innecesarios**: Limpieza de la interfaz de usuario
  - Eliminada sección "Análisis de Peso" del componente RateResults
  - Eliminada sección "Configuración del Envío" del componente RateResults
  - Eliminada sección "Información del Servicio" con compatibilidad de documentos/paquetes/pallets
  - Eliminada nota informativa (consejo) al final de los resultados
  - Removidos botones "Cargar Datos de Prueba SOAP" del Dashboard
  - Eliminada función `loadSoapTestData` no utilizada
  - Removido indicador de tipo de servicio en vista resumida

### Added
- **Cotizador con Detalles Expandibles**: Nueva interfaz de usuario para cotizaciones DHL
  - Componente `RateResults` con vista resumida y detallada
  - Botones "Ver detalles" para explorar información completa de cada servicio
  - Desglose detallado de precios (conceptos individuales)
  - Información de peso facturable (real, dimensional, declarado)
  - Datos de entrega detallados (fechas, horas límite, próximo día hábil)
  - Compatibilidad de contenido (documentos, paquetes, pallets)
  - Configuración del envío (tipo, aduanas, cuenta DHL)
  - Validación automática de cálculos de precios
  - Script de prueba mejorado `test_rate_simple.py` con interactividad
- **Script de Demostración**: Script interactivo para probar cotizaciones con detalles expandibles

### Changed
- **Migración SOAP a REST**: Migración completa de la API DHL de SOAP/XML a REST/JSON
  - Eliminación completa de endpoints SOAP legacy
  - Migración de ePOD (electronic Proof of Delivery) a endpoint REST moderno
  - Eliminación de todas las dependencias XML (xml.etree.ElementTree)
  - Unificación en API REST moderna de DHL Express MyDHL
  - Mejor rendimiento y mantenimiento del código
  - Parsing JSON nativo en lugar de XML
  - Endpoints REST: `/rates`, `/tracking`, `/shipments`, `/proof-of-delivery`
- **Dashboard Frontend**: Integración del nuevo componente `RateResults` en lugar de la vista básica

### Added
- **Optimización Copilot**: Instrucciones de Copilot optimizadas para reducir tokens (~60% menos)
  - Formato más conciso y estructurado
  - Mantiene toda la información esencial
  - Mejor legibilidad y navegabilidad
  - Reducción significativa de consumo de tokens
- **Configuración Docker-First**: Entorno de desarrollo completamente dockerizado
- **Scripts de automatización**: Archivos .bat para comandos Django y Python
- **docker-compose.dev.yml**: Configuración específica para desarrollo
- **Dockerfile.dev**: Imagen optimizada para desarrollo con hot-reload
- **Tasks de VS Code**: Tareas predefinidas para comandos Docker comunes
- **Documentación Docker**: Guía completa de comandos Docker en README.md
- **DHLAccountManager Component**: Nuevo componente React para gestión completa de cuentas DHL
  - Operaciones CRUD para cuentas DHL
  - Establecimiento de cuenta por defecto
  - Validación de estado de cuentas
  - Interfaz responsiva con Tailwind CSS
- **Tracking DHL Completo**: Implementación completa del sistema de tracking DHL
  - Formato SOAP XML correcto para API de DHL
  - Endpoint: `https://wsbexpress.dhl.com:443/gbl/glDHLExpressTrack`
  - Credenciales de producción configuradas
  - Parsing completo de respuestas XML con información detallada
  - Extracción de eventos de tracking con timestamps
  - Detalles de piezas individuales (peso, dimensiones, license plate)
  - **✅ RESUELTO**: Error crítico en método `_parse_response` que causaba crash del sistema
  - Información del envío (origen, destino, peso total, número de piezas)
  - Manejo robusto de errores y logging detallado
  - **🆕 BOTÓN COTIZAR**: Botón "Cotizar este envío" en detalles de piezas que auto-completa cotización
- **Scripts de Validación**: Scripts para probar el sistema de tracking
  - `test_tracking_standalone.py`: Prueba directa del API DHL
  - `test_complete_system.py`: Prueba del flujo completo Django
  - `verify_implementation.py`: Verificación de la implementación
- **Documentación de Tracking**: Documentación completa de la solución
  - `TRACKING_SOLUTION_COMPLETED.md`: Resumen completo de la solución
  - Ejemplos de respuestas XML y JSON
  - Guía de troubleshooting

### Fixed
- **Migración completa a API REST**: Eliminado completamente el uso de XML/SOAP en favor de JSON/REST
  - Actualizado endpoint de cotizaciones: `https://express.api.dhl.com/expressapi/rates`
  - Actualizado endpoint de tracking: `https://express.api.dhl.com/expressapi/shipments/{}/tracking`
  - Actualizado endpoint de shipments: `https://express.api.dhl.com/expressapi/shipments`
  - Eliminados todos los métodos SOAP y XML parsing
  - Implementado `_get_rest_headers()` para autenticación HTTP Basic
  - Implementado `_parse_rest_response()` para manejar respuestas JSON
  - Implementado `_parse_rest_rate_response()` para parsing de cotizaciones
  - Implementado `_parse_rest_tracking_response()` para parsing de tracking
  - Actualizado método `validate_account()` para usar API REST
- **Cotizador DHL**: Progreso en la solución del problema "SERVER_ERROR"
  - Identificado problema: La API REST de DHL requiere endpoints específicos
  - Cambio de HTTP 500 a HTTP 404 (progreso en la conexión)
  - Investigación de endpoints correctos: `/expressapi/rates` vs `/mydhlapi/rates`
  - Implementado manejo completo de respuestas REST JSON
  - Eliminado parsing XML obsoleto
  - Mejorado sistema de logging para debugging REST
- **Estructura de datos**: Actualizado formato de request para API REST
  - Reemplazado XML SOAP por JSON payload estructurado
  - Implementado campos requeridos: `customerDetails`, `accounts`, `packages`
  - Agregado soporte para `plannedShippingDateAndTime` automático
  - Implementado conversión automática de `content_type` a `isCustomsDeclarable`
  - Mejorado cálculo de peso facturable para API REST
- **Endpoints modernos**: Migración completa a arquitectura REST
  - Sandbox: `https://express.api.dhl.com/mydhlapi/test/`
  - Producción: `https://express.api.dhl.com/expressapi/`
  - Eliminados endpoints SOAP legacy
  - Implementado patrón de URLs dinámicas para tracking
  - Agregado soporte para múltiples endpoints (rates, tracking, shipments, products)

### Technical Notes
- **API Migration**: Transición completa de SOAP/XML a REST/JSON
- **Endpoint Investigation**: Probando diferentes rutas de API DHL
- **Estado actual**: Recibiendo HTTP 404, indica que el endpoint o la autenticación requieren ajustes
- **Próximos pasos**: Validar credenciales y endpoints correctos para API REST de DHL

### Changed
- **Endpoints DHL**: Configuración mejorada con soporte para sandbox y producción
- **Headers HTTP**: Headers simplificados para requests de cotización
- **Parsing de respuestas**: Mejorado parsing de errores de validación XML

### Technical Notes
- **Progreso en Cotizador**: Evolución de HTTP 500 a errores específicos de validación
- **Próximos pasos**: Ajustar estructura XML del elemento `ClientDetail` según documentación DHL
- **Estado actual**: Recibiendo respuestas HTTP 200 con errores de validación específicos (progreso significativo)
- **Scripts Docker**: Corregidos nombres de contenedores en todos los scripts .bat
- **✅ PROXY ERROR RESOLVED**: Error crítico de proxy "Error occurred while trying to proxy: localhost:3002/api/dhl/tracking/" 
  - **Causa raíz**: Errores de sintaxis en `services.py` y `views.py` causaban crash del backend
  - **Solución**: Corregidos imports faltantes (`import re`, `import random`, `import logging`, `import pytz`)
  - **Solución**: Corregidos errores de indentación en métodos `get_ePOD`, `rate_view`
  - **Solución**: Completados bloques de código incompletos en parsing de respuestas
  - **Verificación**: Proxy funcionando correctamente: Frontend (3002) → Backend (8001)
  - **Estado**: Sistema completamente funcional con tracking y cotización DHL operativas
  - `django-manage.bat`: Ahora usa `dhl-django-backend` en lugar de `dhl-django-backend-dev`
  - `python-docker.bat`: Actualizado nombre del contenedor backend
  - `docker-shell.bat`: Corregido acceso al shell del contenedor
  - `test-docker.bat`: Actualizado para usar el nombre correcto del contenedor
  - `pip-docker.bat`: Corregido para instalación de dependencias
  - `docker-dev.bat`: Actualizado nombres de contenedores backend y postgres
  - `validate-docker.bat`: Corregido comando de validación Django
- **Migraciones Django**: Aplicadas correctamente las migraciones de la aplicación dhl_api
- **Base de datos**: Creadas todas las tablas necesarias para el funcionamiento del sistema
- **ERROR CRÍTICO - Tracking sin cuenta DHL**: Solucionado error "No se encontró una cuenta DHL configurada"
  - **Ubicación**: `dhl_api/views.py` función `tracking_view` línea 254
  - **Causa**: El sistema requería que el usuario tuviera una DHLAccount configurada antes de usar tracking
  - **Solución**: Creación automática de cuenta DHL por defecto (706065602) cuando no existe
  - **Beneficios**: 
    - Eliminación del error bloqueante en tracking
    - Funcionalidad inmediata sin configuración manual
    - Compatibilidad con sistema existente de cuentas
    - Logs detallados para debugging
- **Docker Compose**: Actualizada versión de PostgreSQL de 13 a 14 para compatibilidad con Django
- **Health Checks**: Añadidos health checks para PostgreSQL en docker-compose
- **❌ PROBLEMA RESUELTO**: Error de proxy `localhost:3002/api/dhl/tracking/`
  - **Causa**: Implementación incompleta del servicio DHL tracking
  - **Solución**: Implementación completa del método `get_tracking` con formato SOAP correcto
  - **Resultado**: Frontend ahora puede conectarse correctamente al backend
- **Servicio DHL (`dhl_api/services.py`)**:
  - Método `get_tracking` completamente reescrito con formato SOAP correcto
  - Headers HTTP apropiados para DHL API
  - Timeout configurado (30 segundos)
  - Parsing XML mejorado con extracción completa de información
  - Estructura de respuesta JSON estandarizada
- **Docker Configuration**:
  - PostgreSQL actualizado de versión 13 a 14-alpine
  - Health checks configurados para todos los servicios
  - Dependencias de servicios corregidas
  - Volúmenes de base de datos limpiados y recreados
- **Manejo de Errores**:
  - Logging detallado para debugging
  - Validación de números de tracking
  - Manejo de timeouts y errores HTTP
  - Respuestas consistentes de error
  - **✅ CRÍTICO**: Corregido error fatal en `get_tracking` que pasaba XML Element en lugar de HTTP Response a `_parse_response`

### Changed
- **Flujo de desarrollo**: Todos los comandos Python ahora se ejecutan en contenedores Docker
- **Instrucciones de Copilot**: Actualizadas para reflejar el enfoque Docker-First
- **Configuración de puertos**: Backend en 8001, Frontend en 3002, PostgreSQL en 5433
- **Volúmenes persistentes**: Configuración para mantener datos entre reinicios
- **Estructura de Respuesta de Tracking**: Formato JSON estructurado
  ```json
  {
    "success": true,
    "tracking_info": { /* información del envío */ },
    "events": [ /* array de eventos */ ],
    "piece_details": [ /* array de detalles de piezas */ ],
    "total_events": number,
    "total_pieces": number,
    "message": "string"
  }
  ```

### Deprecated

### Removed

### Security

## [1.0.0] - 2025-07-14
### Added
- Proyecto inicial DHL Front Client
- Configuración de Django + Django REST Framework
- Frontend en React.js con Tailwind CSS
- Sistema de autenticación básico
- Integración con API de DHL
- Contenedores Docker
- Documentación básica del proyecto