@echo off
REM Script para gestionar el entorno de desarrollo Docker

set COMMAND=%1

if "%COMMAND%"=="up" (
    echo Iniciando servicios Docker para desarrollo...
    docker-compose -f docker-compose.dev.yml up -d
    echo Servicios iniciados:
    echo - Backend: http://localhost:8000
    echo - Frontend: http://localhost:3000
    echo - Admin Django: http://localhost:8000/admin
) else if "%COMMAND%"=="down" (
    echo Deteniendo servicios Docker...
    docker-compose -f docker-compose.dev.yml down
) else if "%COMMAND%"=="build" (
    echo Reconstruyendo imágenes Docker...
    docker-compose -f docker-compose.dev.yml build --no-cache
) else if "%COMMAND%"=="logs" (
    echo Mostrando logs de todos los servicios...
    docker-compose -f docker-compose.dev.yml logs -f
) else if "%COMMAND%"=="logs-back" (
    echo Mostrando logs del backend...
    docker-compose -f docker-compose.dev.yml logs -f backend
) else if "%COMMAND%"=="logs-front" (
    echo Mostrando logs del frontend...
    docker-compose -f docker-compose.dev.yml logs -f frontend
) else if "%COMMAND%"=="status" (
    echo Estado de los servicios...
    docker-compose -f docker-compose.dev.yml ps
) else if "%COMMAND%"=="restart" (
    echo Reiniciando servicios...
    docker-compose -f docker-compose.dev.yml restart
) else if "%COMMAND%"=="db-shell" (
    echo Abriendo shell de PostgreSQL...
    docker-compose -f docker-compose.dev.yml exec postgres psql -U dhl_user -d dhl_db
) else if "%COMMAND%"=="reset-db" (
    echo Reiniciando base de datos...
    docker-compose -f docker-compose.dev.yml down
    docker volume rm dhl-front-client_postgres_data_dev 2>nul
    docker-compose -f docker-compose.dev.yml up -d
) else (
    echo Uso: docker-dev.bat [COMANDO]
    echo Comandos disponibles:
    echo   up         - Iniciar servicios
    echo   down       - Detener servicios
    echo   build      - Reconstruir imágenes
    echo   logs       - Ver logs de todos los servicios
    echo   logs-back  - Ver logs del backend
    echo   logs-front - Ver logs del frontend
    echo   status     - Ver estado de servicios
    echo   restart    - Reiniciar servicios
    echo   db-shell   - Abrir shell de PostgreSQL
    echo   reset-db   - Reiniciar base de datos
)
