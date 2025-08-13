@echo off
echo ================================
echo    DHL API Docker Deployment
echo ================================

echo.
echo Construyendo y desplegando la aplicación...
echo.

REM Detener contenedores existentes
echo Deteniendo contenedores existentes...
docker-compose down

echo.
echo Construyendo imagen de Docker...
docker-compose build

echo.
echo Iniciando servicios...
docker-compose up -d

echo.
echo Esperando a que la base de datos esté lista...
timeout /t 10

echo.
echo Verificando el estado de los contenedores...
docker-compose ps

echo.
echo ================================
echo    Despliegue completado!
echo ================================
echo.
echo La aplicación está corriendo en: http://localhost:8000
echo.
echo Comandos útiles:
echo   Ver logs:           docker-compose logs -f
echo   Detener servicios:  docker-compose down
echo   Reiniciar:          docker-compose restart
echo   Shell del contenedor: docker-compose exec web bash
echo.
echo Presiona cualquier tecla para salir...
pause > nul
