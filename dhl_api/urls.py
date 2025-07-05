from django.urls import path
from . import views

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
] 