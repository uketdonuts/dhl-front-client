#!/bin/bash

# ===========================================
#    DHL API - DEPLOYMENT NATIVO COMPLETO
# ===========================================
# Script único para deployment sin Docker
# Incluye: instalación, configuración y startup
# ===========================================

set -e  # Salir en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Función para detectar OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if [ -f /etc/debian_version ]; then
            DISTRO="debian"
        elif [ -f /etc/redhat-release ]; then
            DISTRO="redhat"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        error "OS no soportado: $OSTYPE"
    fi
    log "OS detectado: $OS ($DISTRO)"
}

# Función para instalar dependencias del sistema
install_system_deps() {
    log "Instalando dependencias del sistema..."
    
    if [ "$OS" = "linux" ]; then
        if [ "$DISTRO" = "debian" ]; then
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx curl git
        elif [ "$DISTRO" = "redhat" ]; then
            sudo yum update -y
            sudo yum install -y python3 python3-pip postgresql postgresql-server nginx curl git
        fi
    elif [ "$OS" = "macos" ]; then
        if ! command -v brew &> /dev/null; then
            error "Homebrew no encontrado. Instala Homebrew primero."
        fi
        brew install python3 postgresql nginx
    fi
}

# Función para configurar PostgreSQL
setup_postgresql() {
    log "Configurando PostgreSQL..."
    
    # Inicializar PostgreSQL si es necesario
    if [ "$DISTRO" = "redhat" ]; then
        sudo postgresql-setup initdb
    fi
    
    # Iniciar servicio
    if [ "$OS" = "linux" ]; then
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    elif [ "$OS" = "macos" ]; then
        brew services start postgresql
    fi
    
    # Crear usuario y base de datos
    sudo -u postgres psql -c "CREATE USER dhl_user WITH PASSWORD 'dhl_secure_password_2025';" || true
    sudo -u postgres psql -c "CREATE DATABASE dhl_db OWNER dhl_user;" || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dhl_db TO dhl_user;" || true
    
    log "PostgreSQL configurado correctamente"
}

# Función para crear entorno virtual Python
setup_python_env() {
    log "Configurando entorno Python..."
    
    # Crear entorno virtual
    python3 -m venv venv
    source venv/bin/activate
    
    # Actualizar pip
    pip install --upgrade pip
    
    # Instalar dependencias
    pip install -r requirements.txt
    
    log "Entorno Python configurado"
}

# Función para configurar variables de entorno
setup_env() {
    log "Configurando variables de entorno..."
    
    if [ ! -f .env ]; then
        cp env.example .env
        warning "Archivo .env creado desde ejemplo. Configura las variables necesarias."
    fi
    
    # Configurar para producción nativa
    cat > .env.production << EOF
DEBUG=False
SECRET_KEY=your-super-secret-key-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
DATABASE_URL=postgresql://dhl_user:dhl_secure_password_2025@localhost:5432/dhl_db
DHL_USERNAME=your-dhl-username
DHL_PASSWORD=your-dhl-password
DHL_BASE_URL=https://express.api.dhl.com
DHL_ENVIRONMENT=production
EOF
    
    log "Variables de entorno configuradas"
}

# Función para configurar Django
setup_django() {
    log "Configurando Django..."
    
    source venv/bin/activate
    
    # Ejecutar migraciones
    python manage.py migrate
    
    # Recopilar archivos estáticos
    python manage.py collectstatic --noinput
    
    # Cargar datos iniciales si existen
    if [ -f dhl_api/ESD.TXT ]; then
        python manage.py load_esd_data || warning "No se pudieron cargar datos ESD"
    fi
    
    log "Django configurado correctamente"
}

# Función para configurar Nginx
setup_nginx() {
    log "Configurando Nginx..."
    
    # Crear configuración de Nginx
    sudo tee /etc/nginx/sites-available/dhl-api << EOF
server {
    listen 80;
    server_name localhost;
    
    # Archivos estáticos
    location /static/ {
        alias $(pwd)/staticfiles/;
    }
    
    location /media/ {
        alias $(pwd)/media/;
    }
    
    # Proxy a Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Habilitar sitio
    sudo ln -sf /etc/nginx/sites-available/dhl-api /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Reiniciar Nginx
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    log "Nginx configurado correctamente"
}

# Función para crear archivos de configuración Gunicorn
create_gunicorn_config() {
    log "Creando configuración de Gunicorn..."
    
    cat > gunicorn.conf.py << EOF
# Configuración de Gunicorn para producción nativa
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 60
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%h %l %u %t "%r" %s %b "%{Referer}i" "%{User-Agent}i"'

# Process naming
proc_name = 'dhl_api'

# Server mechanics
daemon = False
pidfile = '/tmp/gunicorn.pid'
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None
EOF
    
    log "Configuración de Gunicorn creada"
}

# Función para crear servicios systemd
create_systemd_services() {
    log "Creando servicios systemd..."
    
    # Servicio Django
    sudo tee /etc/systemd/system/dhl-api.service << EOF
[Unit]
Description=DHL API Django Application
After=network.target postgresql.service

[Service]
Type=notify
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/gunicorn --config gunicorn.conf.py dhl_project.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Recargar systemd
    sudo systemctl daemon-reload
    sudo systemctl enable dhl-api.service
    
    log "Servicios systemd creados"
}

# Función para crear script de inicio/parada
create_control_script() {
    log "Creando script de control..."
    
    cat > dhl-control.sh << 'EOF'
#!/bin/bash

# Script de control para DHL API

case "$1" in
    start)
        echo "Iniciando DHL API..."
        sudo systemctl start postgresql
        sudo systemctl start nginx
        sudo systemctl start dhl-api
        echo "DHL API iniciado"
        ;;
    stop)
        echo "Deteniendo DHL API..."
        sudo systemctl stop dhl-api
        sudo systemctl stop nginx
        echo "DHL API detenido"
        ;;
    restart)
        echo "Reiniciando DHL API..."
        sudo systemctl restart dhl-api
        sudo systemctl restart nginx
        echo "DHL API reiniciado"
        ;;
    status)
        echo "Estado de los servicios:"
        sudo systemctl status dhl-api --no-pager
        sudo systemctl status nginx --no-pager
        sudo systemctl status postgresql --no-pager
        ;;
    logs)
        echo "Logs de DHL API:"
        sudo journalctl -u dhl-api -f
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
EOF
    
    chmod +x dhl-control.sh
    log "Script de control creado: ./dhl-control.sh"
}

# Función principal de instalación
install() {
    log "=== INICIANDO INSTALACIÓN DHL API ==="
    
    detect_os
    install_system_deps
    setup_postgresql
    setup_python_env
    setup_env
    setup_django
    create_gunicorn_config
    setup_nginx
    create_systemd_services
    create_control_script
    
    log "=== INSTALACIÓN COMPLETADA ==="
    info "Para controlar el servicio usa: ./dhl-control.sh {start|stop|restart|status|logs}"
    info "URL: http://localhost"
}

# Función para inicio rápido (si ya está instalado)
start() {
    log "Iniciando DHL API..."
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Crear directorio de logs si no existe
    mkdir -p logs
    
    # Verificar base de datos
    python manage.py migrate
    
    # Iniciar servicios
    sudo systemctl start postgresql
    sudo systemctl start nginx
    sudo systemctl start dhl-api
    
    log "DHL API iniciado en http://localhost"
}

# Función para desarrollo
dev() {
    log "Iniciando en modo desarrollo..."
    
    source venv/bin/activate
    mkdir -p logs
    
    # Variables de desarrollo
    export DEBUG=True
    export ALLOWED_HOSTS=localhost,127.0.0.1
    
    python manage.py migrate
    python manage.py runserver 0.0.0.0:8000
}

# Función de ayuda
help() {
    echo "DHL API - Deployment Nativo"
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos:"
    echo "  install   - Instalación completa del sistema"
    echo "  start     - Iniciar servicios (modo producción)"
    echo "  dev       - Iniciar en modo desarrollo"
    echo "  help      - Mostrar esta ayuda"
    echo ""
    echo "Después de la instalación, usa ./dhl-control.sh para controlar los servicios"
}

# Script principal
main() {
    case "${1:-help}" in
        install)
            install
            ;;
        start)
            start
            ;;
        dev)
            dev
            ;;
        help|--help|-h)
            help
            ;;
        *)
            echo "Comando desconocido: $1"
            help
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"
