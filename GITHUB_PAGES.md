# GitHub Pages Deployment para DHL Front Client

Este documento explica cómo desplegar el frontend de DHL Front Client a GitHub Pages.

## 🎯 ¿Qué se despliega?

- **Frontend React**: Versión estática optimizada del frontend
- **Modo Demo**: Interfaz de demostración sin backend Django
- **Assets estáticos**: CSS, JS, imágenes optimizadas para producción

## 🚀 Métodos de Deployment

### 1. Automático con GitHub Actions (Recomendado)

El deployment se ejecuta automáticamente cuando:
- Se hace push a la rama `main` o `master`
- Se abre un Pull Request
- Se ejecuta manualmente desde GitHub

**Configuración:**
1. Ve a tu repositorio en GitHub
2. Settings > Pages
3. Source: "GitHub Actions"
4. ¡Listo! El deploy se ejecutará automáticamente

### 2. Build Local con Docker Compose

```bash
# Opción 1: Usar docker compose directamente
docker compose --profile github-pages up --build github-pages-build

# Opción 2: Usar script conveniente (Linux/Mac)
./build-github-pages.sh

# Opción 3: Usar script conveniente (Windows)
build-github-pages.bat
```

Los archivos se generarán en `./github-pages-build/` listos para upload manual.

### 3. Build Local sin Docker

```bash
cd frontend
npm install
npm pkg set homepage="/dhl-front-client"
CI=false REACT_APP_ENVIRONMENT=production npm run build
```

## 🔧 Configuración

### Variables de Entorno para GitHub Pages

```bash
CI=false                           # Evitar que warnings se traten como errores
REACT_APP_ENVIRONMENT=production   # Modo producción
REACT_APP_API_URL=""               # Sin backend API
REACT_APP_BACKEND_URL=""           # Sin backend URL
GENERATE_SOURCEMAP=false           # Sin source maps para producción
```

### Homepage Configuration

El `package.json` se configura automáticamente con:
```json
{
  "homepage": "/dhl-front-client"
}
```

## 📱 Características del Demo

### Modo GitHub Pages
- ✅ **Interfaz completa** de demostración
- ✅ **Responsive design** con Tailwind CSS
- ✅ **Información del proyecto** y tecnologías
- ✅ **Enlaces** al repositorio y documentación
- ✅ **Sin dependencias** del backend Django

### Funcionalidades Mostradas
- 📊 **Cotización de Tarifas** (Rating API)
- 📦 **Creación de Envíos** (Shipment API)
- 🔍 **Seguimiento** (Tracking API)
- 📄 **ePOD** (Electronic Proof of Delivery)

## 🌐 URLs y Acceso

- **GitHub Pages**: https://uketdonuts.github.io/dhl-front-client/
- **Repositorio**: https://github.com/uketdonuts/dhl-front-client
- **Documentación**: README.md principal

## 🔄 Workflow de GitHub Action

### Trigger Events
```yaml
on:
  push:
    branches: [ "main", "master" ]
  pull_request:
    branches: [ "main", "master" ]
  workflow_dispatch:  # Manual execution
```

### Build Steps
1. **Checkout** del código
2. **Setup Node.js** 18
3. **Install dependencies** con npm ci
4. **Configure homepage** para GitHub Pages
5. **Build React app** con variables de producción
6. **Deploy** a GitHub Pages

### Artifacts
- Path: `frontend/build`
- Includes: HTML, CSS, JS, assets estáticos

## 🛠️ Troubleshooting

### Build Failures
```bash
# Verificar sintaxis del workflow
cat .github/workflows/deploy-pages.yml

# Test local build
cd frontend && npm run build
```

### Docker Issues
```bash
# Verificar configuración
docker compose --profile github-pages config

# Build manual
docker compose --profile github-pages up --build github-pages-build
```

### Path Issues
- Verificar que `homepage` esté configurado correctamente
- Router debe usar `basename="/dhl-front-client"`
- Assets deben tener paths relativos

## 📋 Checklist de Deployment

- [ ] GitHub Pages habilitado en Settings
- [ ] Workflow file presente (`.github/workflows/deploy-pages.yml`)
- [ ] Homepage configurado en `package.json`
- [ ] Variables de entorno configuradas
- [ ] Build local exitoso
- [ ] Push a rama main/master

## 🔒 Permisos Requeridos

El workflow necesita:
```yaml
permissions:
  contents: read    # Leer código del repo
  pages: write      # Escribir a GitHub Pages
  id-token: write   # Autenticación con GitHub
```

## 📞 Soporte

Para problemas con el deployment:
1. Verificar los logs del GitHub Action
2. Revisar la configuración del repositorio
3. Probar build local primero
4. Consultar la documentación de GitHub Pages

---

**¡Listo para desplegar!** 🚀