@echo off
REM Script para ejecutar scripts de Python dentro del contenedor Django

set PYTHON_SCRIPT=%1
set PYTHON_ARGS=%2 %3 %4 %5 %6 %7 %8 %9

if "%PYTHON_SCRIPT%"=="" (
    echo Uso: python-docker.bat [script.py] [argumentos...]
    echo Ejecuta un script de Python dentro del contenedor backend
    echo.
    echo Ejemplos:
    echo   python-docker.bat test_shipment_fix.py
    echo   python-docker.bat analyze_dhl_responses.py
    echo   python-docker.bat -c "import django; print(django.VERSION)"
    exit /b 1
)

echo Ejecutando: python %PYTHON_SCRIPT% %PYTHON_ARGS%
docker-compose -f docker-compose.yml exec backend python %PYTHON_SCRIPT% %PYTHON_ARGS%
