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
from decimal import Decimal, ROUND_HALF_UP
from .utils.country_utils import get_country_name_from_iso as _get_country_name_from_iso

# Intentar importar helper de mapeo si existe; definir fallback
try:
    from .utils.service_area_mapping import get_city_service_area_mapping  # type: ignore
except Exception:  # pragma: no cover - fallback seguro
    def get_city_service_area_mapping(country_code: str, city_name: str):
        return None

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
                pass  # Usuario no existe, no registramos a actividad
            
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
            
            # Calcular PESO EFECTIVO para cotizar: mayor entre
            # - weight (input base)
            # - total_weight (si viene)
            # - suma de piezas (si vienen)
            # - suma dimensional de piezas (si vienen L/W/H) con regla sum-then-round (HALF_UP)
            # - mayor peso individual de las piezas (si vienen)
            base_weight = float(serializer.validated_data['weight'])
            total_weight_in = None
            pieces = serializer.validated_data.get('pieces') or []
            sum_pieces = 0.0
            max_piece = 0.0
            # Dimensional: calcularemos ambos modos
            # - sum-then-round (referencia)
            # - round-then-sum (SOAP-style) → este será el candidato principal
            sum_dimensional_sum_then_round = 0.0
            sum_dimensional_round_then_sum = 0.0
            max_piece_dimensional = 0.0
            try:
                total_weight_in = float(serializer.validated_data.get('total_weight')) if serializer.validated_data.get('total_weight') else None
            except Exception:
                total_weight_in = None
            try:
                weights_list = []
                dim_sum_exact = Decimal('0')
                dim_sum_exact = Decimal('0')
                dim_sum_rounded = Decimal('0')
                for p in pieces:
                    try:
                        w = float(p.get('weight') or 0)
                    except Exception:
                        w = 0.0
                    weights_list.append(w)
                    # Dimensional por pieza si hay L/W/H
                    try:
                        L = p.get('length') or p.get('L') or p.get(' largo')
                        W = p.get('width') or p.get('W') or p.get('ancho')
                        H = p.get('height') or p.get('H') or p.get('alto')
                        if L and W and H:
                            dL = Decimal(str(float(L)))
                            dW = Decimal(str(float(W)))
                            dH = Decimal(str(float(H)))
                            dim_exact = (dL * dW * dH) / Decimal('5000')
                            # acumular exacto y trackear máximo por pieza (luego redondeamos)
                            dim_sum_exact += dim_exact
                            piece_dim_rounded_dec = dim_exact.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                            dim_sum_rounded += piece_dim_rounded_dec
                            piece_dim_rounded = float(piece_dim_rounded_dec)
                            if piece_dim_rounded > max_piece_dimensional:
                                max_piece_dimensional = piece_dim_rounded
                    except Exception:
                        pass
                if weights_list:
                    sum_pieces = sum(weights_list)
                    max_piece = max(weights_list)
                # Redondear suma dimensional AL FINAL (sum-then-round)
                try:
                    if dim_sum_exact > 0:
                        sum_dimensional_sum_then_round = float(dim_sum_exact.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
                except Exception:
                    sum_dimensional_sum_then_round = 0.0
                # Sumar por pieza redondeada (round-then-sum)
                try:
                    if dim_sum_rounded > 0:
                        sum_dimensional_round_then_sum = float(dim_sum_rounded.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
                except Exception:
                    sum_dimensional_round_then_sum = float(dim_sum_rounded) if dim_sum_rounded else 0.0
            except Exception:
                sum_pieces = 0.0
                max_piece = 0.0
                sum_dimensional_sum_then_round = 0.0
                sum_dimensional_round_then_sum = 0.0
                max_piece_dimensional = 0.0

            candidates = [base_weight]
            if total_weight_in and total_weight_in > 0:
                candidates.append(total_weight_in)
            if sum_pieces > 0:
                candidates.append(sum_pieces)
            # Usar el dimensional SOAP-style como candidato principal
            if sum_dimensional_round_then_sum > 0:
                candidates.append(sum_dimensional_round_then_sum)
            if max_piece > 0:
                candidates.append(max_piece)

            effective_weight = max(candidates) if candidates else base_weight

            # Redondeo consistente a 2 decimales usando HALF_UP del servicio
            try:
                effective_weight = dhl_service._round_half_up(effective_weight, 2)
                sum_pieces = dhl_service._round_half_up(sum_pieces, 2)
                max_piece = dhl_service._round_half_up(max_piece, 2)
                sum_dimensional_sum_then_round = dhl_service._round_half_up(sum_dimensional_sum_then_round, 2)
                sum_dimensional_round_then_sum = dhl_service._round_half_up(sum_dimensional_round_then_sum, 2)
                max_piece_dimensional = dhl_service._round_half_up(max_piece_dimensional, 2)
                if total_weight_in is not None:
                    total_weight_in = dhl_service._round_half_up(total_weight_in, 2)
                base_weight = dhl_service._round_half_up(base_weight, 2)
            except Exception:
                effective_weight = round(float(effective_weight), 2)

            # Llamar API DHL
            result = dhl_service.get_rate(
                origin=_origin,
                destination=_destination,
                weight=effective_weight,
                dimensions=serializer.validated_data['dimensions'],
                declared_weight=serializer.validated_data.get('declared_weight'),
                content_type=service,
                account_number=account_number
            )

            # Agregar metadatos adicionales
            result['request_timestamp'] = datetime.now().isoformat()
            result['requested_by'] = request.user.username
            # Adjuntar desglose de cómo se eligió el peso efectivo
            result.setdefault('weight_selection', {})
            result['weight_selection'].update({
                'base_weight': base_weight,
                'total_weight_input': total_weight_in,
                'sum_pieces': sum_pieces,
                'sum_dimensional_sum_then_round': sum_dimensional_sum_then_round,
                'sum_dimensional_round_then_sum': sum_dimensional_round_then_sum,
                'max_piece': max_piece,
                'max_piece_dimensional': max_piece_dimensional,
                'effective_weight_used': effective_weight,
                'rule': 'max(base, total_weight, sum_pieces, sum_dimensional(round-then-sum), max_piece)'
            })
            
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
                            'weight_selection': result.get('weight_selection', {}),
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
@permission_classes([IsAuthenticated])
def pickup_view(request):
    """
    Vista para crear una solicitud de recogida (pickup booking) con DHL
    
    Args:
        request: Solicitud HTTP con datos del pickup
        
    Returns:
        Response: Respuesta JSON con resultado de la operación
    """
    try:
        logger.info(f"Pickup request from user: {request.user.username}")
        
        # Obtener datos del request
        pickup_data = request.data.copy()
        
        # Validar campos requeridos
        required_fields = [
            'plannedPickupDateAndTime',
            'account_number',
            'shipper',
            'receiver',
            'bookingRequestor',
            'pickupDetails'
        ]
        
        is_valid, errors = validate_required_fields(pickup_data, required_fields)
        if not is_valid:
            return Response({
                'success': False,
                'error': 'Campos requeridos faltantes',
                'details': errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener instancia del servicio DHL
        dhl_service = DHLService(
            username=settings.DHL_USERNAME,
            password=settings.DHL_PASSWORD,
            base_url=settings.DHL_BASE_URL
        )
        
        # Crear la recogida
        result = dhl_service.create_pickup(pickup_data)
        
        if result.get('success'):
            # Log de actividad del usuario
            UserActivity.objects.create(
                user=request.user,
                action='system_action',
                description=f"Pickup creado: {result.get('dispatch_confirmation_number', 'N/A')}",
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                status='success'
            )
            
            return Response({
                'success': True,
                'message': result.get('message', 'Recogida creada exitosamente'),
                'data': {
                    'dispatch_confirmation_number': result.get('dispatch_confirmation_number', ''),
                    'pickup_info': result.get('pickup_info', {}),
                    'raw_response': result.get('pickup_data', {})
                }
            }, status=status.HTTP_201_CREATED)
        else:
            # Log de error con detalles completos
            logger.error(f"Error al crear pickup - Respuesta completa de DHL: {result}")
            
            UserActivity.objects.create(
                user=request.user,
                action='api_error',
                description=f"Error al crear pickup: {result.get('error', 'Unknown error')}",
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                status='error'
            )
            
            return Response({
                'success': False,
                'error': result.get('error', 'Error desconocido'),
                'error_code': result.get('error_code', 'UNKNOWN_ERROR'),
                'details': result.get('details', ''),
                'raw_response': result.get('raw_response', '')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error en pickup_view: {str(e)}")
        
        # Log de error del sistema
        UserActivity.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action='system_action',
            description=f"Error del sistema: {str(e)}",
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            status='error'
        )
        
        return Response({
            'success': False,
            'error': 'Error interno del servidor',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_client_ip(request):
    """
    Obtiene la IP del cliente desde la solicitud
    
    Args:
        request: Objeto de solicitud HTTP
        
    Returns:
        str: IP del cliente
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


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
        from .models import ServiceZone, ServiceAreaCityMap, CountryISO
        from .utils.country_utils import get_country_name_from_iso
        from .serializers import CountrySerializer

        # Fuente primaria: ServiceAreaCityMap (países con mapeo disponible)
        map_country_codes = list(
            ServiceAreaCityMap.objects
            .values_list('country_code', flat=True)
            .distinct()
            .order_by('country_code')
        )

        countries_list = []
        if map_country_codes:
            # Resolver country_name desde ServiceZone como referencia
            for cc in map_country_codes:
                # Priorizar CountryISO DB; luego ServiceZone; luego util local
                name = CountryISO.resolve_name(
                    cc,
                    fallback=(
                        ServiceZone.objects
                        .filter(country_code=cc)
                        .exclude(country_name__isnull=True)
                        .exclude(country_name='')
                        .values_list('country_name', flat=True)
                        .first() or ''
                    ) or get_country_name_from_iso(cc)
                )
                countries_list.append({'country_code': cc, 'country_name': name})
        else:
            # Fallback: usar ServiceZone
            countries_list = ServiceZone.get_countries()
            # Normalizar nombres si vinieran vacíos
            if countries_list:
                norm = []
                for c in countries_list:
                    code = (c.get('country_code') or '').upper()
                    # Resolver desde CountryISO con fallback a util
                    name = CountryISO.resolve_name(code, fallback=c.get('country_name') or '')
                    if not name:
                        name = get_country_name_from_iso(code)
                    norm.append({'country_code': code, 'country_name': name})
                countries_list = norm

        serializer = CountrySerializer(countries_list, many=True)

        return Response({
            'success': True,
            'message': 'Países obtenidos exitosamente',
            'data': serializer.data,
            'count': len(serializer.data),
            'source': 'ServiceAreaCityMap' if map_country_codes else 'ServiceZone'
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
        from .models import ServiceAreaCityMap
        from .serializers import StateSerializer

        cc = country_code.upper()

        # Usar únicamente ServiceAreaCityMap como fuente de verdad
        map_state_codes = list(
            ServiceAreaCityMap.objects
            .filter(country_code=cc)
            .exclude(state_code__isnull=True)
            .exclude(state_code='')
            .values_list('state_code', flat=True)
            .distinct()
            .order_by('state_code')
        )

        states = [{'state_code': sc, 'state_name': sc} for sc in map_state_codes]

        serializer = StateSerializer(states, many=True)
        
        return Response({
            'success': True,
            'message': f'Estados de {country_code} obtenidos exitosamente',
            'data': serializer.data,
            'count': len(serializer.data),
            'country_code': country_code.upper(),
            'source': 'ServiceAreaCityMap'
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
@cache_page(60 * 5, key_prefix='cities_v2')  # Cache por 5 minutos (v2 para invalidar caché vieja)
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
        from .models import ServiceAreaCityMap, ServiceZone
        from .serializers import CitySerializer

        prefer = (request.GET.get('prefer') or '').strip().lower()
        allowed = {'', 'city_name', 'service_area', 'map'}
        if prefer not in allowed:
            prefer = ''

        cc = country_code.upper()
        sc = state_code.upper() if state_code else None

        # Fuente única: ServiceAreaCityMap
        qs_map = ServiceAreaCityMap.objects.filter(country_code=cc)
        # Para CA, no filtramos por estado para asegurar lista completa
        if sc and cc != 'CA':
            qs_map = qs_map.filter(state_code=sc)

        # Optimizar: devolver ciudades únicas por city_name para evitar explosión por cada rango postal
        q = (request.GET.get('q') or '').strip()
        if q:
            qs_map = qs_map.filter(city_name__icontains=q)

        city_list = (
            qs_map
            .exclude(city_name='')
            .values_list('city_name', flat=True)
            .distinct()
            .order_by('city_name')
        )
        cities = [
            {'name': c, 'code': c, 'display_name': c, 'type': 'map_city'}
            for c in city_list
        ]

        # Fallback/append: incluir ciudades desde ServiceZone (ESD) que no estén en el mapa
        try:
            esd_items = ServiceZone.get_cities_smart(cc, sc)
            # Aplicar filtro de búsqueda si corresponde
            if q:
                q_low = q.lower()
                esd_items = [it for it in esd_items if (it.get('display_name') or '').lower().find(q_low) >= 0]

            existing = set((ci.get('display_name') or '').strip().lower() for ci in cities)
            appended = 0
            for it in esd_items:
                disp = (it.get('display_name') or '').strip()
                if not disp:
                    continue
                key = disp.lower()
                if key in existing:
                    continue
                # Normalizar estructura al mismo formato
                cities.append({
                    'name': it.get('code') or disp,
                    'code': it.get('code') or disp,
                    'display_name': disp,
                    'type': f"esd_{it.get('type') or 'city'}"
                })
                existing.add(key)
                appended += 1
        except Exception as _e:
            # No bloquear si ESD falla
            appended = 0

        location = f'{country_code}'
        if state_code:
            location += f'/{state_code}'

        # Debug: log request parameters and result count
        try:
            logger.info(f"CITIES API -> cc={cc}, sc={sc}, q='{q}', count={len(cities)}")
        except Exception:
            pass

        return Response({
            'success': True,
            'message': f'Ciudades de {location} obtenidas exitosamente',
            'data': cities,
            'count': len(cities),
            'country_code': country_code.upper(),
            'state_code': state_code.upper() if state_code else None,
            'data_type': cities[0]['type'] if cities else 'none',
            'preferences': {
                'prefer': 'map_city_name',
                'optimized': True
            },
            'merge': {
                'source': 'map+esd',
                'appended_from_esd': appended if 'appended' in locals() else 0
            },
            'cache_version': 'cities_v2'
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
        from .models import ServiceAreaCityMap
        from .serializers import ServiceAreaSerializer, PostalCodeSerializer
        from django.db.models import Q, Count

        state_code = request.GET.get('state_code')
        city_name = request.GET.get('city_name')
        service_area = request.GET.get('service_area')
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 100)), 200)
        limit = int(request.GET.get('limit', 5000))

        qs = ServiceAreaCityMap.objects.filter(country_code=country_code.upper())
        if state_code and country_code != 'CA':
            qs = qs.filter(state_code=state_code.upper())

        if city_name:
            correct_service_area = get_city_service_area_mapping(country_code, city_name)
            if correct_service_area:
                qs = qs.filter(
                    Q(city_name__iexact=city_name) | Q(display_name__icontains=city_name),
                    service_area=correct_service_area
                )
            else:
                qs = qs.filter(Q(city_name__iexact=city_name) | Q(display_name__icontains=city_name))

        if service_area:
            qs = qs.filter(service_area=service_area.upper())
        qs = qs.exclude(postal_code_from='').exclude(postal_code_to='')

        # Base: datos desde ServiceAreaCityMap
        rows_all = list(qs.order_by('postal_code_from')[:limit])
        data_all = [
            {
                'postal_code_from': r.postal_code_from,
                'postal_code_to': r.postal_code_to,
                'service_area': r.service_area,
            }
            for r in rows_all
        ]

        # Fallback/append: complementar con rangos desde ServiceZone (ESD)
        try:
            if city_name and not service_area:
                correct_service_area = get_city_service_area_mapping(country_code, city_name)
                esd_qs = ServiceZone.get_postal_codes_by_location(country_code, state_code, city_name, correct_service_area)
            else:
                esd_qs = ServiceZone.get_postal_codes_by_location(country_code, state_code, city_name, service_area)
            esd_list = list(esd_qs)
        except Exception:
            esd_list = []

        # Unificar y deduplicar por (from,to,service_area)
        seen = set()
        unified = []
        city_correct_area = get_city_service_area_mapping(country_code, city_name) if city_name else None
        for item in data_all + esd_list:
            f = (item.get('postal_code_from') or '').strip()
            t = (item.get('postal_code_to') or '').strip()
            s = (item.get('service_area') or '').strip().upper()
            if not f or not t:
                continue
            key = (f, t, s)
            if key in seen:
                continue
            if city_name and city_correct_area and s != city_correct_area:
                continue
            seen.add(key)
            unified.append({'postal_code_from': f, 'postal_code_to': t, 'service_area': s})

        # Ordenar y paginar sobre la unión
        unified.sort(key=lambda x: (x['postal_code_from'], x['postal_code_to'], x['service_area']))
        total = len(unified)
        total_limited = min(total, limit)
        total_pages = (total_limited + page_size - 1) // page_size
        page = max(1, min(page, total_pages or 1))
        start = (page - 1) * page_size
        end = start + page_size
        data = unified[start:end]
        serializer = PostalCodeSerializer(data, many=True)

        # Debug info opcional
        debug_info = {}
        if request.GET.get('debug') == '1' and city_name:
            correct_area = get_city_service_area_mapping(country_code, city_name)
            debug_info = {
                'detected_service_area': correct_area,
                'filter_applied': bool(correct_area),
                'total_before_filter': len(data_all + esd_list),
                'total_after_filter': len(unified)
            }

        # Metadatos
        cc = (country_code or '').upper()
        sc = (state_code or '').upper() if state_code else ''

        response_data = {
            'success': True,
            'message': 'Códigos postales obtenidos exitosamente',
            'data': serializer.data,
            'count': total_limited,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'filters': {
                'country_code': cc,
                'state_code': sc,
                'city_name': city_name,
                'service_area': service_area
            },
            'source': 'Map+ESD'
        }
        if debug_info:
            response_data['debug'] = debug_info

        return Response(response_data, status=status.HTTP_200_OK)

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
@cache_page(60 * 30, key_prefix='analyze_v2')  # Cache por 30 minutos - v2 para invalidar caché previa
def analyze_country_structure(request, country_code):
    """
    Analiza la estructura de datos disponible para un país específico
    Retorna información sobre qué campos están disponibles
    """
    try:
        country_code = country_code.upper()

        base_zones = ServiceZone.objects.filter(country_code=country_code)
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

        total_records = base_zones.count()
        states_count = base_zones.exclude(Q(state_code__isnull=True) | Q(state_code='')).count()
        cities_count = base_zones.exclude(Q(city_name__isnull=True) | Q(city_name='')).count()
        service_area_count = base_zones.exclude(Q(service_area__isnull=True) | Q(service_area='')).count()
        postal_codes_count = base_zones.exclude(Q(postal_code_from__isnull=True) | Q(postal_code_from='')).count()

        has_states = (states_count / total_records) > 0.1
        has_cities = (cities_count / total_records) > 0.1
        has_service_areas = (service_area_count / total_records) > 0.1
        has_postal_codes = (postal_codes_count / total_records) > 0.1

        # Complementar con ServiceAreaCityMap para detectar ciudades aunque ServiceZone no las tenga pobladas
        try:
            from .models import ServiceAreaCityMap
            map_city_exists = ServiceAreaCityMap.objects.filter(
                country_code=country_code.upper()
            ).exclude(city_name='').exists()
            if map_city_exists:
                has_cities = True
        except Exception:
            pass

        effective_cities = has_cities or has_service_areas

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

        # Recomendación de campo de ciudad
        # Siempre preferir city_name cuando esté disponible para evitar mostrar códigos (YMG, YHM) al usuario
        # Excepción: solo cuando NO haya city_name disponible, caer a service_area
        if has_cities:
            recommended_city_field = 'city_name'
        else:
            recommended_city_field = 'service_area' if has_service_areas else 'city_name'

        examples = []
        for zone in base_zones[:3]:
            examples.append({
                'country': zone.country_name,
                'state': zone.state_code or zone.state_name,
                'city': zone.city_name,
                'service_area': zone.service_area,
                'postal_range': f"{zone.postal_code_from}-{zone.postal_code_to}" if zone.postal_code_from else None
            })

        return Response({
            'success': True,
            'country_code': country_code,
            'country_name': base_zones.first().country_name,
            'hasStates': has_states,
            'hasCities': effective_cities,
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
                'recommended_city_field': recommended_city_field
            },
            'recommendations': {
                'priority_fields': [
                    'country',
                    'state' if has_states else '',
                    'city' if effective_cities else '',
                    'postal_code' if has_postal_codes else ''
                ],
                'search_strategy': 'postal_code' if pattern == 'POSTAL_CODES' else 'city' if pattern == 'CITY' else 'mixed',
                'city_field_to_use': recommended_city_field
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
        from django.db.models import Q
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

        # 1. Intentar resolver directamente el nombre del área de servicio
        direct_match = ServiceAreaCityMap.objects.filter(
            country_code=country_code,
            service_area=service_area
        ).first()

        if direct_match:
            return Response({
                'success': True,
                'service_area': direct_match.service_area,
                'display_name': direct_match.display_name or direct_match.service_area,
                'type': 'direct'
            }, status=status.HTTP_200_OK)

        # 2. Si no hay coincidencia directa, intentar con city_name como fallback
        if fallback_city:
            city_fallback = ServiceAreaCityMap.objects.filter(
                country_code=country_code,
                city_name__iexact=fallback_city
            ).first()

            if city_fallback:
                return Response({
                    'success': True,
                    'service_area': city_fallback.service_area,
                    'display_name': city_fallback.display_name or city_fallback.service_area,
                    'type': 'fallback_city'
                }, status=status.HTTP_200_OK)

        # 3. Si aún no hay coincidencia, buscar por patrones en postal_code
        if postal_code:
            postal_fallback = ServiceAreaCityMap.objects.filter(
                country_code=country_code,
                postal_code_from__lte=postal_code,
                postal_code_to__gte=postal_code
            ).first()

            if postal_fallback:
                return Response({
                    'success': True,
                    'service_area': postal_fallback.service_area,
                    'display_name': postal_fallback.display_name or postal_fallback.service_area,
                    'type': 'fallback_postal'
                }, status=status.HTTP_200_OK)

        # 4. Si no se encuentra nada, devolver error amigable
        return Response({
            'success': False,
            'message': f'No se pudo determinar el área de servicio para {service_area}',
            'country_code': country_code,
            'service_area': service_area,
            'postal_code': postal_code,
            'state_code': state_code,
            'fallback_city': fallback_city
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Error resolviendo display de service_area: {str(e)}")
        return Response({
            'success': False,
            'message': 'Ha ocurrido un error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def map_stats_by_country(request, country_code):
    """
    Diagnóstico: devuelve conteos de ServiceAreaCityMap para un país.
    Útil para comprobar que el API apunta a la BD con el dataset completo.
    """
    try:
        from .models import ServiceAreaCityMap

        cc = (country_code or '').upper()
        qs = ServiceAreaCityMap.objects.filter(country_code=cc)
        total_rows = qs.count()
        distinct_cities = qs.exclude(city_name='').values_list('city_name', flat=True).distinct().count()
        distinct_service_areas = qs.exclude(service_area='').values_list('service_area', flat=True).distinct().count()

        sample = list(
            qs.exclude(city_name='')
              .values_list('city_name', flat=True)
              .distinct()[:10]
        )

        db_conf = settings.DATABASES.get('default', {})
        db_info = {
            'engine': db_conf.get('ENGINE', ''),
            'name': db_conf.get('NAME', ''),
            'host': db_conf.get('HOST', ''),
            'port': db_conf.get('PORT', ''),
        }

        return Response({
            'success': True,
            'country_code': cc,
            'totals': {
                'rows': total_rows,
                'distinct_cities': distinct_cities,
                'distinct_service_areas': distinct_service_areas,
            },
            'sample_cities': sample,
            'db': db_info
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error en map_stats_by_country: {e}")
        return Response({'success': False, 'message': 'Error', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def test_city_service_area_mapping(request, country_code, city_name):
    """
    Endpoint de prueba para verificar el mapeo de ciudad a área de servicio
    """
    try:
        from django.db.models import Count, Q
        from .models import ServiceAreaCityMap

        # Mostrar todas las áreas de servicio para esta ciudad
        all_mappings = ServiceAreaCityMap.objects.filter(
            country_code=country_code.upper(),
            city_name__iexact=city_name
        ).values('service_area').annotate(
            total_count=Count('service_area'),
            valid_postal_count=Count(
                'postal_code_from',
                filter=Q(
                    postal_code_from__isnull=False,
                    postal_code_to__isnull=False
                ) & ~Q(postal_code_from='') & ~Q(postal_code_to='')
            ),
        ).order_by('-valid_postal_count', '-total_count')

        # Usar la función de mapeo (con fallback a None si no implementado)
        correct_area = get_city_service_area_mapping(country_code, city_name)

        return Response({
            'success': True,
            'city': city_name,
            'country': country_code.upper(),
            'correct_service_area': correct_area,
            'all_mappings': list(all_mappings),
            'message': f'Área de servicio correcta para {city_name}: {correct_area}'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error en test_city_service_area_mapping: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def debug_city_analysis(request, country_code, city_name):
    """
    Endpoint de debug para analizar en detalle cómo se escoge el service_area para una ciudad
    """
    try:
        from django.db.models import Count, Min, Max, Q
        from .models import ServiceAreaCityMap

        # Análisis detallado por service_area
        areas_analysis = ServiceAreaCityMap.objects.filter(
            country_code=country_code.upper(),
            city_name__iexact=city_name
        ).exclude(
            Q(postal_code_from='') | Q(postal_code_to='') |
            Q(postal_code_from__isnull=True) | Q(postal_code_to__isnull=True)
        ).values('service_area').annotate(
            code_count=Count('postal_code_from', distinct=True),
            min_code=Min('postal_code_from'),
            max_code=Max('postal_code_from')
        )

        debug_info = []
        best_area = None
        best_score = 0
        
        for area in areas_analysis:
            service_area = area['service_area']
            code_count = area['code_count']
            min_code = area['min_code']
            max_code = area['max_code']
            
            # Calcular score (misma lógica que la función principal)
            score = code_count
            score_breakdown = {'base_count': code_count}
            
            if code_count >= 10:
                score += 50
                score_breakdown['primary_bonus'] = 50
            
            if min_code and max_code and min_code.isdigit() and max_code.isdigit():
                try:
                    range_size = int(max_code) - int(min_code) + 1
                    density = code_count / range_size if range_size > 0 else 0
                    if density > 0.5:
                        score += 30
                        score_breakdown['continuity_bonus'] = 30
                except (ValueError, TypeError):
                    pass
            
            if min_code and max_code and len(min_code) == len(max_code):
                if len(min_code) >= 3 and min_code[:3] == max_code[:3]:
                    score += 20
                    score_breakdown['pattern_bonus'] = 20
            
            debug_info.append({
                'service_area': service_area,
                'code_count': code_count,
                'min_code': min_code,
                'max_code': max_code,
                'total_score': score,
                'score_breakdown': score_breakdown,
                'is_best': False
            })
            
            if score > best_score:
                best_score = score
                best_area = service_area
        
        # Marcar el mejor
        for info in debug_info:
            if info['service_area'] == best_area:
                info['is_best'] = True
        
        # Obtener algunos códigos de ejemplo para cada área
        for info in debug_info:
            examples = ServiceAreaCityMap.objects.filter(
                country_code=country_code.upper(),
                city_name__iexact=city_name,
                service_area=info['service_area']
            ).exclude(
                Q(postal_code_from='') | Q(postal_code_to='')
            ).values_list('postal_code_from', 'postal_code_to')[:5]
            info['postal_examples'] = list(examples)
        
        return Response({
            'success': True,
            'city': city_name,
            'country': country_code.upper(),
            'selected_service_area': best_area,
            'analysis': debug_info,
            'message': f'Análisis detallado para {city_name}. Área seleccionada: {best_area}'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def tracking_view(request):
    """Vista para tracking de envíos DHL"""
    try:
        serializer = TrackingRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        tracking_number = serializer.validated_data['tracking_number']
        
        # Usar el servicio DHL para obtener tracking
        dhl_service = DHLService()
        result = dhl_service.get_tracking(tracking_number)
        
        if result.get('success'):
            return Response({
                'success': True,
                'data': result.get('data', {}),
                'message': 'Tracking obtenido exitosamente'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result.get('message', 'Error al obtener tracking')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error en tracking_view: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def epod_view(request):
    """Vista para obtener Proof of Delivery (EPOD)"""
    try:
        serializer = EPODRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        shipment_id = serializer.validated_data['shipment_id']
        
        # Usar el servicio DHL para obtener EPOD
        dhl_service = DHLService()
        result = dhl_service.get_epod(shipment_id)
        
        if result.get('success'):
            return Response({
                'success': True,
                'data': result.get('data', {}),
                'message': 'EPOD obtenido exitosamente'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result.get('message', 'Error al obtener EPOD')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error en epod_view: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def shipment_view(request):
    """Vista para crear envíos DHL"""
    try:
        serializer = ShipmentRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # Usar el servicio DHL para crear envío
        dhl_service = DHLService()
        result = dhl_service.create_shipment(serializer.validated_data)
        
        if result.get('success'):
            return Response({
                'success': True,
                'data': result.get('data', {}),
                'message': 'Envío creado exitosamente'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'error': result.get('message', 'Error al crear envío')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error en shipment_view: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def shipments_list_view(request):
    """Vista para listar envíos"""
    try:
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
        
        shipments = Shipment.objects.filter(user=request.user).order_by('-created_at')
        paginator = Paginator(shipments, page_size)
        
        try:
            shipments_page = paginator.page(page)
        except:
            shipments_page = paginator.page(1)
        
        serializer = ShipmentSerializer(shipments_page, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': {
                'page': shipments_page.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': shipments_page.has_next(),
                'has_previous': shipments_page.has_previous()
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error en shipments_list_view: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def shipment_detail_view(request, shipment_id):
    """Vista para obtener detalle de un envío"""
    try:
        shipment = Shipment.objects.get(id=shipment_id, user=request.user)
        serializer = ShipmentSerializer(shipment)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Shipment.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Envío no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error en shipment_detail_view: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rates_history_view(request):
    """Vista para obtener historial de cotizaciones"""
    try:
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
        
        rates = RateQuote.objects.filter(user=request.user).order_by('-created_at')
        paginator = Paginator(rates, page_size)
        
        try:
            rates_page = paginator.page(page)
        except:
            rates_page = paginator.page(1)
        
        serializer = RateQuoteSerializer(rates_page, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': {
                'page': rates_page.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': rates_page.has_next(),
                'has_previous': rates_page.has_previous()
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error en rates_history_view: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def dhl_status_view(request):
    """Vista para verificar estado de servicios DHL"""
    try:
        dhl_service = DHLService()
        status_info = dhl_service.get_status()
        
        return Response({
            'success': True,
            'data': status_info,
            'message': 'Estado de servicios DHL obtenido exitosamente'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error en dhl_status_view: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_shipment_date_view(request):
    """Vista para validar fechas de envío"""
    try:
        shipment_date = request.data.get('shipment_date')
        if not shipment_date:
            return Response({
                'success': False,
                'error': 'Fecha de envío requerida'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar formato de fecha
        from datetime import datetime
        try:
            date_obj = datetime.fromisoformat(shipment_date.replace('Z', '+00:00'))
        except:
            return Response({
                'success': False,
                'error': 'Formato de fecha inválido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar que no sea fecha pasada
        now = timezone.now()
        if date_obj < now:
            return Response({
                'success': False,
                'error': 'La fecha de envío no puede ser en el pasado'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': 'Fecha de envío válida'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error en validate_shipment_date_view: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dhl_account_list(request):
    """Vista para listar cuentas DHL"""
    try:
        accounts = DHLAccount.objects.filter(created_by=request.user)
        serializer = DHLAccountSerializer(accounts, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error en dhl_account_list: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dhl_account_create(request):
    """Vista para crear cuenta DHL"""
    try:
        serializer = DHLAccountSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        account = serializer.save(created_by=request.user)
        return Response({
            'success': True,
            'data': DHLAccountSerializer(account).data,
            'message': 'Cuenta DHL creada exitosamente'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error en dhl_account_create: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def dhl_account_delete(request, account_id):
    """Vista para eliminar cuenta DHL"""
    try:
        account = DHLAccount.objects.get(id=account_id, created_by=request.user)
        account.delete()
        return Response({
            'success': True,
            'message': 'Cuenta DHL eliminada exitosamente'
        }, status=status.HTTP_200_OK)
        
    except DHLAccount.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Cuenta DHL no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error en dhl_account_delete: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dhl_account_set_default(request, account_id):
    """Vista para establecer cuenta DHL por defecto"""
    try:
        DHLAccount.objects.filter(created_by=request.user).update(is_default=False)
        account = DHLAccount.objects.get(id=account_id, created_by=request.user)
        account.is_default = True
        account.save()
        return Response({
            'success': True,
            'message': 'Cuenta DHL establecida como por defecto'
        }, status=status.HTTP_200_OK)
        
    except DHLAccount.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Cuenta DHL no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error en dhl_account_set_default: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_activities_view(request):
    """Vista para obtener actividades del usuario"""
    try:
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
        
        activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')
        paginator = Paginator(activities, page_size)
        
        try:
            activities_page = paginator.page(page)
        except:
            activities_page = paginator.page(1)
        
        serializer = UserActivitySerializer(activities_page, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': {
                'page': activities_page.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': activities_page.has_next(),
                'has_previous': activities_page.has_previous()
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error en user_activities_view: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_activity_stats_view(request):
    """Vista para obtener estadísticas de actividades del usuario"""
    try:
        # Estadísticas básicas
        total_activities = UserActivity.objects.filter(user=request.user).count()
        
        # Actividades por tipo
        activities_by_type = UserActivity.objects.filter(user=request.user).values('activity_type').annotate(
            count=Count('activity_type')
        ).order_by('-count')
        
        # Actividades recientes (últimos 7 días)
        seven_days_ago = timezone.now() - timezone.timedelta(days=7)
        recent_activities = UserActivity.objects.filter(
            user=request.user, 
            timestamp__gte=seven_days_ago
        ).count()
        
        return Response({
            'success': True,
            'data': {
                'total_activities': total_activities,
                'activities_by_type': list(activities_by_type),
                'recent_activities': recent_activities
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error en user_activity_stats_view: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_postal_codes_by_location(request, country_code):
    """Vista para obtener códigos postales por ubicación"""
    try:
        city_name = request.GET.get('city_name', '').strip()
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 1000)
        limit = request.GET.get('limit', 20000)
        
        if not city_name:
            return Response({
                'success': False,
                'error': 'Nombre de ciudad requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Importar el modelo ServiceAreaCityMap
        from .models import ServiceAreaCityMap
        
        # Buscar códigos postales para la ciudad
        postal_codes = ServiceAreaCityMap.objects.filter(
            country_code=country_code.upper(),
            city_name__iexact=city_name
        ).exclude(
            Q(postal_code_from='') | Q(postal_code_to='')
        ).values(
            'postal_code_from', 
            'postal_code_to', 
            'service_area'
        ).distinct()[:int(limit)]
        
        # Convertir a lista y paginar
        postal_list = list(postal_codes)
        paginator = Paginator(postal_list, page_size)
        
        try:
            postal_page = paginator.page(page)
        except:
            postal_page = paginator.page(1)
        
        return Response({
            'success': True,
            'data': list(postal_page),
            'pagination': {
                'page': postal_page.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': postal_page.has_next(),
                'has_previous': postal_page.has_previous()
            },
            'city': city_name,
            'country': country_code.upper()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error en get_postal_codes_by_location: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_city_service_area_mapping(request, country_code, city_name):
    """Vista para probar el mapeo de ciudad a área de servicio"""
    try:
        # Importar el modelo ServiceAreaCityMap
        from .models import ServiceAreaCityMap
        
        # Buscar mapeos para la ciudad
        mappings = ServiceAreaCityMap.objects.filter(
            country_code=country_code.upper(),
            city_name__iexact=city_name
        ).values(
            'service_area',
            'postal_code_from',
            'postal_code_to'
        )
        
        # Contar códigos postales por área de servicio
        area_counts = {}
        for mapping in mappings:
            area = mapping['service_area']
            if area not in area_counts:
                area_counts[area] = 0
            # Contar códigos postales en el rango
            if mapping['postal_code_from'] and mapping['postal_code_to']:
                try:
                    from_code = int(mapping['postal_code_from'])
                    to_code = int(mapping['postal_code_to'])
                    area_counts[area] += (to_code - from_code + 1)
                except (ValueError, TypeError):
                    area_counts[area] += 1
        
        return Response({
            'success': True,
            'data': {
                'city': city_name,
                'country': country_code.upper(),
                'total_mappings': len(mappings),
                'area_counts': area_counts,
                'mappings': list(mappings[:10])  # Solo primeros 10 para debug
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error en test_city_service_area_mapping: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)