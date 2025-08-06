"""
Django settings for dhl_project project.
"""

import os
from pathlib import Path
from decouple import config, Csv
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment variables
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS', 
    default='localhost,127.0.0.1,0.0.0.0,backend', 
    cast=Csv()
)
# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    # 'django_extensions',  # Comentado para ahorrar memoria
    
    # Local apps
    'dhl_api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dhl_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dhl_project.wsgi.application'

# Database configuration
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL and DATABASE_URL.startswith('sqlite'):
    # SQLite configuration for development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
elif DATABASE_URL and DATABASE_URL.startswith('postgresql'):
    # PostgreSQL configuration using DATABASE_URL
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(default=DATABASE_URL)
    }
else:
    # Default PostgreSQL configuration using individual variables
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='dhl_db'),
            'USER': config('DB_USER', default='dhl_user'),
            'PASSWORD': config('DB_PASSWORD', default='dhl_password'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# URL Configuration
APPEND_SLASH = False

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '300/hour',      # Aumentado para SmartLocationDropdown
        'user': '2000/hour',     # Aumentado para usuarios autenticados
        'service_zones': '600/hour'  # Rate limit específico para service zones
    }
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
}

# CORS settings - Simple y limpio
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True
# DHL Configuration
DHL_USERNAME = config('DHL_USERNAME', default='apO3fS5mJ8zT7h')
DHL_PASSWORD = config('DHL_PASSWORD', default='J^4oF@1qW!0qS!5b')
DHL_BASE_URL = config('DHL_BASE_URL', default='https://express.api.dhl.com')
DHL_ENVIRONMENT = config('DHL_ENVIRONMENT', default='production')

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Logging configuration ÓPTIMO - Enfoque híbrido con nombres timestamped
# Para máximo rendimiento + navegación fácil, usar configuración híbrida:
from datetime import datetime
current_date = datetime.now().strftime('%Y-%m-%d')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'timestamped': {
            'format': '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s',
            'datefmt': '%H:%M:%S',  # Solo hora (fecha ya está en nombre archivo)
            'style': '%',
        },
        'simple': {
            'format': '%(levelname)s: %(message)s',
            'style': '%',
        },
    },
    'handlers': {
        # DJANGO GENERAL - Archivo diario con rotación por tamaño (ÓPTIMO)
        'django_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', f'django_{current_date}.log'),
            'formatter': 'timestamped',
            'maxBytes': 10 * 1024 * 1024,  # 10MB por archivo
            'backupCount': 5,  # django_2025-08-04.log.1, .2, etc.
            'encoding': 'utf-8',
        },
        
        # ERRORES - Archivos por HORA para análisis crítico rápido
        'errors_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', f'errors_{current_date}.log'),
            'formatter': 'timestamped',
            'when': 'H',  # Cada hora
            'interval': 1,
            'backupCount': 48,  # 2 días de errores por hora
            'encoding': 'utf-8',
        },
        
        # DHL API - Archivo por DÍA (balance perfecto navegación/rendimiento)
        'dhl_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', f'dhl_api_{current_date}.log'),
            'formatter': 'timestamped',
            'encoding': 'utf-8',
        },
        
        # REQUESTS - Rotación por tamaño (alto volumen)
        'requests_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', f'requests_{current_date}.log'),
            'formatter': 'timestamped',
            'maxBytes': 5 * 1024 * 1024,  # 5MB
            'backupCount': 3,
            'encoding': 'utf-8',
        },
        
        # PERFORMANCE - Por timestamp específico para análisis detallado
        'performance_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', f'performance_{current_date}_{datetime.now().strftime("%H%M")}.log'),
            'formatter': 'timestamped',
            'encoding': 'utf-8',
        },
        
        # Console handler limpio
        'console': {
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'django_file'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'django_file', 'errors_file'],
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'propagate': False,
        },
        'dhl_api': {
            'handlers': ['console', 'dhl_file', 'errors_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'performance': {
            'handlers': ['performance_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'urllib3': {
            'handlers': ['requests_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'requests': {
            'handlers': ['requests_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.contrib.auth': {
            'handlers': ['django_file', 'errors_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['django_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Security settings for production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_PRELOAD = True

# Create logs directory if it doesn't exist
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True) 
