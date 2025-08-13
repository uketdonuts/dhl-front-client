"""
Orquestador de carga de datos de referencia:
- migrate
- load_countries
- load_esd_data
- load_service_area_map

Uso (dentro del contenedor vía django-manage.bat):
  django-manage.bat load_reference_all \
    --csv-file "/app/dhl_api/Postal_Locations_fullset_20250811010020.csv" \
    --countries CA,US --max-rows 50000 --upsert

Flags útiles:
  --skip-migrate --skip-countries --skip-esd --skip-map
  --delimiter ","  --derive-service-area
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
import time


class Command(BaseCommand):
    help = "Carga orquestada de datos de referencia (migraciones, países, ESD y mapeo service_area)."

    def add_arguments(self, parser):
        # Skips
        parser.add_argument('--skip-migrate', action='store_true', help='Omitir migraciones')
        parser.add_argument('--skip-countries', action='store_true', help='Omitir carga de countries.json')
        parser.add_argument('--skip-esd', action='store_true', help='Omitir carga de ESD.TXT')
        parser.add_argument('--skip-map', action='store_true', help='Omitir carga del CSV de mapeo')

        # CSV mapping options
        parser.add_argument('--csv-file', type=str, default='/app/dhl_api/Postal_Locations_fullset_20250811010020.csv',
                            help='Ruta del CSV masivo (dentro del contenedor)')
        parser.add_argument('--countries', type=str, default='', help='ISO2 separados por coma (ej: CA,US)')
        parser.add_argument('--max-rows', type=int, default=0, help='Máximo de filas a procesar del CSV (0 = sin límite)')
        parser.add_argument('--delimiter', type=str, default='', help='Delimitador CSV; vacío = auto-sniff')
        parser.add_argument('--upsert', action='store_true', help='Actualizar si existe el registro (upsert)')
        parser.add_argument('--derive-service-area', action='store_true', help='Derivar service_area por postal con ServiceZone')

        # Clear switches
        parser.add_argument('--clear-map', action='store_true', help='Vaciar tabla de mapeo antes de cargar')

    def handle(self, *args, **opts):
        t0 = time.time()

        def step(name: str, fn):
            self.stdout.write(self.style.HTTP_INFO(f"→ {name}..."))
            st = time.time()
            fn()
            self.stdout.write(self.style.SUCCESS(f"✔ {name} en {time.time()-st:.1f}s"))

        # 1) Migrate
        if not opts.get('skip_migrate'):
            step('Aplicando migraciones', lambda: call_command('migrate'))
        else:
            self.stdout.write('↷ Migraciones omitidas por bandera --skip-migrate')

        # 2) Countries
        if not opts.get('skip_countries'):
            step('Cargando countries.json', lambda: call_command('load_countries', file='/app/countries.json'))
        else:
            self.stdout.write('↷ Countries omitido por bandera --skip-countries')

        # 3) ESD
        if not opts.get('skip_esd'):
            step('Cargando ESD.TXT', lambda: call_command('load_esd_data', file='/app/dhl_api/ESD.TXT'))
        else:
            self.stdout.write('↷ ESD omitido por bandera --skip-esd')

        # 4) Mapping CSV
        if not opts.get('skip_map'):
            kwargs = {
                'file': opts.get('csv_file'),
            }
            if opts.get('countries'):
                kwargs['countries'] = opts['countries']
            if opts.get('max_rows'):
                kwargs['max_rows'] = int(opts['max_rows'])
            if opts.get('delimiter'):
                kwargs['delimiter'] = opts['delimiter']
            if opts.get('upsert'):
                kwargs['upsert'] = True
            if opts.get('derive_service_area'):
                kwargs['derive_service_area'] = True
            if opts.get('clear_map'):
                kwargs['clear'] = True

            step('Cargando mapeo service_area -> ciudad', lambda: call_command('load_service_area_map', **kwargs))
        else:
            self.stdout.write('↷ Mapeo CSV omitido por bandera --skip-map')

        self.stdout.write(self.style.SUCCESS(f"🎉 Proceso completo en {time.time()-t0:.1f}s"))
