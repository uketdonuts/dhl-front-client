"""
Comando para cargar datos de zonas de servicio desde el archivo ESD.TXT
"""
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Count
from dhl_api.models import ServiceZone, CountryISO


class Command(BaseCommand):
    help = 'Carga datos de zonas de servicio desde el archivo ESD.TXT'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='dhl_api/ESD.TXT',
            help='Ruta al archivo ESD.TXT (por defecto: dhl_api/ESD.TXT)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpia la tabla antes de cargar los datos'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Tamaño del lote para inserción masiva (por defecto: 1000)'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear_table = options['clear']
        batch_size = options['batch_size']
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            raise CommandError(f'El archivo {file_path} no existe')
        
        # Limpiar tabla si se especifica
        if clear_table:
            self.stdout.write('Limpiando tabla ServiceZone...')
            ServiceZone.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Tabla limpiada'))
        
        # Procesar archivo
        self.stdout.write(f'Procesando archivo {file_path}...')
        
        created_count = 0
        error_count = 0
        batch = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_number, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        # Parsear línea del formato ESD
                        # Formato: CO|COLOMBIA||||BUN|051430|051430|
                        parts = line.split('|')
                        
                        if len(parts) < 8:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Línea {line_number}: formato inválido - {line}'
                                )
                            )
                            error_count += 1
                            continue
                        
                        country_code = parts[0].strip()
                        # Normalizar nombre de país: preferir CountryISO si disponible
                        raw_country_name = parts[1].strip()
                        country_name = CountryISO.resolve_name(country_code, fallback=raw_country_name)
                        state_code = parts[2].strip() if parts[2] else ''
                        state_name = parts[3].strip() if parts[3] else ''
                        city_name = parts[4].strip() if parts[4] else ''
                        service_area = parts[5].strip()
                        postal_code_from = parts[6].strip() if parts[6] else ''
                        postal_code_to = parts[7].strip() if parts[7] else ''
                        
                        # Validaciones básicas
                        if not country_code or not country_name or not service_area:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Línea {line_number}: datos obligatorios faltantes - {line}'
                                )
                            )
                            error_count += 1
                            continue
                        
                        # Crear objeto ServiceZone
                        service_zone = ServiceZone(
                            country_code=country_code,
                            country_name=country_name,
                            state_code=state_code,
                            state_name=state_name,
                            city_name=city_name,
                            service_area=service_area,
                            postal_code_from=postal_code_from,
                            postal_code_to=postal_code_to
                        )
                        
                        batch.append(service_zone)
                        
                        # Insertar lote cuando alcance el tamaño especificado
                        if len(batch) >= batch_size:
                            with transaction.atomic():
                                ServiceZone.objects.bulk_create(
                                    batch, 
                                    ignore_conflicts=True,
                                    batch_size=batch_size
                                )
                            created_count += len(batch)
                            batch = []
                            
                            # Mostrar progreso cada 10,000 registros
                            if created_count % 10000 == 0:
                                self.stdout.write(f'Procesados: {created_count} registros')
                    
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Error en línea {line_number}: {str(e)} - {line}'
                            )
                        )
                        error_count += 1
                        continue
                
                # Insertar lote restante
                if batch:
                    with transaction.atomic():
                        ServiceZone.objects.bulk_create(
                            batch, 
                            ignore_conflicts=True,
                            batch_size=len(batch)
                        )
                    created_count += len(batch)
        
        except Exception as e:
            raise CommandError(f'Error procesando archivo: {str(e)}')
        
        # Mostrar resumen
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Proceso completado:\n'
                f'  - Registros creados: {created_count}\n'
                f'  - Errores: {error_count}\n'
                f'  - Total de zonas de servicio en DB: {ServiceZone.objects.count()}'
            )
        )
        
        # Mostrar estadísticas por país
        self.stdout.write('\n📊 Estadísticas por país:')
        countries = ServiceZone.objects.values('country_code', 'country_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        for country in countries:
            self.stdout.write(
                f"  {country['country_name']} ({country['country_code']}): "
                f"{country['count']} zonas"
            )
