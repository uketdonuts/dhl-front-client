from django.urls import path
from . import views

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    
    # Endpoints DHL
    path('dhl/rate/', views.rate_view, name='rate'),
    path('dhl/rate/test/', views.rate_test_view, name='rate_test'),  # Test sin autenticación
    path('dhl/tracking/', views.tracking_view, name='tracking'),
    path('dhl/epod/', views.epod_view, name='epod'),
    path('dhl/shipment/', views.shipment_view, name='shipment'),
    
    # Gestión de envíos
    path('shipments/', views.shipments_list_view, name='shipments_list'),
    path('shipments/<int:shipment_id>/', views.shipment_detail_view, name='shipment_detail'),
    
    # Historial de cotizaciones
    path('rates/history/', views.rates_history_view, name='rates_history'),
    
    # Nuevos endpoints para testing y monitoreo
    path('dhl-status/', views.dhl_status_view, name='dhl_status'),
    path('validate-shipment-date/', views.validate_shipment_date_view, name='validate_shipment_date'),
    path('test-simulator/', views.test_simulator_view, name='test_simulator'),
    path('quick-test/', views.quick_test_view, name='quick_test'),

    # Endpoints para gestión de cuentas DHL
    path('accounts/', views.dhl_account_list, name='dhl_account_list'),
    path('accounts/create/', views.dhl_account_create, name='dhl_account_create'),
    path('accounts/<int:account_id>/delete/', views.dhl_account_delete, name='dhl_account_delete'),
    path('accounts/<int:account_id>/set-default/', views.dhl_account_set_default, name='dhl_account_set_default'),
]