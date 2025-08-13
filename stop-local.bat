@echo off
echo ================================
echo   Deteniendo DHL API Docker
echo ================================

echo.
echo Deteniendo contenedores...
docker-compose down

echo.
echo Eliminando volúmenes (opcional)...
set /p remove_volumes="¿Deseas eliminar los volúmenes de datos? (y/N): "
if /i "%remove_volumes%"=="y" (
    docker-compose down -v
    echo Volúmenes eliminados.
) else (
    echo Volúmenes conservados.
)

echo.
echo ================================
echo     Servicios detenidos
echo ================================
echo.
echo Presiona cualquier tecla para salir...
pause > nul
