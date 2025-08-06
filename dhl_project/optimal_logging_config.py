"""
Configuración de logging ÓPTIMA para proyecto DHL
Combina lo mejor de ambos enfoques: rendimiento + usabilidad
"""

import os
import logging
from datetime import datetime
from pathlib import Path

def get_optimal_log_config(base_dir):
    """
    Configuración de logging óptima que balancea rendimiento y usabilidad
    
    ESTRATEGIA:
    1. Archivos con nombre fecha para FÁCIL navegación
    2. Rotación por tamaño para RENDIMIENTO
    3. Diferentes estrategias según CRITICIDAD del log
    """
    
    logs_dir = Path(base_dir) / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Fecha actual para nombres de archivo
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s',
                'datefmt': '%H:%M:%S',  # Solo hora dentro del archivo (ya tenemos fecha en nombre)
            },
            'simple': {
                'format': '%(levelname)s: %(message)s',
            },
        },
        'handlers': {
            # DJANGO GENERAL - Rotación por tamaño (RENDIMIENTO)
            'django_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': str(logs_dir / f'django_{current_date}.log'),
                'formatter': 'detailed',
                'maxBytes': 10 * 1024 * 1024,  # 10MB por archivo
                'backupCount': 5,  # django_2025-08-04.log.1, .2, etc.
                'encoding': 'utf-8',
            },
            
            # ERRORES - Nombre con fecha + rotación HORARIA (CRÍTICO)
            'errors_file': {
                'level': 'ERROR',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': str(logs_dir / f'errors_{current_date}.log'),
                'formatter': 'detailed',
                'when': 'H',  # Cada hora
                'interval': 1,
                'backupCount': 24,  # 24 horas de errores
                'encoding': 'utf-8',
            },
            
            # DHL API - Archivo por DÍA (BALANCE perfecto)
            'dhl_api_file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': str(logs_dir / f'dhl_api_{current_date}.log'),
                'formatter': 'detailed',
                'encoding': 'utf-8',
            },
            
            # PERFORMANCE - Por sesión/timestamp (ANÁLISIS específico)
            'performance_file': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': str(logs_dir / f'performance_{current_date}_{datetime.now().strftime("%H%M")}.log'),
                'formatter': 'detailed',
                'encoding': 'utf-8',
            },
            
            # REQUESTS - Rotación rápida por tamaño (ALTO volumen)
            'requests_file': {
                'level': 'WARNING',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': str(logs_dir / f'requests_{current_date}.log'),
                'formatter': 'detailed',
                'maxBytes': 5 * 1024 * 1024,  # 5MB (requests pueden ser muchos)
                'backupCount': 3,
                'encoding': 'utf-8',
            },
            
            # CONSOLE - Limpio para desarrollo
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
        },
        'root': {
            'handlers': ['console', 'django_file'],
            'level': 'DEBUG',
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'django_file', 'errors_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'dhl_api': {
                'handlers': ['console', 'dhl_api_file', 'errors_file'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'performance': {
                'handlers': ['performance_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'requests': {
                'handlers': ['requests_file'],
                'level': 'WARNING',
                'propagate': False,
            },
            'urllib3': {
                'handlers': ['requests_file'],
                'level': 'WARNING',
                'propagate': False,
            },
        },
    }

class OptimalFileHandler(logging.FileHandler):
    """
    Handler personalizado que recrea el archivo cada día automáticamente
    ÓPTIMO: Combina nombres inteligentes + rotación automática
    """
    
    def __init__(self, base_filename, mode='a', encoding='utf-8', delay=False):
        self.base_filename = base_filename
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Crear nombre de archivo con fecha actual
        filename = self._get_current_filename()
        super().__init__(filename, mode, encoding, delay)
    
    def _get_current_filename(self):
        """Genera nombre de archivo con fecha actual"""
        base_path = Path(self.base_filename)
        parent = base_path.parent
        stem = base_path.stem
        suffix = base_path.suffix
        
        return str(parent / f"{stem}_{self.current_date}{suffix}")
    
    def emit(self, record):
        """
        Override emit para verificar si cambió el día
        Si cambió, crea nuevo archivo automáticamente
        """
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        if current_date != self.current_date:
            # Cambió el día, cerrar archivo actual y abrir nuevo
            self.close()
            self.current_date = current_date
            self.baseFilename = self._get_current_filename()
            self.stream = None  # Forzar recreación
        
        super().emit(record)

# Configuración HÍBRIDA ultra-optimizada
def get_hybrid_optimal_config(base_dir):
    """
    LA CONFIGURACIÓN MÁS ÓPTIMA POSIBLE
    Usa diferentes estrategias según el tipo de log
    """
    
    logs_dir = Path(base_dir) / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'timestamped': {
                'format': '%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
                'datefmt': '%H:%M:%S',
            },
            'detailed': {
                'format': '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s',
                'datefmt': '%H:%M:%S',
            },
        },
        'handlers': {
            # GENERAL: Archivo diario con rotación por tamaño
            'general': {
                'level': 'INFO',
                'class': 'dhl_project.optimal_logging_config.OptimalFileHandler',
                'base_filename': str(logs_dir / 'django.log'),
                'formatter': 'timestamped',
            },
            
            # ERRORES: Archivo horario para análisis rápido
            'errors': {
                'level': 'ERROR',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': str(logs_dir / f'errors_{datetime.now().strftime("%Y-%m-%d")}.log'),
                'when': 'H',
                'interval': 1,
                'backupCount': 48,  # 2 días de errores por hora
                'formatter': 'detailed',
            },
            
            # DHL: Archivo diario simple (mejor rendimiento)
            'dhl_api': {
                'level': 'DEBUG',
                'class': 'dhl_project.optimal_logging_config.OptimalFileHandler',
                'base_filename': str(logs_dir / 'dhl_api.log'),
                'formatter': 'detailed',
            },
            
            # PERFORMANCE: Por sesión específica
            'performance': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': str(logs_dir / f'performance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                'formatter': 'detailed',
            },
            
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'timestamped',
            },
        },
        'root': {
            'handlers': ['console', 'general'],
            'level': 'DEBUG',
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'general', 'errors'],
                'level': 'INFO',
                'propagate': False,
            },
            'dhl_api': {
                'handlers': ['console', 'dhl_api', 'errors'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'performance': {
                'handlers': ['performance'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }

# Funciones de utilidad para gestión óptima
def cleanup_old_logs(logs_dir, days_to_keep=30):
    """Limpieza inteligente por tipo de log"""
    from datetime import timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    logs_path = Path(logs_dir)
    
    # Patrones por tipo con diferentes retenciones
    cleanup_patterns = {
        'django_*.log': 30,      # 30 días de logs generales
        'errors_*.log': 90,      # 90 días de errores (importante)
        'dhl_api_*.log': 15,     # 15 días de API
        'performance_*.log': 7,   # 7 días de performance
        'requests_*.log': 3,     # 3 días de requests
    }
    
    for pattern, retention_days in cleanup_patterns.items():
        pattern_cutoff = datetime.now() - timedelta(days=retention_days)
        
        for log_file in logs_path.glob(pattern):
            file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_date < pattern_cutoff:
                log_file.unlink()
                print(f"🗑️ Deleted old log: {log_file.name}")

def get_log_stats(logs_dir):
    """Estadísticas optimizadas de logs"""
    logs_path = Path(logs_dir)
    stats = {}
    
    for log_file in logs_path.glob('*.log*'):
        file_size = log_file.stat().st_size
        file_date = datetime.fromtimestamp(log_file.stat().st_mtime).strftime('%Y-%m-%d')
        
        log_type = log_file.name.split('_')[0]
        if log_type not in stats:
            stats[log_type] = {'files': 0, 'total_size': 0, 'dates': set()}
        
        stats[log_type]['files'] += 1
        stats[log_type]['total_size'] += file_size
        stats[log_type]['dates'].add(file_date)
    
    return stats
