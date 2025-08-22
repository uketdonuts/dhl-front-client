from django.core.management.base import BaseCommand
from django.db.models import Q, Count
from dhl_api.models import ServiceZone


class Command(BaseCommand):
    help = (
        'Estadísticas rápidas: ciudades por país y cantidad de rangos de códigos postales '
        'por ciudad/área. Útil para validar cobertura de dropdowns.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--country', '-c', type=str, default=None,
            help='Filtrar por código de país ISO (2 letras), ej: PA, CO, US'
        )
        parser.add_argument(
            '--limit', '-n', type=int, default=15,
            help='Límite de ciudades/áreas a listar por país (por orden de más rangos postales)'
        )

    def handle(self, *args, **options):
        country_filter = (options.get('country') or '').upper().strip() or None
        limit = int(options.get('limit') or 15)

        base_qs = ServiceZone.objects.all()
        if country_filter:
            base_qs = base_qs.filter(country_code=country_filter)

        countries = (
            base_qs.values('country_code', 'country_name')
            .distinct().order_by('country_name')
        )

        if not countries:
            self.stdout.write(self.style.WARNING('No hay datos de ServiceZone cargados.'))
            return

        self.stdout.write(self.style.SUCCESS('=== Estadísticas ESD (ServiceZone) ==='))
        if country_filter:
            self.stdout.write(f"Filtro de país: {country_filter}")
        self.stdout.write('')

        for c in countries:
            cc = c['country_code']
            cn = c['country_name']
            qs = ServiceZone.objects.filter(country_code=cc)
            total = qs.count()
            city_name_count = qs.exclude(Q(city_name__isnull=True) | Q(city_name='')).count()
            service_area_count = qs.exclude(Q(service_area__isnull=True) | Q(service_area='')).count()

            use_city_name = (city_name_count / total) > 0.1 if total else False
            use_service_area = (service_area_count / total) > 0.1 if total else False

            if use_city_name:
                mode = 'city_name'
                cities_qs = (
                    qs.exclude(Q(city_name__isnull=True) | Q(city_name=''))
                      .values('city_name').distinct()
                )
                cities_count = cities_qs.count()

                postal_qs = qs.exclude(
                    Q(postal_code_from__isnull=True) | Q(postal_code_from='') |
                    Q(postal_code_to__isnull=True) | Q(postal_code_to='')
                )
                # Conteo de rangos por ciudad
                per_city = (
                    postal_qs.values('city_name')
                    .annotate(ranges=Count('id'))
                    .order_by('-ranges')
                )
                # Stats rápidas
                counts = list(per_city.values_list('ranges', flat=True))
                total_ranges = sum(counts)
                max_ranges = max(counts) if counts else 0
                min_ranges = min(counts) if counts else 0
                avg_ranges = (total_ranges / len(counts)) if counts else 0

                self.stdout.write(self.style.SUCCESS(f"{cc} - {cn}"))
                self.stdout.write(f"  Registros totales: {total}")
                self.stdout.write(f"  Modo ciudades: city_name (ciudades únicas: {cities_count})")
                self.stdout.write(f"  Rangos postales totales asociados a ciudades: {total_ranges}")
                self.stdout.write(
                    f"  Rangos por ciudad -> max: {max_ranges}, min: {min_ranges}, avg: {avg_ranges:.2f}"
                )
                self.stdout.write("  Top ciudades por rangos postales:")
                for row in per_city[:limit]:
                    self.stdout.write(f"    - {row['city_name'] or '(sin nombre)'}: {row['ranges']} rangos")
                self.stdout.write("")

            elif use_service_area:
                mode = 'service_area'
                areas_qs = (
                    qs.exclude(Q(service_area__isnull=True) | Q(service_area=''))
                      .values('service_area').distinct()
                )
                areas_count = areas_qs.count()

                postal_qs = qs.exclude(
                    Q(postal_code_from__isnull=True) | Q(postal_code_from='') |
                    Q(postal_code_to__isnull=True) | Q(postal_code_to='')
                )
                per_area = (
                    postal_qs.values('service_area')
                    .annotate(ranges=Count('id'))
                    .order_by('-ranges')
                )
                counts = list(per_area.values_list('ranges', flat=True))
                total_ranges = sum(counts)
                max_ranges = max(counts) if counts else 0
                min_ranges = min(counts) if counts else 0
                avg_ranges = (total_ranges / len(counts)) if counts else 0

                self.stdout.write(self.style.SUCCESS(f"{cc} - {cn}"))
                self.stdout.write(f"  Registros totales: {total}")
                self.stdout.write(f"  Modo ciudades: service_area (áreas únicas: {areas_count})")
                self.stdout.write(f"  Rangos postales totales asociados a áreas: {total_ranges}")
                self.stdout.write(
                    f"  Rangos por área -> max: {max_ranges}, min: {min_ranges}, avg: {avg_ranges:.2f}"
                )
                self.stdout.write("  Top áreas por rangos postales:")
                for row in per_area[:limit]:
                    self.stdout.write(f"    - {row['service_area'] or '(sin código)'}: {row['ranges']} rangos")
                self.stdout.write("")

            else:
                self.stdout.write(self.style.SUCCESS(f"{cc} - {cn}"))
                self.stdout.write(f"  Registros totales: {total}")
                self.stdout.write("  Sin datos suficientes de city_name o service_area para derivar ciudades.")
                self.stdout.write("")
