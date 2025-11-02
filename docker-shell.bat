@echo off
REM Script para acceder al shell del contenedor
REM Uso: docker-shell.bat [servicio]

set service=%1
if "%service%"=="" set service=backend

echo Accediendo al shell del contenedor %service%...
docker-compose exec %service% /bin/bash

:end
