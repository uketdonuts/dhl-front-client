from django.core.management.base import BaseCommand
from dhl_api.models import ServiceAreaCityMap


class Command(BaseCommand):
    help = 'Muestra estadísticas del mapeo ServiceAreaCityMap'

    def handle(self, *args, **options):
        total = ServiceAreaCityMap.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Total mappings: {total}'))
        # Mostrar algunos ejemplos
        sample = ServiceAreaCityMap.objects.all()[:5]
        for s in sample:
            self.stdout.write(f'- {s.country_code} {s.service_area} -> {s.display_name}')
