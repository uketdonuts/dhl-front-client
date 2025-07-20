@echo off
REM Script para ejecutar comandos de validación y pruebas

echo Validando entorno Docker DHL...
echo.

echo 1. Verificando contenedores en ejecución...
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.

echo 2. Verificando conectividad del frontend...
curl -s -o NUL -w "Frontend (http://localhost:3002): %%{http_code}\n" http://localhost:3002
echo.

echo 3. Verificando conectividad del backend...
curl -s -o NUL -w "Backend (http://localhost:8001): %%{http_code}\n" http://localhost:8001
echo.

echo 4. Verificando endpoint de salud Django...
curl -s -o NUL -w "Django Health: %%{http_code}\n" http://localhost:8001/admin/
echo.

echo 5. Verificando API DHL endpoints...
curl -s -o NUL -w "API DHL Rate: %%{http_code}\n" http://localhost:8001/api/dhl/rate/
curl -s -o NUL -w "API DHL Tracking: %%{http_code}\n" http://localhost:8001/api/dhl/tracking/
echo.

echo Validación completada.
echo Frontend disponible en: http://localhost:3002
echo Backend disponible en: http://localhost:8001
