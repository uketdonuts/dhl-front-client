@echo off
REM Script para gestión de contenedores Docker en desarrollo
REM Uso: docker-dev.bat [up|down|logs|status|db-shell|reset-db]

if "%1"=="up" (
    echo Iniciando servicios Docker...
    docker-compose up -d
    goto end
)

if "%1"=="down" (
    echo Deteniendo servicios Docker...
    docker-compose down
    goto end
)

if "%1"=="logs" (
    if "%2"=="" (
        echo Mostrando logs de todos los servicios...
        docker-compose logs -f
    ) else (
        echo Mostrando logs del servicio %2...
        docker-compose logs -f %2
    )
    goto end
)

if "%1"=="status" (
    echo Estado de los contenedores...
    docker-compose ps
    goto end
)

if "%1"=="db-shell" (
    echo Conectando a la base de datos PostgreSQL...
    docker-compose exec postgres psql -U dhl_user -d dhl_db
    goto end
)

if "%1"=="reset-db" (
    echo Reseteando base de datos...
    docker-compose down
    docker volume rm dhl-front-client_postgres_data 2>nul
    docker-compose up -d postgres
    timeout /t 10
    docker-compose up -d backend
    goto end
)

echo Uso: docker-dev.bat [up^|down^|logs^|status^|db-shell^|reset-db]
echo.
echo Comandos disponibles:
echo   up        - Inicia los servicios
echo   down      - Detiene los servicios  
echo   logs      - Muestra logs (opcional: nombre del servicio)
echo   status    - Muestra estado de contenedores
echo   db-shell  - Conecta a PostgreSQL
echo   reset-db  - Resetea la base de datos

:end
