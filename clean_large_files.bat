@echo off
echo Limpiando archivos grandes del historial de git...

REM Limpiar el historial de los archivos ESD
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch dhl_api/ESD.TXT dhl_api/ESD-sample.TXT" --prune-empty --tag-name-filter cat -- --all

REM Limpiar referencias
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin

REM Expirar reflog
git reflog expire --expire=now --all

REM Garbage collection agresivo
git gc --prune=now --aggressive

echo Limpieza completada!
