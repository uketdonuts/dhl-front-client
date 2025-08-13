"""
Comando para cargar mapeos de área de servicio → ciudad amigable desde CSV o JSON.

Formatos soportados:
- CSV con encabezados: country_code,service_area,state_code?,city_name,display_name,postal_code_from?,postal_code_to?,notes?
- JSON: lista de objetos con las mismas claves.
"""
import csv
import json
import os
from typing import List, Dict, Tuple, Iterable

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from dhl_api.models import ServiceAreaCityMap, ServiceZone


class Command(BaseCommand):
    help = 'Carga mapeos de área de servicio a nombre de ciudad (CSV o JSON)'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='Ruta al archivo CSV o JSON con el mapeo')
        parser.add_argument('--clear', action='store_true', help='Limpiar tabla antes de cargar')
        parser.add_argument('--upsert', action='store_true', help='Actualizar si existe el registro (por unique_together)')
        parser.add_argument('--batch-size', type=int, default=500, help='Tamaño de lote para inserción')
        parser.add_argument('--countries', type=str, default='', help='ISO2 separados por coma para filtrar (ej: CA,US)')
        parser.add_argument('--max-rows', type=int, default=0, help='Máximo de filas a procesar (0 = sin límite)')
        parser.add_argument('--delimiter', type=str, default='', help='Delimitador CSV (auto si vacío)')
        parser.add_argument('--derive-service-area', action='store_true', help='Derivar service_area usando ServiceZone por código postal')
        parser.add_argument('--start-row', type=int, default=0, help='Saltar N filas de datos (no cuenta el header)')
        parser.add_argument('--progress-every', type=int, default=100000, help='Mostrar progreso cada N filas procesadas')

    def handle(self, *args, **options):
        file_path = options['file']
        clear = options['clear']
        upsert = options['upsert']
        batch_size = options['batch_size']
        countries_filter = [c.strip().upper() for c in options.get('countries', '').split(',') if c.strip()]
        max_rows = int(options.get('max_rows') or 0)
        delimiter_opt = options.get('delimiter') or ''
        derive_sa = bool(options.get('derive_service_area'))

        if not os.path.exists(file_path):
            raise CommandError(f'El archivo {file_path} no existe')

        if clear:
            self.stdout.write('Limpiando tabla ServiceAreaCityMap...')
            ServiceAreaCityMap.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Tabla limpiada'))

        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.csv':
            records, csv_meta = self._read_csv_stream(file_path, delimiter_opt)
        elif ext in ('.json', '.jsonl'):
            records = self._read_json(file_path)
            csv_meta = {'source': 'json'}
        else:
            raise CommandError('Formato no soportado. Use CSV o JSON')

        created, updated, errors = 0, 0, 0
        batch: List[ServiceAreaCityMap] = []

        def _first_key(d: dict, keys: List[str], default: str = '') -> str:
            for k in keys:
                if k in d and d[k] is not None and str(d[k]).strip() != '':
                    return str(d[k])
            return default

        def _normalize_postal(val: str) -> str:
            return val.replace(' ', '').replace('-', '').upper().strip() if val else ''

        def normalize(rec: dict) -> dict:
            # Aliases para columnas comunes
            country_code = _first_key(rec, ['country_code', 'country', 'CountryCode', 'COUNTRY_CODE', 'DHL Country Code']).upper().strip()
            state_code = _first_key(rec, ['state_code', 'state', 'province', 'StateCode', 'STATE_CODE', 'Country Division Code']).upper().strip()
            service_area = _first_key(rec, ['service_area', 'service_area_code', 'ServiceArea', 'SERVICE_AREA', 'Service Area Code', 'ServiceAreaCode']).upper().strip()
            city_name = _first_key(rec, ['city_name', 'city', 'locality', 'City', 'CITY', 'City Name', 'Suburb Name']).strip()
            display_name = _first_key(rec, ['display_name', 'label', 'DisplayName']).strip()
            pc = _first_key(rec, ['postal_code', 'postcode', 'zip', 'ZIP', 'PostalCode', 'Postcode']).strip()
            pfrom = _normalize_postal(_first_key(rec, ['postal_code_from', 'zip_from', 'postcode_from', 'PostalFrom', 'PostalFromCode']))
            pto = _normalize_postal(_first_key(rec, ['postal_code_to', 'zip_to', 'postcode_to', 'PostalTo', 'PostalToCode']))
            notes = _first_key(rec, ['notes', 'comment', 'source']).strip()

            # Derivar service_area por postal si falta y se solicitó
            if derive_sa and not service_area and country_code and (pc or pfrom):
                pc_norm = _normalize_postal(pc or pfrom)
                if pc_norm:
                    sa = ServiceZone.objects.filter(
                        country_code=country_code,
                        postal_code_from__lte=pc_norm,
                        postal_code_to__gte=pc_norm,
                    ).values_list('service_area', flat=True).first()
                    if sa:
                        service_area = sa

            # Derivar display_name si falta
            if not display_name:
                if city_name and pc:
                    display_name = f"{city_name} { _normalize_postal(pc) }"
                elif city_name and pfrom and pto:
                    display_name = f"{city_name} {pfrom}-{pto}"
                elif city_name:
                    display_name = city_name

            return {
                'country_code': country_code,
                'state_code': state_code,
                'service_area': service_area,
                'city_name': city_name,
                'display_name': display_name,
                'postal_code_from': pfrom,
                'postal_code_to': pto,
                'notes': notes,
            }

        try:
            processed = 0
            seen_any = False
            start_row = max(0, int(options.get('start_row') or 0))
            progress_every = max(1, int(options.get('progress_every') or 100000))
            for idx, rec in enumerate(records, 1):
                # Saltar filas iniciales si se indicó (sin contar header)
                if start_row and idx <= start_row:
                    continue
                n = normalize(rec)
                if countries_filter and n['country_code'] not in countries_filter:
                    continue
                processed += 1
                seen_any = True
                if max_rows and processed > max_rows:
                    break

                if not n['country_code'] or not n['service_area'] or not n['display_name']:
                    errors += 1
                    continue

                if upsert:
                    obj, created_flag = ServiceAreaCityMap.objects.update_or_create(
                        country_code=n['country_code'],
                        state_code=n['state_code'],
                        service_area=n['service_area'],
                        postal_code_from=n['postal_code_from'],
                        postal_code_to=n['postal_code_to'],
                        defaults={
                            'city_name': n['city_name'] or n['display_name'],
                            'display_name': n['display_name'],
                            'notes': n['notes'],
                        }
                    )
                    if created_flag:
                        created += 1
                    else:
                        updated += 1
                else:
                    batch.append(ServiceAreaCityMap(**{
                        **n,
                        'city_name': n['city_name'] or n['display_name'],
                    }))
                    if len(batch) >= batch_size:
                        ServiceAreaCityMap.objects.bulk_create(batch, ignore_conflicts=True, batch_size=batch_size)
                        created += len(batch)
                        batch = []

                if progress_every and processed % progress_every == 0:
                    self.stdout.write(f"Progreso: {processed} filas procesadas...")

            if batch:
                ServiceAreaCityMap.objects.bulk_create(batch, ignore_conflicts=True, batch_size=len(batch))
                created += len(batch)

        except Exception as e:
            raise CommandError(f'Error cargando mapeo: {e}')

        if not seen_any:
            self.stdout.write(self.style.WARNING('No se procesaron filas (verifique filtros --countries y --start-row).'))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'✅ Mapeo cargado. Procesados: {processed}, Creados: {created}, Actualizados: {updated}, Errores: {errors}'
            ))

    def _read_csv_stream(self, path: str, delimiter_opt: str = '') -> Tuple[Iterable[dict], Dict[str, str]]:
        # Sniff delimitador con una lectura corta
        with open(path, 'r', encoding='utf-8-sig', newline='') as sniff:
            sample = sniff.read(8192)
            delimiter = delimiter_opt
            if not delimiter:
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                    delimiter = dialect.delimiter
                except Exception:
                    delimiter = ','
        def iterator():
            with open(path, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                # Emitir filas una por una
                count = 0
                for row in reader:
                    count += 1
                    if count % 100000 == 0:
                        # Marca de progreso silenciosa: no imprimir aquí para evitar ruido
                        pass
                    yield row
        # Devolver iterador y metadatos
        # Nota: fieldnames requiere un DictReader; re-abrimos para capturar columnas
        with open(path, 'r', encoding='utf-8-sig', newline='') as f2:
            reader2 = csv.DictReader(f2, delimiter=delimiter)
            columns = reader2.fieldnames or []
        return iterator(), {'delimiter': delimiter, 'columns': columns}

    def _read_json(self, path: str) -> List[dict]:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'data' in data:
                data = data['data']
            if isinstance(data, list):
                return data
            return []
