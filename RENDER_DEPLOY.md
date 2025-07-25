# 🚀 Guía de Despliegue para Render Free Tier

## 📋 Resumen de Optimizaciones

Esta configuración está optimizada para la **versión gratuita de Render** con limitaciones de:
- **500MB RAM**
- **0.1 CPU**
- **SQLite** en lugar de PostgreSQL (ahorra ~200MB)
- **1 worker** de Gunicorn únicamente
- **Frontend estático separado** (sin contenedor React)

## 🗂️ Archivos Creados/Modificados

### Para el Backend (API Django)
- `docker-compose.yml` - Optimizado para desarrollo local ligero
- `Dockerfile.render` - Dockerfile específico para Render
- `requirements.render.txt` - Dependencias mínimas
- `settings_render.py` - Configuración Django ultra-optimizada
- `gunicorn.render.conf.py` - Configuración Gunicorn optimizada
- `start-render.sh` - Script de inicio para Render
- `render.yaml` - Configuración de servicios Render

## 🔧 Pasos para Despliegue en Render

### 1. Configurar el Backend (API Django)

1. **Crear nuevo Web Service en Render:**
   - Build Command: `pip install -r requirements.render.txt && python manage.py collectstatic --noinput`
   - Start Command: `bash start-render.sh`
   - Environment: `Python 3.11`

2. **Variables de Entorno Requeridas:**
   ```
   DJANGO_SETTINGS_MODULE=dhl_project.settings_render
   SECRET_KEY=[generar clave segura]
   DEBUG=False
   DATABASE_URL=sqlite:///db.sqlite3
   DHL_USERNAME=[tu_usuario_dhl]
   DHL_PASSWORD=[tu_password_dhl]
   DHL_BASE_URL=https://express.api.dhl.com
   DHL_ENVIRONMENT=production
   CORS_ALLOWED_ORIGINS=*
   ```

3. **Configuración del Servicio:**
   - **Region:** Oregon (más económico)
   - **Instance Type:** Free
   - **Auto-Deploy:** Habilitado

### 2. Configurar el Frontend (React)

1. **Crear nuevo Static Site en Render:**
   - Build Command: `cd frontend && npm ci && npm run build`
   - Publish Directory: `frontend/build`

2. **Variables de Entorno Frontend:**
   ```
   REACT_APP_API_URL=https://[tu-backend].onrender.com/api
   REACT_APP_BACKEND_URL=https://[tu-backend].onrender.com/api
   REACT_APP_ENVIRONMENT=production
   GENERATE_SOURCEMAP=false
   ```

## ⚡ Optimizaciones Implementadas

### Memoria (RAM)
- ✅ SQLite en lugar de PostgreSQL (-200MB)
- ✅ Solo 1 worker de Gunicorn (-100MB)
- ✅ Sin Celery/Redis (-150MB)
- ✅ Dependencias mínimas (-50MB)
- ✅ Frontend como sitio estático separado (-300MB)

### CPU
- ✅ 1 worker síncono únicamente
- ✅ Timeouts reducidos (60s)
- ✅ Máximo 200 requests por worker
- ✅ Logging mínimo (solo warnings/errores)
- ✅ Sin hot-reload en producción

### Almacenamiento
- ✅ WhiteNoise para archivos estáticos
- ✅ Sin volúmenes persistentes grandes
- ✅ SQLite embebida

## 🔧 Comandos Útiles para Desarrollo Local

```bash
# Usar configuración ligera para desarrollo
docker-compose up

# Probar configuración de Render localmente
docker build -f Dockerfile.render -t dhl-render .
docker run -p 10000:10000 --env-file .env dhl-render

# Ejecutar con settings de Render
python manage.py runserver --settings=dhl_project.settings_render
```

## 📊 Monitoreo de Recursos

### Verificar uso de memoria:
```bash
# En el contenedor de Render
ps aux --sort=-%mem | head -10
free -h
```

### Verificar logs optimizados:
```bash
# Solo errores críticos se registrarán
tail -f /app/logs/django.log
```

## ⚠️ Limitaciones del Free Tier

1. **Hibernación:** El servicio se duerme después de 15 minutos de inactividad
2. **750 horas/mes:** Límite mensual de tiempo activo
3. **Sin HTTPS personalizado:** Solo subdominios .onrender.com
4. **Sin persistencia:** Los archivos se pierden en cada deploy

## 🛠️ Solución de Problemas

### Si la aplicación consume mucha memoria:
1. Verificar que está usando `settings_render.py`
2. Confirmar que PostgreSQL está deshabilitado
3. Revisar que solo hay 1 worker de Gunicorn

### Si la aplicación es lenta:
1. Es normal en Free Tier (CPU compartida 0.1)
2. Implementar caché del lado del cliente
3. Optimizar consultas de base de datos

### Si falla el deploy:
1. Verificar todas las variables de entorno
2. Revisar logs de build en Render
3. Probar configuración localmente primero

## 🔄 Actualizaciones Futuras

Si necesitas más recursos en el futuro:
- **Upgrade a Starter ($7/mes):** 512MB RAM, 0.5 CPU
- **Agregar PostgreSQL:** Cuando tengas más memoria disponible
- **Múltiples workers:** Con más CPU disponible

## 📞 Soporte

Para problemas específicos de Render:
- [Documentación Render](https://render.com/docs)
- [Render Community](https://community.render.com)
