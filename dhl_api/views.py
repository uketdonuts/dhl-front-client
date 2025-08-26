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
from django.conf import settings
from decimal import Decimal, ROUND_HALF_UP

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
        
        
        # Permitir incluir la respuesta cruda de DHL si el cliente lo solicita
        include_raw = False
        try:
            include_raw = bool(request.data.get('include_raw', False))
        except Exception:
            include_raw = False

        # Construir respuesta rica con los campos clave del tracking DHL
        shipment_info = tracking_info.get('shipment_info', {})
        response_data = {
            'success': tracking_info.get('success', False),
            'status': tracking_info.get('status', shipment_info.get('status_description')),  # Estado legible
            'tracking_number': tracking_info.get('tracking_number', tracking_number),
            'dhl_tracking_url': f"https://www.dhl.com/global-en/home/tracking/tracking-express.html?submit=1&tracking-id={tracking_number}",

            # Información principal del envío
            'tracking_info': shipment_info,

            # Eventos y piezas (listas)
            'events': tracking_info.get('events', []),
            'piece_details': tracking_info.get('piece_details', []),

            # Contadores (compatibilidad y claridad)
            'total_events': tracking_info.get('total_events', 0),
            'total_pieces': tracking_info.get('total_pieces', 0),
            'events_count': tracking_info.get('total_events', 0),
            'pieces_count': tracking_info.get('total_pieces', 0),

            # Info adicional resumida
            'additional_info': tracking_info.get('additional_info', {}),
            'message': tracking_info.get('message', ''),
            'request_timestamp': datetime.now(),
            'requested_by': request.user.username if request.user.is_authenticated else 'anonymous'
        }

        # Aliases numéricos para compatibilidad con visores de logs simples
        response_data['pieces'] = response_data.get('total_pieces', 0)
        response_data['events_total'] = response_data.get('total_events', 0)

        # Resumen compacto útil para auditoría/log
        response_data['summary'] = {
            'status': response_data.get('status'),
            'status_code': shipment_info.get('status'),
            'events': response_data.get('total_events', 0),
            'pieces': response_data.get('total_pieces', 0),
            'total_weight': shipment_info.get('total_weight'),
            'weight_unit': shipment_info.get('weight_unit'),
            'origin': shipment_info.get('origin'),
            'destination': shipment_info.get('destination'),
            'service_type': shipment_info.get('service_type', shipment_info.get('service')),
        }

        # Resumen de pesos clave para cotización: total envío, suma de piezas y pieza más pesada
        try:
            def _to_decimal(v):
                """Convierte a Decimal seguro; ignora vacíos, NaN e infinitos."""
                if v is None:
                    return None
                # tratar strings vacíos o 'NaN'
                if isinstance(v, str) and not v.strip():
                    return None
                try:
                    d = Decimal(str(v))
                except Exception:
                    return None
                # Ignorar no finitos (NaN, Inf)
                try:
                    if not d.is_finite():
                        return None
                except Exception:
                    return None
                return d

            def _round_2(v):
                return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            unit = shipment_info.get('weight_unit') or 'KG'
            shipment_total = _to_decimal(shipment_info.get('total_weight'))

            pieces = tracking_info.get('piece_details', []) or []
            piece_weights = []
            for p in pieces:
                w = None
                # Prioridad ampliada: selected > actual(reweigh) > actual > declared > peso_declarado > weight
                wi = p.get('weight_info') or {}

                # Helper para extraer valor desde dict o número
                def _val(x):
                    if isinstance(x, dict):
                        return _to_decimal(x.get('value') if 'value' in x else x.get('amount'))
                    return _to_decimal(x)

                preferred_keys_weightinfo = (
                    'selected_weight',
                    'actual_weight_reweigh',
                    'actual_weight',
                    'declared_weight',
                    'peso_declarado',
                    'repesaje',
                    'weight',
                )
                preferred_keys_piece = preferred_keys_weightinfo

                for key in preferred_keys_weightinfo:
                    if key in wi and w is None:
                        w = _val(wi.get(key))
                if w is None:
                    for key in preferred_keys_piece:
                        if key in p and w is None:
                            w = _val(p.get(key))
                if w is not None:
                    piece_weights.append(w)

            sum_pieces = _round_2(sum(piece_weights, Decimal('0'))) if piece_weights else Decimal('0.00')
            max_piece = _round_2(max(piece_weights)) if piece_weights else Decimal('0.00')
            if shipment_total is not None:
                shipment_total = _round_2(shipment_total)

            candidates = [c for c in (shipment_total, sum_pieces, max_piece) if c is not None]
            highest = _round_2(max(candidates)) if candidates else None

            response_data['weights_summary'] = {
                'shipment_total': float(shipment_total) if shipment_total is not None else None,
                'sum_pieces': float(sum_pieces),
                'max_piece': float(max_piece),
                'unit': unit,
                'highest_for_quote': float(highest) if highest is not None else None
            }

            # Tres sumas estilo SOAP: declarado, repesaje (actual) y volumétrico (round-then-sum)
            sum_declared = Decimal('0')
            sum_actual = Decimal('0')
            sum_dimensional = Decimal('0')

            for p in pieces:
                wi = p.get('weight_info') or {}
                # Declarado: declared_weight | peso_declarado
                dec = (
                    wi.get('declared_weight',
                           p.get('declared_weight', p.get('peso_declarado')))
                )
                # Repesaje/Actual: actual_weight_reweigh | actual_weight | repesaje
                act = (
                    wi.get('actual_weight_reweigh',
                           wi.get('actual_weight',
                                  p.get('actual_weight', p.get('repesaje'))))
                )

                # Dimensional provisto por DHL si existe
                dim = None
                if 'dhl_dimensional_weight' in wi:
                    dim = wi.get('dhl_dimensional_weight')
                elif 'dhl_dimensional_weight' in p:
                    dim = p.get('dhl_dimensional_weight')

                d_dec = _to_decimal(dec)
                d_act = _to_decimal(act)
                d_dim = _to_decimal(dim)

                if d_dec is not None:
                    sum_declared += _round_2(d_dec)
                if d_act is not None:
                    sum_actual += _round_2(d_act)
                if d_dim is not None:
                    sum_dimensional += _round_2(d_dim)

            # Redondeo final a 2 decimales
            sum_declared = _round_2(sum_declared)
            sum_actual = _round_2(sum_actual)
            sum_dimensional = _round_2(sum_dimensional)

            soap_candidates = [c for c in (sum_declared, sum_actual, sum_dimensional) if c is not None]
            soap_highest = _round_2(max(soap_candidates)) if soap_candidates else None

            response_data['weights_three_sums'] = {
                'sum_declared': float(sum_declared),
                'sum_actual': float(sum_actual),
                'sum_dimensional': float(sum_dimensional),
                'unit': unit,
                'highest_for_quote': float(soap_highest) if soap_highest is not None else None
            }

            # Pesos por pieza: declarado, actual (repesaje), volumétrico
            weights_by_piece = []
            for idx, p in enumerate(pieces):
                wi = p.get('weight_info') or {}
                # Declarado con fallback a español
                dec = _to_decimal(
                    wi.get('declared_weight', p.get('declared_weight', p.get('peso_declarado')))
                )
                # Actual/repesaje con alias
                act = _to_decimal(
                    wi.get('actual_weight_reweigh', wi.get('actual_weight', p.get('actual_weight', p.get('repesaje'))))
                )
                dim = None
                if 'dhl_dimensional_weight' in wi:
                    dim = _to_decimal(wi.get('dhl_dimensional_weight'))
                elif 'dhl_dimensional_weight' in p:
                    dim = _to_decimal(p.get('dhl_dimensional_weight'))

                item = {
                    'index': idx,
                    'piece_id': p.get('piece_id') or p.get('pieceNumber') or p.get('id') or None,
                    'declared': float(_round_2(dec)) if dec is not None else None,
                    'actual': float(_round_2(act)) if act is not None else None,
                    'dimensional': float(_round_2(dim)) if dim is not None else None,
                    'unit': unit,
                }
                weights_by_piece.append(item)

            response_data['weights_by_piece'] = weights_by_piece
        except Exception as _we:
            # Siempre incluir las claves aunque falle el cálculo para facilitar el frontend/debug
            logger.warning(f"weights computation failed, returning defaults: {_we}")
            unit = (tracking_info.get('shipment_info') or {}).get('weight_unit') or 'KG'
            response_data['weights_summary'] = {
                'shipment_total': None,
                'sum_pieces': 0.0,
                'max_piece': 0.0,
                'unit': unit,
                'highest_for_quote': None,
            }
            response_data['weights_three_sums'] = {
                'sum_declared': 0.0,
                'sum_actual': 0.0,
                'sum_dimensional': 0.0,
                'unit': unit,
                'highest_for_quote': None,
            }
            response_data['weights_by_piece'] = []

        # Incluir payload crudo de DHL según bandera
        if include_raw:
            # raw_data del parser + metadatos HTTP si están disponibles
            if 'raw_data' in tracking_info:
                response_data['raw_data'] = tracking_info['raw_data']
            if 'http_status' in tracking_info:
                response_data['http_status'] = tracking_info['http_status']
            if 'response_headers' in tracking_info:
                response_data['response_headers'] = tracking_info['response_headers']

        # Reglas de negocio: si DHL no devuelve peso volumétrico, requerir cuenta para cotizar con este peso
        try:
            pieces_for_flags = tracking_info.get('piece_details', []) or []
            shipment_info_for_flags = tracking_info.get('shipment_info', {}) or {}
            # ¿Hay peso volumétrico oficial de DHL?
            dhl_total_dim = shipment_info_for_flags.get('dhl_total_dimensional_weight')
            has_dhl_total_dim = bool(dhl_total_dim) and float(dhl_total_dim) > 0
            has_piece_dhl_dim = any(
                float(p.get('dhl_dimensional_weight') or (p.get('weight_info') or {}).get('dhl_dimensional_weight') or 0) > 0
                for p in pieces_for_flags
            )
            volumetric_from_dhl = bool(has_dhl_total_dim or has_piece_dhl_dim)

            # ¿Hay pesos declarado y repesaje presentes en al menos una pieza?
            declared_present = any(
                (p.get('peso_declarado') is not None) or ((p.get('weight_info') or {}).get('declared_weight') is not None)
                for p in pieces_for_flags
            )
            actual_present = any(
                (p.get('repesaje') is not None) or ((p.get('weight_info') or {}).get('actual_weight_reweigh') is not None) or ((p.get('weight_info') or {}).get('actual_weight') is not None)
                for p in pieces_for_flags
            )

            # Regla dada por negocio: si NO hay volumétrico oficial, debemos pedir crear/usar cuenta antes de cotizar con ese peso
            needs_account_for_quote = not volumetric_from_dhl

            # Peso sugerido para cotización (ya calculado arriba)
            suggested = None
            try:
                w_summary = response_data.get('weights_summary') or {}
                w_three = response_data.get('weights_three_sums') or {}
                cands = [
                    w_summary.get('highest_for_quote'),
                    w_three.get('highest_for_quote'),
                ]
                cands = [float(x) for x in cands if x is not None]
                suggested = max(cands) if cands else None
            except Exception:
                suggested = None

            response_data['account_requirements'] = {
                'volumetric_from_dhl': volumetric_from_dhl,
                'declared_present': declared_present,
                'actual_present': actual_present,
                'needs_account_for_quote': needs_account_for_quote,
                'reason': None if volumetric_from_dhl else 'missing_dhl_volumetric_weight',
                'cta': {
                    'action': 'create_account',
                    'endpoint': '/api/accounts/create/'
                }
            }
            response_data['quote_with_weight'] = {
                'allowed': not needs_account_for_quote,
                'blocked_reason': None if not needs_account_for_quote else 'missing_dhl_volumetric_weight',
                'suggested_weight': suggested,
                'unit': (response_data.get('weights_summary') or {}).get('unit') or 'kg'
            }
        except Exception as _af:
            logger.debug(f"account gating flags skipped: {_af}")

        # Modo "raw_only": devolver únicamente la respuesta cruda de DHL (útil para debugging)
        try:
            raw_only = bool(request.data.get('raw_only', False))
        except Exception:
            raw_only = False
        if raw_only:
            raw_block = {
                'success': tracking_info.get('success', False),
                'http_status': tracking_info.get('http_status'),
                'response_headers': tracking_info.get('response_headers'),
                'raw_data': tracking_info.get('raw_data')
            }
            return Response(raw_block)
        
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
        # Registrar actividad con payloads (success) enriquecidos para visibilidad en UI/logs
        try:
            if request.user.is_authenticated:
                # Resumen compacto
                _si = shipment_info
                _events = tracking_info.get('events', [])
                _last_event = _events[-1] if _events else {}
                _summary = {
                    'status': response_data.get('status'),
                    'total_weight': _si.get('total_weight'),
                    'weight_unit': _si.get('weight_unit'),
                    'origin': _si.get('origin'),
                    'destination': _si.get('destination'),
                    'service_type': _si.get('service_type', _si.get('service')),
                    'last_event': {
                        'description': _last_event.get('description'),
                        'date': _last_event.get('date'),
                        'time': _last_event.get('time'),
                        'location': _last_event.get('location'),
                        'type_code': _last_event.get('type_code')
                    } if _last_event else None,
                    'tracking_url': response_data.get('dhl_tracking_url')
                }

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
                            'pieces': tracking_info.get('total_pieces', 0),
                            'status': _summary['status'],
                            'total_weight': _summary['total_weight'],
                            'weight_unit': _summary['weight_unit'],
                            'origin': _summary['origin'],
                            'destination': _summary['destination'],
                            'service_type': _summary['service_type'],
                            'last_event': _summary['last_event'],
                            'tracking_url': _summary['tracking_url']
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
        from .serializers import ServiceAreaSerializer
        from django.db.models import Q

        state_code = request.GET.get('state_code')
        city_name = request.GET.get('city_name')

        cc = country_code.upper()
        sc = state_code.upper() if state_code else None

        qs = ServiceAreaCityMap.objects.filter(country_code=cc)
        if sc and cc != 'CA':
            qs = qs.filter(state_code=sc)
        if city_name:
            qs = qs.filter(Q(city_name__iexact=city_name) | Q(display_name__icontains=city_name))

        codes = (
            qs.exclude(service_area__isnull=True)
              .exclude(service_area='')
              .values('service_area', 'display_name')
              .distinct()
        )

        enriched = []
        seen = set()
        for row in codes:
            code = row.get('service_area')
            disp = row.get('display_name') or code
            if not code or code in seen:
                continue
            seen.add(code)
            enriched.append({'service_area': code, 'display_name': disp})

        # Asegurar unicidad de display_name
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


def get_city_service_area_mapping(country_code, city_name):
    """
    Obtiene el área de servicio correcta para una ciudad específica basado en:
    1. Análisis de densidad y continuidad de códigos postales
    2. El área de servicio que tenga más códigos postales válidos (no vacíos)
    3. Si hay empate, el que tenga códigos postales con patrones más consistentes
    """
    from django.db.models import Count, Min, Max, Q
    from .models import ServiceAreaCityMap
    
    # Análisis avanzado por densidad de códigos postales
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
    
    if not areas_analysis.exists():
        # Si no hay códigos postales, usar el área más común sin filtrar
        fallback_mapping = ServiceAreaCityMap.objects.filter(
            country_code=country_code.upper(),
            city_name__iexact=city_name
        ).values('service_area').annotate(
            count=Count('service_area')
        ).order_by('-count').first()
        
        return fallback_mapping['service_area'] if fallback_mapping else None
    
    # Calcular score de calidad para cada service_area
    best_area = None
    best_score = 0
    
    for area in areas_analysis:
        service_area = area['service_area']
        code_count = area['code_count']
        min_code = area['min_code']
        max_code = area['max_code']
        
        # Score basado en cantidad de códigos postales
        score = code_count
        
        # Bonus para áreas con más de 10 códigos (consideradas primarias)
        if code_count >= 10:
            score += 50
        
        # Bonus por continuidad de códigos postales (rango compacto)
        if min_code and max_code and min_code.isdigit() and max_code.isdigit():
            try:
                range_size = int(max_code) - int(min_code) + 1
                density = code_count / range_size if range_size > 0 else 0
                if density > 0.5:  # Más del 50% del rango está cubierto
                    score += 30
            except (ValueError, TypeError):
                pass
        
        # Bonus por códigos con patrones consistentes (mismo prefijo)
        if min_code and max_code and len(min_code) == len(max_code):
            if len(min_code) >= 3 and min_code[:3] == max_code[:3]:
                score += 20  # Mismo prefijo de 3 dígitos
        
        if score > best_score:
            best_score = score
            best_area = service_area
    
    return best_area if best_area else areas_analysis.first()['service_area']


@api_view(['GET'])
@permission_classes([AllowAny])
@cache_page(60 * 15)  # Cache por 15 minutos
def get_postal_codes_by_location(request, country_code):
    try:
        from .models import ServiceAreaCityMap, ServiceZone
        from .serializers import PostalCodeSerializer
        from django.db.models import Q, Count

        state_code = request.GET.get('state_code')
        city_name = request.GET.get('city_name')
        service_area = request.GET.get('service_area')
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 100)), 1000)
        limit = int(request.GET.get('limit', 5000))

        cc = country_code.upper()
        sc = state_code.upper() if state_code else None
        sa = service_area.upper() if service_area else None

        qs = ServiceAreaCityMap.objects.filter(country_code=cc)
        if sc and cc != 'CA':
            qs = qs.filter(state_code=sc)
        
        # Filtrado mejorado por ciudad con validación de área de servicio
        if city_name:
            # Buscar el área de servicio correcta para esta ciudad
            correct_service_area = get_city_service_area_mapping(cc, city_name)
            if correct_service_area:
                # Filtrar por ciudad Y área de servicio correcta
                qs = qs.filter(
                    Q(city_name__iexact=city_name) | Q(display_name__icontains=city_name),
                    service_area=correct_service_area
                )
            else:
                # Si no hay mapeo claro, usar filtro tradicional pero con advertencia
                qs = qs.filter(Q(city_name__iexact=city_name) | Q(display_name__icontains=city_name))
        
        if sa:
            qs = qs.filter(service_area=sa)
        qs = qs.exclude(postal_code_from='').exclude(postal_code_to='')

        total = qs.count()
        total_limited = min(total, limit)
        total_pages = (total_limited + page_size - 1) // page_size
        page = max(1, min(page, total_pages or 1))
        start = (page - 1) * page_size
        end = start + page_size

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
            # Para ESD, aplicar el mismo filtro de área de servicio si se especificó ciudad
            if city_name and not sa:
                correct_service_area = get_city_service_area_mapping(cc, city_name)
                esd_qs = ServiceZone.get_postal_codes_by_location(cc, sc, city_name, correct_service_area)
            else:
                esd_qs = ServiceZone.get_postal_codes_by_location(cc, sc, city_name, sa)
            # Convertir a lista de dicts similares
            esd_list = list(esd_qs)
        except Exception:
            esd_list = []

        # Unificar y deduplicar por (from,to,service_area)
        seen = set()
        unified = []
        
        # Obtener el área de servicio correcta para validación adicional
        city_correct_area = None
        if city_name:
            city_correct_area = get_city_service_area_mapping(cc, city_name)
        
        for item in data_all + esd_list:
            f = (item.get('postal_code_from') or '').strip()
            t = (item.get('postal_code_to') or '').strip()
            s = (item.get('service_area') or '').strip().upper()
            key = (f, t, s)
            if not f or not t:
                continue
            if key in seen:
                continue
            
            # Validación adicional: si se especificó ciudad, solo incluir códigos del área correcta
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

        # Debug info si se solicita
        debug_info = {}
        if request.GET.get('debug') == '1' and city_name:
            correct_area = get_city_service_area_mapping(cc, city_name)
            debug_info = {
                'detected_service_area': correct_area,
                'filter_applied': bool(correct_area),
                'total_before_filter': len(data_all + esd_list),
                'total_after_filter': len(unified)
            }

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
                'service_area': sa
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
            valid_postal_count=Count('postal_code_from', filter=Q(
                postal_code_from__isnull=False, 
                postal_code_to__isnull=False
            ) & ~Q(postal_code_from='') & ~Q(postal_code_to=''))
        ).order_by('-valid_postal_count', '-total_count')
        
        # Usar la función de mapeo
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
                    score_breakdown['density'] = density
                    score_breakdown['range_size'] = range_size
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