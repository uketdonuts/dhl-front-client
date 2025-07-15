import multiprocessing
import os

# Configuración básica
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 120

# Configuración de logging
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "debug"
capture_output = True
enable_stdio_inheritance = True

# Configuración de worker
worker_tmp_dir = "/dev/shm"
graceful_timeout = 120
keepalive = 5

# Configuración de proceso
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Configuración de SSL
keyfile = None
certfile = None

# Configuración de debugging
reload = True
reload_engine = "auto"
spew = False
check_config = False

# Configuración de logging detallado
logconfig_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'gunicorn.error': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': True,
        },
        'gunicorn.access': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': True,
        },
    }
} 