from django.urls import path
from . import views
from . import test_views

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    
    # Endpoints DHL
    path('dhl/rate/', views.rate_view, name='rate'),
    path('dhl/tracking/', views.tracking_view, name='tracking'),
    path('dhl/epod/', views.epod_view, name='epod'),
    path('dhl/shipment/', views.shipment_view, name='shipment'),
    
    # Datos de prueba
    path('test-data/', views.test_data_view, name='test_data'),
    
    # Gestión de envíos
    path('shipments/', views.shipments_list_view, name='shipments_list'),
    path('shipments/<int:shipment_id>/', views.shipment_detail_view, name='shipment_detail'),
    
    # Historial de cotizaciones
    path('rates/history/', views.rates_history_view, name='rates_history'),
    
    # Nuevos endpoints para testing y monitoreo
    path('test-dhl-credentials/', views.test_dhl_credentials_view, name='test_dhl_credentials'),
    path('dhl-status/', views.dhl_status_view, name='dhl_status'),
    path('validate-shipment-date/', views.validate_shipment_date_view, name='validate_shipment_date'),
    
    # Endpoints de prueba (SOLO PARA DESARROLLO)
    path('test/shipment-data/', test_views.get_test_shipment_data, name='test_shipment_data'),
    path('test/shipment-direct/', test_views.test_shipment_direct, name='test_shipment_direct'),
    
    # Nuevos endpoints para formato exacto DHL
    path('test/hardcoded-data/', test_views.get_hardcoded_test_data, name='get_hardcoded_test_data'),
    path('test/shipment-new-format/', test_views.test_shipment_new_format, name='test_shipment_new_format'),
    path('test/shipment-direct-service/', test_views.test_shipment_direct_service, name='test_shipment_direct_service'),
    path('test/connection-status/', test_views.test_connection_status, name='test_connection_status'),
    
    # Endpoints para gestión de cuentas DHL
    path('accounts/', views.dhl_account_list, name='dhl_account_list'),
    path('accounts/create/', views.dhl_account_create, name='dhl_account_create'),
    path('accounts/<int:account_id>/delete/', views.dhl_account_delete, name='dhl_account_delete'),
    path('accounts/<int:account_id>/set-default/', views.dhl_account_set_default, name='dhl_account_set_default'),
]