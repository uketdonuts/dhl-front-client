@echo off
REM Script para limpiar archivos grandes del historial de Git

echo Limpiando archivos grandes del historial de Git...
echo.

echo 1. Removiendo dhl_api/ESD.TXT del historial...
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch dhl_api/ESD.TXT" --prune-empty --tag-name-filter cat -- --all

echo.
echo 2. Forzando garbage collection...
git for-each-ref --format="delete %%(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now

echo.
echo 3. Verificando que el archivo ya no esté en el índice...
git ls-files | findstr ESD.TXT

echo.
echo ✅ Limpieza completada.
echo.
echo Próximos pasos:
echo 1. Ejecutar: git add .gitignore
echo 2. Ejecutar: git commit -m "Add large files to gitignore"
echo 3. Ejecutar: git push --force-with-lease origin main
echo.
echo ⚠️  ADVERTENCIA: git push --force-with-lease reescribirá el historial remoto.
