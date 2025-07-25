#!/bin/bash

# Script de build optimizado para Render Static Site
echo "🚀 Iniciando build del frontend React para Render..."

# Verificar Node.js version
echo "📦 Node.js version:"
node --version
npm --version

# Limpiar cache de npm
echo "🧹 Limpiando cache..."
npm cache clean --force

# Instalar dependencias de producción
echo "📥 Instalando dependencias..."
npm ci --only=production --no-audit --no-fund --prefer-offline

# Instalar dependencias de desarrollo necesarias para el build
echo "🔧 Instalando dependencias de desarrollo para build..."
npm install --no-save react-scripts

# Verificar que react-scripts esté disponible
if ! command -v react-scripts &> /dev/null; then
    echo "❌ react-scripts no encontrado, instalando globalmente..."
    npm install -g react-scripts
fi

# Configurar variables de entorno para el build
export NODE_ENV=production
export GENERATE_SOURCEMAP=false
export CI=false
export BUILD_PATH=build

# Ejecutar el build
echo "🏗️ Construyendo aplicación React..."
npm run build

# Verificar que el build fue exitoso
if [ -d "build" ]; then
    echo "✅ Build completado exitosamente!"
    echo "📁 Contenido del directorio build:"
    ls -la build/
else
    echo "❌ Error: Directorio build no encontrado"
    exit 1
fi

echo "🎉 Frontend listo para deploy!"
