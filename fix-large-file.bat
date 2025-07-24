@echo off
echo === SOLUCION RAPIDA PARA ARCHIVO GRANDE ===
echo.
echo El archivo ESD.TXT (118MB) es demasiado grande para GitHub.
echo Sigue estos pasos EN ORDEN:
echo.
echo --- PASO 1: Remover del staging area ---
echo git rm --cached dhl_api/ESD.TXT
echo.
echo --- PASO 2: Verificar que .gitignore incluye el archivo ---
echo type .gitignore | findstr ESD
echo.
echo --- PASO 3: Commit el cambio ---
echo git add .gitignore
echo git commit -m "Remove large ESD.TXT file and update gitignore"
echo.
echo --- PASO 4: Si aun tienes problemas, usar BFG ---
echo Descargar: https://rtyley.github.io/bfg-repo-cleaner/
echo java -jar bfg.jar --delete-files ESD.TXT
echo git reflog expire --expire=now --all
echo git gc --prune=now --aggressive
echo.
echo --- PASO 5: Push forzado ---
echo git push --force-with-lease origin main
echo.
echo ⚠️  Si el archivo sigue apareciendo, el problema esta en commits anteriores
echo    y necesitas limpiar el historial completo.
