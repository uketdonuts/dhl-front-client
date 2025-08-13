"""
Comando para cargar países desde el archivo countries.json
"""
import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from dhl_api.models import ServiceZone


class Command(BaseCommand):
    help = 'Carga países desde el archivo countries.json'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='countries.json',
            help='Ruta al archivo countries.json (por defecto: countries.json)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpia solo los países de la tabla antes de cargar'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear_countries = options['clear']
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            raise CommandError(f'El archivo {file_path} no existe')
        
        # Limpiar países si se especifica
        if clear_countries:
            self.stdout.write('Limpiando países existentes...')
            # Solo eliminamos registros que parecen ser solo países (sin ciudades específicas)
            ServiceZone.objects.filter(
                city_name__isnull=True
            ).filter(
                state_name__isnull=True
            ).delete()
            self.stdout.write(self.style.SUCCESS('Países limpiados'))
        
        # Leer archivo JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except json.JSONDecodeError as e:
            raise CommandError(f'Error al leer el archivo JSON: {e}')
        except Exception as e:
            raise CommandError(f'Error al abrir el archivo: {e}')
        
        # Verificar estructura del JSON
        if not data.get('success') or 'data' not in data:
            raise CommandError('El archivo JSON no tiene la estructura esperada')
        
        countries_data = data['data']
        
        self.stdout.write(f'Procesando {len(countries_data)} países...')
        
        # Preparar datos para inserción
        countries_to_create = []
        existing_countries = set(
            ServiceZone.objects.values_list('country_code', flat=True).distinct()
        )
        
        for country in countries_data:
            country_code = country.get('country_code')
            country_name = country.get('country_name')
            
            if not country_code or not country_name:
                self.stdout.write(
                    self.style.WARNING(f'Saltando país con datos incompletos: {country}')
                )
                continue
            
            # Solo agregar si no existe ya
            if country_code not in existing_countries:
                countries_to_create.append(
                    ServiceZone(
                        country_code=country_code,
                        country_name=country_name,
                        service_area='DEFAULT'  # Área de servicio por defecto para países
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'País {country_code} ya existe, saltando...')
                )
        
        # Inserción masiva con transacción
        if countries_to_create:
            try:
                with transaction.atomic():
                    ServiceZone.objects.bulk_create(
                        countries_to_create,
                        batch_size=100,
                        ignore_conflicts=True
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Se cargaron {len(countries_to_create)} países correctamente'
                    )
                )
                
                # Mostrar estadísticas
                total_countries = ServiceZone.objects.values('country_code').distinct().count()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'📊 Total de países en la base de datos: {total_countries}'
                    )
                )
                
            except Exception as e:
                raise CommandError(f'Error al insertar países: {e}')
        else:
            self.stdout.write(
                self.style.WARNING('No hay países nuevos para cargar')
            )
        
        self.stdout.write(
            self.style.SUCCESS('🎉 Proceso de carga de países completado')
        )
