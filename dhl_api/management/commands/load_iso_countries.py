"""
Comando para cargar países desde el archivo ISO_Country_Codes_fullset_*.csv
"""
import csv
import glob
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from dhl_api.models import CountryISO


class Command(BaseCommand):
    help = 'Carga/actualiza la tabla CountryISO desde el CSV ISO_Country_Codes_fullset_*.csv'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='',
            help='Ruta al CSV; si se omite se buscará el más reciente por patrón en dhl_api/'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpia la tabla antes de cargar'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        if not file_path:
            # Buscar el más reciente en dhl_api/
            base_dir = os.getcwd()
            pattern = os.path.join(base_dir, 'dhl_api', 'ISO_Country_Codes_fullset_*.csv')
            files = sorted(glob.glob(pattern))
            if not files:
                raise CommandError('No se encontró ningún CSV ISO_Country_Codes_fullset_*.csv en dhl_api/')
            file_path = files[-1]

        if not os.path.exists(file_path):
            raise CommandError(f'El archivo {file_path} no existe')

        if options['clear']:
            self.stdout.write('Limpiando tabla CountryISO...')
            CountryISO.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Tabla limpiada'))

        created = 0
        updated = 0

        with open(file_path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Upsert en lotes
        with transaction.atomic():
            for row in rows:
                code = (row.get('ISO Country Code') or '').strip().upper()
                if not code:
                    continue
                defaults = {
                    'iso_short_name': (row.get('ISO Short Name') or '').strip(),
                    'iso_full_name': (row.get('ISO Full Name') or '').strip(),
                    'dhl_short_name': (row.get('DHL Internal Short Name') or '').strip(),
                    'currency_code': (row.get('ISO Currency Code') or '').strip(),
                    'numeric_code': (row.get('ISO Country Numeric Code') or '').strip(),
                    'alt_code': (row.get('ISO Alternate Code') or '').strip(),
                    'dial_in': (row.get('International Dial In Phone Number') or '').strip(),
                    'dial_out': (row.get('International Dial Out Phone Number') or '').strip(),
                    'independent': (row.get('ISO Independent Indicator') or '').strip(),
                }
                obj, created_flag = CountryISO.objects.update_or_create(
                    code=code,
                    defaults=defaults
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'✅ Carga completada. Creados: {created}, Actualizados: {updated}, Total: {CountryISO.objects.count()}'
        ))
