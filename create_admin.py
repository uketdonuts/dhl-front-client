#!/usr/bin/env python3
"""
Script para crear usuario admin/admin
"""
import os
import sys
import django

# Configurar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dhl_project.settings')
django.setup()

from django.contrib.auth.models import User

def create_admin_user():
    """Crear usuario admin/admin"""
    try:
        # Verificar si ya existe
        if User.objects.filter(username='admin').exists():
            print("✅ Usuario admin ya existe")
            user = User.objects.get(username='admin')
            print(f"   - Username: {user.username}")
            print(f"   - Email: {user.email}")
            print(f"   - Is staff: {user.is_staff}")
            print(f"   - Is superuser: {user.is_superuser}")
        else:
            # Crear nuevo usuario
            user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin'
            )
            print("✅ Usuario admin creado exitosamente")
            print(f"   - Username: {user.username}")
            print(f"   - Email: {user.email}")
            print(f"   - Password: admin")
            
    except Exception as e:
        print(f"❌ Error creando usuario: {str(e)}")

if __name__ == "__main__":
    create_admin_user()
