"""
URL configuration for dhl_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def health_check(request):
    """Endpoint de health check para monitoreo"""
    return JsonResponse({
        'status': 'ok',
        'message': 'DHL API Backend is running',
        'debug': settings.DEBUG
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('dhl_api.urls')),
    path('api/health/', health_check, name='health_check'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 