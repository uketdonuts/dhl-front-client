@echo off
REM Script para ejecutar comandos de Django dentro del contenedor

set DJANGO_COMMAND=%*

if "%DJANGO_COMMAND%"=="" (
    echo Uso: django-manage.bat [comando Django]
    echo Ejemplos:
    echo   django-manage.bat migrate
    echo   django-manage.bat makemigrations
    echo   django-manage.bat createsuperuser
    echo   django-manage.bat shell
    exit /b 1
)

echo Ejecutando: python manage.py %DJANGO_COMMAND%
docker-compose -f docker-compose.yml exec backend python manage.py %DJANGO_COMMAND%
