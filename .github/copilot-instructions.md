# Copilot Instructions - DHL Project

## Stack & Language
Django REST + React + Tailwind + PostgreSQL + Docker | Español

## Development Rules
- **Django**: MVT pattern, DRF serializers, ViewSets/APIView, services.py
- **React**: Functional components, hooks, Tailwind CSS, Context API
- **Naming**: Python (snake_case/PascalCase), JS (camelCase/PascalCase), UPPER_CASE constants
- **Tests**: `test_*.py` files

## CHANGELOG (REQUIRED)
Update CHANGELOG.md for significant changes. Use [Keep a Changelog](https://keepachangelog.com/es/1.0.0/) format with semantic versioning.

Categories: Added, Changed, Fixed, Security, Deprecated, Removed

## Code Style
- **Python**: PEP 8, type hints, Spanish docstrings, serializer validation, try-except
- **JS/React**: ES6+, destructuring, arrow functions, Spanish comments, PropTypes

## File Structure
- Components: `frontend/src/components/`
- Contexts: `frontend/src/contexts/`
- Services: `dhl_api/services.py`
- Tests: separate `test_*.py` files

## Docker Commands
```bash
# Core
docker-dev.bat up/down/logs/status
django-manage.bat runserver/test/migrate
python-docker.bat script.py
docker-shell.bat

# DB
docker-dev.bat db-shell/reset-db
```
# Logs
docker-dev.bat logs --tail=100 # últimos 100 logs
docker-dev.bat logs service_name # logs de un servicio específico
docker-dev.bat logs -f --since=10m # seguimiento de logs últimos 10 minutos
docker-dev.bat logs | grep ERROR # filtrar solo errores
## Key Considerations
- **Docker-first**: ALL Python commands run in containers
- **Hot-reload**: Changes reflect automatically
- **API Integration**: DHL API via environment variables
- **Auth**: JWT tokens
- **Error handling**: Try-catch in services.py
- **Multi-env**: dev/staging/production configs