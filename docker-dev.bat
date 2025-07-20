@echo off
REM Script para gestionar el entorno de desarrollo Docker

set COMMAND=%1

if "%COMMAND%"=="up" (
    echo Iniciando servicios Docker...
    docker-compose -f docker-compose.yml up -d
    echo Servicios iniciados. Frontend: http://localhost:3002
) else if "%COMMAND%"=="down" (
    echo Deteniendo servicios Docker...
    docker-compose -f docker-compose.yml down
) else if "%COMMAND%"=="build" (
    echo Reconstruyendo imágenes Docker...
    docker-compose -f docker-compose.yml build --no-cache
) else if "%COMMAND%"=="logs-back" (
    echo Mostrando logs del backend...
    docker-compose -f docker-compose.yml logs -f backend
) else if "%COMMAND%"=="logs-front" (
    echo Mostrando logs del frontend...
    docker-compose -f docker-compose.yml logs -f frontend
) else (
    echo Uso: docker-dev.bat [up^|down^|build^|logs-back^|logs-front]
    echo   up        - Iniciar servicios
    echo   down      - Detener servicios
    echo   build     - Reconstruir imágenes
    echo   logs-back - Ver logs del backend
    echo   logs-front- Ver logs del frontend
)
