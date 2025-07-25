#!/bin/bash

# Script para construir y preparar deployment a GitHub Pages
# Uso: ./build-github-pages.sh

set -e

echo "🚀 Construyendo aplicación para GitHub Pages..."

# Limpiar builds anteriores
if [ -d "github-pages-build" ]; then
    echo "🧹 Limpiando build anterior..."
    rm -rf github-pages-build
fi

# Crear directorio de build
mkdir -p github-pages-build

echo "📦 Ejecutando build con Docker Compose..."

# Ejecutar build usando docker compose
docker compose --profile github-pages up --build github-pages-build

echo "✅ Build completado!"
echo ""
echo "📁 Los archivos están listos en: ./github-pages-build/"
echo ""
echo "📤 Para desplegar a GitHub Pages:"
echo "   1. Hacer push de este código al repositorio"
echo "   2. Activar GitHub Pages en la configuración del repo"
echo "   3. El GitHub Action desplegará automáticamente"
echo ""
echo "🌐 URL esperada: https://uketdonuts.github.io/dhl-front-client/"