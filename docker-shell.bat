@echo off
REM Script para abrir un shell interactivo en el contenedor backend

echo Abriendo shell en el contenedor backend...
docker-compose -f docker-compose.yml exec backend /bin/bash
