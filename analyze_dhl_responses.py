#!/usr/bin/env python
"""
Script para analizar las respuestas de DHL y generar recomendaciones
para ajustar las vistas del backend
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime

class DHLResponseAnalyzer:
    def __init__(self):
        self.recommendations = []
        self.view_adjustments = {}
    
    def analyze_responses(self, results_file):
        """Analiza los resultados de las pruebas DHL"""
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
            
            print("=== ANÁLISIS DE RESPUESTAS DHL ===\n")
            
            # Analizar cada servicio
            for service, result in results.items():
                print(f"--- {service.upper()} ---")
                self.analyze_service_response(service, result)
                print()
            
            # Generar recomendaciones
            self.generate_recommendations()
            
            # Crear código de ajustes
            self.create_view_adjustments()
            
        except Exception as e:
            print(f"Error analizando respuestas: {str(e)}")
    
    def analyze_service_response(self, service, result):
        """Analiza la respuesta de un servicio específico"""
        if result.get('success') == False:
            print(f"❌ Error en {service}: {result.get('error', 'Error desconocido')}")
            
            # Analizar el tipo de error
            if 'HTTP 401' in str(result.get('error', '')):
                self.recommendations.append({
                    'service': service,
                    'issue': 'Credenciales inválidas',
                    'solution': 'Verificar username/password para este endpoint'
                })
            elif 'HTTP 403' in str(result.get('error', '')):
                self.recommendations.append({
                    'service': service,
                    'issue': 'Acceso denegado',
                    'solution': 'Verificar permisos de la cuenta DHL'
                })
            elif 'HTTP 404' in str(result.get('error', '')):
                self.recommendations.append({
                    'service': service,
                    'issue': 'Endpoint no encontrado',
                    'solution': 'Verificar URL del endpoint'
                })
            elif 'timeout' in str(result.get('error', '')).lower():
                self.recommendations.append({
                    'service': service,
                    'issue': 'Timeout de conexión',
                    'solution': 'Aumentar timeout o verificar conectividad'
                })
            
            # Mostrar respuesta para análisis
            if result.get('response'):
                print(f"Respuesta: {result['response'][:200]}...")
        
        else:
            print(f"✅ {service} respondió correctamente")
            
            # Analizar estructura de respuesta exitosa
            if service == 'epod':
                self.analyze_epod_structure(result)
            elif service == 'tracking':
                self.analyze_tracking_structure(result)
            elif service == 'rate':
                self.analyze_rate_structure(result)
    
    def analyze_epod_structure(self, result):
        """Analiza la estructura de respuesta ePOD"""
        print("Estructura ePOD encontrada:")
        
        if result.get('has_pdf_data'):
            print("  - ✅ Contiene datos PDF")
            self.view_adjustments['epod'] = {
                'has_pdf': True,
                'pdf_field': 'Img',
                'response_format': 'base64'
            }
        else:
            print("  - ❌ No contiene datos PDF")
            self.recommendations.append({
                'service': 'epod',
                'issue': 'Sin datos PDF en respuesta',
                'solution': 'Verificar ID de envío válido o parámetros de request'
            })
        
        # Mostrar elementos encontrados
        if result.get('elements'):
            print(f"  - Elementos XML encontrados: {len(result['elements'])}")
            for elem in result['elements'][:5]:  # Mostrar primeros 5
                print(f"    * {elem['tag']}: {elem.get('text', 'No text')[:50]}")
    
    def analyze_tracking_structure(self, result):
        """Analiza la estructura de respuesta de tracking"""
        print("Estructura Tracking encontrada:")
        
        if result.get('elements'):
            print(f"  - Elementos XML encontrados: {len(result['elements'])}")
            
            # Buscar elementos clave
            key_elements = ['AWBNumber', 'ShipmentEvent', 'Status', 'DeliveryDate']
            found_elements = []
            
            for elem in result['elements']:
                if any(key in elem['tag'] for key in key_elements):
                    found_elements.append(elem['tag'])
            
            print(f"  - Elementos clave encontrados: {found_elements}")
            
            self.view_adjustments['tracking'] = {
                'elements_found': found_elements,
                'has_events': 'ShipmentEvent' in str(found_elements),
                'has_status': 'Status' in str(found_elements)
            }
    
    def analyze_rate_structure(self, result):
        """Analiza la estructura de respuesta de cotización"""
        print("Estructura Rate encontrada:")
        
        if result.get('elements'):
            print(f"  - Elementos XML encontrados: {len(result['elements'])}")
            
            # Buscar elementos de tarifas
            rate_elements = ['Rate', 'TotalNet', 'ServiceType', 'Currency']
            found_elements = []
            
            for elem in result['elements']:
                if any(rate_elem in elem['tag'] for rate_elem in rate_elements):
                    found_elements.append(elem['tag'])
            
            print(f"  - Elementos de tarifas encontrados: {found_elements}")
            
            self.view_adjustments['rate'] = {
                'elements_found': found_elements,
                'has_rates': 'Rate' in str(found_elements),
                'has_pricing': 'TotalNet' in str(found_elements)
            }
    
    def generate_recommendations(self):
        """Genera recomendaciones basadas en el análisis"""
        print("=== RECOMENDACIONES ===\n")
        
        if not self.recommendations:
            print("✅ No se encontraron problemas críticos")
            return
        
        for i, rec in enumerate(self.recommendations, 1):
            print(f"{i}. {rec['service'].upper()}: {rec['issue']}")
            print(f"   Solución: {rec['solution']}\n")
    
    def create_view_adjustments(self):
        """Crea código de ajustes para las vistas"""
        print("=== AJUSTES RECOMENDADOS PARA VIEWS.PY ===\n")
        
        # Generar código de ajustes
        adjustments_code = self.generate_view_adjustments_code()
        
        # Guardar en archivo
        with open('/Users/noelsantamaria/Develop/dhl-front-client/view_adjustments.py', 'w') as f:
            f.write(adjustments_code)
        
        print("Código de ajustes guardado en 'view_adjustments.py'")
    
    def generate_view_adjustments_code(self):
        """Genera el código de ajustes para las vistas"""
        code = '''"""
Ajustes recomendados para las vistas DHL basados en análisis de respuestas reales
Generado automáticamente el {timestamp}
"""

# Ajustes para el parsing de respuestas

def parse_epod_response_improved(response_text):
    """Parser mejorado para respuestas ePOD"""
    try:
        root = ET.fromstring(response_text)
        
        # Buscar datos PDF con múltiples enfoques
        pdf_data = None
        
        # Método 1: Buscar atributo Img
        for elem in root.iter():
            if elem.get('Img'):
                pdf_data = elem.get('Img')
                break
        
        # Método 2: Buscar en texto del elemento
        if not pdf_data:
            for elem in root.iter():
                if elem.text and len(elem.text) > 100 and 'JVBERi' in elem.text:
                    pdf_data = elem.text
                    break
        
        # Método 3: Buscar por patrones en el XML
        if not pdf_data:
            import re
            match = re.search(r'Img="([^"]+)"', response_text)
            if match:
                pdf_data = match.group(1)
        
        if pdf_data:
            return {{
                "success": True,
                "pdf_data": pdf_data,
                "format": "base64",
                "message": "PDF obtenido exitosamente"
            }}
        else:
            return {{
                "success": False,
                "message": "No se encontró PDF en la respuesta",
                "raw_response": response_text[:500]
            }}
    
    except Exception as e:
        return {{
            "success": False,
            "message": f"Error parsing ePOD response: {{str(e)}}",
            "raw_response": response_text[:500]
        }}

def parse_tracking_response_improved(response_text):
    """Parser mejorado para respuestas de tracking"""
    try:
        root = ET.fromstring(response_text)
        
        # Buscar información de envío
        shipment_info = {{}}
        events = []
        
        # Buscar AWB Number
        for elem in root.iter():
            if 'AWBNumber' in elem.tag:
                shipment_info['tracking_number'] = elem.text
                break
        
        # Buscar eventos de envío
        for elem in root.iter():
            if 'ShipmentEvent' in elem.tag or 'Event' in elem.tag:
                event = {{}}
                for child in elem:
                    tag_name = child.tag.split('}}')[-1] if '}}' in child.tag else child.tag
                    event[tag_name.lower()] = child.text
                if event:
                    events.append(event)
        
        # Buscar estado general
        for elem in root.iter():
            if 'Status' in elem.tag:
                shipment_info['status'] = elem.text
                break
        
        return {{
            "success": True,
            "tracking_info": shipment_info,
            "events": events,
            "message": "Información de seguimiento obtenida"
        }}
    
    except Exception as e:
        return {{
            "success": False,
            "message": f"Error parsing tracking response: {{str(e)}}",
            "raw_response": response_text[:500]
        }}

def parse_rate_response_improved(response_text):
    """Parser mejorado para respuestas de cotización"""
    try:
        root = ET.fromstring(response_text)
        
        rates = []
        
        # Buscar elementos de tarifa
        for elem in root.iter():
            if 'Rate' in elem.tag:
                rate = {{}}
                for child in elem:
                    tag_name = child.tag.split('}}')[-1] if '}}' in child.tag else child.tag
                    rate[tag_name.lower()] = child.text
                
                if rate:
                    # Normalizar estructura
                    normalized_rate = {{
                        'service_code': rate.get('servicetype', 'Unknown'),
                        'service_name': rate.get('servicename', 'Unknown Service'),
                        'total_charge': float(rate.get('totalnet', 0)),
                        'currency': rate.get('currency', 'USD'),
                        'delivery_time': rate.get('deliverytime', 'Unknown')
                    }}
                    rates.append(normalized_rate)
        
        return {{
            "success": True,
            "rates": rates,
            "message": f"Se encontraron {{len(rates)}} tarifas disponibles"
        }}
    
    except Exception as e:
        return {{
            "success": False,
            "message": f"Error parsing rate response: {{str(e)}}",
            "raw_response": response_text[:500]
        }}

# Ajustes para manejo de errores mejorado

def handle_dhl_error_response(response):
    """Maneja errores de respuesta DHL de manera mejorada"""
    if response.status_code == 401:
        return {{
            "success": False,
            "error_code": "AUTH_ERROR",
            "message": "Credenciales inválidas. Verificar username/password.",
            "suggestion": "Contactar con DHL para verificar credenciales"
        }}
    elif response.status_code == 403:
        return {{
            "success": False,
            "error_code": "ACCESS_DENIED",
            "message": "Acceso denegado. Cuenta sin permisos suficientes.",
            "suggestion": "Verificar permisos de la cuenta DHL"
        }}
    elif response.status_code == 404:
        return {{
            "success": False,
            "error_code": "ENDPOINT_NOT_FOUND",
            "message": "Endpoint no encontrado.",
            "suggestion": "Verificar URL del endpoint"
        }}
    elif response.status_code == 500:
        return {{
            "success": False,
            "error_code": "SERVER_ERROR",
            "message": "Error interno del servidor DHL.",
            "suggestion": "Reintentar más tarde"
        }}
    else:
        return {{
            "success": False,
            "error_code": "UNKNOWN_ERROR",
            "message": f"Error HTTP {{response.status_code}}",
            "response": response.text[:200]
        }}

# Configuración de timeouts mejorada
DHL_REQUEST_TIMEOUT = 30  # segundos
DHL_MAX_RETRIES = 3
DHL_RETRY_DELAY = 2  # segundos

# Headers mejorados
def get_improved_headers(soap_action, auth_type="basic"):
    """Genera headers mejorados para requests DHL"""
    headers = {{
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': soap_action,
        'User-Agent': 'DHL-API-Client/1.0',
        'Accept': 'text/xml, application/soap+xml, */*',
        'Connection': 'keep-alive'
    }}
    
    if auth_type == "basic":
        credentials = "apO3fS5mJ8zT7h:J^4oF@1qW!0qS!5b"
        import base64
        auth_header = base64.b64encode(credentials.encode()).decode()
        headers['Authorization'] = f'Basic {{auth_header}}'
    
    return headers
'''.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        return code

def main():
    """Función principal"""
    analyzer = DHLResponseAnalyzer()
    
    # Verificar si existe archivo de resultados
    results_file = '/Users/noelsantamaria/Develop/dhl-front-client/test_results.json'
    
    try:
        analyzer.analyze_responses(results_file)
    except FileNotFoundError:
        print("❌ No se encontró el archivo test_results.json")
        print("Ejecuta primero test_dhl_credentials.py para generar los resultados")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
