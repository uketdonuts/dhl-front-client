from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone
import json


class Shipment(models.Model):
    """Modelo para almacenar información de envíos"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('created', 'Creado'),
        ('in_transit', 'En Tránsito'),
        ('delivered', 'Entregado'),
        ('failed', 'Fallido'),
    ]
    
    SERVICE_CHOICES = [
        ('P', 'DHL Express Worldwide'),
        ('K', 'DHL Express 9:00'),
        ('U', 'DHL Express 10:30'),
        ('Y', 'DHL Express 12:00'),
    ]
    
    PAYMENT_CHOICES = [
        ('S', 'Remitente'),
        ('R', 'Destinatario'),
        ('T', 'Tercero'),
    ]
    
    # Información básica
    tracking_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    service_type = models.CharField(max_length=1, choices=SERVICE_CHOICES, default='P')
    payment_type = models.CharField(max_length=1, choices=PAYMENT_CHOICES, default='S')
    
    # Información del remitente
    shipper_name = models.CharField(max_length=100)
    shipper_company = models.CharField(max_length=100, blank=True)
    shipper_phone = models.CharField(max_length=20)
    shipper_email = models.EmailField()
    shipper_address = models.TextField()
    shipper_city = models.CharField(max_length=50)
    shipper_state = models.CharField(max_length=50, blank=True)
    shipper_postal_code = models.CharField(max_length=20)
    shipper_country = models.CharField(max_length=2)
    
    # Información del destinatario
    recipient_name = models.CharField(max_length=100)
    recipient_company = models.CharField(max_length=100, blank=True)
    recipient_phone = models.CharField(max_length=20)
    recipient_email = models.EmailField()
    recipient_address = models.TextField()
    recipient_city = models.CharField(max_length=50)
    recipient_state = models.CharField(max_length=50, blank=True)
    recipient_postal_code = models.CharField(max_length=20)
    recipient_country = models.CharField(max_length=2)
    
    # Información del paquete
    package_weight = models.DecimalField(max_digits=8, decimal_places=2)
    package_length = models.DecimalField(max_digits=8, decimal_places=2)
    package_width = models.DecimalField(max_digits=8, decimal_places=2)
    package_height = models.DecimalField(max_digits=8, decimal_places=2)
    package_description = models.TextField()
    package_value = models.DecimalField(max_digits=10, decimal_places=2)
    package_currency = models.CharField(max_length=3, default='USD')
    
    # Información adicional
    estimated_delivery = models.CharField(max_length=50, blank=True)
    cost = models.CharField(max_length=50, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Envío'
        verbose_name_plural = 'Envíos'
    
    def __str__(self):
        return f"Envío {self.tracking_number or self.id} - {self.shipper_name}"


class TrackingEvent(models.Model):
    """Modelo para almacenar eventos de seguimiento"""
    
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='tracking_events')
    event_code = models.CharField(max_length=10)
    description = models.CharField(max_length=200)
    location = models.CharField(max_length=100)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Evento de Seguimiento'
        verbose_name_plural = 'Eventos de Seguimiento'
    
    def __str__(self):
        return f"{self.event_code} - {self.description} - {self.timestamp}"


class RateQuote(models.Model):
    """Modelo para almacenar cotizaciones de tarifas"""
    
    origin_postal_code = models.CharField(max_length=20)
    origin_city = models.CharField(max_length=50)
    origin_country = models.CharField(max_length=2)
    origin_state = models.CharField(max_length=50, blank=True)
    
    destination_postal_code = models.CharField(max_length=20)
    destination_city = models.CharField(max_length=50)
    destination_country = models.CharField(max_length=2)
    destination_state = models.CharField(max_length=50, blank=True)
    
    weight = models.DecimalField(max_digits=8, decimal_places=2)
    length = models.DecimalField(max_digits=8, decimal_places=2)
    width = models.DecimalField(max_digits=8, decimal_places=2)
    height = models.DecimalField(max_digits=8, decimal_places=2)
    
    service_name = models.CharField(max_length=100)
    service_code = models.CharField(max_length=10)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    delivery_time = models.CharField(max_length=50)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
    
    def __str__(self):
        return f"Cotización {self.id} - {self.service_name}"


class EPODDocument(models.Model):
    """Modelo para almacenar documentos ePOD"""
    
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='epod_documents')
    document_id = models.CharField(max_length=50)
    pdf_data = models.TextField()  # Base64 encoded PDF
    file_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Documento ePOD'
        verbose_name_plural = 'Documentos ePOD'
    
    def __str__(self):
        return f"ePOD {self.document_id} - {self.shipment.tracking_number}" 


class DHLAccount(models.Model):
    """Modelo para almacenar y gestionar cuentas DHL"""
    
    account_number = models.CharField(max_length=20, unique=True)
    account_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_validated = models.DateTimeField(null=True, blank=True)
    validation_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendiente'),
            ('valid', 'Válida'),
            ('invalid', 'Inválida'),
        ],
        default='pending'
    )
    
    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name = 'Cuenta DHL'
        verbose_name_plural = 'Cuentas DHL'
    
    def __str__(self):
        return f"{self.account_name} ({self.account_number})"
    
    def save(self, *args, **kwargs):
        # Si esta cuenta se marca como default, quitar el default de otras
        if self.is_default:
            DHLAccount.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs) 


class LandedCostQuote(models.Model):
    """Modelo para almacenar cotizaciones de Landed Cost"""
    
    PURPOSE_CHOICES = [
        ('commercial', 'Comercial'),
        ('personal', 'Personal'),
    ]
    
    TRANSPORT_CHOICES = [
        ('air', 'Aéreo'),
        ('ocean', 'Marítimo'),
        ('ground', 'Terrestre'),
    ]
    
    # Información básica de la cotización
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='landed_cost_quotes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Origen y destino
    origin_postal_code = models.CharField(max_length=20)
    origin_city = models.CharField(max_length=100)
    origin_country = models.CharField(max_length=2)
    destination_postal_code = models.CharField(max_length=20)
    destination_city = models.CharField(max_length=100)
    destination_country = models.CharField(max_length=2)
    
    # Dimensiones y peso del paquete
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    length = models.DecimalField(max_digits=10, decimal_places=2)
    width = models.DecimalField(max_digits=10, decimal_places=2)
    height = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Configuraciones de la cotización
    currency_code = models.CharField(max_length=3, default='USD')
    shipment_purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='personal')
    transportation_mode = models.CharField(max_length=20, choices=TRANSPORT_CHOICES, default='air')
    is_customs_declarable = models.BooleanField(default=True)
    is_dtp_requested = models.BooleanField(default=False)
    is_insurance_requested = models.BooleanField(default=False)
    
    # Resultados del cálculo
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    duties_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    taxes_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fees_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    insurance_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Información adicional
    items_count = models.PositiveIntegerField(default=1)
    total_declared_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    warnings_count = models.PositiveIntegerField(default=0)
    
    # Datos JSON para detalles completos
    full_response = models.JSONField(null=True, blank=True, help_text="Respuesta completa de DHL API")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Cotización Landed Cost'
        verbose_name_plural = 'Cotizaciones Landed Cost'
    
    def __str__(self):
        return f"Landed Cost {self.origin_country}->{self.destination_country} ${self.total_cost} ({self.created_at.strftime('%Y-%m-%d')})"
    
    @property
    def savings_vs_standard_shipping(self):
        """Calcula el ahorro vs shipping estándar (estimado)"""
        return max(0, self.total_cost - self.shipping_cost)
    
    @property
    def effective_tax_rate(self):
        """Calcula la tasa efectiva de impuestos"""
        if self.total_declared_value > 0:
            return (self.duties_cost + self.taxes_cost) / self.total_declared_value * 100
        return 0


class UserActivity(models.Model):
    """Modelo para almacenar el historial de actividades de usuarios"""
    
    ACTION_CHOICES = [
        ('login', 'Inicio de sesión'),
        ('logout', 'Cierre de sesión'),
        ('create_shipment', 'Crear envío'),
        ('view_shipment', 'Ver envío'),
        ('edit_shipment', 'Editar envío'),
        ('delete_shipment', 'Eliminar envío'),
        ('track_shipment', 'Rastrear envío'),
        ('get_rate', 'Obtener cotización'),
        ('compare_rates', 'Comparar cotizaciones'),
        ('create_account', 'Crear cuenta DHL'),
        ('edit_account', 'Editar cuenta DHL'),
        ('delete_account', 'Eliminar cuenta DHL'),
        ('set_default_account', 'Establecer cuenta por defecto'),
        ('landed_cost_quote', 'Cotización Landed Cost'),
        ('validate_landed_cost', 'Validar Landed Cost'),
        ('epod_request', 'Solicitud ePOD'),
        ('api_error', 'Error de API'),
        ('system_action', 'Acción del sistema'),
    ]
    
    STATUS_CHOICES = [
        ('success', 'Exitoso'),
        ('error', 'Error'),
        ('warning', 'Advertencia'),
        ('info', 'Información'),
    ]
    
    # Información básica
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='success')
    
    # Detalles de la actividad
    description = models.TextField(help_text="Descripción detallada de la acción")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    # Contexto adicional
    resource_type = models.CharField(max_length=50, null=True, blank=True, 
                                   help_text="Tipo de recurso afectado (ej: shipment, account)")
    resource_id = models.CharField(max_length=50, null=True, blank=True,
                                 help_text="ID del recurso afectado")
    
    # Datos adicionales en JSON
    metadata = models.JSONField(null=True, blank=True, 
                              help_text="Datos adicionales de la actividad")
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Actividad de Usuario'
        verbose_name_plural = 'Actividades de Usuario'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    @classmethod
    def log_activity(cls, user, action, description, status='success', **kwargs):
        """
        Método de utilidad para registrar actividades de usuario
        
        Args:
            user: Usuario que realiza la acción
            action: Tipo de acción (debe estar en ACTION_CHOICES)
            description: Descripción de la acción
            status: Estado de la acción (success, error, warning, info)
            **kwargs: Argumentos adicionales (ip_address, user_agent, resource_type, resource_id, metadata)
        """
        return cls.objects.create(
            user=user,
            action=action,
            description=description,
            status=status,
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent'),
            resource_type=kwargs.get('resource_type'),
            resource_id=kwargs.get('resource_id'),
            metadata=kwargs.get('metadata')
        )
    
    def to_dict(self):
        """Convierte la actividad a diccionario para serialización"""
        return {
            'id': self.id,
            'user': self.user.username,
            'action': self.action,
            'action_display': self.get_action_display(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'description': self.description,
            'ip_address': self.ip_address,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


class Contact(models.Model):
    """Modelo para almacenar agenda de contactos general para remitentes y destinatarios"""
    
    # Información básica
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=100, verbose_name='Nombre')
    company = models.CharField(max_length=100, blank=True, verbose_name='Empresa')
    phone = models.CharField(max_length=20, verbose_name='Teléfono')
    email = models.EmailField(verbose_name='Correo Electrónico')
    
    # Información de dirección
    address = models.TextField(verbose_name='Dirección')
    city = models.CharField(max_length=50, verbose_name='Ciudad')
    state = models.CharField(max_length=50, blank=True, verbose_name='Estado/Provincia')
    postal_code = models.CharField(max_length=20, verbose_name='Código Postal')
    country = models.CharField(max_length=2, verbose_name='País')
    
    # Metadatos
    is_favorite = models.BooleanField(default=False, verbose_name='Favorito')
    usage_count = models.PositiveIntegerField(default=0, verbose_name='Veces Usado')
    last_used = models.DateTimeField(null=True, blank=True, verbose_name='Último Uso')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_favorite', '-usage_count', '-last_used', '-created_at']
        verbose_name = 'Contacto'
        verbose_name_plural = 'Contactos'
        # Evitar duplicados por usuario
        unique_together = [['created_by', 'email', 'name']]
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    def increment_usage(self):
        """Incrementa el contador de uso y actualiza last_used"""
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])
    
    def to_dict(self):
        """Convierte el contacto a diccionario para API"""
        return {
            'id': self.id,
            'name': self.name,
            'company': self.company,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'is_favorite': self.is_favorite,
            'usage_count': self.usage_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        } 


class ServiceZone(models.Model):
    """Modelo para almacenar las zonas de servicio DHL (ESD)"""
    
    country_code = models.CharField(max_length=2, help_text="Código de país ISO (2 letras)")
    country_name = models.CharField(max_length=100, help_text="Nombre del país")
    state_code = models.CharField(max_length=10, blank=True, help_text="Código del estado/provincia")
    state_name = models.CharField(max_length=100, blank=True, help_text="Nombre del estado/provincia")
    city_name = models.CharField(max_length=100, blank=True, help_text="Nombre de la ciudad")
    service_area = models.CharField(max_length=10, help_text="Código del área de servicio DHL")
    postal_code_from = models.CharField(max_length=20, blank=True, help_text="Código postal inicial")
    postal_code_to = models.CharField(max_length=20, blank=True, help_text="Código postal final")
    
    # Campos para optimizar consultas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Zona de Servicio'
        verbose_name_plural = 'Zonas de Servicio'
        indexes = [
            models.Index(fields=['country_code']),
            models.Index(fields=['country_code', 'state_code']),
            models.Index(fields=['country_code', 'city_name']),
            models.Index(fields=['service_area']),
        ]
        # Evitar duplicados
        unique_together = [['country_code', 'state_code', 'city_name', 'postal_code_from', 'postal_code_to']]
    
    def __str__(self):
        location_parts = [self.country_name]
        if self.state_name:
            location_parts.append(self.state_name)
        if self.city_name:
            location_parts.append(self.city_name)
        location = ", ".join(location_parts)
        
        if self.postal_code_from and self.postal_code_to:
            return f"{location} ({self.postal_code_from}-{self.postal_code_to}) - {self.service_area}"
        else:
            return f"{location} - {self.service_area}"
    
    @classmethod
    def get_countries(cls):
        """Obtiene lista única de países"""
        return cls.objects.values('country_code', 'country_name').distinct().order_by('country_name')
    
    @classmethod
    def get_states_by_country(cls, country_code):
        """Obtiene estados/provincias por país"""
        return cls.objects.filter(
            country_code=country_code,
            state_name__isnull=False
        ).exclude(
            state_name=''
        ).values('state_code', 'state_name').distinct().order_by('state_name')
    
    @classmethod
    def get_cities_by_country_state(cls, country_code, state_code=None):
        """
        Obtiene ciudades por país y opcionalmente por estado.
        Detecta automáticamente si usar city_name o service_area según el país.
        """
        queryset = cls.objects.filter(country_code=country_code)
        if state_code:
            queryset = queryset.filter(state_code=state_code)
        
        # Contar qué tipo de datos hay disponibles
        total_records = queryset.count()
        if total_records == 0:
            return queryset.none()
        
        city_name_count = queryset.exclude(
            Q(city_name__isnull=True) | Q(city_name='')
        ).count()
        
        service_area_count = queryset.exclude(
            Q(service_area__isnull=True) | Q(service_area='')
        ).count()
        
        # Determinar qué campo usar
        use_city_name = (city_name_count / total_records) > 0.1  # >10% tienen city_name
        use_service_area = (service_area_count / total_records) > 0.1  # >10% tienen service_area
        
        if use_city_name:
            # Usar city_name (como Panamá)
            return queryset.filter(
                city_name__isnull=False
            ).exclude(
                city_name=''
            ).values('city_name').annotate(
                name=models.F('city_name'),
                code=models.F('city_name'),
                display_name=models.F('city_name')
            ).distinct().order_by('city_name')
        elif use_service_area:
            # Usar service_area (como Colombia) 
            return queryset.filter(
                service_area__isnull=False
            ).exclude(
                service_area=''
            ).values('service_area').annotate(
                name=models.F('service_area'),
                code=models.F('service_area'),
                display_name=models.F('service_area')
            ).distinct().order_by('service_area')
        else:
            # No hay datos de ciudad
            return queryset.none()

    @classmethod
    def get_cities_smart(cls, country_code, state_code=None):
        """
        Método mejorado que retorna ciudades con estructura consistente.
        Detecta automáticamente el campo correcto según el país.
        """
        queryset = cls.objects.filter(country_code=country_code)
        if state_code:
            queryset = queryset.filter(state_code=state_code)
        
        if not queryset.exists():
            return []
        
        # Analizar estructura del país
        total = queryset.count()
        city_name_count = queryset.exclude(Q(city_name__isnull=True) | Q(city_name='')).count()
        service_area_count = queryset.exclude(Q(service_area__isnull=True) | Q(service_area='')).count()
        
        use_city_name = (city_name_count / total) > 0.1
        use_service_area = (service_area_count / total) > 0.1
        
        if use_city_name:
            # Países como Panamá - usar city_name
            cities = queryset.exclude(
                Q(city_name__isnull=True) | Q(city_name='')
            ).values_list('city_name', flat=True).distinct().order_by('city_name')
            
            return [
                {
                    'name': city,
                    'code': city,
                    'display_name': city,
                    'type': 'city_name'
                } for city in cities
            ]
        elif use_service_area:
            # Países como Colombia - usar service_area
            areas = queryset.exclude(
                Q(service_area__isnull=True) | Q(service_area='')
            ).values_list('service_area', flat=True).distinct().order_by('service_area')
            
            return [
                {
                    'name': area,
                    'code': area, 
                    'display_name': area,
                    'type': 'service_area'
                } for area in areas
            ]
        else:
            return []
    
    @classmethod
    def get_service_areas_by_location(cls, country_code, state_code=None, city_name=None):
        """Obtiene áreas de servicio por ubicación"""
        queryset = cls.objects.filter(country_code=country_code)
        if state_code:
            queryset = queryset.filter(state_code=state_code)
        if city_name:
            queryset = queryset.filter(city_name=city_name)
        
        return queryset.values('service_area').distinct().order_by('service_area')
    
    @classmethod
    def get_postal_codes_by_location(cls, country_code, state_code=None, city_name=None, service_area=None):
        """Obtiene códigos postales por ubicación"""
        queryset = cls.objects.filter(country_code=country_code)
        if state_code:
            queryset = queryset.filter(state_code=state_code)
        if city_name:
            queryset = queryset.filter(city_name=city_name)
        if service_area:
            queryset = queryset.filter(service_area=service_area)
        
        # Obtener rangos de códigos postales únicos
        postal_codes = queryset.filter(
            postal_code_from__isnull=False,
            postal_code_to__isnull=False
        ).exclude(
            postal_code_from='',
            postal_code_to=''
        ).values(
            'postal_code_from', 
            'postal_code_to',
            'service_area'
        ).distinct().order_by('postal_code_from')
        
        return postal_codes


class ServiceAreaCityMap(models.Model):
    """Mapa de área de servicio DHL a nombres de ciudad amigables por país.

    Permite resolver códigos como YHM/YYZ, etc., a un nombre presentado al usuario
    según convenciones por país. Puede opcionalmente acotar por estado y/o rango postal.
    """

    country_code = models.CharField(max_length=2, help_text="Código de país ISO (2 letras)")
    state_code = models.CharField(max_length=10, blank=True, help_text="Código de estado/provincia (opcional)")
    service_area = models.CharField(max_length=10, help_text="Código de área de servicio DHL (ej: YHM)")

    # Datos de presentación
    city_name = models.CharField(max_length=120, help_text="Nombre base de ciudad (ej: Richmond Hill)")
    display_name = models.CharField(max_length=180, help_text="Nombre final a mostrar (ej: Richmond Hill L4B 1B1)")

    # Acotadores opcionales
    postal_code_from = models.CharField(max_length=20, blank=True)
    postal_code_to = models.CharField(max_length=20, blank=True)

    notes = models.TextField(blank=True, help_text="Notas o fuente del mapeo")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mapa Área de Servicio-Ciudad'
        verbose_name_plural = 'Mapas Área de Servicio-Ciudad'
        indexes = [
            models.Index(fields=['country_code', 'service_area']),
            models.Index(fields=['country_code', 'state_code', 'service_area']),
        ]
        unique_together = [
            ['country_code', 'state_code', 'service_area', 'postal_code_from', 'postal_code_to']
        ]

    def __str__(self) -> str:
        scope = self.country_code
        if self.state_code:
            scope += f"-{self.state_code}"
        rng = ''
        if self.postal_code_from and self.postal_code_to:
            rng = f" [{self.postal_code_from}-{self.postal_code_to}]"
        return f"{scope} {self.service_area} → {self.display_name}{rng}"

    @classmethod
    def resolve_display(
        cls,
        *,
        country_code: str,
        service_area: str,
        postal_code: str | None = None,
        state_code: str | None = None,
        fallback_city: str | None = None,
    ) -> dict:
        """Resuelve un nombre amigable para mostrar basado en el mapeo.

        Retorna un dict con: display_name, source ('exact'|'range'|'area'|'fallback'),
        and used_mapping (id or None).
        """
        country_code = (country_code or '').upper()
        service_area = (service_area or '').upper()
        state_code = (state_code or '').upper() if state_code else None
        pc = (postal_code or '').replace(' ', '').upper() if postal_code else None

        qs = cls.objects.filter(country_code=country_code, service_area=service_area)
        if state_code:
            qs = qs.filter(models.Q(state_code=state_code) | models.Q(state_code=''))

        # 1) Intentar match por rango postal si se proporcionó postal_code
        if pc:
            rng_match = qs.exclude(postal_code_from='').exclude(postal_code_to='')
            # Comparación simple lexicográfica tras normalizar (sirve para CA/US donde longitud es constante)
            rng_match = rng_match.filter(postal_code_from__lte=pc, postal_code_to__gte=pc)
            obj = rng_match.order_by('-state_code').first()
            if obj:
                return {
                    'display_name': obj.display_name,
                    'source': 'range',
                    'used_mapping': obj.id,
                }

        # 2) Match por área (sin rango)
        area_match = qs.filter(models.Q(postal_code_from='') | models.Q(postal_code_from__isnull=True))
        obj = area_match.order_by('-state_code').first()
        if obj:
            return {
                'display_name': obj.display_name,
                'source': 'area',
                'used_mapping': obj.id,
            }

        # 3) Fallback a ciudad provista o al propio service_area
        display = fallback_city or service_area
        return {
            'display_name': display,
            'source': 'fallback',
            'used_mapping': None,
        }