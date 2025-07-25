import os

# Configuración optimizada para Render Free Tier (500MB RAM, 0.1 CPU)
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"

# Solo 1 worker para conservar memoria
workers = 1
worker_class = "sync"
worker_connections = 50

# Timeouts reducidos para liberar recursos rápidamente
timeout = 60
graceful_timeout = 30
keepalive = 2

# Límites de requests para evitar memory leaks
max_requests = 200
max_requests_jitter = 20

# Logging mínimo para conservar recursos
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "warning"  # Solo warnings y errores
capture_output = True
enable_stdio_inheritance = True

# Configuración de memoria
preload_app = True  # Cargar app una vez y compartir entre workers
worker_tmp_dir = "/dev/shm"  # Usar memoria compartida si está disponible

# Configuración de proceso
daemon = False
pidfile = None
umask = 0

# Configuración adicional para optimización
forwarded_allow_ips = "*"
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}
