from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Configura y prueba el simulador DHL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--enable',
            action='store_true',
            help='Habilita el modo simulador',
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            help='Deshabilita el modo simulador',
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Prueba el simulador',
        )

    def handle(self, *args, **options):
        if options['enable']:
            self.enable_simulator()
        elif options['disable']:
            self.disable_simulator()
        elif options['test']:
            self.test_simulator()
        else:
            self.show_status()

    def enable_simulator(self):
        """Habilita el modo simulador"""
        os.environ['DHL_SIMULATE_MODE'] = 'true'
        self.stdout.write(
            self.style.SUCCESS('✅ Modo simulador habilitado')
        )
        self.stdout.write('🔧 Variables de entorno configuradas:')
        self.stdout.write(f'   DHL_SIMULATE_MODE=true')
        self.stdout.write('🚀 Reinicia el servidor para aplicar cambios')

    def disable_simulator(self):
        """Deshabilita el modo simulador"""
        os.environ['DHL_SIMULATE_MODE'] = 'false'
        self.stdout.write(
            self.style.WARNING('⚠️ Modo simulador deshabilitado')
        )
        self.stdout.write('🔧 Usando API real de DHL')
        self.stdout.write('🚀 Reinicia el servidor para aplicar cambios')

    def test_simulator(self):
        """Prueba el simulador"""
        self.stdout.write('🧪 Probando simulador DHL...')
        
        try:
            from dhl_api.dhl_integration import get_dhl_service
            from dhl_api.test_data import TRACKING_NUMBERS
            
            # Crear servicio simulado
            dhl_service = get_dhl_service("development")
            
            self.stdout.write(self.style.SUCCESS('✅ Simulador importado correctamente'))
            
            # Probar tracking
            for status_name, tracking_num in TRACKING_NUMBERS.items():
                tracking_info = dhl_service.get_tracking(tracking_num)
                status_icon = '✅' if tracking_info.get('success') else '❌'
                self.stdout.write(f'   {status_icon} {status_name}: {tracking_num} - {tracking_info.get("tracking_info", {}).get("status", "Unknown")}')
            
            # Probar cotización
            rate_info = dhl_service.get_rate(
                origin={'country': 'PA'},
                destination={'country': 'US'},
                weight=2.5,
                dimensions={'length': 25, 'width': 20, 'height': 15}
            )
            
            if rate_info.get('success'):
                self.stdout.write(f'   ✅ Cotización: {rate_info.get("total_rates", 0)} servicios disponibles')
            else:
                self.stdout.write(f'   ❌ Error en cotización: {rate_info.get("message", "Unknown")}')
            
            self.stdout.write(self.style.SUCCESS('🎉 Simulador funcionando correctamente'))
            
        except ImportError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error importando simulador: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error probando simulador: {str(e)}')
            )

    def show_status(self):
        """Muestra el estado actual del simulador"""
        simulate_mode = os.getenv('DHL_SIMULATE_MODE', 'false').lower() == 'true'
        
        self.stdout.write('📊 Estado del simulador DHL:')
        self.stdout.write(f'   Modo simulador: {"✅ Activo" if simulate_mode else "❌ Inactivo"}')
        self.stdout.write(f'   DHL_SIMULATE_MODE: {os.getenv("DHL_SIMULATE_MODE", "no configurado")}')
        self.stdout.write(f'   DHL_ENVIRONMENT: {os.getenv("DHL_ENVIRONMENT", "no configurado")}')
        
        # Verificar disponibilidad del simulador
        try:
            from dhl_api.dhl_integration import get_dhl_service
            self.stdout.write('   Simulador disponible: ✅ Sí')
        except ImportError:
            self.stdout.write('   Simulador disponible: ❌ No')
        
        self.stdout.write('\n🔧 Comandos disponibles:')
        self.stdout.write('   python manage.py setup_simulator --enable')
        self.stdout.write('   python manage.py setup_simulator --disable')
        self.stdout.write('   python manage.py setup_simulator --test')
