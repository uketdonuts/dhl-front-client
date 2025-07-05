#!/bin/bash

# Script de inicio rápido para DHL Front Client (Django + React)
# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Iniciando DHL Front Client (Django + React)...${NC}"

# Verificar si Docker está corriendo
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker no está corriendo. Por favor inicia Docker y vuelve a intentar.${NC}"
    exit 1
fi

# Verificar si existe el archivo .env
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Archivo .env no encontrado. Copiando desde env.example...${NC}"
    cp env.example .env
    echo -e "${GREEN}✅ Archivo .env creado. Puedes editarlo si necesitas configuraciones específicas.${NC}"
fi

# Detener contenedores existentes
echo -e "${BLUE}🔄 Deteniendo contenedores existentes...${NC}"
docker-compose down

# Construir y levantar contenedores
echo -e "${BLUE}🔨 Construyendo y levantando contenedores...${NC}"
docker-compose up -d --build

# Esperar a que los servicios estén listos
echo -e "${BLUE}⏳ Esperando a que los servicios estén listos...${NC}"
sleep 30

# Verificar estado de los contenedores
echo -e "${BLUE}🔍 Verificando estado de los contenedores...${NC}"
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Todos los contenedores están corriendo${NC}"
else
    echo -e "${RED}❌ Algunos contenedores no están corriendo. Revisando logs...${NC}"
    docker-compose logs
    exit 1
fi

# Inicializar Django
echo -e "${BLUE}🔧 Inicializando Django...${NC}"
docker-compose exec -T backend python init_django.py

# Verificar que la API esté respondiendo
echo -e "${BLUE}🔍 Verificando que la API esté respondiendo...${NC}"
sleep 10

if curl -s http://localhost:8000/api/login/ > /dev/null; then
    echo -e "${GREEN}✅ API Django funcionando correctamente${NC}"
else
    echo -e "${YELLOW}⚠️  API Django no responde aún. Puede tardar unos minutos más...${NC}"
fi

# Mostrar información de acceso
echo -e "${GREEN}"
echo "🎉 ¡DHL Front Client iniciado exitosamente!"
echo ""
echo "📋 Información de acceso:"
echo "   🌐 Frontend: http://localhost:3002"
echo "   🔌 API: http://localhost:8000/api"
echo "   ⚙️  Admin Django: http://localhost:8000/admin"
echo ""
echo "🔑 Credenciales por defecto:"
echo "   👤 Usuario: admin"
echo "   🔒 Contraseña: admin123"
echo ""
echo "📚 Endpoints disponibles:"
echo "   POST /api/login/ - Autenticación"
echo "   POST /api/dhl/rate/ - Cotización de tarifas"
echo "   POST /api/dhl/shipment/ - Crear envío"
echo "   POST /api/dhl/tracking/ - Seguimiento"
echo "   POST /api/dhl/epod/ - Obtener ePOD"
echo ""
echo "🔧 Comandos útiles:"
echo "   docker-compose logs -f backend    # Ver logs del backend"
echo "   docker-compose logs -f frontend   # Ver logs del frontend"
echo "   docker-compose down               # Detener servicios"
echo "   docker-compose restart            # Reiniciar servicios"
echo "${NC}"

# Opcional: abrir el navegador
read -p "¿Quieres abrir el frontend en el navegador? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v open > /dev/null; then
        open http://localhost:3002
    elif command -v xdg-open > /dev/null; then
        xdg-open http://localhost:3002
    else
        echo -e "${YELLOW}⚠️  No se pudo abrir el navegador automáticamente. Abre manualmente: http://localhost:3002${NC}"
    fi
fi

echo -e "${GREEN}✨ ¡Listo! Tu aplicación DHL Front Client está corriendo.${NC}" 