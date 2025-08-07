# Configuración de Django optimizada para producción
import os
from .settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Allowed hosts
ALLOWED_HOSTS = ['*']  # Configurar con tu dominio específico

# Database optimizada para SQLite en producción con recursos limitados
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 10,
            'init_command': """
                PRAGMA journal_mode=WAL;
                PRAGMA synchronous=NORMAL;
                PRAGMA cache_size=1000;
                PRAGMA temp_store=MEMORY;
                PRAGMA mmap_size=134217728;
            """
        }
    }
}

# Cache optimizado para memoria limitada
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 4,
        }
    }
}

# Session optimizado
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 1800  # 30 minutos

# Logging optimizado para producción
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file_django': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/django.log',
            'maxBytes': 5*1024*1024,  # 5MB
            'backupCount': 2,
            'formatter': 'verbose',
        },
        'file_dhl_api': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/dhl_api.log',
            'maxBytes': 5*1024*1024,  # 5MB
            'backupCount': 2,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file_django', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'dhl_api': {
            'handlers': ['file_dhl_api', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Static files optimizado
STATIC_URL = '/static/'
STATIC_ROOT = '/app/staticfiles'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = '/app/media'

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CORS optimizado
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",  # Cambiar por tu dominio
]

# Email backend para logs críticos (opcional)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Optimizaciones de performance
USE_TZ = True
USE_I18N = False  # Desactivar si no necesitas internacionalización
USE_L10N = False

# Database connection pooling (para SQLite no es necesario)
# Para PostgreSQL en el futuro:
# CONN_MAX_AGE = 60

# File upload optimizations
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB

# DHL API settings
DHL_USERNAME = os.getenv('DHL_USERNAME')
DHL_PASSWORD = os.getenv('DHL_PASSWORD')
DHL_BASE_URL = os.getenv('DHL_BASE_URL', 'https://express.api.dhl.com')
DHL_ENVIRONMENT = os.getenv('DHL_ENVIRONMENT', 'production')

# Throttling para API
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '100/hour',
    'user': '1000/hour',
    'dhl_api': '60/minute',
}
