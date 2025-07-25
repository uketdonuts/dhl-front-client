@echo off
REM Script para construir y preparar deployment a GitHub Pages
REM Uso: build-github-pages.bat

echo 🚀 Construyendo aplicación para GitHub Pages...

REM Limpiar builds anteriores
if exist "github-pages-build" (
    echo 🧹 Limpiando build anterior...
    rmdir /s /q github-pages-build
)

REM Crear directorio de build
mkdir github-pages-build

echo 📦 Ejecutando build con Docker Compose...

REM Ejecutar build usando docker compose
docker compose --profile github-pages up --build github-pages-build

echo ✅ Build completado!
echo.
echo 📁 Los archivos están listos en: .\github-pages-build\
echo.
echo 📤 Para desplegar a GitHub Pages:
echo    1. Hacer push de este código al repositorio
echo    2. Activar GitHub Pages en la configuración del repo
echo    3. El GitHub Action desplegará automáticamente
echo.
echo 🌐 URL esperada: https://uketdonuts.github.io/dhl-front-client/

pause