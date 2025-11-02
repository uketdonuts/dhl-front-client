@echo off
REM Script para ejecutar comandos Django dentro del contenedor
REM Uso: django-manage.bat [comando]

if "%1"=="" (
    echo Uso: django-manage.bat [comando]
    echo.
    echo Ejemplos:
    echo   django-manage.bat runserver
    echo   django-manage.bat migrate
    echo   django-manage.bat makemigrations
    echo   django-manage.bat shell
    echo   django-manage.bat createsuperuser
    echo   django-manage.bat collectstatic
    echo   django-manage.bat test
    goto end
)

echo Ejecutando: python manage.py %*
docker-compose exec backend python manage.py %*

:end
