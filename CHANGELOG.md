# ### Fixed
## [Unreleased]
### Fixed
- **✅ Postal Code en Landing Cost**: Corregido error donde `origin.postal_code` se requería como obligatorio en el validador de landing cost. Ahora usa "0" como valor por defecto cuando está vacío, igual que el endpoint de cotizaciones (rate)
- **🔧 Peso declarado en cotizaciones**: Corregido error donde `declared_weight` permanecía en 0 mientras `weight` se actualizaba, causando validación fallida en API
- **⚖️ Sincronización de peso**: La función `updateRateData` ahora sincroniza automáticamente `declared_weight` con `weight` cuando el usuario ingresa el peso
- **⚠️ Warning React corregido**: Eliminado warning "defaultProps will be removed" reemplazando con parámetros por defecto en ShipmentTab
- **✅ RESUELTO: Dropdowns de país en formulario de envío**: Corregido problema donde dropdowns mostraban "selecciona un país" aunque los datos se transfirieran correctamente
- **🔄 Sincronización de formularios**: Agregados useEffect para sincronizar SmartLocationDropdown cuando cambian los datos desde cotizaciones
- **✅ RESUELTO: Transferencia de datos país en cotizaciones**: Los datos de país SÍ se transferían correctamente, el problema era una validación demasiado estricta
- **🔍 Debugging exitoso**: Confirmado que países llegan correctamente (PA→Panamá, AL→Albania) desde cotizaciones a envíos
- **🚀 Transferencia de datos país en cotizaciones**: Corregido el problema donde los datos de país no se transferían de las cotizaciones al crear envíos
- **✅ Validación mejorada**: Agregada validación específica que alerta al usuario si faltan datos de país antes de crear un envío
- **💬 Feedback de usuario**: El sistema ahora informa claramente al usuario cuando debe seleccionar países en los dropdowns de ubicaciónelog
## [Unreleased]
### Fixed
- **� Debugging transferencia de datos país**: Investigando problema donde ciudad se transfiere pero país no
- **�🚀 Transferencia de datos país en cotizaciones**: Corregido el problema donde los datos de país no se transferían de las cotizaciones al crear envíos
- **✅ Validación mejorada**: Agregada validación específica que alerta al usuario si faltan datos de país antes de crear un envío
- **💬 Feedback de usuario**: El sistema ahora informa claramente al usuario cuando debe seleccionar países en los dropdowns de ubicación

### Changed
- **🚀 Mejorado Botón "Crear Envío" en Cotizaciones**:
  - Cambiado texto del botón de "Crear Shipment" a "Crear Envío" (español)
  - Mejorado prellenado de datos del destinatario con plantillas más realistas
  - Agregados números de teléfono de ejemplo en formatos internacionales
  - Mejorado mensaje de notificación para indicar qué datos completar
  - Agregadas clases CSS para resaltar campos prellenados que requieren atención
- **🔧 Debugging mejorado**: Agregado logging detallado para rastrear la transferencia de datos entre cotización y envío

### Added
- **⚡ Optimización de Rate Limiting y Cache para Service Zones**:
  - Agregado cache de 30 minutos al endpoint `analyze_country_structure`
  - Agregado cache de 15 minutos al endpoint `search_service_zones`
  - Implementadas throttle classes personalizadas para service zones
  - Aumentado límite de requests anónimos de 100/hora a 300/hora
  - Aumentado límite de requests autenticados de 1000/hora a 2000/hora
  - Nuevo rate limit específico: 600/hora para consultas de service zones
  - Solución al error "Solicitud fue regulada (throttled)" en SmartLocationDropdown
- **📱 Navegación Móvil Mejorada**: Optimizada la navegación para dispositivos móviles de 390px y superiores
  - Grid de navegación 3x2 especialmente diseñado para móviles (hidden en desktop)
  - Botones con iconos grandes y texto corto optimizados para táctil
  - Navegación desktop preservada con `hidden md:flex` (hidden en móvil)
  - Header responsive con layout vertical en móvil y horizontal en desktop
  - Badges de usuario adaptables con text-xs en móvil
  - Selector de cuenta DHL con padding adaptativo (p-3 móvil, p-4 desktop)
  - Container principal con padding responsive (py-4 md:py-8, px-2 md:px-4)
  - Títulos escalables (text-xl md:text-2xl) para mejor legibilidad
  - Texto adaptativo (text-sm md:text-base) para diferentes tamaños de pantalla
- **🧹 Eliminados Labels de Debug**: Removidos elementos de información técnica que aparecían en pantalla
  - Eliminada sección "Debug Info" del componente SmartLocationDropdown
  - Ya no se muestra información técnica como patrones, campos de ciudad, estados, etc.
  - Interfaz más limpia y profesional sin información de desarrollo
  - Componentes optimizados para producción sin elementos de depuración
- **🧹 Formularios Completamente Limpios**: Eliminados todos los datos precargados/ejemplo
  - Formulario de cotización (Rate) inicia con campos vacíos: peso=0, dimensiones=0x0x0
  - Formulario de envío (Shipment) inicia sin datos personales precargados 
  - Formulario de Landed Cost inicia completamente vacío sin productos de ejemplo
  - Solo se preservan datos cuando se transfiere desde cotizaciones/landed cost
  - Experiencia más limpia para usuarios que prefieren empezar desde cero
  - Validaciones actualizadas para requerir peso > 0 en cotizaciones
- **📦 Botón "Crear Envío" en Landed Cost**: Nueva funcionalidad para crear envíos desde resultados de costo arancelario
  - Botón "📦 Crear Envío con estos Datos" integrado en los resultados de Landed Cost
  - Pre-llenado automático de datos del remitente y destinatario con información del cálculo
  - Navegación automática a la pestaña "Crear Envío" al hacer clic
  - Transferencia completa de datos: origen, destino, peso, dimensiones y costo estimado
  - Notificación informativa mostrando los datos que se van a transferir
  - Integración perfecta con el flujo existente de creación de shipments
  - Funcionalidad consistente con el botón "Crear Envío" de cotizaciones (Rate)
- **⚡ Optimizaze_country_structure`
  - Agregado cache de 15 minutos al endpoint `search_service_zones`
  - Implementadas throttle classes personalizadas para service zones
  - Aumentado límite de requests anónimos de 100/hora a 300/hora
  - Aumentado límite de requests autenticados de 1000/hora a 2000/hora
  - Nuevo rate limit específico: 600/hora para consultas de service zones
  - Solución al error "Solicitud fue regulada (throttled)" en SmartLocationDropdown
- **🚀 SmartLo# Changelog
## [Unreleased]
### Added
- **🎨 Sistema de Diseño Profesional Completo**:
  - Nuevo sistema de colores corporativo con paleta extendida (50-900)
  - Integración de fuente Inter para mayor profesionalismo y legibilidad
  - Sistema de clases CSS utilitarias reutilizables (btn, card, form, alert, etc.)
  - Configuración Tailwind expandida con spacing, shadows y typography mejorados
  - Scrollbar personalizada y micro-interacciones suaves
- **🎯 Interfaz de Usuario Completamente Rediseñada**:
  - Navegación principal mejorada con logo profesional y badges de estado
  - Login rediseñado con cards, iconografía SVG y estados de carga animados
  - Dashboard con header informativo, navegación por pestañas mejorada y layout responsivo
  - AccountDropdown con diseño consistente y mejor organización visual
  - Todas las pestañas actualizadas con el nuevo sistema de diseño
- **📱 Responsive Design Completo**:
  - Layout adaptativo para desktop, tablet y mobile
  - Grid system flexible que se ajusta automáticamente
  - Navegación colapsable en dispositivos pequeños
  - Typography escalable según el dispositivo
- **🔧 Componentes Mejorados Manteniendo Funcionalidad**:
  - RateTabImproved con cards temáticas, proceso visual numerado e iconografía contextual
  - Sistema de alertas unificado (success, warning, error, info) con iconos SVG
  - Botones con estados de hover, focus y loading mejorados
  - Forms con labels informativos, tooltips y validación visual
  - Notificaciones con botón de cierre y transiciones suavesligentes para remitente y destinatario
  - Validación automática de ubicaciones con servicio DHL Express disponible
  - Interfaz consistente con RateTabImproved y LandedCostTab
  - Manejo automático de códigos de país, estado, ciudad y código postal
  - Reducción significativa de errores en datos de ubicación para envíos
  - Iconografía visual distintiva (📍) para identificar secciones de ubicación
  - Sección de ayuda informativa sobre cobertura de DHL Express
- **🌟 SmartLocationDropdown integrado en LandedCostTab**:
  - Reemplazados inputs manuales por dropdowns inteligentes para origen y destino
  - Validación automática de ubicaciones con servicio DHL Express disponible
  - Interfaz consistente con RateTabImproved para mejor experiencia de usuario
  - Manejo automático de códigos de país, ciudad y código postal
  - Reducción significativa de errores de entrada de ubicaciones
  - Sección de ayuda informativa sobre cobertura de DHL Express
- **� Sistema de logging avanzado con rotación por timestamp**:angelog
## [Unreleased]
### Added
- **� Sistema de logging avanzado con rotación por timestamp**:
  - Configuración de logging con `TimedRotatingFileHandler` para rotación diaria automática
  - Logs separados por funcionalidad: `django.log`, `errors.log`, `dhl_api.log`, `requests.log`
  - Formato timestamped con información detallada: timestamp, nivel, módulo, función, línea
  - Retención configurable de archivos históricos (7-60 días según tipo)
  - Logs específicos para DHL API, errores críticos, requests HTTP y eventos de autenticación
  - Configuración diferenciada por entorno (development/staging/production)
- **🛠️ Herramientas de gestión de logs**:
  - Script `manage_logs.py` con menú interactivo para gestión completa de logs
  - Script batch `logs-manager.bat` para Windows con opciones de visualización en tiempo real
  - Funciones de análisis: estadísticas de logs, búsqueda por patrones, limpieza automática
  - Compresión automática de logs antiguos para optimización de espacio
  - Visualización de logs por fecha y timestamp específico
- **⚙️ Configuración de logging personalizable**:
  - Módulo `logging_config.py` con configuraciones avanzadas por entorno
  - Mixins para logging de performance y eventos de seguridad
  - Decorators para logging automático de tiempo de ejecución de funciones
  - Logger específico para llamadas API DHL con métricas de rendimiento
  - Logging estructurado en formato JSON para análisis automatizado
- **�💡 Tooltips de ayuda en cotización de tarifas**:
  - Tooltips informativos con FieldTooltip en todos los campos del formulario de cotización
  - Información detallada sobre límites, ejemplos y validaciones para cada campo
  - Documentación específica para origen, destino, peso, dimensiones y configuraciones
  - Nota informativa para usuarios sobre la disponibilidad de ayuda contextual
  - Definiciones de campos específicas para rate en fieldInfo.js con ejemplos de DHL
- **🔍 Frontend ePOD completamente rediseñado**:angelog
## [Unreleased]
### Added
- **� Frontend ePOD completamente rediseñado**:
  - Sección de estado del procesamiento con información técnica detallada
  - Troubleshooting automático con causas posibles y sugerencias específicas
  - Visualización de validaciones realizadas (base64, PDF, estructura DHL, autenticación)
  - Información técnica expandible con datos completos de la API
  - Estados visuales mejorados: éxito (verde), error (rojo), warning (amarillo)
  - Métricas de procesamiento: tiempo de respuesta, documentos encontrados, cuenta utilizada
  - Detalles de la API DHL: endpoint, content-type, HTTP status, tiempo de respuesta
  - Ejemplo completo en `example_frontend_responses.py` mostrando todos los escenarios
- **�🎯 Manejo mejorado de respuestas para cliente en ePOD**: 
  - Vista `epod_view` completamente reescrita con información detallada para el cliente
  - Estados claros: "found", "not_found", "connection_error", "validation_error", "internal_error"
  - Información de procesamiento en tiempo real: validación, contacto API, recepción respuesta
  - Métricas de rendimiento: tiempo de respuesta API, tamaño de documentos, contadores
  - Guías de resolución de problemas (troubleshooting) automáticas para cada tipo de error
  - IDs de error únicos para soporte técnico con timestamps
  - Mensajes amigables y sugerencias específicas para cada escenario
- **📋 Serializer ePOD mejorado**:
  - Parámetro `content_type` con validación de tipos DHL oficiales
  - Opciones: epod-summary, epod-detail, epod-detail-esig, epod-summary-esig, etc.
  - Validación de entrada más robusta
- **📄 Manejo mejorado de respuestas ePOD**: 
  - Parser completamente reescrito basado en documentación oficial DHL
  - Validación robusta de contenido base64 con verificación de formato
  - Manejo inteligente de múltiples documentos (selecciona automáticamente el válido)
  - Información detallada de cada documento: tamaño, formato, validez
  - Estadísticas completas: documentos válidos/inválidos, tamaños en MB/bytes
  - Códigos de error específicos y sugerencias para cada tipo de fallo
  - Soporte para diferentes formatos (PDF, etc.) y tipos de documento (POD, SIGNATURE)
  - Logging mejorado para debugging y monitoreo
- **🔍 Validación avanzada de base64**:
  - Verificación de caracteres válidos y longitud correcta
  - Decodificación segura con manejo de errores
  - Detección automática de contenido PDF
- **📄 Headers mejorados para ePOD API**: 
  - Nuevo método `_get_epod_headers()` con todos los headers recomendados por DHL
  - Headers adicionales: Message-Reference, Message-Reference-Date, Plugin-Name, Plugin-Version
  - Headers de plataforma: Shipping-System-Platform-Name/Version, Webstore-Platform-Name/Version
  - Header x-version con versión de API DHL (3.0.0)
  - Generación automática de UUID para Message-Reference y timestamp RFC 2822
- **🔧 Configuración de desarrollo local mejorada**:s cambios importantes de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto se adhiere al [Versionado Semántico](https://semver.org/lang/es/).

# Changelog

Todos los cambios importantes de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto se adhiere al [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]
### Added
- **� Headers mejorados para ePOD API**: 
  - Nuevo método `_get_epod_headers()` con todos los headers recomendados por DHL
  - Headers adicionales: Message-Reference, Message-Reference-Date, Plugin-Name, Plugin-Version
  - Headers de plataforma: Shipping-System-Platform-Name/Version, Webstore-Platform-Name/Version
  - Header x-version con versión de API DHL (3.0.0)
  - Generación automática de UUID para Message-Reference y timestamp RFC 2822
- **�🔧 Configuración de desarrollo local mejorada**: 
  - Nuevo `docker-compose.dev.yml` para desarrollo con frontend y backend
  - Configuración `.env` actualizada con variables para desarrollo
  - Script `docker-dev.bat` mejorado con más comandos útiles
  - Soporte para SQLite en desarrollo local
  - Health check endpoint en `/api/health/`
  - Configuración automática de base de datos según DATABASE_URL
- **⚠️ Validación de Warning 200200 (Códigos HS)**:
  - Detecta automáticamente códigos HS incompletos o inválidos
  - Explica por qué DHL no puede calcular aranceles sin códigos HS completos
  - Proporciona ejemplos de códigos HS correctos por categoría de producto
  - Warnings específicos para códigos genéricos (999999), inválidos, o muy cortos
  - Demo educativo `demo_warning_200200.py` con ejemplos prácticos
- **💰 Sistema de validación de precio mejorado**:
  - Validaciones automáticas para opciones que afectan precio (DTP, seguro, cargos)
  - Estimaciones de impacto en costo antes del cálculo
  - Warnings específicos sobre combinaciones costosas
  - Documentación completa en PRICE_IMPACT_ANALYSIS.md

### Fixed
- **🔧 Error de build**: Eliminado `pkg-resources==0.0.0` de requirements.txt que causaba fallo de instalación
  - `pkg-resources` es un paquete virtual que no debe ser instalado explícitamente

### Changed
- **📦 Base de datos flexible**: Settings.py ahora soporta SQLite, PostgreSQL via DATABASE_URL o configuración individual
- **🐳 Docker optimizado**: Separación clara entre desarrollo (dev) y producción (render)
- **🚀 Configuración para Render Free Tier**: Optimización completa para despliegue en Render gratuito (500MB RAM, 0.1 CPU)
  - `docker-compose.yml` optimizado con límites de memoria (400MB para backend)
  - `Dockerfile.render` específico para producción en Render
  - `requirements.render.txt` con dependencias mínimas (sin PostgreSQL, Celery, etc.)
  - `settings_render.py` con configuración Django ultra-optimizada
  - `gunicorn.render.conf.py` con 1 worker y timeouts reducidos
  - `start-render.sh` script de inicio automatizado
  - `render.yaml` configuración de servicios (backend API + frontend estático)
  - `RENDER_DEPLOY.md` guía completa de despliegue

### Changed
- **💾 Base de Datos**: Cambiado de PostgreSQL a SQLite para ahorrar ~200MB de memoria
- **⚡ Servidor**: Configuración Gunicorn optimizada (1 worker, timeouts reducidos, max 200 requests)
- **🗂️ Frontend**: Separado como sitio estático independiente para reducir consumo de memoria
- **📝 Logging**: Reducido a nivel WARNING para conservar recursos
- **🔧 Middleware**: Removidos componentes no esenciales para desarrollo

### Removed
- **PostgreSQL**: Comentado en docker-compose.yml para usar SQLite
- **Múltiples workers**: Solo 1 worker de Gunicorn para conservar memoria
- **Hot-reload**: Deshabilitado en producción para optimizar rendimiento
- **Dependencias pesadas**: Celery, django-extensions, Faker removidos de requirements.render.txt

### Security
- **Configuración de producción**: HTTPS forzado, headers de seguridad, DEBUG=False por defecto

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