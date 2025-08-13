from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
import logging
from datetime import datetime
from django.utils import timezone
import requests
import pytz
from django.db.models import Q, Count
from .models import DHLAccount
from .throttles import ServiceZoneThrottle, ServiceZoneAnonThrottle
from .serializers import (
    DHLAccountSerializer,
    LoginSerializer,
    RateRequestSerializer,
    EPODRequestSerializer,
    ShipmentRequestSerializer,
    ShipmentSerializer,
    RateQuoteSerializer,
    TrackingRequestSerializer,
    LandedCostRequestSerializer,
    UserActivitySerializer,
    UserActivityFilterSerializer,
    ContactSerializer,
    ContactCreateSerializer
)
from .services import DHLService
from .models import Shipment, RateQuote, LandedCostQuote, UserActivity, Contact, ServiceZone
from .validators import LandedCostValidator
from django.conf import settings
import os
import requests
import json
from django.core.paginator import Paginator
from django.db.models import Q

logger = logging.getLogger(__name__)


def validate_required_fields(data, required_fields):
    """
    Valida que todos los campos requeridos estén presentes y no vacíos
    
    Args:
        data (dict): Datos a validar
        required_fields (list): Lista de campos requeridos
        
    Returns:
        tuple: (is_valid, errors_list)
    """
    errors = []
    
    for field in required_fields:
        # Soporte para campos anidados (ej: "origin.city")
        if '.' in field:
            keys = field.split('.')
            value = data
            
            try:
                for key in keys:
                    value = value[key]
            except (KeyError, TypeError):
                value = None
        else:
            value = data.get(field)
        
        # Validar que el campo no esté vacío
        if value is None or (isinstance(value, str) and value.strip() == ''):
            errors.append(f"Campo requerido faltante o vacío: '{field}'")
        # Para campos numéricos, solo considerar como vacío si es exactamente 0 Y es un campo de peso/dimensiones
        elif isinstance(value, (int, float)) and value <= 0 and any(x in field.lower() for x in ['weight', 'length', 'width', 'height']):
            errors.append(f"Campo requerido faltante o vacío: '{field}'")
    
    return len(errors) == 0, errors


def validate_form_completeness(request_data, form_type):
    """
    Valida que un formulario esté completo antes de procesarlo
    
    Args:
        request_data (dict): Datos del request
        form_type (str): Tipo de formulario ('rate', 'landedCost', 'tracking', 'epod', 'shipment')
        
    Returns:
        tuple: (is_valid, error_response_or_none)
    """
    required_fields_map = {
        'rate': [
            'origin.postal_code', 'origin.city', 'origin.country',
            'destination.postal_code', 'destination.city', 'destination.country',
            'weight', 'dimensions.length', 'dimensions.width', 'dimensions.height'
        ],
        'landedCost': [
            'origin.postal_code', 'origin.city', 'origin.country',
            'destination.postal_code', 'destination.city', 'destination.country',
            'weight', 'dimensions.length', 'dimensions.width', 'dimensions.height',
            'currency_code', 'items'
        ],
        'tracking': ['tracking_number'],
        'epod': ['shipment_id'],
        'shipment': [
            'shipper.city', 'shipper.country',
            'recipient.city', 'recipient.country',
            'package.weight', 'package.length', 'package.width', 'package.height',
            'shipper.name', 'shipper.email', 'shipper.phone',
            'recipient.name', 'recipient.email', 'recipient.phone'
        ]
    }
    
    required_fields = required_fields_map.get(form_type, [])
    is_valid, errors = validate_required_fields(request_data, required_fields)
    
    # Validaciones específicas adicionales
    if form_type == 'landedCost':
        items = request_data.get('items', [])
        if not items:
            is_valid = False
            errors.append("Se requiere al menos un producto para calcular landed cost")
        else:
            for idx, item in enumerate(items):
                item_required = ['name', 'description', 'manufacturer_country', 'quantity', 'unit_price', 'customs_value', 'commodity_code']
                for field in item_required:
                    if not item.get(field):
                        is_valid = False
                        errors.append(f"Producto {idx + 1}: Campo '{field}' es requerido")
    
    if not is_valid:
        return False, Response({
            'success': False,
            'message': 'Formulario incompleto',
            'errors': errors,
            'missing_count': len(errors),
            'form_validation': {
                'is_valid': False,
                'errors': errors,
                'summary': f"❌ Faltan {len(errors)} campo(s) requerido(s)",
                'action_required': 'Complete todos los campos obligatorios antes de continuar'
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return True, None


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Endpoint para autenticación de usuarios.
    
    Autentica un usuario usando username y password, y retorna tokens JWT
    para acceso a los endpoints protegidos.
    
    **Método HTTP:** POST
    **Permisos:** Público (AllowAny)
    
    **Parámetros de entrada:**
    - username (str): Nombre de usuario
    - password (str): Contraseña del usuario
    
    **Respuesta exitosa (200):**
    {
        "success": true,
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "user": {
            "id": 1,
            "username": "usuario",
            "email": "usuario@ejemplo.com"
        }
    }
    
    **Respuesta de error (401):**
    {
        "success": false,
        "message": "Credenciales inválidas"
    }
    
    **Respuesta de error (400):**
    {
        "success": false,
        "message": "Ha ocurrido un error"
    }
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            
            # Registrar actividad de login exitoso
            UserActivity.log_activity(
                user=user,
                action='login',
                description=f'Usuario {username} inició sesión correctamente',
                status='success',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            return Response({
                'success': True,
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
        else:
            # Registrar intento de login fallido (si el usuario existe)
            try:
                from django.contrib.auth.models import User
                failed_user = User.objects.get(username=username)
                UserActivity.log_activity(
                    user=failed_user,
                    action='login',
                    description=f'Intento de login fallido para usuario {username}',
                    status='error',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )
            except User.DoesNotExist:
                pass  # Usuario no existe, no registramos la actividad
            
            return Response({
                'success': False,
                'message': 'Credenciales inválidas'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response({
        'success': False,
        'message': 'Ha ocurrido un error'
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_view(request):
    """
    Endpoint para obtener cotizaciones de tarifas de envío DHL.
    
    Este endpoint permite obtener cotizaciones de precios para envíos utilizando
    las credenciales DHL configuradas. Valida los datos de entrada, consulta
    la API de DHL, y guarda las cotizaciones exitosas en la base de datos.
    
    **Método HTTP:** POST
    **Permisos:** Usuario autenticado (IsAuthenticated)
    
    **Parámetros de entrada (JSON):**
    - origin (dict): Información del origen
        - postal_code (str): Código postal
        - city (str): Ciudad
        - country (str): País (código ISO)
        - state (str, opcional): Estado/provincia
    - destination (dict): Información del destino
        - postal_code (str): Código postal
        - city (str): Ciudad
        - country (str): País (código ISO)
        - state (str, opcional): Estado/provincia
    - weight (float): Peso del paquete en kg
    - dimensions (dict): Dimensiones del paquete
        - length (float): Largo en cm
        - width (float): Ancho en cm
        - height (float): Alto en cm
    
    **Respuesta exitosa (200):**
    {
        "success": true,
        "rates": [
            {
                "service_name": "EXPRESS WORLDWIDE",
                "service_code": "N",
                "total_charge": 125.50,
                "currency": "USD",
                "delivery_time": "1-2 Business Days"
            }
        ],
        "request_timestamp": "2025-07-07T10:30:00",
        "requested_by": "username"
    }
    
    **Respuesta de error (400/500):**
    {
        "success": false,
        "message": "Ha ocurrido un error",
        "error_type": "validation_error|internal_error",
        "request_timestamp": "2025-07-07T10:30:00"
    }
    
    **Notas:**
    - Las cotizaciones exitosas se guardan automáticamente en la base de datos
    - Se registra cada solicitud en los logs para auditoría
    - Los errores se manejan de forma consistente con metadatos
    """
    serializer = RateRequestSerializer(data=request.data)

    # Helper para sanear payloads de ubicación
    def _sanitize_loc_payload(d):
        try:
            d = dict(d or {})
        except Exception:
            return d
        d.pop('service_area_name', None)
        d.pop('serviceAreaName', None)
        if d.get('service_area') and d.get('city') and d['service_area'] == d['city']:
            d.pop('service_area', None)
        if d.get('serviceArea') and d.get('city') and d['serviceArea'] == d['city']:
            d.pop('serviceArea', None)
        return d
    
    # ✅ Validar completitud del formulario ANTES del serializer
    is_complete, validation_error = validate_form_completeness(request.data, 'rate')
    if not is_complete:
        return validation_error
    
    # Agregar logging para debugging
    logger.info(f"=== RATE REQUEST DEBUG ===")
    try:
        _raw_sanitized = {
            **(request.data if isinstance(request.data, dict) else {}),
            'origin': _sanitize_loc_payload((request.data or {}).get('origin', {})),
            'destination': _sanitize_loc_payload((request.data or {}).get('destination', {})),
        }
    except Exception:
        _raw_sanitized = request.data
    logger.info(f"Raw request data: {_raw_sanitized}")
    logger.info(f"Serializer valid: {serializer.is_valid()}")
    if not serializer.is_valid():
        logger.error(f"Serializer errors: {serializer.errors}")
    
    if serializer.is_valid():
        try:
            # Instanciar servicio real de DHL
            dhl_service = DHLService(
                username=settings.DHL_USERNAME,
                password=settings.DHL_PASSWORD,
                base_url=settings.DHL_BASE_URL,
                environment=settings.DHL_ENVIRONMENT
            )
            # Obtener tipo de servicio (P=NON_DOCUMENTS, D=DOCUMENTS)
            service = serializer.validated_data.get('service', 'P')
            # Llamar a get_rate con el tipo de contenido dinámico
            # Obtener número de cuenta si se proporcionó en el request
            account_number = serializer.validated_data.get('account_number') or None
            
            # Logging para debugging
            # Sanear payloads validados y usar estos en logs y llamada al servicio
            _origin = _sanitize_loc_payload(serializer.validated_data['origin'])
            _destination = _sanitize_loc_payload(serializer.validated_data['destination'])

            logger.info(f"=== CALLING DHL SERVICE ===")
            logger.info(f"Origin: {_origin}")
            logger.info(f"Destination: {_destination}")
            logger.info(f"Weight: {serializer.validated_data['weight']}")
            logger.info(f"Dimensions: {serializer.validated_data['dimensions']}")
            logger.info(f"Account number: {account_number}")
            logger.info(f"Service: {service}")
            
            # Llamar API DHL
            result = dhl_service.get_rate(
                origin=_origin,
                destination=_destination,
                weight=serializer.validated_data['weight'],
                dimensions=serializer.validated_data['dimensions'],
                declared_weight=serializer.validated_data.get('declared_weight'),
                content_type=service,
                account_number=account_number
            )

            # Agregar metadatos adicionales
            result['request_timestamp'] = datetime.now().isoformat()
            result['requested_by'] = request.user.username
            
            # Guardar cotización en la base de datos si es exitosa
            if result.get('success') and result.get('rates'):
                for rate in result['rates']:
                    try:
                        RateQuote.objects.create(
                            origin_postal_code=serializer.validated_data['origin'].get('postal_code', ''),
                            origin_city=serializer.validated_data['origin'].get('city', ''),
                            origin_country=serializer.validated_data['origin'].get('country', ''),
                            origin_state=serializer.validated_data['origin'].get('state', ''),
                            destination_postal_code=serializer.validated_data['destination'].get('postal_code', ''),
                            destination_city=serializer.validated_data['destination'].get('city', ''),
                            destination_country=serializer.validated_data['destination'].get('country', ''),
                            destination_state=serializer.validated_data['destination'].get('state', ''),
                            weight=serializer.validated_data['weight'],
                            length=serializer.validated_data['dimensions'].get('length', 0),
                            width=serializer.validated_data['dimensions'].get('width', 0),
                            height=serializer.validated_data['dimensions'].get('height', 0),
                            service_name=rate.get('service_name', 'Unknown'),
                            service_code=rate.get('service_code', 'Unknown'),
                            total_price=rate.get('total_charge', 0),
                            currency=rate.get('currency', 'USD'),
                            delivery_time=rate.get('delivery_time', 'Unknown'),
                            created_by=request.user
                        )
                    except Exception as db_error:
                        logger.warning(f"Error saving rate quote to DB: {str(db_error)}")
            
            # Log del resultado para debugging
            logger.info(f"Rate request by {request.user.username}: {result.get('success', False)}, rates found: {len(result.get('rates', []))}")
            
            # Registrar actividad de cotización
            if result.get('success'):
                UserActivity.log_activity(
                    user=request.user,
                    action='get_rate',
                    description=f'Obtuvo cotización exitosa: {len(result.get("rates", []))} tarifas encontradas',
                    status='success',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    resource_type='rate_quote',
                    metadata={
                        'origin_country': serializer.validated_data['origin'].get('country'),
                        'destination_country': serializer.validated_data['destination'].get('country'),
                        'weight': str(serializer.validated_data['weight']),
                        'rates_count': len(result.get('rates', [])),
                        'service_type': serializer.validated_data.get('service', 'P'),
                        # Captura de payloads para historial
                        'request_payload': {
                            'origin': _origin,
                            'destination': _destination,
                            'weight': serializer.validated_data['weight'],
                            'dimensions': serializer.validated_data['dimensions'],
                            'declared_weight': serializer.validated_data.get('declared_weight'),
                            'account_number': account_number,
                            'content_type': service
                        },
                        'response_payload': {
                            'http_status': 200,
                            'success': result.get('success', False),
                            'total_rates': result.get('total_rates', len(result.get('rates', []))),
                            'message': result.get('message', ''),
                            'weight_breakdown': result.get('weight_breakdown', {}),
                            # Evitar almacenar todo raw_data pesado si no es necesario
                        }
                    }
                )
            else:
                UserActivity.log_activity(
                    user=request.user,
                    action='get_rate',
                    description=f'Error en cotización: {result.get("message", "Error desconocido")}',
                    status='error',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    metadata={
                        'error_message': result.get('message'),
                        'error_code': result.get('error_code'),
                        'http_status': result.get('http_status'),
                        'raw_response_preview': result.get('raw_response'),
                        'origin_country': serializer.validated_data['origin'].get('country'),
                        'destination_country': serializer.validated_data['destination'].get('country'),
                        # Captura de payloads para historial
                        'request_payload': {
                            'origin': serializer.validated_data['origin'],
                            'destination': serializer.validated_data['destination'],
                            'weight': serializer.validated_data['weight'],
                            'dimensions': serializer.validated_data['dimensions'],
                            'declared_weight': serializer.validated_data.get('declared_weight'),
                            'account_number': account_number,
                            'content_type': service
                        },
                        'response_payload': {
                            'success': result.get('success', False),
                            'message': result.get('message', ''),
                            'error_code': result.get('error_code'),
                            'http_status': result.get('http_status'),
                            'raw_response_preview': result.get('raw_response')
                        }
                    }
                )
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error en rate_view: {str(e)}")
            
            # Registrar actividad de error
            UserActivity.log_activity(
                user=request.user,
                action='get_rate',
                description=f'Error interno en cotización: {str(e)}',
                status='error',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                metadata={'error': str(e)}
            )
            
            return Response({
                'success': False,
                'message': 'Ha ocurrido un error',
                'error_type': 'internal_error',
                'request_timestamp': datetime.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'message': 'Ha ocurrido un error',
        'error_type': 'validation_error',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_compare_view(request):
    """
    Endpoint para comparar tarifas entre DOCUMENTS y NON_DOCUMENTS.
    
    Permite a los usuarios entender las diferencias de precio y restricciones
    entre enviar algo como documento vs como paquete.
    
    **Método HTTP:** POST
    **Permisos:** Usuario autenticado (IsAuthenticated)
    
    **Parámetros de entrada (JSON):** (Mismos que rate_view)
    - origin (dict): Información del origen
    - destination (dict): Información del destino  
    - weight (float): Peso del paquete en kg
    - dimensions (dict): Dimensiones del paquete
    
    **Respuesta exitosa (200):**
    {
        "success": true,
        "comparison_type": "DOCUMENTS vs NON_DOCUMENTS",
        "packages_rates": [...],
        "documents_rates": [...],
        "summary": {
            "packages_count": 3,
            "documents_count": 2,
            "cheapest_option": {...},
            "price_differences": [...]
        },
        "recommendations": [...],
        "important_differences": [...],
        "customs_info": {...}
    }
    """
    serializer = RateRequestSerializer(data=request.data)
    
    logger.info(f"=== RATE COMPARE REQUEST ===")
    logger.info(f"User: {request.user.username}")
    logger.info(f"Request data: {request.data}")
    
    if serializer.is_valid():
        try:
            # Instanciar servicio DHL
            dhl_service = DHLService(
                username=settings.DHL_USERNAME,
                password=settings.DHL_PASSWORD,
                base_url=settings.DHL_BASE_URL,
                environment=settings.DHL_ENVIRONMENT
            )
            
            # Obtener número de cuenta
            account_number = serializer.validated_data.get('account_number') or None
            
            logger.info(f"=== CALLING DHL COMPARISON SERVICE ===")
            logger.info(f"Account number: {account_number}")
            
            # Llamar al servicio de comparación
            result = dhl_service.compare_content_types(
                origin=serializer.validated_data['origin'],
                destination=serializer.validated_data['destination'],
                weight=serializer.validated_data['weight'],
                dimensions=serializer.validated_data['dimensions'],
                declared_weight=serializer.validated_data.get('declared_weight'),
                account_number=account_number
            )
            
            # Agregar metadatos
            result['request_timestamp'] = datetime.now().isoformat()
            result['requested_by'] = request.user.username
            
            logger.info(f"Comparison request by {request.user.username}: {result.get('success', False)}")
            
            if result.get('success'):
                pkg_count = len(result.get('packages_rates', {}).get('rates', []))
                doc_count = len(result.get('documents_rates', {}).get('rates', []))
                logger.info(f"Comparison successful: {pkg_count} package rates, {doc_count} document rates")
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error en rate_compare_view: {str(e)}")
            return Response({
                'success': False,
                'message': 'Ha ocurrido un error',
                'error_type': 'internal_error',
                'request_timestamp': datetime.now().isoformat(),
                'requested_by': request.user.username
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'message': 'Ha ocurrido un error',
        'error_type': 'validation_error',
        'errors': serializer.errors,
        'request_timestamp': datetime.now().isoformat(),
        'requested_by': request.user.username
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_landed_cost_view(request):
    """
    Endpoint de validación previa para datos de Landed Cost.
    
    Permite al usuario validar sus datos antes de hacer el cálculo real,
    mostrando errores, advertencias y recomendaciones específicas.
    
    **Método HTTP:** POST
    **Permisos:** Usuario autenticado
    
    **Respuesta:**
    {
        "is_valid": true/false,
        "can_proceed": true/false,
        "summary": "Resumen del estado de validación",
        "errors": {
            "count": 2,
            "items": ["Error 1", "Error 2"],
            "action_required": "Corrija los errores antes de continuar"
        },
        "warnings": {
            "count": 1,
            "items": ["Advertencia 1"],
            "action_required": "Revise las advertencias..."
        },
        "recommendations": {
            "count": 3,
            "items": ["Recomendación 1", "Recomendación 2"],
            "action_required": "Sugerencias para optimizar..."
        }
    }
    """
    try:
        # Validar estructura básica con serializer
        serializer = LandedCostRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            # Convertir errores del serializer a formato amigable
            errors = []
            for field, field_errors in serializer.errors.items():
                for error in field_errors:
                    errors.append(f"❌ {field}: {error}")
            
            return Response({
                'is_valid': False,
                'can_proceed': False,
                'summary': '❌ Errores de formato en los datos',
                'errors': {
                    'count': len(errors),
                    'items': errors,
                    'action_required': 'Corrija el formato de los datos antes de continuar'
                }
            })
        
        # Validación completa con reglas de negocio
        is_valid, errors, warnings, recommendations = LandedCostValidator.validate_request(
            serializer.validated_data
        )
        
        # Formatear respuesta
        response = LandedCostValidator.format_validation_response(
            is_valid, errors, warnings, recommendations
        )
        
        # Agregar metadatos
        response['validation_timestamp'] = datetime.now().isoformat()
        response['validated_by'] = request.user.username
        
        # Log para auditoría
        logger.info(f"Landed cost validation by {request.user.username}: "
                   f"Valid={is_valid}, Errors={len(errors)}, Warnings={len(warnings)}")
        
        return Response(response)
        
    except Exception as e:
        logger.error(f"Error en validate_landed_cost_view: {str(e)}")
        return Response({
            'is_valid': False,
            'can_proceed': False,
            'summary': '❌ Error interno en validación',
            'errors': {
                'count': 1,
                'items': ['Error interno del servidor. Contacte soporte técnico.'],
                'action_required': 'Reporte este error al equipo de soporte'
            },
            'validation_timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def landed_cost_view(request):
    """
    Endpoint para calcular el costo total de importación (Landed Cost).
    
    Este endpoint calcula el costo total que pagará el comprador final,
    incluyendo shipping, duties, taxes, fees y otros cargos de importación.
    Ideal para e-commerce internacional donde se necesita transparencia
    en los costos totales.
    
    **Método HTTP:** POST
    **Permisos:** Usuario autenticado (IsAuthenticated)
    
    **Parámetros de entrada (JSON):**
    - origin (dict): Información del origen
    - destination (dict): Información del destino
    - weight (float): Peso del paquete en kg
    - dimensions (dict): Dimensiones del paquete
    - currency_code (str): Código de moneda (ej: "USD", "EUR")
    - is_customs_declarable (bool): Si el envío requiere declaración aduanera
    - is_dtp_requested (bool): Si se solicita DTP (Duties & Taxes Paid)
    - is_insurance_requested (bool): Si se solicita seguro
    - get_cost_breakdown (bool): Si se quiere desglose detallado
    - shipment_purpose (str): "commercial" o "personal"
    - transportation_mode (str): "air", "ocean", "ground"
    - merchant_selected_carrier_name (str): "DHL", "UPS", "FEDEX", etc.
    - items (list): Lista de productos con detalles aduaneros
        - name (str): Nombre del producto
        - description (str): Descripción detallada
        - manufacturer_country (str): País de manufactura
        - quantity (int): Cantidad
        - unit_price (float): Precio unitario
        - customs_value (float): Valor para aduanas
        - commodity_code (str): Código HS/commodity
        - weight (float): Peso del item
    
    **Respuesta exitosa (200):**
    {
        "success": true,
        "landed_cost": {
            "total_cost": 458.75,
            "currency": "USD",
            "shipping_cost": 125.50,
            "duties": 45.00,
            "taxes": 67.25,
            "fees": 25.00,
            "insurance": 15.00,
            "breakdown": [
                {
                    "name": "SPRQN",
                    "description": "DHL Shipping Cost",
                    "amount": 125.50,
                    "currency": "USD"
                },
                {
                    "name": "DUTY",
                    "description": "Import Duties",
                    "amount": 45.00,
                    "currency": "USD"
                }
            ]
        },
        "items_breakdown": [...],
        "warnings": [...],
        "customs_info": {...},
        "request_timestamp": "2025-07-25T10:30:00",
        "requested_by": "username"
    }
    
    **Respuesta de error (400/500):**
    {
        "success": false,
        "message": "Ha ocurrido un error",
        "error_type": "validation_error|internal_error",
        "request_timestamp": "2025-07-25T10:30:00"
    }
    
    **Notas:**
    - Incluye todos los costos: shipping + duties + taxes + fees
    - Requiere información detallada de productos para cálculo aduanero
    - Ideal para mostrar precio final real al comprador
    - Se registra cada solicitud en los logs para auditoría
    """
    serializer = LandedCostRequestSerializer(data=request.data)
    
    # ✅ Validar completitud del formulario ANTES del serializer
    is_complete, validation_error = validate_form_completeness(request.data, 'landedCost')
    if not is_complete:
        return validation_error
    
    logger.info(f"=== LANDED COST REQUEST ===")
    logger.info(f"User: {request.user.username}")
    def _sanitize_loc_payload(d):
        try:
            d = dict(d or {})
        except Exception:
            return d
        d.pop('service_area_name', None)
        d.pop('serviceAreaName', None)
        if d.get('service_area') and d.get('city') and d['service_area'] == d['city']:
            d.pop('service_area', None)
        if d.get('serviceArea') and d.get('city') and d['serviceArea'] == d['city']:
            d.pop('serviceArea', None)
        return d
    try:
        _raw_sanitized = {
            **(request.data if isinstance(request.data, dict) else {}),
            'origin': _sanitize_loc_payload((request.data or {}).get('origin', {})),
            'destination': _sanitize_loc_payload((request.data or {}).get('destination', {})),
        }
    except Exception:
        _raw_sanitized = request.data
    logger.info(f"Request data: {_raw_sanitized}")
    
    if serializer.is_valid():
        try:
            # VALIDACIÓN PREVIA OBLIGATORIA
            logger.info(f"=== VALIDATING REQUEST DATA ===")
            is_valid, errors, warnings, recommendations = LandedCostValidator.validate_request(
                serializer.validated_data
            )
            
            if not is_valid:
                logger.warning(f"Landed cost validation failed for {request.user.username}: {errors}")
                validation_response = LandedCostValidator.format_validation_response(
                    is_valid, errors, warnings, recommendations
                )
                validation_response['success'] = False
                validation_response['message'] = 'Ha ocurrido un error'
                validation_response['error_type'] = 'validation_error'
                validation_response['request_timestamp'] = datetime.now().isoformat()
                validation_response['requested_by'] = request.user.username
                
                return Response(validation_response, status=status.HTTP_400_BAD_REQUEST)
            
            # Log warnings and recommendations
            if warnings:
                logger.info(f"Landed cost warnings for {request.user.username}: {warnings}")
            if recommendations:
                logger.info(f"Landed cost recommendations for {request.user.username}: {recommendations}")
            
            # Instanciar servicio DHL
            dhl_service = DHLService(
                username=settings.DHL_USERNAME,
                password=settings.DHL_PASSWORD,
                base_url=settings.DHL_BASE_URL,
                environment=settings.DHL_ENVIRONMENT
            )
            
            # ✅ VALIDACIÓN OBLIGATORIA: account_number
            account_number = serializer.validated_data.get('account_number')
            if not account_number:
                logger.error(f"Account number missing for {request.user.username}")
                return Response({
                    'success': False,
                    'message': 'Número de cuenta DHL es obligatorio para calcular landed cost',
                    'error_type': 'validation_error',
                    'request_timestamp': datetime.now().isoformat(),
                    'requested_by': request.user.username
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"=== CALLING DHL LANDED COST SERVICE ===")
            logger.info(f"Account number: {account_number}")
            logger.info(f"Currency: {serializer.validated_data.get('currency_code', 'USD')}")
            logger.info(f"Items count: {len(serializer.validated_data.get('items', []))}")
            
            # ✅ Llamar al servicio simplificado
            _origin = _sanitize_loc_payload(serializer.validated_data['origin'])
            _destination = _sanitize_loc_payload(serializer.validated_data['destination'])
            result = dhl_service.get_landed_cost(
                origin=_origin,
                destination=_destination,
                weight=serializer.validated_data['weight'],
                dimensions=serializer.validated_data['dimensions'],
                currency_code=serializer.validated_data.get('currency_code', 'USD'),
                is_customs_declarable=serializer.validated_data.get('is_customs_declarable', True),
                get_cost_breakdown=serializer.validated_data.get('get_cost_breakdown', True),
                items=serializer.validated_data['items'],
                account_number=account_number,
                service=serializer.validated_data.get('service', 'P')
            )
            
            # Agregar metadatos
            result['request_timestamp'] = datetime.now().isoformat()
            result['requested_by'] = request.user.username
            
            logger.info(f"Landed cost request by {request.user.username}: {result.get('success', False)}")
            
            if result.get('success'):
                total_cost = result.get('landed_cost', {}).get('total_cost', 0)
                logger.info(f"Landed cost calculation successful: Total ${total_cost}")
                
                # Guardar landed cost en la base de datos
                try:
                    landed_cost_data = result.get('landed_cost', {})
                    LandedCostQuote.objects.create(
                        created_by=request.user,
                        origin_postal_code=serializer.validated_data['origin'].get('postal_code', ''),
                        origin_city=serializer.validated_data['origin'].get('city', ''),
                        origin_country=serializer.validated_data['origin'].get('country', ''),
                        destination_postal_code=serializer.validated_data['destination'].get('postal_code', ''),
                        destination_city=serializer.validated_data['destination'].get('city', ''),
                        destination_country=serializer.validated_data['destination'].get('country', ''),
                        weight=serializer.validated_data['weight'],
                        length=serializer.validated_data['dimensions'].get('length', 0),
                        width=serializer.validated_data['dimensions'].get('width', 0),
                        height=serializer.validated_data['dimensions'].get('height', 0),
                        currency_code=serializer.validated_data.get('currency_code', 'USD'),
                        shipment_purpose=serializer.validated_data.get('shipment_purpose', 'personal'),
                        transportation_mode=serializer.validated_data.get('transportation_mode', 'air'),
                        is_customs_declarable=serializer.validated_data.get('is_customs_declarable', True),
                        is_dtp_requested=serializer.validated_data.get('is_dtp_requested', False),
                        is_insurance_requested=serializer.validated_data.get('is_insurance_requested', False),
                        total_cost=landed_cost_data.get('total_cost', 0),
                        shipping_cost=landed_cost_data.get('shipping_cost', 0),
                        duties_cost=landed_cost_data.get('duties', 0),
                        taxes_cost=landed_cost_data.get('taxes', 0),
                        fees_cost=landed_cost_data.get('fees', 0),
                        insurance_cost=landed_cost_data.get('insurance', 0),
                        items_count=len(serializer.validated_data.get('items', [])),
                        total_declared_value=sum([item.get('customs_value', 0) for item in serializer.validated_data.get('items', [])]),
                        warnings_count=len(result.get('warnings', [])),
                        full_response=result
                    )
                    logger.info(f"Landed cost quote saved to database for user {request.user.username}")
                except Exception as db_error:
                    logger.warning(f"Error saving landed cost quote to DB: {str(db_error)}")
                    # No fallar la request si hay error en DB, pero informar
                    result['db_warning'] = 'Landed cost calculated but not saved to database'
            
            # Registrar actividad con payloads
            try:
                UserActivity.log_activity(
                    user=request.user,
                    action='landed_cost_quote',
                    description='Landed cost calculado' if result.get('success') else f"Error Landed Cost: {result.get('message', '')}",
                    status='success' if result.get('success') else 'error',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    resource_type='landed_cost',
                    metadata={
                        'request_payload': {
                            **serializer.validated_data,
                            'origin': _origin,
                            'destination': _destination,
                        },
                        'response_payload': {
                            'success': result.get('success'),
                            'message': result.get('message'),
                            'error_code': result.get('error_code'),
                            'http_status': result.get('http_status'),
                            'raw_response_preview': result.get('raw_response'),
                            'totals': result.get('landed_cost', {})
                        }
                    }
                )
            except Exception as _e:
                logger.debug(f"Activity log for landed_cost_view skipped: {_e}")

            return Response(result)
            
        except Exception as e:
            logger.error(f"Error en landed_cost_view: {str(e)}")
            return Response({
                'success': False,
                'message': 'Ha ocurrido un error',
                'error_type': 'internal_error',
                'request_timestamp': datetime.now().isoformat(),
                'requested_by': request.user.username
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'message': 'Ha ocurrido un error',
        'error_type': 'validation_error',
        'errors': serializer.errors,
        'request_timestamp': datetime.now().isoformat(),
        'requested_by': request.user.username
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def tracking_view(request):
    """
    Endpoint para rastrear envíos DHL usando el número de tracking.
    """
    try:
        # ✅ Validar completitud del formulario
        is_complete, validation_error = validate_form_completeness(request.data, 'tracking')
        if not is_complete:
            return validation_error
            
        tracking_number = request.data.get('tracking_number')
        username = request.user.username if request.user.is_authenticated else 'anonymous'
        logger.info(f"Tracking request received for {tracking_number} by {username}")
        
        
        if not tracking_number:
            logger.warning("No tracking number provided")
            return Response({
                'success': False,
                'message': 'Número de tracking requerido',
                'request_timestamp': datetime.now(),
                'requested_by': username
            }, status=status.HTTP_400_BAD_REQUEST)
        
        
        try:
            dhl_account = None
            if request.user.is_authenticated:
                dhl_account = DHLAccount.objects.filter(created_by=request.user).first()
                if not dhl_account:
                    logger.info(f"No DHL account found for user {request.user.username}, creating default account")
                    
                    
                    dhl_account = DHLAccount.objects.create(
                        account_number="706065602",
                        account_name="Cuenta DHL por defecto",
                        is_active=True,
                        is_default=True,
                        created_by=request.user,
                        validation_status='pending'
                    )
                    logger.info(f"Default DHL account created for user {request.user.username}")
            else:
                logger.info("Using default DHL configuration for anonymous user")
                
        except Exception as e:
            logger.error(f"Error creating default DHL account: {str(e)}")
            return Response({
                'success': False,
                'message': 'Ha ocurrido un error',
                'error_code': 'DB_ERROR',
                'request_timestamp': datetime.now(),
                'requested_by': username
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if dhl_account:
            logger.info(f"Using DHL account: {dhl_account.account_name} ({dhl_account.account_number})")
        else:
            logger.info("Using default DHL configuration from settings")
        
        # Usar el servicio DHL que ya tiene el parsing correcto
        logger.info(f"Using DHL service for tracking number {tracking_number}")
        
        try:
            dhl_service = DHLService(
                username=settings.DHL_USERNAME,
                password=settings.DHL_PASSWORD,
                base_url=settings.DHL_BASE_URL,
                environment=settings.DHL_ENVIRONMENT
            )
            
            # Usar el servicio que ya tiene el parsing correcto para repesaje
            tracking_info = dhl_service.get_tracking(tracking_number)
            
            logger.info(f"DHL service response: {tracking_info}")
            
        except Exception as e:
            logger.error(f"Error with DHL service: {str(e)}")
            return Response({
                'success': False,
                'message': 'Ha ocurrido un error',
                'error_type': 'dhl_service_error',
                'request_timestamp': datetime.now().isoformat(),
                'tracking_number': tracking_number,
                'requested_by': request.user.username if request.user.is_authenticated else 'anonymous'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        response_data = {
            'success': tracking_info.get('success', False),
            'tracking_info': tracking_info.get('shipment_info', {}),  # Usar shipment_info que es donde está la data
            'events': tracking_info.get('events', []),
            'piece_details': tracking_info.get('piece_details', []),
            'total_events': tracking_info.get('total_events', 0),
            'total_pieces': tracking_info.get('total_pieces', 0),
            'message': tracking_info.get('message', ''),
            'request_timestamp': datetime.now(),
            'tracking_number': tracking_number,
            'requested_by': request.user.username if request.user.is_authenticated else 'anonymous'
        }
        
        if not tracking_info.get('success'):
            logger.warning(f"Tracking failed for {tracking_number}: {tracking_info.get('message')}")
            response_data.update({
                'error_code': tracking_info.get('error_code', 'TRACKING_ERROR'),
                'suggestion': tracking_info.get('suggestion', 'Reintentar más tarde'),
                'raw_response': tracking_info.get('raw_response', '')
            })
            # Registrar actividad con payloads (error)
            try:
                if request.user.is_authenticated:
                    UserActivity.log_activity(
                        user=request.user,
                        action='track_shipment',
                        description=f"Error tracking {tracking_number}: {tracking_info.get('message', '')}",
                        status='error',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT'),
                        resource_type='tracking',
                        resource_id=str(tracking_number),
                        metadata={
                            'request_payload': {'tracking_number': tracking_number},
                            'response_payload': {
                                'success': False,
                                'message': tracking_info.get('message'),
                                'error_code': tracking_info.get('error_code'),
                                'raw_response_preview': tracking_info.get('raw_response')
                            }
                        }
                    )
            except Exception as _e:
                logger.debug(f"Activity log for tracking error skipped: {_e}")
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.info(f"Tracking successful for {tracking_number}")
        # Registrar actividad con payloads (success)
        try:
            if request.user.is_authenticated:
                UserActivity.log_activity(
                    user=request.user,
                    action='track_shipment',
                    description=f'Tracking consultado - {tracking_number}',
                    status='success',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    resource_type='tracking',
                    resource_id=str(tracking_number),
                    metadata={
                        'request_payload': {'tracking_number': tracking_number},
                        'response_payload': {
                            'success': True,
                            'message': tracking_info.get('message'),
                            'events': tracking_info.get('total_events', 0),
                            'pieces': tracking_info.get('total_pieces', 0)
                        }
                    }
                )
        except Exception as _e:
            logger.debug(f"Activity log for tracking success skipped: {_e}")
        return Response(response_data)
        
    except Exception as e:
        logger.exception(f"Error in tracking_view: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error_code': 'SERVER_ERROR',
            'suggestion': 'Reintentar más tarde',
            'request_timestamp': datetime.now(),
            'tracking_number': tracking_number if 'tracking_number' in locals() else None,
            'requested_by': request.user.username
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def epod_view(request):
    """
    Endpoint para obtener Electronic Proof of Delivery (ePOD) de envíos DHL.
    
    Este endpoint permite obtener documentos ePOD de envíos DHL que incluyen
    información detallada sobre la entrega, firmante, fecha y hora de entrega,
    y otros detalles relevantes del proceso de entrega.
    
    **Método HTTP:** POST
    **Permisos:** Usuario autenticado (IsAuthenticated)
    
    **Parámetros de entrada (JSON):**
    - shipment_id (str): Número de tracking DHL
    - account_number (str, opcional): Número de cuenta DHL
    - content_type (str, opcional): Tipo de contenido ePOD (epod-summary por defecto)
    
    **Respuesta exitosa (200):**
    {
        "success": true,
        "status": "found|not_found|processing_error",
        "message": "Mensaje descriptivo del resultado",
        "epod_data": {
            "pdf_data": "base64-encoded-pdf...",
            "format": "PDF",
            "type_code": "POD",
            "size_mb": 0.5,
            "total_documents": 1
        },
        "processing_info": {
            "search_performed": true,
            "documents_found": 1,
            "valid_documents": 1,
            "invalid_documents": 0,
            "largest_document_mb": 0.5
        },
        "request_info": {
            "shipment_id": "1234567890",
            "content_type": "epod-summary", 
            "account_number": "123456789",
            "timestamp": "2025-07-26T12:00:00",
            "requested_by": "username"
        }
    }
    
    **Respuesta de error o sin resultados (200/400/500):**
    {
        "success": false,
        "status": "not_found|error|validation_error",
        "message": "Descripción clara del problema",
        "error_code": "NO_DOCUMENTS|INVALID_CREDENTIALS|etc",
        "suggestion": "Acción recomendada para el usuario",
        "processing_info": {
            "search_performed": true,
            "api_contacted": true,
            "response_received": true,
            "documents_found": 0
        },
        "request_info": {...}
    }
    """
    
    # ✅ Validar completitud del formulario
    is_complete, validation_error = validate_form_completeness(request.data, 'epod')
    if not is_complete:
        return validation_error
    
    # Información de la solicitud
    request_timestamp = datetime.now()
    request_info = {
        "timestamp": request_timestamp.isoformat(),
        "requested_by": request.user.username,
        "user_id": request.user.id
    }
    
    logger.info(f"ePOD request initiated by user {request.user.username} at {request_timestamp}")
    
    serializer = EPODRequestSerializer(data=request.data)
    if not serializer.is_valid():
        logger.warning(f"ePOD validation failed for user {request.user.username}: {serializer.errors}")
        return Response({
            'success': False,
            'status': 'validation_error',
            'message': 'Ha ocurrido un error',
            'error_type': 'validation_error',
            'errors': serializer.errors,
            'processing_info': {
                'search_performed': False,
                'validation_passed': False,
                'api_contacted': False
            },
            'request_info': request_info
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Extraer datos validados
    shipment_id = serializer.validated_data['shipment_id']
    account_number = serializer.validated_data.get('account_number')
    content_type = serializer.validated_data.get('content_type', 'epod-summary')
    
    # Actualizar información de la solicitud
    request_info.update({
        'shipment_id': shipment_id,
        'account_number': account_number or 'default',
        'content_type': content_type
    })
    
    logger.info(f"ePOD search starting for shipment {shipment_id}, content: {content_type}")
    
    try:
        # Inicializar información de procesamiento
        processing_info = {
            'search_performed': False,
            'validation_passed': True,
            'api_contacted': False,
            'response_received': False,
            'documents_found': 0,
            'valid_documents': 0,
            'invalid_documents': 0,
            'api_response_time_ms': 0
        }
        
        # Crear servicio DHL
        dhl_service = DHLService(
            username=settings.DHL_USERNAME,
            password=settings.DHL_PASSWORD,
            base_url=settings.DHL_BASE_URL,
            environment=settings.DHL_ENVIRONMENT
        )
        
        processing_info['search_performed'] = True
        logger.info(f"DHL service initialized for ePOD search")
        
        # Realizar búsqueda de ePOD
        search_start = datetime.now()
        result = dhl_service.get_ePOD(
            shipment_id=shipment_id,
            account_number=account_number,
            content_type=content_type
        )
        search_end = datetime.now()
        
        # Calcular tiempo de respuesta
        response_time_ms = int((search_end - search_start).total_seconds() * 1000)
        processing_info['api_response_time_ms'] = response_time_ms
        processing_info['api_contacted'] = True
        processing_info['response_received'] = True
        
        logger.info(f"ePOD API response received in {response_time_ms}ms")
        
        # Analizar resultado y preparar respuesta para el cliente
        if result.get('success'):
            # ePOD encontrado exitosamente
            processing_info.update({
                'documents_found': result.get('total_documents', 0),
                'valid_documents': result.get('valid_documents', 0),
                'invalid_documents': result.get('invalid_documents', 0),
                'largest_document_mb': result.get('processing_summary', {}).get('largest_document_mb', 0)
            })
            
            client_response = {
                'success': True,
                'status': 'found',
                'message': f'ePOD encontrado exitosamente - {result.get("valid_documents", 1)} documento(s) disponible(s)',
                'epod_data': {
                    'pdf_data': result.get('pdf_data', ''),
                    'format': result.get('format', 'PDF'),
                    'type_code': result.get('type_code', 'POD'),
                    'size_bytes': result.get('size_bytes', 0),
                    'size_mb': result.get('size_mb', 0),
                    'is_pdf': result.get('is_pdf', True),
                    'total_documents': result.get('total_documents', 0),
                    'all_documents': result.get('all_documents', [])
                },
                'processing_info': processing_info,
                'request_info': request_info
            }
            
            logger.info(f"ePOD found successfully for {shipment_id}: {result.get('size_mb', 0)}MB")
            # Registrar actividad ePOD success
            try:
                UserActivity.log_activity(
                    user=request.user,
                    action='epod_request',
                    description=f"ePOD encontrado - {shipment_id}",
                    status='success',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    resource_type='epod',
                    resource_id=str(shipment_id),
                    metadata={
                        'request_payload': {
                            'shipment_id': shipment_id,
                            'account_number': account_number,
                            'content_type': content_type
                        },
                        'response_payload': {
                            'success': True,
                            'message': result.get('message'),
                            'documents_found': result.get('total_documents', 0),
                            'valid_documents': result.get('valid_documents', 0),
                            'size_mb': result.get('size_mb', 0)
                        }
                    }
                )
            except Exception as _e:
                logger.debug(f"Activity log for ePOD success skipped: {_e}")
            return Response(client_response, status=status.HTTP_200_OK)
            
        else:
            # ePOD no encontrado o error
            error_code = result.get('error_code', 'UNKNOWN_ERROR')
            error_message = result.get('message', 'Error desconocido')
            suggestion = result.get('suggestion', 'Contactar soporte técnico')
            
            # Actualizar información de procesamiento
            processing_info.update({
                'documents_found': result.get('total_documents', 0),
                'valid_documents': result.get('valid_documents', 0),
                'invalid_documents': result.get('invalid_documents', 0),
                'error_code': error_code
            })
            
            # Determinar estado según el tipo de error
            if error_code in ['NO_DOCUMENTS', '404']:
                status_code = 'not_found'
                user_message = 'Ha ocurrido un error'
            elif error_code in ['401', 'INVALID_CREDENTIALS']:
                status_code = 'authentication_error'
                user_message = 'Ha ocurrido un error'
            elif error_code in ['TIMEOUT_ERROR', 'CONNECTION_ERROR']:
                status_code = 'connection_error'
                user_message = 'Ha ocurrido un error'
            else:
                status_code = 'processing_error'
                user_message = 'Ha ocurrido un error'
            
            client_response = {
                'success': False,
                'status': status_code,
                'message': user_message,
                'error_code': error_code,
                'suggestion': suggestion,
                'processing_info': processing_info,
                'request_info': request_info,
                'troubleshooting': {
                    'shipment_delivered': 'Verifique que el envío haya sido entregado',
                    'tracking_number': 'Confirme que el número de tracking sea correcto',
                    'account_access': 'Verifique que su cuenta tenga acceso a ePOD',
                    'contact_support': 'Si persiste el problema, contacte soporte'
                }
            }
            
            logger.warning(f"ePOD not found for {shipment_id}: {error_code} - {error_message}")
            
            # Determinar código HTTP según el tipo de error
            if error_code in ['NO_DOCUMENTS', '404']:
                http_status = status.HTTP_200_OK  # No es error del servidor
            elif error_code in ['401', 'INVALID_CREDENTIALS']:
                http_status = status.HTTP_401_UNAUTHORIZED
            elif error_code in ['TIMEOUT_ERROR', 'CONNECTION_ERROR']:
                http_status = status.HTTP_503_SERVICE_UNAVAILABLE
            else:
                http_status = status.HTTP_200_OK  # Error controlado
            # Registrar actividad ePOD error/not found
            try:
                UserActivity.log_activity(
                    user=request.user,
                    action='epod_request',
                    description=f"ePOD no disponible - {shipment_id}: {error_code}",
                    status='error',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    resource_type='epod',
                    resource_id=str(shipment_id),
                    metadata={
                        'request_payload': {
                            'shipment_id': shipment_id,
                            'account_number': account_number,
                            'content_type': content_type
                        },
                        'response_payload': {
                            'success': False,
                            'message': error_message,
                            'error_code': error_code,
                            'http_status': http_status,
                            'suggestion': suggestion
                        }
                    }
                )
            except Exception as _e:
                logger.debug(f"Activity log for ePOD error skipped: {_e}")
            
            return Response(client_response, status=http_status)
            
    except Exception as e:
        # Error interno no controlado
        logger.exception(f"Unexpected error in ePOD view for shipment {shipment_id}: {str(e)}")
        
        processing_info.update({
            'search_performed': True,
            'unexpected_error': True,
            'error_details': str(e)
        })
        
        error_response = {
            'success': False,
            'status': 'internal_error',
            'message': 'Ha ocurrido un error',
            'error_code': 'INTERNAL_ERROR',
            'suggestion': 'Intente nuevamente en unos minutos o contacte soporte si persiste',
            'processing_info': processing_info,
            'request_info': request_info,
            'support_info': {
                'error_id': f"epod-{request_timestamp.strftime('%Y%m%d-%H%M%S')}-{request.user.id}",
                'contact': 'Proporcione este ID al contactar soporte técnico'
            }
        }
        
        # Registrar actividad ePOD unexpected error
        try:
            UserActivity.log_activity(
                user=request.user,
                action='epod_request',
                description=f"Error interno ePOD - {shipment_id}",
                status='error',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                resource_type='epod',
                resource_id=str(shipment_id),
                metadata={
                    'request_payload': {
                        'shipment_id': shipment_id,
                        'account_number': account_number,
                        'content_type': content_type
                    },
                    'response_payload': {
                        'success': False,
                        'message': 'Ha ocurrido un error',
                        'error_code': 'INTERNAL_ERROR'
                    }
                }
            )
        except Exception as _e:
            logger.debug(f"Activity log for ePOD exception skipped: {_e}")
        return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def shipment_view(request):
    """
    Endpoint para crear nuevos envíos DHL.
    
    Este endpoint permite crear nuevos envíos utilizando la API de DHL.
    Valida los datos de entrada, crea el envío en el sistema DHL,
    y guarda la información del envío en la base de datos local.
    
    **Método HTTP:** POST
    **Permisos:** Usuario autenticado (IsAuthenticated)
    
    **Parámetros de entrada (JSON):**
    - shipment_date (str): Fecha de envío en formato YYYY-MM-DD
    - origin (dict): Información del origen
        - name (str): Nombre del remitente
        - company (str): Empresa
        - address (str): Dirección
        - postal_code (str): Código postal
        - city (str): Ciudad
        - country (str): País (código ISO)
        - phone (str): Teléfono
    - destination (dict): Información del destino
        - name (str): Nombre del destinatario
        - company (str): Empresa
        - address (str): Dirección
        - postal_code (str): Código postal
        - city (str): Ciudad
        - country (str): País (código ISO)
        - phone (str): Teléfono
    - packages (list): Lista de paquetes
        - weight (float): Peso en kg
        - dimensions (dict): Dimensiones en cm
            - length (float): Largo
            - width (float): Ancho
            - height (float): Alto
    - service_code (str): Código del servicio DHL
    - payment_info (dict): Información de pago
        - account_number (str): Número de cuenta DHL
    
    **Respuesta exitosa (200):**
    {
        "success": true,
        "shipment_data": {
            "tracking_number": "1234567890",
            "shipment_id": "ABC123456",
            "total_cost": 125.50,
            "currency": "USD",
            "estimated_delivery": "2025-07-10",
            "label_url": "https://example.com/label.pdf"
        },
        "request_timestamp": "2025-07-07T10:30:00",
        "requested_by": "username"
    }
    
    **Respuesta de error (400/500):**
    {
        "success": false,
        "message": "Ha ocurrido un error",
        "error_type": "validation_error|shipment_error|internal_error",
        "request_timestamp": "2025-07-07T10:30:00"
    }
    
    **Notas:**
    - Los envíos exitosos se guardan automáticamente en la base de datos
    - Se registra cada solicitud en los logs para auditoría
    - Los errores se manejan de forma consistente con metadatos
    """
    # ✅ Validar completitud del formulario ANTES del serializer
    is_complete, validation_error = validate_form_completeness(request.data, 'shipment')
    if not is_complete:
        return validation_error
    
    serializer = ShipmentRequestSerializer(data=request.data)
    if serializer.is_valid():
        try:
            dhl_service = DHLService(
                username=settings.DHL_USERNAME,
                password=settings.DHL_PASSWORD,
                base_url=settings.DHL_BASE_URL,
                environment=settings.DHL_ENVIRONMENT
            )
            
            # Transformar los datos para el servicio DHL
            shipment_data = serializer.validated_data.copy()
            # Sanear campos no soportados en shipper/recipient
            def _sanitize_party(p):
                try:
                    p = dict(p or {})
                except Exception:
                    return p
                p.pop('service_area_name', None)
                p.pop('serviceAreaName', None)
                if p.get('service_area') and p.get('city') and p['service_area'] == p['city']:
                    p.pop('service_area', None)
                if p.get('serviceArea') and p.get('city') and p['serviceArea'] == p['city']:
                    p.pop('serviceArea', None)
                return p
            if 'shipper' in shipment_data:
                shipment_data['shipper'] = _sanitize_party(shipment_data['shipper'])
            if 'recipient' in shipment_data:
                shipment_data['recipient'] = _sanitize_party(shipment_data['recipient'])
            
            # Convertir 'package' (singular) a 'packages' (plural) que espera el servicio
            if 'package' in shipment_data:
                shipment_data['packages'] = [shipment_data.pop('package')]
            
            result = dhl_service.create_shipment(
                shipment_data=shipment_data
            )
            
            # Agregar metadatos adicionales
            result['request_timestamp'] = datetime.now().isoformat()
            result['requested_by'] = request.user.username
            
            # Verificar si el resultado del servicio DHL fue exitoso
            if result.get('success'):
                # Guardar envío en la base de datos si es exitoso
                try:
                    shipper = shipment_data['shipper']
                    recipient = shipment_data['recipient']
                    package = shipment_data['packages'][0]  # Tomar el primer paquete
                    
                    shipment = Shipment.objects.create(
                        tracking_number=result.get('tracking_number'),
                        status='created',
                        service_type=shipment_data.get('service', 'P'),
                        payment_type=shipment_data.get('payment', 'S'),
                        shipper_name=shipper.get('name', ''),
                        shipper_company=shipper.get('company', ''),
                        shipper_phone=shipper.get('phone', ''),
                        shipper_email=shipper.get('email', ''),
                        shipper_address=shipper.get('address', ''),
                        shipper_city=shipper.get('city', ''),
                        shipper_state=shipper.get('state', ''),
                        shipper_postal_code=shipper.get('postalCode', ''),
                        shipper_country=shipper.get('country', ''),
                        recipient_name=recipient.get('name', ''),
                        recipient_company=recipient.get('company', ''),
                        recipient_phone=recipient.get('phone', ''),
                        recipient_email=recipient.get('email', ''),
                        recipient_address=recipient.get('address', ''),
                        recipient_city=recipient.get('city', ''),
                        recipient_state=recipient.get('state', ''),
                        recipient_postal_code=recipient.get('postalCode', ''),
                        recipient_country=recipient.get('country', ''),
                        package_weight=package.get('weight', 0),
                        package_length=package.get('length', 0),
                        package_width=package.get('width', 0),
                        package_height=package.get('height', 0),
                        package_description=package.get('description', ''),
                        package_value=package.get('value', 0),
                        package_currency=package.get('currency', 'USD'),
                        estimated_delivery=result.get('estimated_delivery', ''),
                        cost=result.get('cost', ''),
                        created_by=request.user
                    )
                    
                    # Agregar el envío al resultado
                    result['shipment_id'] = shipment.id
                    result['shipment_status'] = 'created'
                    
                    # Log del resultado para debugging
                    logger.info(f"Shipment created successfully by {request.user.username}: {result.get('tracking_number', 'No tracking')}")
                    
                    # Registrar actividad de creación de envío
                    UserActivity.log_activity(
                        user=request.user,
                        action='create_shipment',
                        description=f'Creó envío exitosamente - Tracking: {result.get("tracking_number", "No tracking")}',
                        status='success',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT'),
                        resource_type='shipment',
                        resource_id=str(shipment.id),
                        metadata={
                            'tracking_number': result.get('tracking_number'),
                            'service_type': serializer.validated_data.get('service_type'),
                            'destination_country': serializer.validated_data.get('destination', {}).get('country'),
                            # Captura de payloads
                            'request_payload': {
                                'shipment': shipment_data
                            },
                            'response_payload': {
                                'success': True,
                                'message': result.get('message'),
                                'tracking_number': result.get('tracking_number')
                            }
                        }
                    )
                    
                except Exception as db_error:
                    logger.warning(f"Error saving shipment to DB: {str(db_error)}")
                    # No fallar la request si hay error en DB, pero informar
                    result['db_warning'] = 'Shipment created but not saved to database'
                
                # Retornar respuesta exitosa con HTTP 200
                return Response(result)
            else:
                # El servicio DHL retornó un error
                error_type = result.get('error_type', 'shipment_error')
                
                # Registrar actividad de error
                UserActivity.log_activity(
                    user=request.user,
                    action='create_shipment',
                    description=f'Error en DHL API: {result.get("message", "Error desconocido")}',
                    status='error',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    metadata={
                        'error_type': error_type,
                        'dhl_message': result.get('message'),
                        'request_data': serializer.validated_data,
                        # Captura de payloads
                        'request_payload': {
                            'shipment': shipment_data
                        },
                        'response_payload': {
                            'success': False,
                            'message': result.get('message'),
                            'error_code': result.get('error_code'),
                            'http_status': result.get('http_status'),
                            'raw_response_preview': result.get('raw_response')
                        }
                    }
                )
                
                # Determinar el código de estado HTTP apropiado
                if error_type == 'billing_country_mismatch':
                    status_code = status.HTTP_400_BAD_REQUEST
                elif error_type == 'validation_error':
                    status_code = status.HTTP_400_BAD_REQUEST
                else:
                    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
                
                # Retornar error con código de estado apropiado
                return Response(result, status=status_code)
            
        except Exception as e:
            logger.error(f"Error en shipment_view: {str(e)}")
            
            # Registrar actividad de error
            UserActivity.log_activity(
                user=request.user,
                action='create_shipment',
                description=f'Error al crear envío: {str(e)}',
                status='error',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                metadata={'error': str(e)}
            )
            
            return Response({
                'success': False,
                'message': 'Ha ocurrido un error',
                'error_type': 'internal_error',
                'request_timestamp': datetime.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'message': 'Ha ocurrido un error',
        'error_type': 'validation_error',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def shipments_list_view(request):
    """Endpoint para listar envíos del usuario"""
    try:
        shipments = Shipment.objects.filter(created_by=request.user)
        serializer = ShipmentSerializer(shipments, many=True)
        
        return Response({
            'success': True,
            'shipments': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error en shipments_list_view: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def shipment_detail_view(request, shipment_id):
    """Endpoint para obtener detalles de un envío"""
    try:
        shipment = Shipment.objects.get(id=shipment_id, created_by=request.user)
        serializer = ShipmentSerializer(shipment)
        
        return Response({
            'success': True,
            'shipment': serializer.data
        })
        
    except Shipment.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Envío no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error en shipment_detail_view: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rates_history_view(request):
    """Endpoint para obtener historial de cotizaciones"""
    try:
        rates = RateQuote.objects.filter(created_by=request.user)
        serializer = RateQuoteSerializer(rates, many=True)
        
        return Response({
            'success': True,
            'rates': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error en rates_history_view: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dhl_status_view(request):
    """
    Endpoint para obtener el estado actual de la configuración DHL.
    
    Este endpoint proporciona información sobre la configuración actual
    de DHL, incluyendo credenciales, URLs de endpoints, y estado de
    los servicios disponibles.
    
    **Método HTTP:** GET
    **Permisos:** Usuario autenticado (IsAuthenticated)
    
    **Parámetros de entrada:** Ninguno (GET request)
    
    **Respuesta exitosa (200):**
    {
        "success": true,
        "dhl_status": {
            "configuration": {
                "credentials_configured": true,
                "username": "apO3fS5mJ8zT7h",
                "password": "***masked***",
                "base_url": "https://xmlpi-ea.dhl.com/XMLShippingServlet",
                "environment": "production"
            },
            "endpoints": {
                "rates": "/api/rates/",
                "tracking": "/api/tracking/",
                "epod": "/api/epod/",
                "shipment": "/api/shipment/",
                "dhl_status": "/api/dhl-status/"
            },
            "services_available": [
                "rates",
                "tracking",
                "epod",
                "shipment"
            ],
            "last_check": "2025-07-07T09:00:00"
        },
        "request_timestamp": "2025-07-07T10:30:00",
        "requested_by": "username"
    }
    
    **Respuesta de error (500):**
    {
        "success": false,
        "message": "Ha ocurrido un error",
        "error_type": "internal_error",
        "request_timestamp": "2025-07-07T10:30:00"
    }
    
    **Notas:**
    - La contraseña se muestra enmascarada por seguridad
    - Se registra cada consulta en los logs para auditoría
    - Los errores se manejan de forma consistente con metadatos
    """
    try:
        config_status = {
            'credentials_configured': bool(settings.DHL_USERNAME and settings.DHL_PASSWORD),
            'username': settings.DHL_USERNAME,
            'base_url': settings.DHL_BASE_URL,
            'environment': settings.DHL_ENVIRONMENT,
            'endpoints': {
                'epod': 'https://wsbexpress.dhl.com/gbl/getePOD',
                'rate': 'https://wsbexpress.dhl.com/sndpt/expressRateBook',
                'tracking': 'https://wsbexpress.dhl.com/gbl/glDHLExpressTrack',
                'shipment': 'https://wsbexpress.dhl.com/sndpt/expressRateBook'
            },
            'last_check': datetime.now().isoformat(),
            'checked_by': request.user.username
        }
        
        return Response({
            'success': True,
            'config': config_status,
            'message': 'Configuración DHL obtenida exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error en dhl_status_view: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error_type': 'internal_error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_shipment_date_view(request):
    """
    Endpoint para validar fechas de envío antes de crear el envío.
    
    Este endpoint permite validar si una fecha de envío es válida según
    los requisitos de DHL (no en el pasado, no más de 10 días en el futuro).
    
    **Método HTTP:** POST
    **Permisos:** Usuario autenticado (IsAuthenticated)
    
    **Parámetros de entrada (JSON):**
    - shipment_date (str, opcional): Fecha de envío en formato ISO (YYYY-MM-DDTHH:MM:SS)
    
    **Respuesta exitosa (200):**
    {
        "success": true,
        "validation_result": {
            "requested_date": "2025-07-15T10:00:00",
            "validated_date": "2025-07-15T10:00:00GMT+00:00",
            "is_valid": true,
            "adjustments_made": false,
            "message": "Fecha válida para envío DHL"
        },
        "request_timestamp": "2025-07-07T10:30:00",
        "requested_by": "username"
    }
    
    **Respuesta con ajustes (200):**
    {
        "success": true,
        "validation_result": {
            "requested_date": "2025-06-01T10:00:00",
            "validated_date": "2025-07-08T10:00:00GMT+00:00",
            "is_valid": false,
            "adjustments_made": true,
            "adjustment_reason": "Fecha en el pasado, ajustada a mañana",
            "message": "Fecha ajustada automáticamente"
        },
        "request_timestamp": "2025-07-07T10:30:00",
        "requested_by": "username"
    }
    
    **Respuesta de error (500):**
    {
        "success": false,
        "message": "Ha ocurrido un error",
        "error_type": "internal_error",
        "request_timestamp": "2025-07-07T10:30:00"
    }
    
    **Notas:**
    - Si no se proporciona fecha, se usa mañana por defecto
    - Se registra cada validación en los logs para auditoría
    - Los errores se manejan de forma consistente con metadatos
    """
    try:
        from datetime import datetime, timedelta
        import pytz
        
        # Obtener la fecha solicitada
        requested_date = request.data.get('shipment_date')
        
        # Crear instancia del servicio DHL para usar su método de validación
        dhl_service = DHLService(
            username=settings.DHL_USERNAME,
            password=settings.DHL_PASSWORD,
            base_url=settings.DHL_BASE_URL,
            environment=settings.DHL_ENVIRONMENT
        )
        
        # Validar la fecha
        now = datetime.now(pytz.UTC)
        original_date = requested_date
        
        # Generar fecha válida
        validated_timestamp = dhl_service._get_valid_ship_timestamp(requested_date)
        
        # Determinar si se hicieron ajustes
        adjustments_made = False
        adjustment_reason = None
        
        if requested_date:
            try:
                # Parsear la fecha solicitada para comparar
                if isinstance(requested_date, str):
                    if 'GMT' in requested_date:
                        requested_date = requested_date.replace('GMT+00:00', '+00:00')
                    parsed_requested = datetime.fromisoformat(requested_date.replace('Z', '+00:00'))
                    if parsed_requested.tzinfo is None:
                        parsed_requested = parsed_requested.replace(tzinfo=pytz.UTC)
                    
                    # Comparar con la fecha validada
                    validated_dt = datetime.strptime(validated_timestamp.replace('GMT+00:00', '+00:00'), '%Y-%m-%dT%H:%M:%S%z')
                    
                    if abs((parsed_requested - validated_dt).total_seconds()) > 3600:  # Diferencia mayor a 1 hora
                        adjustments_made = True
                        if parsed_requested <= now:
                            adjustment_reason = "Fecha en el pasado, ajustada a mañana"
                        elif parsed_requested > now + timedelta(days=9):
                            adjustment_reason = "Fecha muy lejana, ajustada a máximo permitido"
                        else:
                            adjustment_reason = "Fecha ajustada por requisitos de DHL"
                            
            except (ValueError, TypeError):
                adjustments_made = True
                adjustment_reason = "Formato de fecha inválido, usando fecha por defecto"
        else:
            adjustments_made = True
            adjustment_reason = "No se proporcionó fecha, usando fecha por defecto"
        
        validation_result = {
            'requested_date': original_date,
            'validated_date': validated_timestamp,
            'is_valid': not adjustments_made,
            'adjustments_made': adjustments_made,
            'message': 'Fecha válida para envío DHL' if not adjustments_made else 'Fecha ajustada automáticamente',
            'dhl_requirements': {
                'min_date': (now + timedelta(hours=1)).isoformat(),
                'max_date': (now + timedelta(days=9)).isoformat(),
                'timezone': 'UTC',
                'format': 'YYYY-MM-DDTHH:MM:SSGMT+00:00'
            }
        }
        
        if adjustments_made:
            validation_result['adjustment_reason'] = adjustment_reason
        
        # Log de la validación
        logger.info(f"Date validation by {request.user.username}: requested={original_date}, validated={validated_timestamp}, adjusted={adjustments_made}")
        
        return Response({
            'success': True,
            'validation_result': validation_result,
            'request_timestamp': datetime.now().isoformat(),
            'requested_by': request.user.username
        })
        
    except Exception as e:
        logger.error(f"Error en validate_shipment_date_view: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error_type': 'internal_error',
            'request_timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dhl_account_list(request):
    """
    Lista todas las cuentas DHL del usuario autenticado
    """
    accounts = DHLAccount.objects.filter(created_by=request.user)
    serializer = DHLAccountSerializer(accounts, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dhl_account_create(request):
    """
    Crea una nueva cuenta DHL y valida su existencia con DHL
    """
    serializer = DHLAccountSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        # Crear la cuenta primero
        account = serializer.save()
        
        try:
            # Intentar validar la cuenta con DHL
            dhl_service = DHLService()
            is_valid = dhl_service.validate_account(account.account_number)
            
            # Actualizar el estado de validación
            account.last_validated = timezone.now()
            account.validation_status = 'valid' if is_valid else 'invalid'
            account.save()
            
            if not is_valid:
                return Response({
                    'success': False,
                    'message': 'La cuenta no es válida en DHL',
                    'account': DHLAccountSerializer(account).data
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'message': 'Cuenta creada y validada correctamente',
                'account': DHLAccountSerializer(account).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            account.validation_status = 'invalid'
            account.save()
            return Response({
                'success': False,
                'message': 'Ha ocurrido un error',
                'account': DHLAccountSerializer(account).data
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def dhl_account_delete(request, account_id):
    """
    Elimina una cuenta DHL
    """
    try:
        account = DHLAccount.objects.get(id=account_id, created_by=request.user)
        account.delete()
        return Response({
            'success': True,
            'message': 'Cuenta eliminada correctamente'
        })
    except DHLAccount.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Cuenta no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dhl_account_set_default(request, account_id):
    """
    Establece una cuenta como predeterminada
    """
    try:
        account = DHLAccount.objects.get(id=account_id, created_by=request.user)
        account.is_default = True
        account.save()  # Esto activará el save() personalizado que desactiva otros defaults
        return Response({
            'success': True,
            'message': 'Cuenta establecida como predeterminada',
            'account': DHLAccountSerializer(account).data
        })
    except DHLAccount.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Cuenta no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def field_info(request):
    """
    Endpoint para obtener información de tooltips y validaciones de campos
    
    **Método HTTP:** GET
    **Permisos:** Público (AllowAny)
    
    **Respuesta exitosa (200):**
    ```json
    {
        "field_info": {
            "origin": {
                "description": "Dirección de origen del envío",
                "example": "{\"country\": \"PA\", \"city\": \"Panama City\", \"postal_code\": \"0816\"}"
            },
            ...
        },
        "limits": {
            "max_name_length": 512,
            "max_description_length": 255,
            ...
        },
        "valid_values": {
            "currencies": ["USD", "EUR", "GBP", ...],
            "service_types": ["P", "D"],
            ...
        }
    }
    ```
    
    **Casos de uso:**
    - Mostrar tooltips en formularios del frontend
    - Validación en tiempo real en el cliente
    - Documentación automática de campos
    """
    try:
        return Response({
            'success': True,
            'field_info': LandedCostValidator.get_all_field_info(),
            'limits': LandedCostValidator.get_field_limits(),
            'valid_values': LandedCostValidator.get_valid_values()
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error obteniendo información de campos: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def field_info_specific(request, field_name):
    """
    Endpoint para obtener información específica de un campo
    
    **Método HTTP:** GET
    **Permisos:** Público (AllowAny)
    **Parámetros URL:** field_name (string) - Nombre del campo
    
    **Respuesta exitosa (200):**
    ```json
    {
        "success": true,
        "field_name": "description",
        "info": {
            "description": "Descripción completa del producto",
            "example": "KNITWEAR 100% COTTON REDUCTION PRICE FALL COLLECTION"
        }
    }
    ```
    
    **Respuesta campo no encontrado (404):**
    ```json
    {
        "success": false,
        "message": "Campo no encontrado"
    }
    ```
    """
    try:
        info = LandedCostValidator.get_field_info(field_name)
        if info:
            return Response({
                'success': True,
                'field_name': field_name,
                'info': info
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Campo no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Error obteniendo información del campo {field_name}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_activities_view(request):
    """
    Endpoint para obtener el historial de actividades de usuarios.
    
    Permite ver las actividades de todos los usuarios (para admins) o solo las del 
    usuario actual. Incluye filtros por usuario, acción, estado, fechas, etc.
    
    **Método HTTP:** GET
    **Permisos:** Usuario autenticado
    
    **Parámetros de consulta:**
    - `user_id` (int, opcional): ID del usuario específico
    - `username` (str, opcional): Nombre de usuario específico
    - `action` (str, opcional): Tipo de acción (login, create_shipment, etc.)
    - `status` (str, opcional): Estado (success, error, warning, info)
    - `date_from` (datetime, opcional): Fecha inicio (YYYY-MM-DD HH:MM:SS)
    - `date_to` (datetime, opcional): Fecha fin (YYYY-MM-DD HH:MM:SS)
    - `resource_type` (str, opcional): Tipo de recurso (shipment, account, etc.)
    - `page` (int, opcional): Número de página (default: 1)
    - `page_size` (int, opcional): Elementos por página (default: 20, max: 100)
    
    **Respuesta exitosa (200):**
    ```json
    {
        "success": true,
        "data": {
            "activities": [
                {
                    "id": 1,
                    "user": {
                        "id": 1,
                        "username": "admin",
                        "email": "admin@example.com"
                    },
                    "action": "login",
                    "action_display": "Inicio de sesión",
                    "status": "success",
                    "status_display": "Exitoso",
                    "description": "Usuario inició sesión correctamente",
                    "ip_address": "192.168.1.100",
                    "resource_type": null,
                    "resource_id": null,
                    "created_at": "2025-08-02T10:30:00Z",
                    "created_at_formatted": "02/08/2025 10:30:00"
                }
            ],
            "pagination": {
                "current_page": 1,
                "total_pages": 5,
                "total_items": 100,
                "page_size": 20,
                "has_next": true,
                "has_previous": false
            },
            "filters": {
                "actions": [
                    {"value": "login", "label": "Inicio de sesión"},
                    {"value": "create_shipment", "label": "Crear envío"}
                ],
                "statuses": [
                    {"value": "success", "label": "Exitoso"},
                    {"value": "error", "label": "Error"}
                ]
            }
        }
    }
    ```
    """
    try:
        # Validar filtros de entrada
        filter_serializer = UserActivityFilterSerializer(data=request.GET)
        if not filter_serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Ha ocurrido un error',
                'errors': filter_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        filters = filter_serializer.validated_data
        
        # Construir queryset base
        queryset = UserActivity.objects.select_related('user').all()
        
        # Aplicar filtros de permisos
        # Si no es superuser, solo puede ver sus propias actividades
        if not request.user.is_superuser:
            queryset = queryset.filter(user=request.user)
        
        # Aplicar filtros adicionales
        if filters.get('user_id'):
            queryset = queryset.filter(user_id=filters['user_id'])
        
        if filters.get('username'):
            queryset = queryset.filter(user__username__icontains=filters['username'])
        
        if filters.get('action'):
            queryset = queryset.filter(action=filters['action'])
        
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        
        if filters.get('date_from'):
            queryset = queryset.filter(created_at__gte=filters['date_from'])
        
        if filters.get('date_to'):
            queryset = queryset.filter(created_at__lte=filters['date_to'])
        
        if filters.get('resource_type'):
            queryset = queryset.filter(resource_type__icontains=filters['resource_type'])
        
        # Paginación
        page = filters.get('page', 1)
        page_size = filters.get('page_size', 20)
        paginator = Paginator(queryset, page_size)
        
        try:
            activities_page = paginator.page(page)
        except:
            activities_page = paginator.page(1)
        
        # Serializar actividades
        serializer = UserActivitySerializer(activities_page.object_list, many=True)
        
        # Preparar opciones para filtros en frontend
        filter_options = {
            'actions': [{'value': choice[0], 'label': choice[1]} for choice in UserActivity.ACTION_CHOICES],
            'statuses': [{'value': choice[0], 'label': choice[1]} for choice in UserActivity.STATUS_CHOICES]
        }
        
        # Registrar esta consulta como actividad
        UserActivity.log_activity(
            user=request.user,
            action='system_action',
            description=f'Consultó historial de actividades (página {page})',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            metadata={'filters': filters}
        )
        
        return Response({
            'success': True,
            'data': {
                'activities': serializer.data,
                'pagination': {
                    'current_page': activities_page.number,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'page_size': page_size,
                    'has_next': activities_page.has_next(),
                    'has_previous': activities_page.has_previous()
                },
                'filters': filter_options
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo actividades de usuario: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_activity_stats_view(request):
    """
    Endpoint para obtener estadísticas de actividades de usuario.
    
    Proporciona métricas y resúmenes sobre las actividades de usuarios,
    útil para dashboards administrativos.
    
    **Método HTTP:** GET
    **Permisos:** Usuario autenticado (superuser para estadísticas globales)
    
    **Parámetros de consulta:**
    - `days` (int, opcional): Número de días atrás para las estadísticas (default: 30)
    - `user_id` (int, opcional): ID de usuario específico (solo superuser)
    
    **Respuesta exitosa (200):**
    ```json
    {
        "success": true,
        "data": {
            "summary": {
                "total_activities": 156,
                "unique_users": 12,
                "success_rate": 98.5,
                "most_common_action": "login",
                "period_days": 30
            },
            "by_action": {
                "login": 45,
                "create_shipment": 23,
                "get_rate": 18
            },
            "by_status": {
                "success": 150,
                "error": 4,
                "warning": 2
            },
            "by_day": [
                {"date": "2025-08-01", "count": 12},
                {"date": "2025-08-02", "count": 8}
            ],
            "top_users": [
                {"username": "admin", "activity_count": 45},
                {"username": "user1", "activity_count": 23}
            ]
        }
    }
    ```
    """
    try:
        days = int(request.GET.get('days', 30))
        user_id = request.GET.get('user_id')
        
        # Validar permisos
        if user_id and not request.user.is_superuser:
            return Response({
                'success': False,
                'message': 'No tienes permisos para ver estadísticas de otros usuarios'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Fecha límite
        from datetime import timedelta
        date_limit = timezone.now() - timedelta(days=days)
        
        # Construir queryset base
        queryset = UserActivity.objects.filter(created_at__gte=date_limit)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        elif not request.user.is_superuser:
            queryset = queryset.filter(user=request.user)
        
        # Estadísticas básicas
        from django.db.models import Count, Q
        from collections import Counter
        
        total_activities = queryset.count()
        unique_users = queryset.values('user').distinct().count()
        success_count = queryset.filter(status='success').count()
        success_rate = (success_count / total_activities * 100) if total_activities > 0 else 0
        
        # Acción más común
        action_counts = queryset.values('action').annotate(count=Count('action')).order_by('-count')
        most_common_action = action_counts.first()['action'] if action_counts else None
        
        # Estadísticas por acción
        by_action = {item['action']: item['count'] for item in action_counts}
        
        # Estadísticas por estado
        status_counts = queryset.values('status').annotate(count=Count('status'))
        by_status = {item['status']: item['count'] for item in status_counts}
        
        # Actividades por día (últimos días)
        from django.db.models.functions import TruncDate
        daily_counts = (queryset
                       .annotate(date=TruncDate('created_at'))
                       .values('date')
                       .annotate(count=Count('id'))
                       .order_by('date'))
        
        by_day = [
            {
                'date': item['date'].strftime('%Y-%m-%d'),
                'count': item['count']
            }
            for item in daily_counts
        ]
        
        # Top usuarios (solo para superuser)
        top_users = []
        if request.user.is_superuser:
            user_counts = (queryset
                          .values('user__username')
                          .annotate(activity_count=Count('id'))
                          .order_by('-activity_count')[:10])
            top_users = [
                {
                    'username': item['user__username'],
                    'activity_count': item['activity_count']
                }
                for item in user_counts
            ]
        
        # Registrar esta consulta
        UserActivity.log_activity(
            user=request.user,
            action='system_action',
            description=f'Consultó estadísticas de actividades ({days} días)',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            metadata={'days': days, 'user_id': user_id}
        )
        
        return Response({
            'success': True,
            'data': {
                'summary': {
                    'total_activities': total_activities,
                    'unique_users': unique_users,
                    'success_rate': round(success_rate, 2),
                    'most_common_action': most_common_action,
                    'period_days': days
                },
                'by_action': by_action,
                'by_status': by_status,
                'by_day': by_day,
                'top_users': top_users
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de actividades: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# ENDPOINTS PARA AGENDA DE CONTACTOS
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def contacts_view(request):
    """
    Gestión de contactos de la agenda.
    
    GET: Lista todos los contactos del usuario con opción de búsqueda
    POST: Crea un nuevo contacto
    """
    if request.method == 'GET':
        try:
            # Obtener parámetros de búsqueda
            search = request.GET.get('search', '').strip()
            favorites_only = request.GET.get('favorites', '').lower() == 'true'
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 20)), 100)
            
            # Construir query base
            queryset = Contact.objects.filter(created_by=request.user)
            
            # Aplicar filtros
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(company__icontains=search) |
                    Q(email__icontains=search) |
                    Q(phone__icontains=search) |
                    Q(city__icontains=search)
                )
            
            if favorites_only:
                queryset = queryset.filter(is_favorite=True)
            
            # Paginación
            paginator = Paginator(queryset, page_size)
            contacts_page = paginator.get_page(page)
            
            # Serializar datos
            serializer = ContactSerializer(contacts_page.object_list, many=True, context={'request': request})
            
            return Response({
                'success': True,
                'data': {
                    'contacts': serializer.data,
                    'pagination': {
                        'current_page': page,
                        'total_pages': paginator.num_pages,
                        'total_count': paginator.count,
                        'has_next': contacts_page.has_next(),
                        'has_previous': contacts_page.has_previous(),
                    }
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error obteniendo contactos: {str(e)}")
            return Response({
                'success': False,
                'message': 'Ha ocurrido un error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            serializer = ContactSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                contact = serializer.save(created_by=request.user)
                
                # Registrar actividad
                UserActivity.create_activity(
                    user=request.user,
                    action='CREATE_CONTACT',
                    description=f'Contacto creado: {contact.name}',
                    resource_type='contact',
                    resource_id=str(contact.id)
                )
                
                return Response({
                    'success': True,
                    'message': 'Contacto creado exitosamente',
                    'data': ContactSerializer(contact, context={'request': request}).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Ha ocurrido un error',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error creando contacto: {str(e)}")
            return Response({
                'success': False,
                'message': 'Ha ocurrido un error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def contact_detail_view(request, contact_id):
    """
    Gestión individual de contactos.
    
    GET: Obtiene detalles de un contacto
    PUT: Actualiza un contacto
    DELETE: Elimina un contacto
    """
    try:
        contact = Contact.objects.get(id=contact_id, created_by=request.user)
    except Contact.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Contacto no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        try:
            serializer = ContactSerializer(contact, context={'request': request})
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error obteniendo contacto {contact_id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Ha ocurrido un error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            serializer = ContactSerializer(contact, data=request.data, context={'request': request})
            if serializer.is_valid():
                updated_contact = serializer.save()
                
                # Registrar actividad
                UserActivity.create_activity(
                    user=request.user,
                    action='UPDATE_CONTACT',
                    description=f'Contacto actualizado: {updated_contact.name}',
                    resource_type='contact',
                    resource_id=str(contact_id)
                )
                
                return Response({
                    'success': True,
                    'message': 'Contacto actualizado exitosamente',
                    'data': ContactSerializer(updated_contact, context={'request': request}).data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Ha ocurrido un error',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error actualizando contacto {contact_id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Ha ocurrido un error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            contact_name = contact.name
            contact.delete()
            
            # Registrar actividad
            UserActivity.create_activity(
                user=request.user,
                action='DELETE_CONTACT',
                description=f'Contacto eliminado: {contact_name}',
                resource_type='contact',
                resource_id=str(contact_id)
            )
            
            return Response({
                'success': True,
                'message': 'Contacto eliminado exitosamente'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error eliminando contacto {contact_id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Ha ocurrido un error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def contact_toggle_favorite_view(request, contact_id):
    """
    Togglea el estado de favorito de un contacto.
    """
    try:
        contact = Contact.objects.get(id=contact_id, created_by=request.user)
        contact.is_favorite = not contact.is_favorite
        contact.save(update_fields=['is_favorite'])
        
        # Registrar actividad
        action = 'ADD_FAVORITE' if contact.is_favorite else 'REMOVE_FAVORITE'
        UserActivity.create_activity(
            user=request.user,
            action=action,
            description=f'Contacto {"agregado a" if contact.is_favorite else "removido de"} favoritos: {contact.name}',
            resource_type='contact',
            resource_id=str(contact_id)
        )
        
        return Response({
            'success': True,
            'message': f'Contacto {"agregado a" if contact.is_favorite else "removido de"} favoritos',
            'data': {
                'is_favorite': contact.is_favorite
            }
        }, status=status.HTTP_200_OK)
        
    except Contact.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Contacto no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error toggleando favorito para contacto {contact_id}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def contact_use_view(request, contact_id):
    """
    Marca un contacto como usado (incrementa usage_count y actualiza last_used).
    """
    try:
        contact = Contact.objects.get(id=contact_id, created_by=request.user)
        contact.increment_usage()
        
        return Response({
            'success': True,
            'message': 'Uso de contacto registrado',
            'data': {
                'usage_count': contact.usage_count,
                'last_used': contact.last_used.isoformat()
            }
        }, status=status.HTTP_200_OK)
        
    except Contact.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Contacto no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error registrando uso de contacto {contact_id}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_contact_from_shipment_view(request):
    """
    Crea contactos automáticamente a partir de datos de envío.
    Recibe datos de remitente y/o destinatario y los guarda como contactos.
    """
    try:
        shipper_data = request.data.get('shipper')
        recipient_data = request.data.get('recipient')
        created_contacts = []
        
        # Crear contacto de remitente si se proporciona
        if shipper_data:
            shipper_contact_data = shipper_data.copy()
            # Verificar si ya existe
            existing_shipper = Contact.objects.filter(
                created_by=request.user,
                email=shipper_data.get('email'),
                name=shipper_data.get('name')
            ).first()
            
            if not existing_shipper:
                shipper_serializer = ContactCreateSerializer(data=shipper_contact_data)
                if shipper_serializer.is_valid():
                    shipper_contact = shipper_serializer.save(created_by=request.user)
                    created_contacts.append({
                        'type': 'shipper',
                        'contact': ContactSerializer(shipper_contact, context={'request': request}).data
                    })
        
        # Crear contacto de destinatario si se proporciona
        if recipient_data:
            recipient_contact_data = recipient_data.copy()
            # Verificar si ya existe
            existing_recipient = Contact.objects.filter(
                created_by=request.user,
                email=recipient_data.get('email'),
                name=recipient_data.get('name')
            ).first()
            
            if not existing_recipient:
                recipient_serializer = ContactCreateSerializer(data=recipient_contact_data)
                if recipient_serializer.is_valid():
                    recipient_contact = recipient_serializer.save(created_by=request.user)
                    created_contacts.append({
                        'type': 'recipient',
                        'contact': ContactSerializer(recipient_contact, context={'request': request}).data
                    })
        
        # Registrar actividad si se crearon contactos
        if created_contacts:
            UserActivity.create_activity(
                user=request.user,
                action='AUTO_CREATE_CONTACTS',
                description=f'Contactos creados automáticamente desde envío: {len(created_contacts)} contactos',
                resource_type='contact'
            )
        
        return Response({
            'success': True,
            'message': f'Se crearon {len(created_contacts)} contactos automáticamente',
            'data': {
                'created_contacts': created_contacts,
                'count': len(created_contacts)
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creando contactos desde envío: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =================================
# VISTAS PARA ZONAS DE SERVICIO (ESD)
# =================================

@api_view(['GET'])
@permission_classes([AllowAny])
@cache_page(60 * 15)  # Cache por 15 minutos
def get_countries(request):
    """
    Obtiene lista de países disponibles para envío DHL.
    
    Returns:
        - Lista de países con código y nombre
    """
    try:
        from .models import ServiceZone
        from .serializers import CountrySerializer
        
        countries = ServiceZone.get_countries()
        serializer = CountrySerializer(countries, many=True)
        
        return Response({
            'success': True,
            'message': 'Países obtenidos exitosamente',
            'data': serializer.data,
            'count': len(serializer.data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo países: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
@cache_page(60 * 15)  # Cache por 15 minutos
def get_states_by_country(request, country_code):
    """
    Obtiene lista de estados/provincias por país.
    
    Args:
        country_code: Código de país ISO (2 letras)
    
    Returns:
        - Lista de estados/provincias del país especificado
    """
    try:
        from .models import ServiceZone
        from .serializers import StateSerializer
        
        states = ServiceZone.get_states_by_country(country_code.upper())
        serializer = StateSerializer(states, many=True)
        
        return Response({
            'success': True,
            'message': f'Estados de {country_code} obtenidos exitosamente',
            'data': serializer.data,
            'count': len(serializer.data),
            'country_code': country_code.upper()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo estados para {country_code}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
@cache_page(60 * 15)  # Cache por 15 minutos
def get_cities_by_country_state(request, country_code, state_code=None):
    """
    Obtiene lista de ciudades por país y opcionalmente por estado.
    Detecta automáticamente si usar city_name o service_area según el país.
    
    Args:
        country_code: Código de país ISO (2 letras)
        state_code: Código de estado/provincia (opcional)
    
    Returns:
        - Lista de ciudades/áreas de servicio del país/estado especificado
    """
    try:
        from .models import ServiceZone
        
        cities = ServiceZone.get_cities_smart(
            country_code.upper(), 
            state_code.upper() if state_code else None
        )
        
        location = f'{country_code}'
        if state_code:
            location += f'/{state_code}'
        
        return Response({
            'success': True,
            'message': f'Ciudades de {location} obtenidas exitosamente',
            'data': cities,
            'count': len(cities),
            'country_code': country_code.upper(),
            'state_code': state_code.upper() if state_code else None,
            'data_type': cities[0]['type'] if cities else 'none'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo ciudades para {country_code}/{state_code}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
@cache_page(60 * 15)  # Cache por 15 minutos
def get_service_areas_by_location(request, country_code):
    """
    Obtiene áreas de servicio por ubicación.
    
    Args:
        country_code: Código de país ISO (2 letras)
    
    Query parameters:
        - state_code: Código de estado/provincia (opcional)
        - city_name: Nombre de ciudad (opcional)
    
    Returns:
        - Lista de áreas de servicio disponibles
    """
    try:
        from .models import ServiceZone, ServiceAreaCityMap
        from .serializers import ServiceAreaSerializer
        
        state_code = request.GET.get('state_code')
        city_name = request.GET.get('city_name')
        
        raw_service_areas = ServiceZone.get_service_areas_by_location(
            country_code.upper(),
            state_code.upper() if state_code else None,
            city_name
        )
        # Resolver nombres amigables desde ServiceAreaCityMap
        codes = [sa['service_area'] for sa in raw_service_areas]
        display_by_code = {}
        if codes:
            mappings = (ServiceAreaCityMap.objects
                        .filter(country_code=country_code.upper(), service_area__in=codes)
                        .values('service_area', 'display_name')
                        .distinct())
            # Priorizar nombres únicos por código; si hay múltiples, tomamos el primero
            for m in mappings:
                display_by_code.setdefault(m['service_area'], m['display_name'])

        enriched = []
        for sa in raw_service_areas:
            code = sa.get('service_area')
            dn = display_by_code.get(code, code)
            enriched.append({
                'service_area': code,
                'display_name': dn,
            })

        # Asegurar unicidad de display_name: si se repite, concatenar código
        counts = {}
        for item in enriched:
            counts[item['display_name']] = counts.get(item['display_name'], 0) + 1
        for item in enriched:
            if counts.get(item['display_name'], 0) > 1:
                item['display_name'] = f"{item['display_name']} - {item['service_area']}"

        serializer = ServiceAreaSerializer(enriched, many=True)
        
        return Response({
            'success': True,
            'message': 'Áreas de servicio obtenidas exitosamente',
            'data': serializer.data,
            'count': len(serializer.data),
            'filters': {
                'country_code': country_code.upper(),
                'state_code': state_code.upper() if state_code else None,
                'city_name': city_name
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo áreas de servicio: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
@cache_page(60 * 15)  # Cache por 15 minutos
def get_postal_codes_by_location(request, country_code):
    """
    Obtiene códigos postales por ubicación con paginación y límites inteligentes.
    
    Args:
        country_code: Código de país ISO (2 letras)
    
    Query parameters:
        - state_code: Código de estado/provincia (opcional)
        - city_name: Nombre de ciudad (opcional)
        - service_area: Código de área de servicio (opcional, ej: YYZ, YVR)
        - page: Número de página (opcional, por defecto 1)
        - page_size: Tamaño de página (opcional, por defecto 100, máximo 1000)
        - limit: Límite total de resultados (opcional, por defecto 5000)
        - force_all: Forzar obtener todos los resultados (opcional, solo para admin)
    
    Returns:
        - Lista paginada de rangos de códigos postales disponibles
    """
    try:
        from .models import ServiceZone
        from .serializers import PostalCodeSerializer
        
        state_code = request.GET.get('state_code')
        city_name = request.GET.get('city_name')
        service_area = request.GET.get('service_area')
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 100)), 1000)  # Máximo 1000
        limit = int(request.GET.get('limit', 5000))  # Límite por defecto 5000
        force_all = request.GET.get('force_all', '').lower() == 'true'
        
        # Países con muchos códigos postales (requieren filtros específicos)
        LARGE_COUNTRIES = ['CA', 'US', 'GB', 'DE', 'FR', 'AU', 'IN']
        
        # Obtener queryset base
        postal_codes_qs = ServiceZone.get_postal_codes_by_location(
            country_code.upper(),
            state_code.upper() if state_code else None,
            city_name,
            service_area.upper() if service_area else None
        )
        
        total_count = postal_codes_qs.count()
        
        # Para países grandes sin filtros específicos, requerir al menos state_code
        if (country_code.upper() in LARGE_COUNTRIES and 
            not state_code and 
            not city_name and 
            not service_area and
            not force_all and
            total_count > 10000):
            
            # Obtener estados disponibles
            available_states = list(ServiceZone.objects.filter(
                country_code=country_code.upper(),
                state_code__isnull=False
            ).exclude(
                state_code=''
            ).values_list('state_code', flat=True).distinct().order_by('state_code'))
            
            # Si no hay estados, obtener algunas ciudades como alternativa
            available_cities = []
            if not available_states:
                available_cities = list(ServiceZone.objects.filter(
                    country_code=country_code.upper(),
                    city_name__isnull=False
                ).exclude(
                    city_name=''
                ).values_list('city_name', flat=True).distinct().order_by('city_name')[:20])  # Limitar a 20 ciudades
            
            # Si tampoco hay ciudades, usar service_area como filtro alternativo
            available_service_areas = []
            if not available_states and not available_cities:
                available_service_areas = list(ServiceZone.objects.filter(
                    country_code=country_code.upper(),
                    service_area__isnull=False
                ).exclude(
                    service_area=''
                ).values_list('service_area', flat=True).distinct().order_by('service_area')[:15])
            
            # Crear mensaje más específico basado en qué filtros están disponibles
            filter_message = f'Para {country_code.upper()}, se requiere especificar '
            suggestion_message = 'Agregue '
            
            if available_states:
                filter_message += 'provincia/estado o ciudad debido al gran volumen de datos'
                suggestion_message += '?state_code=XX o ?city_name=Ciudad para filtrar los resultados'
            elif available_cities:
                filter_message += 'ciudad debido al gran volumen de datos'
                suggestion_message += '?city_name=Ciudad para filtrar los resultados'
            elif available_service_areas:
                filter_message += 'área de servicio debido al gran volumen de datos'
                suggestion_message += '?service_area=YYZ para filtrar los resultados'
            else:
                filter_message += 'filtros específicos debido al gran volumen de datos'
                suggestion_message += 'filtros específicos para reducir los resultados'
            
            return Response({
                'success': False,
                'message': filter_message,
                'error': 'FILTERS_REQUIRED',
                'total_count': total_count,
                'available_filters': {
                    'states': available_states,
                    'cities': available_cities,
                    'service_areas': available_service_areas
                },
                'suggestion': suggestion_message,
                'recommendations': {
                    'use_city_filter': not available_states and len(available_cities) > 0,
                    'use_service_area_filter': not available_states and not available_cities and len(available_service_areas) > 0,
                    'message': (
                        'Use filtro de ciudad ya que no hay provincias/estados disponibles' if not available_states and available_cities else
                        'Use filtro de área de servicio ya que no hay provincias/estados o ciudades disponibles' if not available_states and not available_cities and available_service_areas else
                        None
                    )
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Aplicar límite si no está forzado
        if not force_all and total_count > limit:
            postal_codes_qs = postal_codes_qs[:limit]
            limited = True
        else:
            limited = False
        
        # Implementar paginación
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        postal_codes_page = postal_codes_qs[start_index:end_index]
        
        serializer = PostalCodeSerializer(postal_codes_page, many=True)
        
        # Calcular información de paginación
        total_pages = (min(total_count, limit if not force_all else total_count) + page_size - 1) // page_size
        
        return Response({
            'success': True,
            'message': 'Códigos postales obtenidos exitosamente',
            'data': serializer.data,
            'pagination': {
                'count': len(serializer.data),
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1,
                'limited': limited,
                'limit_applied': limit if limited else None
            },
            'filters': {
                'country_code': country_code.upper(),
                'state_code': state_code.upper() if state_code else None,
                'city_name': city_name,
                'service_area': service_area.upper() if service_area else None
            },
            'performance': {
                'is_large_dataset': country_code.upper() in LARGE_COUNTRIES,
                'requires_filters': country_code.upper() in LARGE_COUNTRIES and not state_code and not city_name and not service_area
            }
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        logger.error(f"Error de parámetros obteniendo códigos postales: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': f'Error en parámetros: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error obteniendo códigos postales: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ServiceZoneThrottle])
@cache_page(60 * 15)  # Cache por 15 minutos - búsquedas frecuentes
def search_service_zones(request):
    """
    Búsqueda avanzada de zonas de servicio.
    
    Query parameters:
        - q: Término de búsqueda (nombre de país, estado, ciudad)
        - country_code: Filtrar por código de país
        - page: Número de página (por defecto: 1)
        - page_size: Tamaño de página (por defecto: 50, máximo: 200)
    
    Returns:
        - Lista paginada de zonas de servicio que coincidan con los criterios
    """
    try:
        from .models import ServiceZone
        from .serializers import ServiceZoneSerializer
        
        # Parámetros de búsqueda
        query = request.GET.get('q', '').strip()
        country_code = request.GET.get('country_code', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 50)), 200)
        
        # Construir queryset
        queryset = ServiceZone.objects.all()
        
        # Filtrar por país si se especifica
        if country_code:
            queryset = queryset.filter(country_code=country_code.upper())
        
        # Búsqueda por texto
        if query:
            queryset = queryset.filter(
                Q(country_name__icontains=query) |
                Q(state_name__icontains=query) |
                Q(city_name__icontains=query) |
                Q(service_area__icontains=query)
            )
        
        # Ordenar y paginar
        queryset = queryset.order_by('country_name', 'state_name', 'city_name')
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serializar datos
        serializer = ServiceZoneSerializer(page_obj.object_list, many=True)
        
        return Response({
            'success': True,
            'message': 'Búsqueda completada exitosamente',
            'data': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            },
            'filters': {
                'query': query,
                'country_code': country_code.upper() if country_code else None
            }
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error en búsqueda de zonas de servicio: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([ServiceZoneAnonThrottle])
@cache_page(60 * 30)  # Cache por 30 minutos - análisis de países es estático
def analyze_country_structure(request, country_code):
    """
    Analiza la estructura de datos disponible para un país específico
    Retorna información sobre qué campos están disponibles
    """
    try:
        country_code = country_code.upper()
        
        # Obtener QuerySet base para el país (sin slice)
        base_zones = ServiceZone.objects.filter(
            country_code=country_code
        )
        
        if not base_zones.exists():
            return Response({
                'success': False,
                'message': f'No se encontraron zonas de servicio para el país {country_code}',
                'country_code': country_code,
                'hasStates': False,
                'hasCities': False,
                'hasPostalCodes': False,
                'pattern': 'NO_DATA'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Analizar campos disponibles usando el QuerySet base
        total_records = base_zones.count()
        
        # Contar registros con estados no vacíos
        states_count = base_zones.exclude(
            Q(state_code__isnull=True) | Q(state_code='')
        ).count()
        
        # Contar registros con ciudades no vacías (city_name O service_area)
        cities_count = base_zones.exclude(
            Q(city_name__isnull=True) | Q(city_name='')
        ).count()
        
        # Contar registros con service_area (códigos de ciudad/aeropuerto)
        service_area_count = base_zones.exclude(
            Q(service_area__isnull=True) | Q(service_area='')
        ).count()
        
        # Contar registros con códigos postales
        postal_codes_count = base_zones.exclude(
            Q(postal_code_from__isnull=True) | Q(postal_code_from='')
        ).count()
        
        # Determinar patrones (considerar service_area como indicador de ciudades)
        has_states = (states_count / total_records) > 0.1  # >10% tienen estados
        has_cities = (cities_count / total_records) > 0.1  # >10% tienen city_name
        has_service_areas = (service_area_count / total_records) > 0.1  # >10% tienen service_area
        has_postal_codes = (postal_codes_count / total_records) > 0.1  # >10% tienen códigos postales
        
        # Si no hay city_name pero sí service_area, usar service_area como ciudades
        effective_cities = has_cities or has_service_areas
        
        # Determinar patrón principal
        if has_postal_codes and not effective_cities:
            pattern = 'POSTAL_CODES'
        elif effective_cities and not has_postal_codes:
            pattern = 'CITY'
        elif effective_cities and has_postal_codes:
            pattern = 'MIXED'
        elif has_states:
            pattern = 'STATES'
        else:
            pattern = 'BASIC'
        
        # Obtener ejemplos de datos
        examples = []
        sample_zones = base_zones[:3]  # Obtener muestra para ejemplos
        for zone in sample_zones:
            examples.append({
                'country': zone.country_name,
                'state': zone.state_code or zone.state_name,
                'city': zone.city_name,
                'service_area': zone.service_area,  # Códigos como BOG, MED, BAQ
                'postal_range': f"{zone.postal_code_from}-{zone.postal_code_to}" if zone.postal_code_from else None
            })
        
        return Response({
            'success': True,
            'country_code': country_code,
            'country_name': base_zones.first().country_name,
            'hasStates': has_states,
            'hasCities': effective_cities,  # Usar la lógica combinada
            'hasPostalCodes': has_postal_codes,
            'pattern': pattern,
            'statistics': {
                'total_records': total_records,
                'states_percentage': round((states_count / total_records) * 100, 1),
                'cities_percentage': round((cities_count / total_records) * 100, 1),
                'service_areas_percentage': round((service_area_count / total_records) * 100, 1),
                'postal_codes_percentage': round((postal_codes_count / total_records) * 100, 1)
            },
            'examples': examples,
            'data_structure': {
                'city_name_available': has_cities,
                'service_area_available': has_service_areas,
                'recommended_city_field': 'service_area' if has_service_areas and not has_cities else 'city_name'
            },
            'recommendations': {
                'priority_fields': [
                    'country' if True else '',
                    'state' if has_states else '',
                    'city' if effective_cities else '',
                    'postal_code' if has_postal_codes else ''
                ],
                'search_strategy': 'postal_code' if pattern == 'POSTAL_CODES' else 'city' if pattern == 'CITY' else 'mixed',
                'city_field_to_use': 'service_area' if has_service_areas and not has_cities else 'city_name'
            }
        })
        
    except Exception as e:
        logger.error(f"Error analizando estructura del país {country_code}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
@cache_page(60 * 10)
def resolve_service_area_display(request):
    """Resuelve nombre amigable para un service_area dado.

    Query params:
      - country_code (requerido)
      - service_area (requerido)
      - postal_code (opcional)
      - state_code (opcional)
      - fallback_city (opcional)
    """
    try:
        from .models import ServiceAreaCityMap

        country_code = (request.GET.get('country_code') or '').upper().strip()
        service_area = (request.GET.get('service_area') or '').upper().strip()
        postal_code = request.GET.get('postal_code')
        state_code = request.GET.get('state_code')
        fallback_city = request.GET.get('fallback_city')

        if not country_code or not service_area:
            return Response({
                'success': False,
                'message': 'country_code y service_area son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = ServiceAreaCityMap.resolve_display(
            country_code=country_code,
            service_area=service_area,
            postal_code=postal_code,
            state_code=state_code,
            fallback_city=fallback_city,
        )

        return Response({
            'success': True,
            'data': result,
            'inputs': {
                'country_code': country_code,
                'service_area': service_area,
                'postal_code': postal_code,
                'state_code': state_code,
                'fallback_city': fallback_city,
            }
        })
    except Exception as e:
        logger.error(f"Error resolviendo display de service_area: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)