"""
Vista de health check para monitoreo de la aplicación
"""
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import logging

logger = logging.getLogger(__name__)

@never_cache
@csrf_exempt
def health_check(request):
    """
    Endpoint de health check para verificar el estado de la aplicación
    """
    try:
        # Verificar conexión a la base de datos
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Todo OK
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': None  # Se puede agregar timestamp si es necesario
        }, status=200)
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JsonResponse({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }, status=503)
