# DHL Front Client - Django + React

Integración completa de la API de DHL Express MyDHL con backend en Django y frontend en React, optimizada para producción.

## 🚀 Características

### Backend Django
- ✅ **API REST completa** con Django REST Framework
- ✅ **Autenticación JWT** con tokens de acceso y refresh
- ✅ **Base de datos PostgreSQL** para persistencia de datos
- ✅ **Cache en memoria** para mejorar rendimiento
- ✅ **Logging avanzado** con rotación de archivos
- ✅ **Rate limiting** para proteger la API
- ✅ **CORS configurado** para frontend
- ✅ **Admin de Django** para gestión de datos
- ✅ **Configuración de producción** con Gunicorn y Nginx

### Frontend React
- ✅ **Interfaz moderna** con Tailwind CSS
- ✅ **Autenticación completa** con JWT
- ✅ **Cotización de tarifas** en tiempo real
- ✅ **Seguimiento de envíos** con eventos detallados
- ✅ **Creación de envíos** con formulario completo
- ✅ **ePOD (Proof of Delivery)** con previsualización PDF
- ✅ **Datos de prueba** generados automáticamente
- ✅ **Responsive design** para móviles y desktop

### Servicios DHL
- ✅ **Rating API** - Cotización de tarifas
- ✅ **Shipment API** - Creación de envíos
- ✅ **Tracking API** - Seguimiento de envíos
- ✅ **ePOD API** - Comprobantes de entrega
- ✅ **Modo sandbox** para desarrollo y pruebas

## 🛠️ Tecnologías

### Backend
- **Django 4.2.7** - Framework web
- **Django REST Framework** - API REST
- **PostgreSQL** - Base de datos

- **Gunicorn** - Servidor WSGI
- **Nginx** - Proxy reverso (producción)

### Frontend
- **React 18** - Framework frontend
- **Tailwind CSS** - Framework CSS
- **Axios** - Cliente HTTP
- **React Router** - Navegación

### DevOps
- **Docker** - Contenedores
- **Docker Compose** - Orquestación
- **Nginx** - Proxy y estáticos

## 📋 Requisitos

- Docker y Docker Compose
- Git
- 4GB RAM mínimo
- 10GB espacio libre

## 🚀 Instalación Rápida

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd dhl-front-client
```

### 2. Configurar variables de entorno
```bash
cp env.example .env
# Editar .env con tus configuraciones
```

### 3. Desplegar con Docker
```bash
# Desarrollo (sin Nginx)
docker-compose up -d

# Producción (con Nginx)
docker-compose --profile production up -d
```

### 4. Inicializar Django
```bash
# Crear superusuario y migraciones
docker-compose exec backend python init_django.py
```

### 5. Acceder a la aplicación
- **Frontend**: http://localhost:3002
- **API**: http://localhost:8000/api
- **Admin Django**: http://localhost:8000/admin
- **Credenciales**: admin / admin123

## 🔧 Configuración Detallada

### Variables de Entorno

#### Desarrollo (.env)
```env
DEBUG=True
SECRET_KEY=tu-clave-secreta
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos
DB_NAME=dhl_db
DB_USER=dhl_user
DB_PASSWORD=dhl_password
DB_HOST=postgres
DB_PORT=5432



# DHL API
DHL_USERNAME=tu-username
DHL_PASSWORD=tu-password
DHL_BASE_URL=https://wsbexpress.dhl.com
DHL_ENVIRONMENT=sandbox

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3002
```

#### Producción
```env
DEBUG=False
SECRET_KEY=clave-super-segura-de-produccion
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Configuraciones adicionales de producción...
```

### Estructura del Proyecto
```
dhl-front-client/
├── dhl_project/          # Configuración Django
│   ├── settings.py       # Configuraciones
│   ├── urls.py          # URLs principales
│   └── wsgi.py          # WSGI para producción
├── dhl_api/             # App principal
│   ├── models.py        # Modelos de datos
│   ├── views.py         # Vistas API
│   ├── serializers.py   # Serializers DRF
│   ├── services.py      # Servicio DHL
│   └── admin.py         # Admin Django
├── frontend/            # React app
├── docker-compose.yml   # Orquestación Docker
├── Dockerfile          # Docker Django
├── nginx.conf          # Configuración Nginx
├── start.sh            # Script de inicio
└── requirements.txt    # Dependencias Python
```

## 📚 API Endpoints

### Autenticación
- `POST /api/login/` - Login de usuario

### DHL API
- `POST /api/dhl/rate/` - Cotización de tarifas
- `POST /api/dhl/shipment/` - Crear envío
- `POST /api/dhl/tracking/` - Seguimiento
- `POST /api/dhl/epod/` - Obtener ePOD

### Gestión
- `GET /api/shipments/` - Listar envíos
- `GET /api/shipments/{id}/` - Detalle de envío
- `GET /api/rates/history/` - Historial de cotizaciones
- `GET /api/test-data/` - Datos de prueba

## 🔒 Seguridad

### Autenticación
- JWT tokens con expiración
- Refresh tokens automáticos
- Rate limiting por usuario

### API Security
- CORS configurado
- Headers de seguridad
- Validación de datos
- Logging de auditoría

### Producción
- HTTPS obligatorio
- Headers de seguridad
- Rate limiting
- Monitoreo de logs

## 📊 Monitoreo y Logs

### Logs de Django
```bash
# Ver logs del backend
docker-compose logs backend

# Ver logs en tiempo real
docker-compose logs -f backend
```

### Logs de Nginx
```bash
# Ver logs de acceso
docker-compose exec nginx tail -f /var/log/nginx/access.log

# Ver logs de error
docker-compose exec nginx tail -f /var/log/nginx/error.log
```

### Health Checks
- **Backend**: http://localhost:8000/health/
- **Frontend**: http://localhost:3002
- **Database**: Automático en Docker Compose

## 🚀 Despliegue en Producción

### 1. Configurar variables de producción
```bash
cp env.example .env.prod
# Editar con configuraciones de producción
```

### 2. Desplegar con Nginx
```bash
docker-compose --profile production up -d
```

### 3. Configurar SSL (opcional)
```bash
# Editar nginx.conf y descomentar sección HTTPS
# Agregar certificados SSL
```

### 4. Monitoreo
```bash
# Verificar estado de servicios
docker-compose ps

# Ver logs
docker-compose logs -f
```

## 🧪 Testing

### Endpoints de Prueba
```bash
# Login
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Cotización
curl -X POST http://localhost:8000/api/dhl/rate/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"origin":{"address":"123 Main St","city":"New York","state":"NY","postal_code":"10001","country":"US"},"destination":{"address":"456 Oak Ave","city":"Los Angeles","state":"CA","postal_code":"90210","country":"US"},"weight":2.5,"dimensions":{"length":15,"width":10,"height":8}}'
```

## 🔧 Comandos Útiles

### Django Management
```bash
# Migraciones
docker-compose exec backend python manage.py migrate

# Crear superusuario
docker-compose exec backend python manage.py createsuperuser

# Shell de Django
docker-compose exec backend python manage.py shell

# Collect static
docker-compose exec backend python manage.py collectstatic
```

### Docker
```bash
# Reconstruir imágenes
docker-compose build --no-cache

# Reiniciar servicios
docker-compose restart

# Ver logs
docker-compose logs -f [service]

# Limpiar volúmenes
docker-compose down -v
```

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📞 Soporte

Para soporte técnico o preguntas:
- Crear un issue en GitHub
- Contactar al equipo de desarrollo
- Revisar la documentación de DHL Express API

---

**Desarrollado con ❤️ para integración con DHL Express API** 