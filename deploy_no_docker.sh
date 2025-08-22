#!/usr/bin/env bash
set -euo pipefail

# Despliegue sin Docker para Ubuntu (bash)
# - Crea/activa un virtualenv en .venv
# - Instala dependencias desde requirements.txt
# - Aplica migraciones
# - Carga countries.json (management command load_countries)
# - Opcional: carga datos de referencia completos (load_reference_all)
# - Opcional: construye frontend (npm)
# - Opcional: crea superusuario si se pasan variables de entorno

ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON_CMD=python3
SKIP_FRONTEND=0
SKIP_REFERENCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-frontend) SKIP_FRONTEND=1; shift ;;
    --skip-reference) SKIP_REFERENCE=1; shift ;;
    --python) PYTHON_CMD="$2"; shift 2 ;;
    -h|--help) echo "Usage: $0 [--skip-frontend] [--skip-reference] [--python /path/to/python]"; exit 0 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

echo "[deploy_no_docker] Proyecto: $ROOT"
echo "[deploy_no_docker] Python: $PYTHON_CMD"

# 1) Revisar que python está disponible
if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
  echo "ERROR: $PYTHON_CMD no encontrado. Instale Python 3 y vuelva a intentarlo." >&2
  exit 2
fi

# 2) Crear virtualenv si hace falta
VENVDIR="$ROOT/.venv"
if [[ ! -d "$VENVDIR" ]]; then
  echo "Creando virtualenv en $VENVDIR..."
  "$PYTHON_CMD" -m venv "$VENVDIR"
fi

# 3) Activar virtualenv
# shellcheck source=/dev/null
source "$VENVDIR/bin/activate"
echo "Entorno virtual activado: $(which python) ($(python --version 2>&1))"

# 4) Actualizar pip e instalar dependencias
if [[ -f "$ROOT/requirements.txt" ]]; then
  echo "Instalando dependencias desde requirements.txt..."
  pip install --upgrade pip
  pip install -r "$ROOT/requirements.txt"
else
  echo "Aviso: requirements.txt no encontrado en $ROOT - saltando instalación de pip" >&2
fi

# 5) Variables de entorno Django
export PYTHONPATH="$ROOT"
export DJANGO_SETTINGS_MODULE="dhl_project.settings"
echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"

cd "$ROOT"

# 6) Migraciones
echo "Aplicando migraciones..."
python manage.py migrate --noinput

# 7) Cargar countries.json
COUNTRIES_FILE="$ROOT/countries.json"
if [[ -f "$COUNTRIES_FILE" ]]; then
  echo "Cargando países desde $COUNTRIES_FILE..."
  python manage.py load_countries --file "$COUNTRIES_FILE"
else
  echo "Advertencia: $COUNTRIES_FILE no existe, saltando carga de países" >&2
fi

# 8) Cargar referencia completa (opcional)
if [[ "$SKIP_REFERENCE" -eq 0 ]]; then
  if [[ -f "$ROOT/dhl_api/Postal_Locations_fullset_20250811010020.csv" ]]; then
    echo "Cargando datos de referencia completos (load_reference_all)... Esto puede tardar." 
    python manage.py load_reference_all --csv-file "$ROOT/dhl_api/Postal_Locations_fullset_20250811010020.csv"
  else
    echo "Archivo CSV de mapeo postal no encontrado en dhl_api/, omitiendo load_reference_all." >&2
  fi
else
  echo "Omitiendo carga de referencia por --skip-reference"
fi

# 9) Collectstatic (opcional, recomendable en producción)
echo "Ejecutando collectstatic --noinput"
python manage.py collectstatic --noinput || echo "collectstatic falló o no está configurado; verificar configuración STATICFILES" >&2

# 10) Frontend build (opcional)
if [[ "$SKIP_FRONTEND" -eq 0 ]]; then
  if command -v npm >/dev/null 2>&1 && [[ -d "$ROOT/frontend" ]]; then
    echo "Construyendo frontend: npm ci && npm run build"
    pushd "$ROOT/frontend" >/dev/null
    npm ci
    npm run build
    popd >/dev/null
    echo "Frontend construido. Revise cómo integrar los artefactos (staticfiles)."
  else
    echo "npm no encontrado o carpeta frontend ausente; omitiendo build frontend" >&2
  fi
else
  echo "Omitiendo build frontend por --skip-frontend"
fi

# 11) Crear superusuario si están definidas variables de entorno
if [[ -n "${ADMIN_USERNAME:-}" ]] && [[ -n "${ADMIN_EMAIL:-}" ]] && [[ -n "${ADMIN_PASSWORD:-}" ]]; then
  echo "Creando/actualizando superusuario $ADMIN_USERNAME (sin prompt)..."
  python - <<PYCODE
from django.contrib.auth import get_user_model
User = get_user_model()
u, created = User.objects.update_or_create(
    username='$ADMIN_USERNAME',
    defaults={'email': '$ADMIN_EMAIL'}
)
if created:
    u.set_password('$ADMIN_PASSWORD')
    u.is_staff = True
    u.is_superuser = True
    u.save()
    print('Superusuario creado')
else:
    print('Superusuario ya existía; contraseña no cambiada automáticamente')
PYCODE
else
  echo "No se creará superusuario automático (defina ADMIN_USERNAME, ADMIN_EMAIL y ADMIN_PASSWORD si desea)."
fi

echo "Despliegue completado. Revise la salida para errores y ajuste variables de entorno según su producción."
