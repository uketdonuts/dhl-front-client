#!/usr/bin/env python3
"""
Script de gestión de logs del proyecto DHL
Permite limpiar, analizar y gestionar los archivos de log generados.
"""

import os
import glob
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path

def get_log_directory():
    """Obtiene el directorio de logs del proyecto"""
    base_dir = Path(__file__).resolve().parent
    logs_dir = base_dir / 'logs'
    return logs_dir

def list_log_files():
    """Lista todos los archivos de log disponibles"""
    logs_dir = get_log_directory()
    if not logs_dir.exists():
        print("❌ No existe el directorio de logs")
        return []
    
    log_files = []
    patterns = ['*.log', '*.log.*']
    
    for pattern in patterns:
        log_files.extend(glob.glob(str(logs_dir / pattern)))
    
    log_files.sort(key=os.path.getmtime, reverse=True)
    return log_files

def analyze_log_stats():
    """Analiza estadísticas de los archivos de log"""
    log_files = list_log_files()
    
    print("\n📊 ESTADÍSTICAS DE LOGS")
    print("=" * 50)
    
    total_size = 0
    log_types = {}
    
    for log_file in log_files:
        file_path = Path(log_file)
        file_size = file_path.stat().st_size
        total_size += file_size
        
        # Determinar tipo de log
        log_type = file_path.stem.split('.')[0]
        if log_type not in log_types:
            log_types[log_type] = {'count': 0, 'size': 0}
        
        log_types[log_type]['count'] += 1
        log_types[log_type]['size'] += file_size
        
        # Información del archivo
        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        size_mb = file_size / (1024 * 1024)
        
        print(f"📄 {file_path.name}")
        print(f"   📅 Fecha: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   💾 Tamaño: {size_mb:.2f} MB")
        print()
    
    print(f"📈 RESUMEN:")
    print(f"   Total archivos: {len(log_files)}")
    print(f"   Tamaño total: {total_size / (1024 * 1024):.2f} MB")
    print()
    
    print("📊 POR TIPO DE LOG:")
    for log_type, stats in log_types.items():
        size_mb = stats['size'] / (1024 * 1024)
        print(f"   {log_type}: {stats['count']} archivos, {size_mb:.2f} MB")

def clean_old_logs(days_to_keep=30):
    """Limpia logs más antiguos que X días"""
    logs_dir = get_log_directory()
    if not logs_dir.exists():
        print("❌ No existe el directorio de logs")
        return
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    log_files = list_log_files()
    
    cleaned_files = []
    total_freed = 0
    
    for log_file in log_files:
        file_path = Path(log_file)
        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        if mod_time < cutoff_date:
            file_size = file_path.stat().st_size
            total_freed += file_size
            cleaned_files.append(file_path.name)
            file_path.unlink()
    
    print(f"\n🧹 LIMPIEZA DE LOGS")
    print("=" * 30)
    print(f"Archivos eliminados: {len(cleaned_files)}")
    print(f"Espacio liberado: {total_freed / (1024 * 1024):.2f} MB")
    
    if cleaned_files:
        print("\n📋 Archivos eliminados:")
        for filename in cleaned_files:
            print(f"   🗑️ {filename}")

def compress_old_logs(days_old=7):
    """Comprime logs más antiguos que X días"""
    logs_dir = get_log_directory()
    if not logs_dir.exists():
        print("❌ No existe el directorio de logs")
        return
    
    cutoff_date = datetime.now() - timedelta(days=days_old)
    log_files = glob.glob(str(logs_dir / "*.log"))
    
    compressed_files = []
    total_saved = 0
    
    for log_file in log_files:
        file_path = Path(log_file)
        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        if mod_time < cutoff_date and not file_path.name.endswith('.gz'):
            original_size = file_path.stat().st_size
            
            # Comprimir archivo
            with open(file_path, 'rb') as f_in:
                with gzip.open(f"{file_path}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            compressed_size = Path(f"{file_path}.gz").stat().st_size
            saved_space = original_size - compressed_size
            total_saved += saved_space
            
            compressed_files.append(file_path.name)
            file_path.unlink()  # Eliminar archivo original
    
    print(f"\n🗜️ COMPRESIÓN DE LOGS")
    print("=" * 30)
    print(f"Archivos comprimidos: {len(compressed_files)}")
    print(f"Espacio ahorrado: {total_saved / (1024 * 1024):.2f} MB")
    
    if compressed_files:
        print("\n📋 Archivos comprimidos:")
        for filename in compressed_files:
            print(f"   📦 {filename} → {filename}.gz")

def tail_log(log_name="django", lines=50):
    """Muestra las últimas líneas de un log específico"""
    logs_dir = get_log_directory()
    log_file = logs_dir / f"{log_name}.log"
    
    if not log_file.exists():
        print(f"❌ No existe el archivo {log_file}")
        return
    
    print(f"\n📄 ÚLTIMAS {lines} LÍNEAS DE {log_name}.log")
    print("=" * 60)
    
    with open(log_file, 'r', encoding='utf-8') as f:
        log_lines = f.readlines()
        recent_lines = log_lines[-lines:]
        
        for line in recent_lines:
            print(line.rstrip())

def search_logs(pattern, log_name=None):
    """Busca un patrón en los logs"""
    logs_dir = get_log_directory()
    
    if log_name:
        log_files = [logs_dir / f"{log_name}.log"]
    else:
        log_files = [Path(f) for f in glob.glob(str(logs_dir / "*.log"))]
    
    print(f"\n🔍 BÚSQUEDA: '{pattern}'")
    print("=" * 50)
    
    total_matches = 0
    
    for log_file in log_files:
        if not log_file.exists():
            continue
            
        matches = []
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if pattern.lower() in line.lower():
                    matches.append((line_num, line.strip()))
        
        if matches:
            print(f"\n📄 {log_file.name} ({len(matches)} coincidencias)")
            for line_num, line in matches[-10:]:  # Últimas 10 coincidencias
                print(f"   {line_num:4d}: {line}")
            
            total_matches += len(matches)
    
    print(f"\n📈 Total coincidencias encontradas: {total_matches}")

def main():
    """Función principal con menú interactivo"""
    print("\n🚀 GESTOR DE LOGS DHL PROJECT")
    print("=" * 40)
    print("1. 📊 Ver estadísticas de logs")
    print("2. 📄 Listar archivos de log")
    print("3. 👀 Ver últimas líneas de un log")
    print("4. 🔍 Buscar en logs")
    print("5. 🗜️ Comprimir logs antiguos")
    print("6. 🧹 Limpiar logs antiguos")
    print("7. 🚪 Salir")
    
    while True:
        try:
            choice = input("\n➤ Selecciona una opción (1-7): ").strip()
            
            if choice == '1':
                analyze_log_stats()
            elif choice == '2':
                log_files = list_log_files()
                print(f"\n📋 ARCHIVOS DE LOG ({len(log_files)})")
                print("=" * 40)
                for log_file in log_files:
                    print(f"📄 {Path(log_file).name}")
            elif choice == '3':
                log_name = input("Nombre del log (django/dhl_api/errors/requests): ").strip()
                lines = input("Número de líneas (50): ").strip()
                lines = int(lines) if lines else 50
                tail_log(log_name, lines)
            elif choice == '4':
                pattern = input("Patrón a buscar: ").strip()
                log_name = input("Log específico (Enter para todos): ").strip()
                log_name = log_name if log_name else None
                search_logs(pattern, log_name)
            elif choice == '5':
                days = input("Comprimir logs con más de X días (7): ").strip()
                days = int(days) if days else 7
                compress_old_logs(days)
            elif choice == '6':
                days = input("Eliminar logs con más de X días (30): ").strip()
                days = int(days) if days else 30
                clean_old_logs(days)
            elif choice == '7':
                print("👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción inválida")
                
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
