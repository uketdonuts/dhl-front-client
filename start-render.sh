#!/bin/bash

# Script de inicio para Render Free Tier
echo "🚀 Iniciando aplicación DHL en Render..."

# Verificar variables de entorno críticas
if [ -z "$SECRET_KEY" ]; then
    echo "❌ ERROR: SECRET_KEY no está configurado"
    exit 1
fi

# Ejecutar migraciones
echo "📦 Ejecutando migraciones de base de datos..."
python manage.py migrate --noinput

# Crear superusuario si no existe (opcional)
if [ "$CREATE_SUPERUSER" = "true" ]; then
    echo "👤 Verificando superusuario..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superusuario creado: admin/admin123')
else:
    print('Superusuario ya existe')
"
fi

# Recolectar archivos estáticos (solo si no está deshabilitado)
if [ "$DISABLE_COLLECTSTATIC" != "1" ]; then
    echo "📁 Recolectando archivos estáticos..."
    python manage.py collectstatic --noinput
fi

# Verificar configuración
echo "✅ Verificando configuración..."
python manage.py check --deploy

echo "🎯 Iniciando servidor Gunicorn..."

# Comando optimizado para Render Free Tier
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --timeout 60 \
    --max-requests 200 \
    --max-requests-jitter 20 \
    --worker-class sync \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level warning \
    dhl_project.wsgi:application
