from django.urls import path
from . import views

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    
    # Endpoints DHL
    path('dhl/rate/', views.rate_view, name='rate'),
    path('dhl/rate/compare/', views.rate_compare_view, name='rate_compare'),
    path('dhl/landed-cost/validate/', views.validate_landed_cost_view, name='validate_landed_cost'),
    path('dhl/landed-cost/', views.landed_cost_view, name='landed_cost'),
    path('dhl/tracking/', views.tracking_view, name='tracking'),
    path('dhl/epod/', views.epod_view, name='epod'),
    path('dhl/shipment/', views.shipment_view, name='shipment'),
    
    # Gestión de envíos
    path('shipments/', views.shipments_list_view, name='shipments_list'),
    path('shipments/<int:shipment_id>/', views.shipment_detail_view, name='shipment_detail'),
    
    # Historial de cotizaciones
    path('rates/history/', views.rates_history_view, name='rates_history'),
    
    # Nuevos endpoints para monitoreo
    path('dhl-status/', views.dhl_status_view, name='dhl_status'),
    path('validate-shipment-date/', views.validate_shipment_date_view, name='validate_shipment_date'),

    # Endpoints para gestión de cuentas DHL
    path('accounts/', views.dhl_account_list, name='dhl_account_list'),
    path('accounts/create/', views.dhl_account_create, name='dhl_account_create'),
    path('accounts/<int:account_id>/delete/', views.dhl_account_delete, name='dhl_account_delete'),
    path('accounts/<int:account_id>/set-default/', views.dhl_account_set_default, name='dhl_account_set_default'),
    
    # Endpoints para historial de actividades de usuarios
    path('user-activities/', views.user_activities_view, name='user_activities'),
    path('user-activities/stats/', views.user_activity_stats_view, name='user_activity_stats'),
    
    # Endpoints para agenda de contactos
    path('contacts/', views.contacts_view, name='contacts_list'),
    path('contacts/<int:contact_id>/', views.contact_detail_view, name='contact_detail'),
    path('contacts/<int:contact_id>/favorite/', views.contact_toggle_favorite_view, name='contact_toggle_favorite'),
    path('contacts/<int:contact_id>/use/', views.contact_use_view, name='contact_use'),
    path('contacts/from-shipment/', views.create_contact_from_shipment_view, name='create_contact_from_shipment'),
    
    # Endpoints para zonas de servicio DHL (dropdowns)
    path('service-zones/countries/', views.get_countries, name='get_countries'),
    path('service-zones/states/<str:country_code>/', views.get_states_by_country, name='get_states_by_country'),
    path('service-zones/cities/<str:country_code>/', views.get_cities_by_country_state, name='get_cities_by_country'),
    path('service-zones/cities/<str:country_code>/<str:state_code>/', views.get_cities_by_country_state, name='get_cities_by_country_state'),
    path('service-zones/areas/<str:country_code>/', views.get_service_areas_by_location, name='get_service_areas'),
    path('service-zones/postal-codes/<str:country_code>/', views.get_postal_codes_by_location, name='get_postal_codes'),
    path('service-zones/resolve-display/', views.resolve_service_area_display, name='resolve_service_area_display'),
    path('service-zones/search/', views.search_service_zones, name='search_service_zones'),
    path('service-zones/analyze-country/<str:country_code>/', views.analyze_country_structure, name='analyze_country_structure'),
]
