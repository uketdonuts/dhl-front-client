from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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