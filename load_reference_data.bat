@echo off
REM Carga de datos de referencia (países, zonas ESD y mapeo service_area -> ciudad)
REM Requiere: docker-compose en marcha y servicio backend activo.

REM ===================== CONFIGURACIÓN =====================
REM Ruta del CSV masivo dentro del contenedor (monta el repo en /app)
set "CSV_CONTAINER_PATH=/app/dhl_api/Postal_Locations_fullset_20250811010020.csv"

REM Filtros para mapeo (ej: CA,US). Deja vacío para todos
set "MAP_COUNTRIES="

REM Límite de filas a procesar por corrida (0 = sin límite). Para cargar TODO, usar 0.
set "MAP_MAX_ROWS=0"

REM Delimitador CSV. Deja vacío para auto (sniffer). Para forzar coma: ,
set "MAP_DELIMITER="

REM Habilitar upsert (actualiza si existe). Usa --upsert cuando sea TRUE
set "MAP_UPSERT=TRUE"

REM Intentar derivar service_area por código postal usando ServiceZone (TRUE/FALSE)
set "MAP_DERIVE_SA=FALSE"

REM Permitir override de la ruta por argumento 1 (ya en ruta de contenedor)
if not "%~1"=="" set "CSV_CONTAINER_PATH=%~1"

echo ============================================
echo  Carga de datos de referencia - DHL Project
echo  CSV: %CSV_CONTAINER_PATH%
echo  Mapeo Paises: %MAP_COUNTRIES%  Filas: %MAP_MAX_ROWS%
echo ============================================

REM ===================== PRE-CHEQUEOS =====================
echo.
echo [1/6] Verificando estado de contenedores...
docker-dev.bat status
if errorlevel 1 (
  echo Error consultando estado de docker.
  exit /b 1
)

REM ===================== MIGRACIONES =====================
echo.
echo [2/6] Aplicando migraciones...
django-manage.bat migrate
if errorlevel 1 (
  echo Fallo migrate.
  exit /b 1
)

REM ===================== PAÍSES =====================
echo.
echo [3/6] Cargando paises (countries.json)...
django-manage.bat load_countries --file="/app/countries.json"
if errorlevel 1 (
  echo Fallo load_countries.
  exit /b 1
)

REM ===================== ZONAS ESD =====================
echo.
echo [4/6] Cargando zonas de servicio (ESD.TXT)...
django-manage.bat load_esd_data --file="/app/dhl_api/ESD.TXT"
if errorlevel 1 (
  echo Fallo load_esd_data.
  exit /b 1
)

REM ===================== MAPEO SERVICE AREA =====================
echo.
echo [5/6] Cargando mapeo service_area -> ciudad (puede tardar)...
set "UPSERT_FLAG="
if /I "%MAP_UPSERT%"=="TRUE" set "UPSERT_FLAG=--upsert"

set "DERIVE_SA_FLAG="
if /I "%MAP_DERIVE_SA%"=="TRUE" set "DERIVE_SA_FLAG=--derive-service-area"

set "DELIM_FLAG="
if not "%MAP_DELIMITER%"=="" set "DELIM_FLAG=--delimiter=%MAP_DELIMITER%"

set "COUNTRIES_FLAG="
if not "%MAP_COUNTRIES%"=="" set "COUNTRIES_FLAG=--countries=%MAP_COUNTRIES%"

set "MAXROWS_FLAG="
if not "%MAP_MAX_ROWS%"=="0" if not "%MAP_MAX_ROWS%"=="" set "MAXROWS_FLAG=--max-rows=%MAP_MAX_ROWS%"

echo Ejecutando: load_service_area_map %COUNTRIES_FLAG% %MAXROWS_FLAG% %DELIM_FLAG% %UPSERT_FLAG% %DERIVE_SA_FLAG%
django-manage.bat load_service_area_map --file="%CSV_CONTAINER_PATH%" %COUNTRIES_FLAG% %MAXROWS_FLAG% %DELIM_FLAG% %UPSERT_FLAG% %DERIVE_SA_FLAG%
if errorlevel 1 (
  echo Fallo load_service_area_map.
  exit /b 1
)

REM ===================== STATS =====================
echo.
echo [6/6] Resumen de mapeos cargados...
django-manage.bat service_area_map_stats

echo.
echo === Proceso completado ===
exit /b 0
