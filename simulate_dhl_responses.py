#!/usr/bin/env python
"""
Script para simular respuestas DHL y ajustar las vistas
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime

# Respuestas simuladas basadas en documentación DHL
SIMULATED_RESPONSES = {
    "epod": {
        "success": """<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
    <SOAP-ENV:Body>
        <ns1:shipmentDocumentRetrieveResp xmlns:ns1="glDHLExpressePOD/providers/DocumentRetrieve">
            <MSG>
                <Hdr Dtm="2018-08-06T08:08:41.914+02:00" Id="1533535721914" Ver="1.038"/>
                <Bd>
                    <Shp Id="2287013540">
                        <ShpInDoc>
                            <SDoc DocTyCd="POD" Img="JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PAovVGl0bGUgKP7/AEQASABMACAAZQBQAE8ARAB" DocId="123456"/>
                        </ShpInDoc>
                    </Shp>
                </Bd>
            </MSG>
        </ns1:shipmentDocumentRetrieveResp>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>""",
        "error": """<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
    <SOAP-ENV:Body>
        <SOAP-ENV:Fault>
            <faultcode>SOAP-ENV:Server</faultcode>
            <faultstring>Authentication failed</faultstring>
        </SOAP-ENV:Fault>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
    },
    "tracking": {
        "success": """<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
    <SOAP-ENV:Body>
        <ns1:trackShipmentResponse xmlns:ns1="http://scxgxtt.phx-dc.dhl.com/glDHLExpressTrack">
            <TrackingResponse>
                <AWBInfo>
                    <AWBNumber>1234567890</AWBNumber>
                    <Status>
                        <ActionStatus>delivered</ActionStatus>
                        <StatusText>Delivered</StatusText>
                    </Status>
                    <ShipmentInfo>
                        <OriginServiceArea>
                            <ServiceAreaCode>MIA</ServiceAreaCode>
                            <Description>Miami</Description>
                        </OriginServiceArea>
                        <DestinationServiceArea>
                            <ServiceAreaCode>NYC</ServiceAreaCode>
                            <Description>New York</Description>
                        </DestinationServiceArea>
                        <Weight>2.5</Weight>
                        <WeightUnit>KG</WeightUnit>
                        <Pieces>1</Pieces>
                    </ShipmentInfo>
                    <ShipmentEvent>
                        <Date>2024-01-15</Date>
                        <Time>10:30:00</Time>
                        <ServiceEvent>
                            <EventCode>PU</EventCode>
                            <Description>Picked up</Description>
                        </ServiceEvent>
                        <ServiceArea>
                            <ServiceAreaCode>MIA</ServiceAreaCode>
                            <Description>Miami, FL</Description>
                        </ServiceArea>
                    </ShipmentEvent>
                    <ShipmentEvent>
                        <Date>2024-01-16</Date>
                        <Time>08:15:00</Time>
                        <ServiceEvent>
                            <EventCode>DL</EventCode>
                            <Description>Delivered</Description>
                        </ServiceEvent>
                        <ServiceArea>
                            <ServiceAreaCode>NYC</ServiceAreaCode>
                            <Description>New York, NY</Description>
                        </ServiceArea>
                    </ShipmentEvent>
                </AWBInfo>
            </TrackingResponse>
        </ns1:trackShipmentResponse>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>""",
        "error": """<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
    <SOAP-ENV:Body>
        <SOAP-ENV:Fault>
            <faultcode>SOAP-ENV:Client</faultcode>
            <faultstring>Invalid tracking number</faultstring>
        </SOAP-ENV:Fault>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
    },
    "rate": {
        "success": """<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
    <SOAP-ENV:Body>
        <ns1:RateResponse xmlns:ns1="http://scxgxtt.phx-dc.dhl.com/euExpressRateBook">
            <Provider>
                <Service>
                    <ServiceType>P</ServiceType>
                    <ServiceName>Express Worldwide</ServiceName>
                    <TotalNet>
                        <Amount>156.75</Amount>
                        <Currency>USD</Currency>
                    </TotalNet>
                    <DeliveryTime>
                        <DayOfWeek>5</DayOfWeek>
                        <Date>2024-01-17</Date>
                        <Time>12:00:00</Time>
                    </DeliveryTime>
                </Service>
                <Service>
                    <ServiceType>K</ServiceType>
                    <ServiceName>Express Economy</ServiceName>
                    <TotalNet>
                        <Amount>98.50</Amount>
                        <Currency>USD</Currency>
                    </TotalNet>
                    <DeliveryTime>
                        <DayOfWeek>1</DayOfWeek>
                        <Date>2024-01-19</Date>
                        <Time>12:00:00</Time>
                    </DeliveryTime>
                </Service>
            </Provider>
        </ns1:RateResponse>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>""",
        "error": """<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
    <SOAP-ENV:Body>
        <SOAP-ENV:Fault>
            <faultcode>SOAP-ENV:Client</faultcode>
            <faultstring>Invalid origin/destination</faultstring>
        </SOAP-ENV:Fault>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
    }
}

def analyze_dhl_responses():
    """Analiza las respuestas DHL simuladas"""
    print("=== ANÁLISIS DE RESPUESTAS DHL (SIMULADAS) ===\n")
    
    analysis_results = {}
    
    for service, responses in SIMULATED_RESPONSES.items():
        print(f"--- Analizando servicio: {service.upper()} ---")
        
        # Analizar respuesta exitosa
        success_analysis = analyze_xml_response(responses["success"])
        
        # Analizar respuesta de error
        error_analysis = analyze_xml_response(responses["error"])
        
        analysis_results[service] = {
            "success": success_analysis,
            "error": error_analysis
        }
        
        print(f"✅ Elementos encontrados en respuesta exitosa: {len(success_analysis['elements'])}")
        print(f"❌ Elementos encontrados en respuesta de error: {len(error_analysis['elements'])}")
        
        # Mostrar elementos clave
        if service == "epod":
            pdf_elements = [elem for elem in success_analysis['elements'] if 'Img' in elem.get('attributes', {})]
            if pdf_elements:
                print(f"📄 Elementos PDF encontrados: {len(pdf_elements)}")
            else:
                print("📄 No se encontraron elementos PDF")
        
        elif service == "tracking":
            event_elements = [elem for elem in success_analysis['elements'] if 'Event' in elem['tag']]
            status_elements = [elem for elem in success_analysis['elements'] if 'Status' in elem['tag']]
            print(f"📍 Eventos de seguimiento: {len(event_elements)}")
            print(f"📊 Elementos de estado: {len(status_elements)}")
        
        elif service == "rate":
            service_elements = [elem for elem in success_analysis['elements'] if 'Service' in elem['tag']]
            amount_elements = [elem for elem in success_analysis['elements'] if 'Amount' in elem['tag']]
            print(f"💰 Servicios encontrados: {len(service_elements)}")
            print(f"💵 Precios encontrados: {len(amount_elements)}")
        
        print()
    
    return analysis_results

def analyze_xml_response(xml_text):
    """Analiza una respuesta XML"""
    try:
        root = ET.fromstring(xml_text)
        
        elements = []
        namespaces = set()
        
        for elem in root.iter():
            # Extraer namespace si existe
            if elem.tag.startswith('{'):
                namespace = elem.tag.split('}')[0] + '}'
                namespaces.add(namespace)
                tag_name = elem.tag.split('}')[1]
            else:
                tag_name = elem.tag
            
            elements.append({
                'tag': tag_name,
                'full_tag': elem.tag,
                'text': elem.text,
                'attributes': dict(elem.attrib),
                'has_children': len(list(elem)) > 0
            })
        
        # Verificar si es un fault
        is_fault = any('fault' in elem['tag'].lower() for elem in elements)
        
        return {
            'elements': elements,
            'namespaces': list(namespaces),
            'is_fault': is_fault,
            'root_tag': root.tag
        }
    
    except ET.ParseError as e:
        return {
            'error': f'XML Parse Error: {str(e)}',
            'elements': [],
            'namespaces': [],
            'is_fault': True
        }

def generate_improved_views():
    """Genera código mejorado para las vistas"""
    print("=== GENERANDO VISTAS MEJORADAS ===\n")
    
    # Código mejorado para el servicio DHL
    improved_service_code = '''
# Servicio DHL mejorado basado en análisis de respuestas

import xml.etree.ElementTree as ET
import base64
import re
from datetime import datetime

class ImprovedDHLService:
    def __init__(self, username, password, base_url, environment="sandbox"):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.environment = environment
        
        # Configuración de timeouts mejorada
        self.timeout = 30
        self.max_retries = 3
        
        # Namespaces comunes en respuestas DHL
        self.namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'epod': 'glDHLExpressePOD/providers/DocumentRetrieve',
            'track': 'http://scxgxtt.phx-dc.dhl.com/glDHLExpressTrack',
            'rate': 'http://scxgxtt.phx-dc.dhl.com/euExpressRateBook'
        }
    
    def parse_epod_response(self, response_text):
        """Parser mejorado para respuestas ePOD"""
        try:
            root = ET.fromstring(response_text)
            
            # Verificar si es un fault
            if self._is_fault_response(root):
                return self._parse_fault_response(root)
            
            # Buscar datos PDF con múltiples estrategias
            pdf_data = None
            
            # Estrategia 1: Atributo Img en cualquier elemento
            for elem in root.iter():
                if elem.get('Img'):
                    pdf_data = elem.get('Img')
                    break
            
            # Estrategia 2: Elemento con texto que parece PDF
            if not pdf_data:
                for elem in root.iter():
                    if elem.text and len(elem.text) > 100:
                        # Verificar si parece base64 de PDF
                        if elem.text.startswith('JVBERi') or elem.text.startswith('%PDF'):
                            pdf_data = elem.text
                            break
            
            # Estrategia 3: Regex en texto completo
            if not pdf_data:
                pdf_match = re.search(r'Img="([^"]*JVBERi[^"]*)"', response_text)
                if pdf_match:
                    pdf_data = pdf_match.group(1)
            
            if pdf_data:
                # Validar que sea base64 válido
                try:
                    base64.b64decode(pdf_data)
                    return {
                        "success": True,
                        "pdf_data": pdf_data,
                        "format": "base64",
                        "size": len(pdf_data),
                        "message": "PDF obtenido exitosamente"
                    }
                except Exception:
                    return {
                        "success": False,
                        "message": "Datos PDF inválidos",
                        "pdf_preview": pdf_data[:100] if pdf_data else None
                    }
            else:
                return {
                    "success": False,
                    "message": "No se encontró PDF en la respuesta",
                    "elements_found": self._get_element_summary(root)
                }
        
        except ET.ParseError as e:
            return {
                "success": False,
                "message": f"Error parsing XML: {str(e)}",
                "raw_response": response_text[:500]
            }
    
    def parse_tracking_response(self, response_text):
        """Parser mejorado para respuestas de tracking"""
        try:
            root = ET.fromstring(response_text)
            
            # Verificar si es un fault
            if self._is_fault_response(root):
                return self._parse_fault_response(root)
            
            # Extraer información del envío
            shipment_info = {}
            events = []
            
            # Buscar AWB Number
            awb_elements = root.findall('.//AWBNumber') + root.findall('.//*[contains(local-name(), "AWBNumber")]')
            if awb_elements:
                shipment_info['tracking_number'] = awb_elements[0].text
            
            # Buscar estado
            status_elements = root.findall('.//Status') + root.findall('.//*[contains(local-name(), "Status")]')
            for status_elem in status_elements:
                if status_elem.text:
                    shipment_info['status'] = status_elem.text
                    break
                # Buscar en elementos hijos
                for child in status_elem:
                    if child.text:
                        shipment_info['status'] = child.text
                        break
            
            # Buscar información del envío
            weight_elements = root.findall('.//Weight') + root.findall('.//*[contains(local-name(), "Weight")]')
            if weight_elements and weight_elements[0].text:
                shipment_info['weight'] = weight_elements[0].text
            
            # Buscar eventos
            event_elements = root.findall('.//*[contains(local-name(), "Event")]')
            for event_elem in event_elements:
                event = {}
                for child in event_elem:
                    tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    event[tag_name.lower()] = child.text
                
                if event:
                    events.append(event)
            
            return {
                "success": True,
                "tracking_info": shipment_info,
                "events": events,
                "total_events": len(events),
                "message": "Información de seguimiento obtenida"
            }
        
        except ET.ParseError as e:
            return {
                "success": False,
                "message": f"Error parsing XML: {str(e)}",
                "raw_response": response_text[:500]
            }
    
    def parse_rate_response(self, response_text):
        """Parser mejorado para respuestas de cotización"""
        try:
            root = ET.fromstring(response_text)
            
            # Verificar si es un fault
            if self._is_fault_response(root):
                return self._parse_fault_response(root)
            
            rates = []
            
            # Buscar servicios
            service_elements = root.findall('.//Service') + root.findall('.//*[contains(local-name(), "Service")]')
            
            for service_elem in service_elements:
                rate = {}
                
                # Extraer información del servicio
                for child in service_elem:
                    tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    
                    if tag_name == 'ServiceType':
                        rate['service_code'] = child.text
                    elif tag_name == 'ServiceName':
                        rate['service_name'] = child.text
                    elif tag_name == 'TotalNet':
                        # Buscar monto y moneda
                        for net_child in child:
                            net_tag = net_child.tag.split('}')[-1] if '}' in net_child.tag else net_child.tag
                            if net_tag == 'Amount':
                                rate['total_charge'] = float(net_child.text) if net_child.text else 0
                            elif net_tag == 'Currency':
                                rate['currency'] = net_child.text
                    elif tag_name == 'DeliveryTime':
                        # Extraer tiempo de entrega
                        delivery_parts = []
                        for dt_child in child:
                            if dt_child.text:
                                delivery_parts.append(dt_child.text)
                        rate['delivery_time'] = ' '.join(delivery_parts) if delivery_parts else 'Unknown'
                
                if rate.get('service_code'):
                    # Asegurar valores por defecto
                    rate.setdefault('service_name', f"Service {rate['service_code']}")
                    rate.setdefault('total_charge', 0.0)
                    rate.setdefault('currency', 'USD')
                    rate.setdefault('delivery_time', 'Unknown')
                    
                    rates.append(rate)
            
            return {
                "success": True,
                "rates": rates,
                "total_rates": len(rates),
                "message": f"Se encontraron {len(rates)} tarifas disponibles"
            }
        
        except ET.ParseError as e:
            return {
                "success": False,
                "message": f"Error parsing XML: {str(e)}",
                "raw_response": response_text[:500]
            }
    
    def _is_fault_response(self, root):
        """Verifica si la respuesta es un fault"""
        fault_elements = root.findall('.//{http://schemas.xmlsoap.org/soap/envelope/}Fault')
        return len(fault_elements) > 0
    
    def _parse_fault_response(self, root):
        """Parsea respuesta de error/fault"""
        fault_elements = root.findall('.//{http://schemas.xmlsoap.org/soap/envelope/}Fault')
        
        if fault_elements:
            fault = fault_elements[0]
            fault_code = fault.find('.//{http://schemas.xmlsoap.org/soap/envelope/}faultcode')
            fault_string = fault.find('.//{http://schemas.xmlsoap.org/soap/envelope/}faultstring')
            
            return {
                "success": False,
                "error_type": "soap_fault",
                "fault_code": fault_code.text if fault_code is not None else "Unknown",
                "fault_string": fault_string.text if fault_string is not None else "Unknown error",
                "message": f"Error SOAP: {fault_string.text if fault_string is not None else 'Unknown error'}"
            }
        
        return {
            "success": False,
            "error_type": "unknown_fault",
            "message": "Error desconocido en respuesta"
        }
    
    def _get_element_summary(self, root):
        """Obtiene resumen de elementos en el XML"""
        elements = []
        for elem in root.iter():
            tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            elements.append({
                'tag': tag_name,
                'has_text': bool(elem.text and elem.text.strip()),
                'has_attributes': bool(elem.attrib),
                'attributes': list(elem.attrib.keys()) if elem.attrib else []
            })
        return elements[:10]  # Primeros 10 elementos
'''
    
    # Guardar el código mejorado
    with open('/Users/noelsantamaria/Develop/dhl-front-client/improved_dhl_service.py', 'w') as f:
        f.write(improved_service_code)
    
    print("✅ Código del servicio mejorado guardado en 'improved_dhl_service.py'")
    
    # Ahora generar ajustes para views.py
    view_adjustments = '''
# Ajustes para views.py basados en análisis de respuestas

# En dhl_api/views.py, reemplazar los métodos de parsing:

def epod_view(request):
    """Endpoint mejorado para obtener ePOD"""
    serializer = EPODRequestSerializer(data=request.data)
    if serializer.is_valid():
        try:
            # Usar servicio mejorado
            dhl_service = ImprovedDHLService(
                username=settings.DHL_USERNAME,
                password=settings.DHL_PASSWORD,
                base_url=settings.DHL_BASE_URL,
                environment=settings.DHL_ENVIRONMENT
            )
            
            # Hacer request a DHL
            response = dhl_service.get_ePOD(serializer.validated_data['shipment_id'])
            
            # Usar parser mejorado
            result = dhl_service.parse_epod_response(response.text)
            
            # Agregar información adicional
            result['request_timestamp'] = datetime.now().isoformat()
            result['shipment_id'] = serializer.validated_data['shipment_id']
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error en epod_view: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error interno: {str(e)}',
                'error_type': 'internal_error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'message': 'ID de envío requerido',
        'error_type': 'validation_error'
    }, status=status.HTTP_400_BAD_REQUEST)

# Similar para tracking_view y rate_view...
'''
    
    with open('/Users/noelsantamaria/Develop/dhl-front-client/view_adjustments_recommended.py', 'w') as f:
        f.write(view_adjustments)
    
    print("✅ Ajustes recomendados para views.py guardados en 'view_adjustments_recommended.py'")

def main():
    """Función principal"""
    print("🚀 Iniciando análisis de respuestas DHL...\n")
    
    # Analizar respuestas simuladas
    analysis_results = analyze_dhl_responses()
    
    # Generar vistas mejoradas
    generate_improved_views()
    
    print("\n=== RESUMEN DE MEJORAS ===")
    print("✅ Análisis de respuestas XML completado")
    print("✅ Parsers mejorados generados")
    print("✅ Manejo de errores mejorado")
    print("✅ Código de vistas optimizado")
    
    print("\n=== PRÓXIMOS PASOS ===")
    print("1. Revisar 'improved_dhl_service.py' para el servicio mejorado")
    print("2. Aplicar cambios de 'view_adjustments_recommended.py' en views.py")
    print("3. Probar con credenciales reales")
    print("4. Ajustar según respuestas reales si es necesario")

if __name__ == "__main__":
    main()
