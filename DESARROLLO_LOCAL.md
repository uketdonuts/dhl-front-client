# DHL API - Desarrollo Local

Este proyecto está configurado para funcionar tanto en desarrollo local con Docker Compose como en producción en Render.

## 🚀 Inicio Rápido - Desarrollo Local

### 1. Prerrequisitos
- Docker y Docker Compose instalados
- Git

### 2. Configuración

```bash
# Clonar el repositorio
git clone <tu-repo>
cd dhl-front-client

# El archivo .env ya está configurado para desarrollo local
# Revisa las credenciales DHL en .env si es necesario
```

### 3. Ejecutar el proyecto

```bash
# Iniciar todos los servicios
docker-dev.bat up

# Los servicios estarán disponibles en:
# - Backend Django: http://localhost:8000
# - Frontend React: http://localhost:3000
# - Admin Django: http://localhost:8000/admin
# - Health Check: http://localhost:8000/api/health/
```

## 🛠️ Comandos Útiles

```bash
# Ver estado de servicios
docker-dev.bat status

# Ver logs
docker-dev.bat logs              # Todos los servicios
docker-dev.bat logs-back         # Solo backend
docker-dev.bat logs-front        # Solo frontend

# Reconstruir imágenes
docker-dev.bat build

# Detener servicios
docker-dev.bat down

# Reiniciar servicios
docker-dev.bat restart
```

## 🗄️ Base de Datos

Por defecto usa **SQLite** para desarrollo local (no requiere configuración adicional).

### Migraciones

```bash
# Ejecutar migraciones
django-manage.bat migrate

# Crear nuevas migraciones
django-manage.bat makemigrations

# Crear superusuario
django-manage.bat createsuperuser
```

### Opcional: Usar PostgreSQL

Si prefieres usar PostgreSQL en desarrollo:

1. Descomenta el servicio `postgres` en `docker-compose.dev.yml`
2. Cambia `DATABASE_URL` en `.env`:
   ```
   DATABASE_URL=postgresql://dhl_user:dhl_password@postgres:5432/dhl_db
   ```

## 🔧 Configuración de Entorno

El archivo `.env` está configurado para desarrollo:

```env
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
DHL_ENVIRONMENT=sandbox
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3002
REACT_APP_API_URL=http://localhost:8000/api
```

## 📱 Frontend React

El frontend está configurado con:
- Hot reload automático
- Variables de entorno para desarrollo
- Proxy configurado para comunicarse con el backend
- Tailwind CSS

## 🔍 Debugging

### Ver logs en tiempo real
```bash
docker-dev.bat logs
```

### Acceder al shell del backend
```bash
docker-shell.bat
```

### Verificar servicios
```bash
# Health check
curl http://localhost:8000/api/health/

# Estado de Docker
docker-dev.bat status
```

## 🚢 Despliegue en Render

El proyecto también está configurado para Render con:
- `render.yaml` - Configuración de servicios
- `docker-compose.yml` - Configuración optimizada para producción
- `requirements.render.txt` - Dependencias mínimas

Para deployar en Render, simplemente conecta tu repositorio GitHub y Render usará automáticamente `render.yaml`.

## 📁 Estructura del Proyecto

```
dhl-front-client/
├── dhl_api/                 # App Django principal
├── dhl_project/             # Configuración Django
├── frontend/                # App React
├── docker-compose.dev.yml   # Docker para desarrollo
├── docker-compose.yml       # Docker para producción
├── .env                     # Variables de entorno desarrollo
├── render.yaml              # Configuración Render
└── docker-dev.bat          # Scripts de gestión
```

## 🆘 Solución de Problemas

### Puerto ocupado
```bash
# Si el puerto 8000 o 3000 están ocupados
docker-dev.bat down
# Cambiar puertos en docker-compose.dev.yml si es necesario
```

### Errores de permisos
```bash
# En Windows, ejecutar terminal como administrador
# En Linux/Mac, usar sudo si es necesario
```

### Base de datos corrupta
```bash
# Resetear base de datos SQLite
docker-dev.bat down
# Eliminar db.sqlite3 si existe
docker-dev.bat up
```
