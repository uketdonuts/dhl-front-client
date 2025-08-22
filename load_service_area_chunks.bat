@echo off
REM Carga en trozos (chunks) de ServiceAreaCityMap desde Postal_Locations_fullset
REM Parametrizado para 250k filas por chunk

setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

REM Configuración
set "FILE=/app/dhl_api/Postal_Locations_fullset_20250811010020.csv"
set "CHUNK=250000"
set "TOTAL=12122548"
set "BATCH=20000"
set "USE_UPSERT=FALSE"
set "CLEAR_FIRST=TRUE"

echo ============================================
echo Carga chunked ServiceAreaCityMap
echo Archivo: %FILE%
echo Total aprox: %TOTAL% ^| Chunk: %CHUNK% ^| Batch: %BATCH%
echo ============================================

REM Nota: La tabla debe estar vacía o se hará upsert sin duplicar

for /L %%S in (0,%CHUNK%,%TOTAL%) do (
  echo.
  echo === Chunk desde %%S ^(max %CHUNK%^) ===
  set "CMD=django-manage.bat load_service_area_map --file=%FILE% --format=postal_locations --no-header --batch-size=%BATCH% --progress-every=250000 --start-row=%%S --max-rows=%CHUNK%"
  if /I "%USE_UPSERT%"=="TRUE" set "CMD=!CMD! --upsert"
  if %%S==0 if /I "%CLEAR_FIRST%"=="TRUE" set "CMD=!CMD! --clear"
  echo Ejecutando: !CMD!
  call !CMD!
  if errorlevel 1 (
    echo [WARN] Fallo en chunk %%S. Reintentando tras 5s...
    timeout /t 5 /nobreak >nul
  call !CMD!
  )
)

echo.
echo === Proceso chunked finalizado ===
endlocal
