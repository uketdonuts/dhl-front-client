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

from .serializers import (
    RateRequestSerializer, TrackingRequestSerializer, EPODRequestSerializer,
    ShipmentRequestSerializer, LoginSerializer, TestDataSerializer,
    ShipmentSerializer, RateQuoteSerializer
)
from .services import DHLService
from .models import Shipment, RateQuote
from faker import Faker
from django.conf import settings

logger = logging.getLogger(__name__)
fake = Faker()


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Endpoint para autenticación de usuarios"""
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
    """Endpoint para cotización de tarifas"""
    serializer = RateRequestSerializer(data=request.data)
    if serializer.is_valid():
        try:
            dhl_service = DHLService(
                username=settings.DHL_USERNAME,
                password=settings.DHL_PASSWORD,
                base_url=settings.DHL_BASE_URL,
                environment=settings.DHL_ENVIRONMENT
            )
            result = dhl_service.get_rate(
                origin=serializer.validated_data['origin'],
                destination=serializer.validated_data['destination'],
                weight=serializer.validated_data['weight'],
                dimensions=serializer.validated_data['dimensions']
            )
            
            # Guardar cotización en la base de datos
            if result.get('success') and result.get('rates'):
                for rate in result['rates']:
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
                        service_name=rate['service_name'],
                        service_code=rate['service_code'],
                        total_price=rate['total_charge'],
                        currency=rate['currency'],
                        delivery_time=rate['delivery_time'],
                        created_by=request.user
                    )
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error en rate_view: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'message': 'Datos inválidos'
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def tracking_view(request):
    """Endpoint para seguimiento de envíos"""
    serializer = TrackingRequestSerializer(data=request.data)
    if serializer.is_valid():
        try:
            dhl_service = DHLService(
                username=settings.DHL_USERNAME,
                password=settings.DHL_PASSWORD,
                base_url=settings.DHL_BASE_URL,
                environment=settings.DHL_ENVIRONMENT
            )
            result = dhl_service.get_tracking(
                tracking_number=serializer.validated_data['tracking_number']
            )
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error en tracking_view: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'message': 'Número de seguimiento requerido'
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def epod_view(request):
    """Endpoint para obtener ePOD"""
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
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error en epod_view: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'message': 'ID de envío requerido'
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def shipment_view(request):
    """Endpoint para crear envíos"""
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
            
            # Guardar envío en la base de datos
            if result.get('success'):
                shipment_data = serializer.validated_data
                shipper = shipment_data['shipper']
                recipient = shipment_data['recipient']
                package = shipment_data['package']
                
                shipment = Shipment.objects.create(
                    tracking_number=result.get('tracking_number'),
                    status='created',
                    service_type=shipment_data['service'],
                    payment_type=shipment_data['payment'],
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
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error en shipment_view: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'message': 'Datos inválidos'
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_data_view(request):
    """Endpoint para obtener datos de prueba"""
    try:
        # Generar datos de prueba con Faker
        test_data = {
            'shipper': {
                'name': fake.name(),
                'company': fake.company(),
                'phone': fake.phone_number(),
                'email': fake.email(),
                'address': fake.street_address(),
                'city': fake.city(),
                'state': fake.state_abbr(),
                'postalCode': fake.postcode(),
                'country': 'US'
            },
            'recipient': {
                'name': fake.name(),
                'company': fake.company(),
                'phone': fake.phone_number(),
                'email': fake.email(),
                'address': fake.street_address(),
                'city': fake.city(),
                'state': fake.state_abbr(),
                'postalCode': fake.postcode(),
                'country': 'US'
            },
            'package': {
                'weight': round(fake.random.uniform(0.5, 10.0), 2),
                'length': round(fake.random.uniform(5, 50), 1),
                'width': round(fake.random.uniform(5, 30), 1),
                'height': round(fake.random.uniform(2, 20), 1),
                'description': fake.sentence(nb_words=6),
                'value': round(fake.random.uniform(10, 500), 2),
                'currency': 'USD'
            }
        }
        
        return Response({
            'success': True,
            'data': test_data
        })
        
    except Exception as e:
        logger.error(f"Error en test_data_view: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_page(60 * 15)  # Cache por 15 minutos
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