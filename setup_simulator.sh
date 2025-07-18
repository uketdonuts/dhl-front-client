#!/bin/bash

# Script para configurar variables de entorno en el contenedor Django
# Ejecutar este script para activar el modo simulador

echo "🔧 Configurando modo simulador DHL..."

# Exportar variables de entorno
export DHL_SIMULATE_MODE=true
export DHL_USERNAME=test_user
export DHL_PASSWORD=test_password
export DHL_BASE_URL=https://test.dhl.com
export DHL_ENVIRONMENT=development
export DEBUG=true

echo "✅ Variables de entorno configuradas:"
echo "   DHL_SIMULATE_MODE=$DHL_SIMULATE_MODE"
echo "   DHL_ENVIRONMENT=$DHL_ENVIRONMENT"
echo "   DEBUG=$DEBUG"

# Reiniciar el servidor Django
echo "🔄 Reiniciando servidor Django..."
python manage.py collectstatic --noinput
python manage.py migrate --noinput

echo "🚀 Servidor listo en modo simulador"
