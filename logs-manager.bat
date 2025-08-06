@echo off
REM Script de gestión de logs para proyecto DHL
REM Permite gestionar logs usando Docker

echo.
echo ====================================
echo   GESTOR DE LOGS DHL PROJECT
echo ====================================
echo.

:menu
echo Opciones disponibles:
echo.
echo 1. Ver logs en tiempo real (Django)
echo 2. Ver logs en tiempo real (Frontend) 
echo 3. Ver estadisticas de logs
echo 4. Buscar en logs
echo 5. Limpiar logs antiguos
echo 6. Comprimir logs
echo 7. Ver logs por fecha
echo 8. Ejecutar gestor interactivo
echo 9. Salir
echo.

set /p choice="Selecciona una opcion (1-9): "

if "%choice%"=="1" goto django_logs
if "%choice%"=="2" goto frontend_logs
if "%choice%"=="3" goto stats
if "%choice%"=="4" goto search
if "%choice%"=="5" goto clean
if "%choice%"=="6" goto compress
if "%choice%"=="7" goto by_date
if "%choice%"=="8" goto interactive
if "%choice%"=="9" goto exit
goto invalid

:django_logs
echo.
echo 📄 Logs de Django en tiempo real...
echo ====================================
docker-dev.bat logs -f backend
goto menu

:frontend_logs
echo.
echo 📄 Logs de Frontend en tiempo real...
echo ====================================
docker-dev.bat logs -f frontend
goto menu

:stats
echo.
echo 📊 Estadisticas de logs...
echo ========================
python-docker.bat manage_logs.py --stats
goto menu

:search
set /p pattern="Patron a buscar: "
echo.
echo 🔍 Buscando '%pattern%' en logs...
echo ================================
python-docker.bat manage_logs.py --search "%pattern%"
goto menu

:clean
set /p days="Dias a mantener (30): "
if "%days%"=="" set days=30
echo.
echo 🧹 Limpiando logs con mas de %days% dias...
echo ==========================================
python-docker.bat manage_logs.py --clean %days%
goto menu

:compress
set /p days="Comprimir logs con mas de X dias (7): "
if "%days%"=="" set days=7
echo.
echo 🗜️ Comprimiendo logs con mas de %days% dias...
echo ============================================
python-docker.bat manage_logs.py --compress %days%
goto menu

:by_date
echo.
echo 📅 Logs por fecha disponibles:
echo =============================
dir /b logs\*.log.*
echo.
set /p date="Fecha a ver (YYYY-MM-DD): "
if exist "logs\django.log.%date%" (
    echo.
    echo 📄 Log de Django para %date%:
    echo ============================
    type "logs\django.log.%date%"
) else (
    echo ❌ No existe log para la fecha %date%
)
goto menu

:interactive
echo.
echo 🚀 Iniciando gestor interactivo...
echo ================================
python-docker.bat manage_logs.py
goto menu

:invalid
echo.
echo ❌ Opcion invalida. Por favor selecciona 1-9.
goto menu

:exit
echo.
echo 👋 ¡Hasta luego!
pause
