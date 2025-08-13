#!/usr/bin/env python
"""
Script para crear superusuario admin/admin
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dhl_project.settings')
django.setup()

from django.contrib.auth.models import User

# Eliminar usuario admin si existe
if User.objects.filter(username='admin').exists():
    User.objects.filter(username='admin').delete()
    print("Usuario admin existente eliminado")

# Crear nuevo superusuario
admin_user = User.objects.create_superuser(
    username='admin',
    email='admin@example.com',
    password='admin'
)

print(f"✅ Superusuario creado exitosamente:")
print(f"   Username: {admin_user.username}")
print(f"   Email: {admin_user.email}")
print(f"   Es superusuario: {admin_user.is_superuser}")
print(f"   Es staff: {admin_user.is_staff}")
print(f"   Es activo: {admin_user.is_active}")
print(f"\n🔐 Credenciales:")
print(f"   Usuario: admin")
print(f"   Contraseña: admin")
print(f"\n🌐 Acceso admin: http://localhost:8000/admin/")
