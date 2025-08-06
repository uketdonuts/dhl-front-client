@echo off
REM Script para gestionar nginx en el proyecto DHL

set NGINX_SERVICE=nginx

if "%1"=="up" (
    echo Iniciando nginx...
    docker-compose up -d %NGINX_SERVICE%
    echo Nginx iniciado. Disponible en:
    echo   - Puerto 80: http://localhost
    echo   - Puerto 10000: http://localhost:10000
    goto :end
)

if "%1"=="down" (
    echo Deteniendo nginx...
    docker-compose stop %NGINX_SERVICE%
    goto :end
)

if "%1"=="restart" (
    echo Reiniciando nginx...
    docker-compose restart %NGINX_SERVICE%
    goto :end
)

if "%1"=="logs" (
    echo Mostrando logs de nginx...
    docker-compose logs -f %NGINX_SERVICE%
    goto :end
)

if "%1"=="status" (
    echo Estado de nginx:
    docker-compose ps %NGINX_SERVICE%
    goto :end
)

if "%1"=="test" (
    echo Probando configuración de nginx...
    docker-compose exec %NGINX_SERVICE% nginx -t
    goto :end
)

if "%1"=="reload" (
    echo Recargando configuración de nginx...
    docker-compose exec %NGINX_SERVICE% nginx -s reload
    goto :end
)

echo.
echo Uso: nginx-manager.bat [comando]
echo.
echo Comandos disponibles:
echo   up       - Iniciar nginx
echo   down     - Detener nginx
echo   restart  - Reiniciar nginx
echo   logs     - Ver logs de nginx
echo   status   - Ver estado de nginx
echo   test     - Probar configuración de nginx
echo   reload   - Recargar configuración de nginx
echo.
echo Ejemplos:
echo   nginx-manager.bat up
echo   nginx-manager.bat logs
echo   nginx-manager.bat test

:end
