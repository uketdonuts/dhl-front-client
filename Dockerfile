# Usar imagen más ligera
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=dhl_project.settings

WORKDIR /app

# Solo instalar dependencias esenciales (sin PostgreSQL para SQLite)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Crear directorio para logs
RUN mkdir -p logs

EXPOSE 8000

# Comando optimizado para Render
CMD python manage.py migrate && gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 dhl_project.wsgi:application
