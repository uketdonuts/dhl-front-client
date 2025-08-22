from django.contrib import admin
from .models import Shipment, TrackingEvent, RateQuote, EPODDocument, UserActivity, Contact, ServiceZone
from .models import ServiceAreaCityMap, CountryISO


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


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'get_action_display', 'status', 'get_status_display', 'resource_type', 'resource_id', 'created_at']
    list_filter = ['action', 'status', 'resource_type', 'created_at']
    search_fields = ['user__username', 'user__email', 'description', 'ip_address', 'resource_id']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Usuario y Acción', {
            'fields': ('user', 'action', 'status', 'description')
        }),
        ('Contexto', {
            'fields': ('resource_type', 'resource_id', 'ip_address', 'user_agent')
        }),
        ('Metadatos', {
            'fields': ('metadata', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_action_display(self, obj):
        return obj.get_action_display()
    get_action_display.short_description = 'Acción'
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    get_status_display.short_description = 'Estado'
    
    def has_add_permission(self, request):
        """No permitir agregar actividades manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Solo permitir ver, no editar"""
        return False


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'company', 'city', 'country', 'is_favorite', 'usage_count', 'created_by', 'created_at']
    list_filter = ['is_favorite', 'country', 'created_at', 'created_by']
    search_fields = ['name', 'email', 'phone', 'company', 'city', 'address']
    readonly_fields = ['usage_count', 'last_used', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'company', 'phone', 'email')
        }),
        ('Dirección', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Configuración', {
            'fields': ('is_favorite', 'created_by')
        }),
        ('Estadísticas', {
            'fields': ('usage_count', 'last_used', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ServiceZone)
class ServiceZoneAdmin(admin.ModelAdmin):
    list_display = ['country_name', 'state_name', 'city_name', 'service_area', 'postal_code_range', 'created_at']
    list_filter = ['country_code', 'service_area', 'created_at']
    search_fields = ['country_name', 'state_name', 'city_name', 'service_area', 'postal_code_from', 'postal_code_to']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        ('Ubicación', {
            'fields': ('country_code', 'country_name', 'state_code', 'state_name', 'city_name')
        }),
        ('Servicio', {
            'fields': ('service_area',)
        }),
        ('Códigos Postales', {
            'fields': ('postal_code_from', 'postal_code_to'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def postal_code_range(self, obj):
        """Muestra el rango de códigos postales"""
        if obj.postal_code_from and obj.postal_code_to:
            if obj.postal_code_from == obj.postal_code_to:
                return obj.postal_code_from
            else:
                return f"{obj.postal_code_from} - {obj.postal_code_to}"
        return "-"
    postal_code_range.short_description = 'Códigos Postales'
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related()
    
    # Acciones administrativas
    actions = ['export_selected_zones']
    
    def export_selected_zones(self, request, queryset):
        """Exportar zonas seleccionadas a CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="service_zones.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['País', 'Estado', 'Ciudad', 'Área de Servicio', 'CP Desde', 'CP Hasta'])
        
        for zone in queryset:
            writer.writerow([
                zone.country_name,
                zone.state_name or '',
                zone.city_name or '',
                zone.service_area,
                zone.postal_code_from or '',
                zone.postal_code_to or ''
            ])
        
        return response
    export_selected_zones.short_description = "Exportar zonas seleccionadas a CSV"


@admin.register(ServiceAreaCityMap)
class ServiceAreaCityMapAdmin(admin.ModelAdmin):
    list_display = ('country_code', 'state_code', 'service_area', 'city_name', 'display_name', 'postal_code_from', 'postal_code_to', 'updated_at')
    list_filter = ('country_code', 'state_code', 'service_area')
    search_fields = ('country_code', 'state_code', 'service_area', 'city_name', 'display_name')
    ordering = ('country_code', 'state_code', 'service_area', 'city_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CountryISO)
class CountryISOAdmin(admin.ModelAdmin):
    list_display = ('code', 'display_name', 'currency_code', 'numeric_code')
    search_fields = ('code', 'iso_short_name', 'iso_full_name', 'dhl_short_name')
    list_filter = ('currency_code',)


# Configuración del sitio admin
admin.site.site_header = "DHL Express API - Administración"
admin.site.site_title = "DHL Express API"
admin.site.index_title = "Panel de Administración" 