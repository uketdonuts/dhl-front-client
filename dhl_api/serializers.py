from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Shipment, TrackingEvent, RateQuote, EPODDocument, DHLAccount, UserActivity, Contact, ServiceZone, ServiceAreaCityMap


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


class ServiceAreaCityMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceAreaCityMap
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
    # Opcional: permitir informar el peso total o piezas para calcular el peso efectivo de cotización
    total_weight = serializers.FloatField(required=False, allow_null=True,
                                          help_text="Peso total a usar en la cotización (prioritario si se envía)")
    pieces = serializers.ListField(child=serializers.DictField(), required=False,
                                   help_text="Lista de piezas con al menos 'weight' para calcular el peso total")
    dimensions = serializers.DictField()
    declared_weight = serializers.FloatField(required=False, allow_null=True,
                                           help_text="Peso declarado en kg (opcional)")
    service = serializers.ChoiceField(choices=[('P', 'NON_DOCUMENTS'), ('D', 'DOCUMENTS')],
                                      default='P',
                                      help_text="Tipo de contenido: P (NON_DOCUMENTS) o D (DOCUMENTS)")
    account_number = serializers.CharField(max_length=50, required=False, allow_blank=True,
                                           default='',
                                           help_text="Número de cuenta DHL a usar para la cotización")
    
    def validate_declared_weight(self, value):
        """Validar que el peso declarado sea positivo"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("El peso declarado debe ser mayor que 0")
        return value


class TrackingRequestSerializer(serializers.Serializer):
    """Serializer para requests de seguimiento"""
    tracking_number = serializers.CharField(max_length=50)


class EPODRequestSerializer(serializers.Serializer):
    """Serializer para requests de ePOD"""
    shipment_id = serializers.CharField(max_length=50)
    account_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    content_type = serializers.ChoiceField(
        choices=[
            ('epod-summary', 'Resumen básico'),
            ('epod-detail', 'Detalle completo'),
            ('epod-detail-esig', 'Detalle con firma electrónica'),
            ('epod-summary-esig', 'Resumen con firma electrónica'),
            ('epod-table', 'Formato tabla'),
            ('epod-table-detail', 'Tabla con detalle'),
            ('epod-table-esig', 'Tabla con firma electrónica')
        ],
        default='epod-summary',
        required=False
    )


class ShipmentRequestSerializer(serializers.Serializer):
    """Serializer para requests de creación de envío"""
    shipper = serializers.DictField()
    recipient = serializers.DictField()
    package = serializers.DictField()
    service = serializers.CharField(max_length=1, default='P')
    payment = serializers.CharField(max_length=1, default='S')
    account_number = serializers.CharField(max_length=20, required=False)
    
    def validate(self, data):
        """Validación a nivel de objeto para evitar envío completamente duplicado"""
        shipper = data.get('shipper', {})
        recipient = data.get('recipient', {})
        
        # Solo validar si TODOS los datos principales son idénticos
        # (esto evita errores de copia-pega completa, pero permite casos legítimos)
        shipper_email = shipper.get('email', '').lower().strip()
        recipient_email = recipient.get('email', '').lower().strip()
        shipper_name = shipper.get('name', '').lower().strip()
        recipient_name = recipient.get('name', '').lower().strip()
        shipper_phone = shipper.get('phone', '').strip()
        recipient_phone = recipient.get('phone', '').strip()
        shipper_address = shipper.get('address', '').lower().strip()
        recipient_address = recipient.get('address', '').lower().strip()
        
        # Solo prohibir si ALL los datos críticos son exactamente iguales
        # (esto indica probable error de usuario, no caso legítimo)
        if (shipper_email and recipient_email and 
            shipper_name and recipient_name and 
            shipper_phone and recipient_phone and
            shipper_address and recipient_address and
            shipper_email == recipient_email and
            shipper_name == recipient_name and
            shipper_phone == recipient_phone and
            shipper_address == recipient_address):
            raise serializers.ValidationError({
                'recipient': 'Los datos del remitente y destinatario son idénticos. Verifique que no sea un error de copia.'
            })
        
        return data


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


class ItemSerializer(serializers.Serializer):
    """Serializer para items de landed cost"""
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=255)  # Corregido según documentación DHL API
    manufacturer_country = serializers.CharField(max_length=2, help_text="Código ISO de país de manufactura")
    part_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    quantity = serializers.IntegerField(min_value=1)
    quantity_type = serializers.CharField(max_length=10, default='pcs')
    unit_price = serializers.FloatField(min_value=0)
    unit_price_currency_code = serializers.CharField(max_length=3, default='USD')
    customs_value = serializers.FloatField(min_value=0)
    customs_value_currency_code = serializers.CharField(max_length=3, default='USD')
    commodity_code = serializers.CharField(max_length=15, help_text="Código HS/commodity")
    weight = serializers.FloatField(min_value=0)
    weight_unit_of_measurement = serializers.CharField(max_length=10, default='metric')
    category = serializers.CharField(max_length=10, required=False, allow_blank=True)
    brand = serializers.CharField(max_length=50, required=False, allow_blank=True)


class LandedCostRequestSerializer(serializers.Serializer):
    """Serializer para requests de Landed Cost"""
    origin = serializers.DictField()
    destination = serializers.DictField()
    weight = serializers.FloatField()
    dimensions = serializers.DictField()
    currency_code = serializers.CharField(max_length=3, default='USD', 
                                         help_text="Código de moneda para el cálculo")
    is_customs_declarable = serializers.BooleanField(default=True,
                                                    help_text="Si el envío requiere declaración aduanera")
    is_dtp_requested = serializers.BooleanField(default=False,
                                               help_text="Si se solicita DTP (Duties & Taxes Paid)")
    is_insurance_requested = serializers.BooleanField(default=False,
                                                     help_text="Si se solicita seguro")
    get_cost_breakdown = serializers.BooleanField(default=True,
                                                 help_text="Si se quiere desglose detallado de costos")
    shipment_purpose = serializers.ChoiceField(
        choices=[('commercial', 'Comercial'), ('personal', 'Personal')],
        default='personal',
        help_text="Propósito del envío"
    )
    transportation_mode = serializers.ChoiceField(
        choices=[('air', 'Aéreo'), ('ocean', 'Marítimo'), ('ground', 'Terrestre')],
        default='air',
        help_text="Modo de transporte"
    )
    merchant_selected_carrier_name = serializers.ChoiceField(
        choices=[('DHL', 'DHL'), ('UPS', 'UPS'), ('FEDEX', 'FedEx'), 
                ('TNT', 'TNT'), ('POST', 'Postal'), ('OTHERS', 'Otros')],
        default='DHL',
        help_text="Transportista seleccionado"
    )
    service = serializers.ChoiceField(choices=[('P', 'NON_DOCUMENTS'), ('D', 'DOCUMENTS')],
                                      default='P',
                                      help_text="Tipo de contenido: P (NON_DOCUMENTS) o D (DOCUMENTS)")
    items = ItemSerializer(many=True, help_text="Lista de productos con detalles aduaneros")
    account_number = serializers.CharField(max_length=50, required=False, allow_blank=True,
                                         help_text="Número de cuenta DHL")
    
    def validate_currency_code(self, value):
        """Validar código de moneda"""
        if len(value) != 3:
            raise serializers.ValidationError("El código de moneda debe tener exactamente 3 caracteres")
        return value.upper()
    
    def validate_items(self, value):
        """Validar que haya al menos un item"""
        if not value or len(value) == 0:
            raise serializers.ValidationError("Debe incluir al menos un producto para calcular landed cost")
        return value


class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer para actividades de usuario"""
    user = UserSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'action', 'action_display', 'status', 'status_display',
            'description', 'ip_address', 'user_agent', 'resource_type', 
            'resource_id', 'metadata', 'created_at', 'created_at_formatted'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_created_at_formatted(self, obj):
        """Formatear fecha para mostrar en el frontend"""
        return obj.created_at.strftime('%d/%m/%Y %H:%M:%S')


class UserActivityFilterSerializer(serializers.Serializer):
    """Serializer para filtros de actividades de usuario"""
    user_id = serializers.IntegerField(required=False, help_text="ID del usuario")
    username = serializers.CharField(required=False, help_text="Nombre de usuario")
    action = serializers.ChoiceField(
        choices=UserActivity.ACTION_CHOICES, 
        required=False, 
        help_text="Tipo de acción a filtrar"
    )
    status = serializers.ChoiceField(
        choices=UserActivity.STATUS_CHOICES, 
        required=False, 
        help_text="Estado de la acción"
    )
    date_from = serializers.DateTimeField(
        required=False, 
        help_text="Fecha de inicio (formato: YYYY-MM-DD HH:MM:SS)"
    )
    date_to = serializers.DateTimeField(
        required=False, 
        help_text="Fecha de fin (formato: YYYY-MM-DD HH:MM:SS)"
    )
    resource_type = serializers.CharField(
        required=False, 
        help_text="Tipo de recurso"
    )
    page = serializers.IntegerField(default=1, min_value=1, help_text="Número de página")
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100, help_text="Elementos por página")


class ContactSerializer(serializers.ModelSerializer):
    """Serializer para contactos de la agenda"""
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'id', 'name', 'company', 'phone', 'email', 'address', 
            'city', 'state', 'postal_code', 'country',
            'is_favorite', 'usage_count', 'last_used', 'created_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['usage_count', 'last_used', 'created_by', 'created_at', 'updated_at']
    
    def validate_email(self, value):
        """Validar que el email no esté duplicado para el mismo usuario"""
        user = self.context['request'].user
        queryset = Contact.objects.filter(created_by=user, email=value)
        
        # Si estamos actualizando, excluir el contacto actual
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("Ya existe un contacto con este email.")
        return value
    
    def validate_country(self, value):
        """Validar que el código de país tenga 2 caracteres"""
        if len(value) != 2:
            raise serializers.ValidationError("El código de país debe tener 2 caracteres (ej: PA, CO, US)")
        return value.upper()


class ContactCreateSerializer(serializers.ModelSerializer):
    """Serializer simplificado para crear contactos desde envíos"""
    
    class Meta:
        model = Contact
        fields = [
            'name', 'company', 'phone', 'email', 'address',
            'city', 'state', 'postal_code', 'country'
        ]
    
    def validate_country(self, value):
        """Validar que el código de país tenga 2 caracteres"""
        if len(value) != 2:
            raise serializers.ValidationError("El código de país debe tener 2 caracteres")
        return value.upper() 


class ServiceZoneSerializer(serializers.ModelSerializer):
    """Serializer para zonas de servicio DHL"""
    
    class Meta:
        model = ServiceZone
        fields = [
            'id', 'country_code', 'country_name', 'state_code', 'state_name',
            'city_name', 'service_area', 'postal_code_from', 'postal_code_to'
        ]


class CountrySerializer(serializers.Serializer):
    """Serializer para lista de países"""
    country_code = serializers.CharField(max_length=2)
    country_name = serializers.CharField(max_length=100)


class StateSerializer(serializers.Serializer):
    """Serializer para lista de estados/provincias"""
    state_code = serializers.CharField(max_length=10)
    state_name = serializers.CharField(max_length=100)


class CitySerializer(serializers.Serializer):
    """Serializer para lista de ciudades"""
    city_name = serializers.CharField(max_length=100)


class ServiceAreaSerializer(serializers.Serializer):
    """Serializer para áreas de servicio"""
    service_area = serializers.CharField(max_length=10)
    display_name = serializers.CharField(max_length=180, required=False, allow_blank=True)


class PostalCodeSerializer(serializers.Serializer):
    """Serializer para códigos postales"""
    postal_code_from = serializers.CharField(max_length=20)
    postal_code_to = serializers.CharField(max_length=20)
    service_area = serializers.CharField(max_length=10)