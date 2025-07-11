from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Shipment, TrackingEvent, RateQuote, EPODDocument, DHLAccount


class UserSerializer(serializers.ModelSerializer):
    """Serializer para usuarios"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class ShipmentSerializer(serializers.ModelSerializer):
    """Serializer para envíos"""
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Shipment
        fields = '__all__'
        read_only_fields = ['tracking_number', 'status', 'estimated_delivery', 'cost', 'created_by', 'created_at', 'updated_at']


class TrackingEventSerializer(serializers.ModelSerializer):
    """Serializer para eventos de seguimiento"""
    class Meta:
        model = TrackingEvent
        fields = '__all__'


class RateQuoteSerializer(serializers.ModelSerializer):
    """Serializer para cotizaciones"""
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = RateQuote
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at']


class EPODDocumentSerializer(serializers.ModelSerializer):
    """Serializer para documentos ePOD"""
    class Meta:
        model = EPODDocument
        fields = '__all__'


# Serializers para requests de la API
class RateRequestSerializer(serializers.Serializer):
    """Serializer para requests de cotización"""
    origin = serializers.DictField()
    destination = serializers.DictField()
    weight = serializers.FloatField()
    dimensions = serializers.DictField()


class TrackingRequestSerializer(serializers.Serializer):
    """Serializer para requests de seguimiento"""
    tracking_number = serializers.CharField(max_length=50)


class EPODRequestSerializer(serializers.Serializer):
    """Serializer para requests de ePOD"""
    shipment_id = serializers.CharField(max_length=50)


class ShipmentRequestSerializer(serializers.Serializer):
    """Serializer para requests de creación de envío"""
    shipper = serializers.DictField()
    recipient = serializers.DictField()
    package = serializers.DictField()
    service = serializers.CharField(max_length=1, default='P')
    payment = serializers.CharField(max_length=1, default='S')


class LoginSerializer(serializers.Serializer):
    """Serializer para login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class TestDataSerializer(serializers.Serializer):
    """Serializer para datos de prueba"""
    shipper = serializers.DictField()
    recipient = serializers.DictField()
    package = serializers.DictField() 


class DHLAccountSerializer(serializers.ModelSerializer):
    """Serializador para cuentas DHL"""
    
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = DHLAccount
        fields = [
            'id', 'account_number', 'account_name', 'is_active', 
            'is_default', 'created_by', 'created_at', 'updated_at',
            'last_validated', 'validation_status'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_validated', 'validation_status']
    
    def validate_account_number(self, value):
        """Validar que el número de cuenta tenga el formato correcto"""
        if not value.isdigit() or len(value) < 9:
            raise serializers.ValidationError(
                "El número de cuenta debe contener al menos 9 dígitos numéricos"
            )
        return value 