# Usar imagen oficial de Python
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=dhl_project.settings

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del proyecto
COPY . .

# Crear directorio para logs
RUN mkdir -p logs

# Crear usuario no-root
RUN adduser --disabled-password --gecos '' django
RUN chown -R django:django /app
USER django

# Exponer puerto
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "dhl_project.wsgi:application"] 