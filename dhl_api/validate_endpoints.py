#!/usr/bin/env python3
"""
Script para validar endpoints DHL
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dhl_project.settings')
django.setup()

from dhl_api.services import DHLService
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def validate_endpoints():
    """Valida la configuración de endpoints"""
    
    try:
        # Configuración del servicio
        username = "apO3fS5mJ8zT7h"
        password = "J^4oF@1qW!0qS!5b"
        base_url = "https://express.api.dhl.com"
        environment = "sandbox"
        
        logger.info("=== VALIDANDO ENDPOINTS DHL ===")
        logger.info(f"Username: {username}")
        logger.info(f"Environment: {environment}")
        logger.info(f"Base URL: {base_url}")
        
        # Inicializar servicio
        dhl_service = DHLService(username, password, base_url, environment)
        
        # Mostrar endpoints configurados
        logger.info("\n=== ENDPOINTS CONFIGURADOS ===")
        for key, endpoint in dhl_service.endpoints.items():
            logger.info(f"{key}: {endpoint}")
        
        # Verificar si hay endpoints legacy
        if hasattr(dhl_service, 'legacy_endpoints'):
            logger.info("\n=== ENDPOINTS LEGACY ===")
            for key, endpoint in dhl_service.legacy_endpoints.items():
                logger.info(f"{key}: {endpoint}")
        
        # Verificar endpoint específico de cotización
        rate_endpoint = dhl_service.endpoints.get('rate')
        logger.info(f"\n=== ENDPOINT DE COTIZACIÓN ===")
        logger.info(f"Rate endpoint: {rate_endpoint}")
        
        # Verificar que sea el endpoint correcto para sandbox
        expected_sandbox_endpoint = "https://express.api.dhl.com/mydhlapi/test/rates"
        if rate_endpoint == expected_sandbox_endpoint:
            logger.info("✅ Endpoint de cotización correcto para sandbox")
            return True
        else:
            logger.error(f"❌ Endpoint incorrecto. Esperado: {expected_sandbox_endpoint}")
            return False
            
    except Exception as e:
        logger.exception(f"Error validando endpoints: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== VALIDACIÓN DE ENDPOINTS DHL ===")
    
    success = validate_endpoints()
    
    if success:
        print("\n✅ Endpoints validados correctamente")
    else:
        print("\n❌ Validación de endpoints falló")
        sys.exit(1)
