#!/usr/bin/env python
"""
Script de inicialización para Django DHL API
Crea un superusuario y configura la base de datos inicial
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dhl_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.management import execute_from_command_line


def create_superuser():
    """Crear superusuario si no existe"""
    try:
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@dhl-api.com',
                password='admin123'
            )
            print("✅ Superusuario 'admin' creado exitosamente")
            print("   Usuario: admin")
            print("   Contraseña: admin123")
        else:
            print("ℹ️  El superusuario 'admin' ya existe")
    except Exception as e:
        print(f"❌ Error creando superusuario: {e}")


def run_migrations():
    """Ejecutar migraciones"""
    try:
        print("🔄 Ejecutando migraciones...")
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migraciones completadas")
    except Exception as e:
        print(f"❌ Error en migraciones: {e}")


def collect_static():
    """Recolectar archivos estáticos"""
    try:
        print("🔄 Recolectando archivos estáticos...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print("✅ Archivos estáticos recolectados")
    except Exception as e:
        print(f"❌ Error recolectando estáticos: {e}")


def main():
    """Función principal"""
    print("🚀 Inicializando Django DHL API...")
    
    # Ejecutar migraciones
    run_migrations()
    
    # Crear superusuario
    create_superuser()
    
    # Recolectar archivos estáticos
    collect_static()
    
    print("\n🎉 Inicialización completada!")
    print("\n📋 Información de acceso:")
    print("   - Admin Django: http://localhost:8000/admin/")
    print("   - API Endpoints: http://localhost:8000/api/")
    print("   - Frontend: http://localhost:3002/")
    print("\n🔑 Credenciales:")
    print("   - Usuario: admin")
    print("   - Contraseña: admin123")


if __name__ == '__main__':
    main() 