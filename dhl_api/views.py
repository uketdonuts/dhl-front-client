from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
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
from .models import DHLAccount
from .serializers import (
    DHLAccountSerializer,
    LoginSerializer,
    RateRequestSerializer,
    EPODRequestSerializer,
    ShipmentRequestSerializer,
    ShipmentSerializer,
    RateQuoteSerializer,
    TrackingRequestSerializer
)
from .services import DHLService
from .models import Shipment, RateQuote
from faker import Faker
from django.conf import settings
import os

logger = logging.getLogger(__name__)
fake = Faker()


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
        "message": "Datos inválidos"
    }
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
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
            return Response({
                'success': False,
                'message': 'Credenciales inválidas'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response({
        'success': False,
        'message': 'Datos inválidos'
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
        "message": "Error descriptivo",
        "error_type": "validation_error|internal_error",
        "request_timestamp": "2025-07-07T10:30:00"
    }
    
    **Notas:**
    - Las cotizaciones exitosas se guardan automáticamente en la base de datos
    - Se registra cada solicitud en los logs para auditoría
    - Los errores se manejan de forma consistente con metadatos
    """
    serializer = RateRequestSerializer(data=request.data)
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
            result = dhl_service.get_rate(
                origin=serializer.validated_data['origin'],
                destination=serializer.validated_data['destination'],
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
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error en rate_view: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error interno: {str(e)}',
                'error_type': 'internal_error',
                'request_timestamp': datetime.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'message': 'Datos inválidos para cotización',
        'error_type': 'validation_error',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def tracking_view(request):
    """
    Endpoint para rastrear envíos DHL usando el número de tracking.
    """
    try:
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
                'message': 'Error al crear cuenta DHL por defecto. Contacta al administrador.',
                'error_code': 'DB_ERROR',
                'request_timestamp': datetime.now(),
                'requested_by': username
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if dhl_account:
            logger.info(f"Using DHL account: {dhl_account.account_name} ({dhl_account.account_number})")
        else:
            logger.info("Using default DHL configuration from settings")
        
        # Usar siempre el servicio real
        logger.info(f"Using real DHL service for tracking number {tracking_number}")
        
        try:
            dhl_service = DHLService(
                username=settings.DHL_USERNAME,
                password=settings.DHL_PASSWORD,
                base_url=settings.DHL_BASE_URL,
                environment=settings.DHL_ENVIRONMENT
            )
            
            # Obtener información de tracking
            tracking_info = dhl_service.get_tracking(tracking_number)
            logger.info(f"DHL service response: {tracking_info}")
            
        except Exception as e:
            logger.error(f"Error with real DHL service: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error interno: {str(e)}',
                'error_type': 'internal_error',
                'request_timestamp': datetime.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        response_data = {
            'success': tracking_info.get('success', False),
            'tracking_info': tracking_info.get('tracking_info', {}),
            'events': tracking_info.get('events', []),
            'piece_details': tracking_info.get('piece_details', []),
            'total_events': tracking_info.get('total_events', 0),
            'total_pieces': tracking_info.get('total_pieces', 0),
            'message': tracking_info.get('message', ''),
            'request_timestamp': datetime.now(),
            'tracking_number': tracking_number,
            'requested_by': request.user.username,
            'is_simulated': tracking_info.get('is_simulated', False),
            'simulation_reason': tracking_info.get('simulation_reason', None)
        }
        
        if not tracking_info.get('success'):
            logger.warning(f"Tracking failed for {tracking_number}: {tracking_info.get('message')}")
            response_data.update({
                'error_code': tracking_info.get('error_code', 'TRACKING_ERROR'),
                'suggestion': tracking_info.get('suggestion', 'Reintentar más tarde'),
                'raw_response': tracking_info.get('raw_response', '')
            })
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.info(f"Tracking successful for {tracking_number}")
        return Response(response_data)
        
    except Exception as e:
        logger.exception(f"Error in tracking_view: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error interno del servidor',
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
    - tracking_number (str): Número de tracking DHL
    - shipment_date (str): Fecha de envío en formato YYYY-MM-DD
    
    **Respuesta exitosa (200):**
    {
        "success": true,
        "epod_data": {
            "tracking_number": "1234567890",
            "delivery_date": "2025-07-08",
            "delivery_time": "14:30:00",
            "signed_by": "John Doe",
            "delivery_location": "Front Door",
            "proof_of_delivery": "data:application/pdf;base64,JVBERi0xLjQKJd...",
            "delivery_notes": "Package delivered successfully"
        },
        "request_timestamp": "2025-07-07T10:30:00",
        "requested_by": "username"
    }
    
    **Respuesta de error (400/500):**
    {
        "success": false,
        "message": "Error descriptivo",
        "error_type": "validation_error|epod_error|internal_error",
        "request_timestamp": "2025-07-07T10:30:00"
    }
    
    **Notas:**
    - El ePOD solo está disponible para envíos entregados
    - Se registra cada consulta en los logs para auditoría
    - Los errores se manejan de forma consistente con metadatos
    """
    serializer = EPODRequestSerializer(data=request.data)
    if serializer.is_valid():
        try:
            dhl_service = DHLService(
                username=settings.DHL_USERNAME,
                password=settings.DHL_PASSWORD,
                base_url=settings.DHL_BASE_URL,
                environment=settings.DHL_ENVIRONMENT
            )
            result = dhl_service.get_ePOD(
                shipment_id=serializer.validated_data['shipment_id']
            )
            
            # Agregar metadatos adicionales
            result['request_timestamp'] = datetime.now().isoformat()
            result['shipment_id'] = serializer.validated_data['shipment_id']
            result['requested_by'] = request.user.username
            
            # Log del resultado para debugging
            logger.info(f"ePOD request for shipment {serializer.validated_data['shipment_id']} by {request.user.username}: {result.get('success', False)}")
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error en epod_view: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error interno: {str(e)}',
                'error_type': 'internal_error',
                'request_timestamp': datetime.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'message': 'ID de envío requerido',
        'error_type': 'validation_error',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


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
        "message": "Error descriptivo",
        "error_type": "validation_error|shipment_error|internal_error",
        "request_timestamp": "2025-07-07T10:30:00"
    }
    
    **Notas:**
    - Los envíos exitosos se guardan automáticamente en la base de datos
    - Se registra cada solicitud en los logs para auditoría
    - Los errores se manejan de forma consistente con metadatos
    """
    serializer = ShipmentRequestSerializer(data=request.data)
    if serializer.is_valid():
        try:
            dhl_service = DHLService(
                username=settings.DHL_USERNAME,
                password=settings.DHL_PASSWORD,
                base_url=settings.DHL_BASE_URL,
                environment=settings.DHL_ENVIRONMENT
            )
            result = dhl_service.create_shipment(
                shipment_data=serializer.validated_data
            )
            
            # Agregar metadatos adicionales
            result['request_timestamp'] = datetime.now().isoformat()
            result['requested_by'] = request.user.username
            
            # Guardar envío en la base de datos si es exitoso
            if result.get('success'):
                try:
                    shipment_data = serializer.validated_data
                    shipper = shipment_data['shipper']
                    recipient = shipment_data['recipient']
                    package = shipment_data['package']
                    
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
                    
                except Exception as db_error:
                    logger.warning(f"Error saving shipment to DB: {str(db_error)}")
                    # No fallar la request si hay error en DB, pero informar
                    result['db_warning'] = 'Shipment created but not saved to database'
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error en shipment_view: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error interno: {str(e)}',
                'error_type': 'internal_error',
                'request_timestamp': datetime.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'message': 'Datos inválidos para crear envío',
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
            'message': f'Error interno: {str(e)}'
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
            'message': f'Error interno: {str(e)}'
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
            'message': f'Error interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_dhl_credentials_view(request):
    """
    Endpoint para probar las credenciales DHL en tiempo real.
    
    Este endpoint permite probar las credenciales DHL configuradas realizando
    una llamada real a la API de DHL para verificar que las credenciales
    son válidas y que los servicios están disponibles.
    
    **Método HTTP:** POST
    **Permisos:** Usuario autenticado (IsAuthenticated)
    
    **Parámetros de entrada (JSON):**
    - service_type (str, opcional): Tipo de servicio a probar
        - "rates": Probar servicio de cotización
        - "tracking": Probar servicio de seguimiento
        - "epod": Probar servicio de ePOD (default)
        - "shipment": Probar servicio de creación de envíos
        - "all": Probar todos los servicios
    - test_data (dict, opcional): Datos específicos para la prueba
    
    **Respuesta exitosa (200):**
    {
        "success": true,
        "credential_test": {
            "test_timestamp": "2025-07-07T10:30:00",
            "service_type": "epod",
            "credentials_valid": true,
            "response_time": 1.25,
            "service_available": true,
            "test_details": {
                "request_sent": true,
                "response_received": true,
                "authentication_successful": true,
                "service_functional": true
            }
        },
        "request_timestamp": "2025-07-07T10:30:00",
        "requested_by": "username"
    }
    
    **Respuesta de error (400/500):**
    {
        "success": false,
        "message": "Error descriptivo",
        "error_type": "validation_error|credential_error|internal_error",
        "request_timestamp": "2025-07-07T10:30:00"
    }
    
    **Notas:**
    - Esta función realiza llamadas reales a la API de DHL
    - Se registra cada prueba en los logs para auditoría
    - Los errores se manejan de forma consistente con metadatos
    """
    try:
        # Obtener el tipo de servicio a probar (por defecto ePOD)
        service_type = request.data.get('service_type', 'epod')
        test_data = request.data.get('test_data', {})
        
        dhl_service = DHLService(
            username=settings.DHL_USERNAME,
            password=settings.DHL_PASSWORD,
            base_url=settings.DHL_BASE_URL,
            environment=settings.DHL_ENVIRONMENT
        )
        
        result = {
            'request_timestamp': datetime.now().isoformat(),
            'requested_by': request.user.username,
            'service_type': service_type,
            'credentials_used': {
                'username': settings.DHL_USERNAME,
                'base_url': settings.DHL_BASE_URL,
                'environment': settings.DHL_ENVIRONMENT
            }
        }
        
        if service_type == 'epod':
            # Probar ePOD con ID de prueba
            shipment_id = test_data.get('shipment_id', '2287013540')
            test_result = dhl_service.get_ePOD(shipment_id)
            result.update(test_result)
            result['test_parameters'] = {'shipment_id': shipment_id}
            
        elif service_type == 'tracking':
            # Probar tracking con número de prueba
            tracking_number = test_data.get('tracking_number', '1234567890')
            test_result = dhl_service.get_tracking(tracking_number)
            result.update(test_result)
            result['test_parameters'] = {'tracking_number': tracking_number}
            
        elif service_type == 'rate':
            # Probar cotización con datos de prueba
            origin = test_data.get('origin', {
                'postal_code': '12345',
                'city': 'Test City',
                'country': 'US',
                'state': 'CA'
            })
            destination = test_data.get('destination', {
                'postal_code': '54321',
                'city': 'Destination City',
                'country': 'US',
                'state': 'NY'
            })
            weight = test_data.get('weight', 1.5)
            dimensions = test_data.get('dimensions', {
                'length': 10,
                'width': 10,
                'height': 10
            })
            
            test_result = dhl_service.get_rate(origin, destination, weight, dimensions)
            result.update(test_result)
            result['test_parameters'] = {
                'origin': origin,
                'destination': destination,
                'weight': weight,
                'dimensions': dimensions
            }
            
        elif service_type == 'shipment':
            # Probar creación de envío con datos de prueba
            shipment_data = test_data if test_data else {
                'shipper': {
                    'name': 'Test Shipper',
                    'company': 'Test Company',
                    'phone': '1234567890',
                    'email': 'test@example.com',
                    'address': '123 Test St',
                    'city': 'Test City',
                    'state': 'CA',
                    'postalCode': '12345',
                    'country': 'US'
                },
                'recipient': {
                    'name': 'Test Recipient',
                    'company': 'Recipient Company',
                    'phone': '0987654321',
                    'email': 'recipient@example.com',
                    'address': '456 Recipient St',
                    'city': 'Recipient City',
                    'state': 'NY',
                    'postalCode': '54321',
                    'country': 'US'
                },
                'package': {
                    'weight': 1.5,
                    'length': 10,
                    'width': 10,
                    'height': 10,
                    'description': 'Test Package',
                    'value': 100,
                    'currency': 'USD'
                },
                'service': 'P',
                'payment': 'S'
            }
            
            test_result = dhl_service.create_shipment(shipment_data)
            result.update(test_result)
            result['test_parameters'] = shipment_data
            
        else:
            return Response({
                'success': False,
                'message': 'Tipo de servicio no válido. Opciones: epod, tracking, rate, shipment',
                'error_type': 'validation_error'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Log del resultado para debugging
        logger.info(f"DHL credentials test for {service_type} by {request.user.username}: {result.get('success', False)}")
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Error en test_dhl_credentials_view: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error interno: {str(e)}',
            'error_type': 'internal_error',
            'request_timestamp': datetime.now().isoformat()
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
                "test_credentials": "/api/test-dhl-credentials/",
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
        "message": "Error descriptivo",
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
            'message': f'Error interno: {str(e)}',
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
        "message": "Error descriptivo",
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
            'message': f'Error interno: {str(e)}',
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
                'message': f'Error al validar la cuenta: {str(e)}',
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