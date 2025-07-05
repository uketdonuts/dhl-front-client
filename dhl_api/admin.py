from django.contrib import admin
from .models import Shipment, TrackingEvent, RateQuote, EPODDocument


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['tracking_number', 'shipper_name', 'recipient_name', 'status', 'created_at']
    list_filter = ['status', 'service_type', 'payment_type', 'created_at']
    search_fields = ['tracking_number', 'shipper_name', 'recipient_name', 'shipper_email', 'recipient_email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('tracking_number', 'status', 'service_type', 'payment_type')
        }),
        ('Remitente', {
            'fields': ('shipper_name', 'shipper_company', 'shipper_phone', 'shipper_email', 
                      'shipper_address', 'shipper_city', 'shipper_state', 'shipper_postal_code', 'shipper_country')
        }),
        ('Destinatario', {
            'fields': ('recipient_name', 'recipient_company', 'recipient_phone', 'recipient_email',
                      'recipient_address', 'recipient_city', 'recipient_state', 'recipient_postal_code', 'recipient_country')
        }),
        ('Paquete', {
            'fields': ('package_weight', 'package_length', 'package_width', 'package_height',
                      'package_description', 'package_value', 'package_currency')
        }),
        ('Información Adicional', {
            'fields': ('estimated_delivery', 'cost', 'created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(TrackingEvent)
class TrackingEventAdmin(admin.ModelAdmin):
    list_display = ['shipment', 'event_code', 'description', 'location', 'timestamp']
    list_filter = ['event_code', 'timestamp']
    search_fields = ['shipment__tracking_number', 'description', 'location']
    readonly_fields = ['created_at']
    date_hierarchy = 'timestamp'


@admin.register(RateQuote)
class RateQuoteAdmin(admin.ModelAdmin):
    list_display = ['service_name', 'total_price', 'currency', 'delivery_time', 'created_by', 'created_at']
    list_filter = ['service_code', 'currency', 'created_at']
    search_fields = ['service_name', 'origin_city', 'destination_city']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Origen', {
            'fields': ('origin_postal_code', 'origin_city', 'origin_country', 'origin_state')
        }),
        ('Destino', {
            'fields': ('destination_postal_code', 'destination_city', 'destination_country', 'destination_state')
        }),
        ('Paquete', {
            'fields': ('weight', 'length', 'width', 'height')
        }),
        ('Servicio', {
            'fields': ('service_name', 'service_code', 'total_price', 'currency', 'delivery_time')
        }),
        ('Usuario', {
            'fields': ('created_by', 'created_at')
        }),
    )


@admin.register(EPODDocument)
class EPODDocumentAdmin(admin.ModelAdmin):
    list_display = ['document_id', 'shipment', 'file_name', 'created_at']
    list_filter = ['created_at']
    search_fields = ['document_id', 'shipment__tracking_number', 'file_name']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


# Configuración del sitio admin
admin.site.site_header = "DHL Express API - Administración"
admin.site.site_title = "DHL Express API"
admin.site.index_title = "Panel de Administración" 