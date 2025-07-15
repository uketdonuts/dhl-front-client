#!/usr/bin/env python3
"""
Script para probar el tracking de DHL con el número 5339266472
y hacer cotización usando los datos obtenidos
"""
import sys
import os
import django
from datetime import datetime
import requests
import xml.etree.ElementTree as ET

# Configurar Django
sys.path.append('/Users/noelsantamaria/Develop/dhl-front-client')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dhl_project.settings')
django.setup()

from dhl_api.services import DHLService

def test_tracking():
    """Prueba el tracking con el número real"""
    
    # Crear servicio DHL
    dhl_service = DHLService(
        username="apO3fS5mJ8zT7h",
        password="J^4oF@1qW!0qS!5b",
        base_url="https://wsbexpress.dhl.com:443",
        environment="production"
    )
    
    # Número de tracking del ejemplo
    tracking_number = "5339266472"
    
    print(f"🚀 Probando tracking para: {tracking_number}")
    print(f"📅 Fecha: {datetime.now()}")
    print("=" * 50)
    
    try:
        # Obtener información de tracking
        result = dhl_service.get_tracking(tracking_number)
        
        print(f"✅ Éxito: {result.get('success', False)}")
        print(f"💬 Mensaje: {result.get('message', 'N/A')}")
        
        if result.get('success'):
            # Información básica
            tracking_info = result.get('tracking_info', {})
            print("\n📦 INFORMACIÓN DEL ENVÍO:")
            print(f"   AWB: {tracking_info.get('awb_number', 'N/A')}")
            print(f"   Estado: {tracking_info.get('status', 'N/A')}")
            print(f"   Origen: {tracking_info.get('origin', 'N/A')}")
            print(f"   Destino: {tracking_info.get('destination', 'N/A')}")
            print(f"   Peso: {tracking_info.get('weight', 'N/A')}")
            print(f"   Piezas: {tracking_info.get('pieces', 'N/A')}")
            print(f"   Fecha envío: {tracking_info.get('shipment_date', 'N/A')}")
            
            # Detalles de piezas
            piece_details = result.get('piece_details', [])
            if piece_details:
                print(f"\n📦 DETALLES DE PIEZAS ({len(piece_details)} piezas):")
                for i, piece in enumerate(piece_details):
                    print(f"   Pieza {i+1}:")
                    print(f"     - Número: {piece.get('piece_number', 'N/A')}")
                    print(f"     - License Plate: {piece.get('license_plate', 'N/A')}")
                    print(f"     - Peso real: {piece.get('actual_weight', 'N/A')} {piece.get('weight_unit', 'N/A')}")
                    print(f"     - Dimensiones reales: {piece.get('actual_length', 'N/A')} x {piece.get('actual_width', 'N/A')} x {piece.get('actual_height', 'N/A')}")
                    print(f"     - Peso dimensional: {piece.get('dim_weight', 'N/A')} {piece.get('weight_unit', 'N/A')}")
                    print(f"     - Tipo: {piece.get('package_type', 'N/A')}")
            
            # Eventos
            events = result.get('events', [])
            if events:
                print(f"\n📅 EVENTOS ({len(events)} eventos):")
                for event in events:
                    print(f"   {event.get('date', 'N/A')} {event.get('time', 'N/A')} - {event.get('code', 'N/A')}")
                    print(f"     {event.get('description', 'N/A')} - {event.get('location', 'N/A')}")
                    if event.get('signatory'):
                        print(f"     Firmado por: {event.get('signatory')}")
        else:
            print(f"\n❌ Error: {result.get('message', 'Error desconocido')}")
            
    except Exception as e:
        print(f"❌ Error al ejecutar: {str(e)}")

def test_rate_quote_with_tracking_data(tracking_result):
    """
    Hace una cotización usando los datos del tracking
    """
    if not tracking_result.get('success'):
        print("❌ No se puede hacer cotización sin datos de tracking válidos")
        return
    
    piece_details = tracking_result.get('piece_details', [])
    if not piece_details:
        print("❌ No se encontraron detalles de piezas para cotizar")
        return
    
    print(f"\n💰 INICIANDO COTIZACIÓN CON DATOS DEL TRACKING")
    print("=" * 60)
    
    # Usar los datos de la primera pieza como ejemplo
    first_piece = piece_details[0]
    
    # Construir el XML SOAP para la cotización
    soap_envelope = f"""<soapenv:Envelope xmlns:rat="http://scxgxtt.phx-dc.dhl.com/euExpressRateBook/RateMsgRequest" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
    <soapenv:Header>
        <wsse:Security soapenv:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
            <wsse:UsernameToken>
                <wsse:Username>apO3fS5mJ8zT7h</wsse:Username>
                <wsse:Password>J^4oF@1qW!0qS!5b</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </soapenv:Header>
    <soapenv:Body>
        <rat:RateRequest>
            <ClientDetail>
                <sso>testsso</sso>
                <plant>testplant</plant>
            </ClientDetail>
            <RequestedShipment>
                <DropOffType>REQUEST_COURIER</DropOffType>
                <NextBusinessDay>Y</NextBusinessDay>
                <Ship>
                    <Shipper>
                        <StreetLines>River House</StreetLines>
                        <StreetLines2>1</StreetLines2>
                        <StreetLines3>1</StreetLines3>
                        <StreetName>Eas Wall road</StreetName>
                        <StreetNumber>1</StreetNumber>
                        <City>Panama</City>
                        <StateOrProvinceCode>PA</StateOrProvinceCode>
                        <PostalCode>0</PostalCode>
                        <CountryCode>PA</CountryCode>
                    </Shipper>
                    <Recipient>
                        <StreetLines>River House</StreetLines>
                        <StreetLines2>1</StreetLines2>
                        <StreetLines3>1</StreetLines3>
                        <StreetName>Eas Wall road</StreetName>
                        <StreetNumber>1</StreetNumber>
                        <City>Santa Cruz</City>
                        <PostalCode>0</PostalCode>
                        <CountryCode>BO</CountryCode>
                    </Recipient>
                </Ship>
                <Packages>"""
    
    # Agregar cada pieza con sus datos reales
    for i, piece in enumerate(piece_details):
        soap_envelope += f"""
                    <RequestedPackages number="{i+1}">
                        <Weight>
                            <Value>{piece.get('actual_weight', '45')}</Value>
                        </Weight>
                        <Dimensions>
                            <Length>{float(piece.get('actual_length', '1')) / 100}</Length>
                            <Width>{float(piece.get('actual_width', '1')) / 100}</Width>
                            <Height>{float(piece.get('actual_height', '1')) / 100}</Height>
                        </Dimensions>
                    </RequestedPackages>"""
    
    soap_envelope += f"""
                </Packages>
                <ShipTimestamp>{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}GMT+00:00</ShipTimestamp>
                <UnitOfMeasurement>SI</UnitOfMeasurement>
                <Content>NON_DOCUMENTS</Content>
                <PaymentInfo>DDU</PaymentInfo>
                <Account>706100990</Account>
            </RequestedShipment>
        </rat:RateRequest>
    </soapenv:Body>
</soapenv:Envelope>"""
    
    # Configurar headers
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': '"RateRequest"',
        'Authorization': 'Basic YXBPM2ZTNW1KOHpUN2g6Sl40b0ZAMXFXITBxUyE1Yg=='
    }
    
    print(f"📊 Cotizando con {len(piece_details)} piezas:")
    for i, piece in enumerate(piece_details):
        print(f"   Pieza {i+1}:")
        print(f"     - Peso: {piece.get('actual_weight', 'N/A')} kg")
        print(f"     - Dimensiones: {piece.get('actual_length', 'N/A')} x {piece.get('actual_width', 'N/A')} x {piece.get('actual_height', 'N/A')} cm")
        print(f"     - Peso dimensional: {piece.get('dim_weight', 'N/A')} kg")
    
    try:
        # Hacer la solicitud
        print(f"\n🌐 Enviando solicitud de cotización a DHL...")
        response = requests.post(
            'https://wsbexpress.dhl.com/sndpt/expressRateBook',
            data=soap_envelope,
            headers=headers,
            verify=False,
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Length: {len(response.text)} characters")
        
        if response.status_code == 200:
            # Parsear la respuesta XML
            root = ET.fromstring(response.text)
            
            # Buscar los elementos de cotización
            rate_quotes = []
            
            # Namespaces para DHL
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'rat': 'http://scxgxtt.phx-dc.dhl.com/euExpressRateBook/RateMsgRequest'
            }
            
            print(f"\n✅ RESPUESTA DE COTIZACIÓN:")
            print("=" * 50)
            
            # Imprimir la respuesta completa para debugging
            print(f"📋 Respuesta XML completa:")
            print(response.text[:2000] + "..." if len(response.text) > 2000 else response.text)
            
            # Buscar errores
            error_elements = root.findall('.//ErrorMessage')
            if error_elements:
                print(f"\n❌ ERRORES ENCONTRADOS:")
                for error in error_elements:
                    print(f"   - {error.text}")
            
            # Buscar cotizaciones
            services = root.findall('.//Service')
            if services:
                print(f"\n💰 COTIZACIONES ENCONTRADAS:")
                for i, service in enumerate(services):
                    service_type = service.get('type', 'N/A')
                    
                    # Obtener el precio total
                    total_net = service.find('.//TotalNet/Amount')
                    currency = service.find('.//TotalNet/Currency')
                    
                    # Obtener la fecha de entrega
                    delivery_time = service.find('.//DeliveryTime')
                    cutoff_time = service.find('.//CutoffTime')
                    
                    # Obtener el tipo de servicio principal
                    main_charge = service.find('.//Charge/ChargeType')
                    
                    print(f"   🚛 Servicio {i+1} (Tipo: {service_type}):")
                    if main_charge is not None:
                        print(f"     - Servicio: {main_charge.text}")
                    if total_net is not None and currency is not None:
                        print(f"     - Precio Total: {total_net.text} {currency.text}")
                    if delivery_time is not None:
                        print(f"     - Fecha entrega: {delivery_time.text}")
                    if cutoff_time is not None:
                        print(f"     - Fecha límite: {cutoff_time.text}")
                    
                    # Mostrar desglose de cargos
                    charges = service.findall('.//Charge')
                    if charges:
                        print(f"     - Desglose de cargos:")
                        for charge in charges:
                            charge_type = charge.find('ChargeType')
                            charge_amount = charge.find('ChargeAmount')
                            if charge_type is not None and charge_amount is not None:
                                print(f"       * {charge_type.text}: {charge_amount.text}")
                    
                    print(f"   ---")
            else:
                print("⚠️ No se encontraron cotizaciones en la respuesta")
                
        else:
            print(f"❌ Error en la solicitud: {response.status_code}")
            print(f"📄 Response: {response.text[:1000]}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {str(e)}")
    except ET.ParseError as e:
        print(f"❌ Error al parsear XML: {str(e)}")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")

def test_tracking_and_quote():
    """Prueba el tracking con el número real y luego hace cotización"""
    
    # Crear servicio DHL
    dhl_service = DHLService(
        username="apO3fS5mJ8zT7h",
        password="J^4oF@1qW!0qS!5b",
        base_url="https://wsbexpress.dhl.com:443",
        environment="production"
    )
    
    # Número de tracking del ejemplo
    tracking_number = "5339266472"
    
    print(f"🚀 Probando tracking para: {tracking_number}")
    print(f"📅 Fecha: {datetime.now()}")
    print("=" * 50)
    
    try:
        # Obtener información de tracking
        result = dhl_service.get_tracking(tracking_number)
        
        print(f"✅ Éxito: {result.get('success', False)}")
        print(f"💬 Mensaje: {result.get('message', 'N/A')}")
        
        if result.get('success'):
            # Información básica
            tracking_info = result.get('tracking_info', {})
            print("\n📦 INFORMACIÓN DEL ENVÍO:")
            print(f"   AWB: {tracking_info.get('awb_number', 'N/A')}")
            print(f"   Estado: {tracking_info.get('status', 'N/A')}")
            print(f"   Origen: {tracking_info.get('origin', 'N/A')}")
            print(f"   Destino: {tracking_info.get('destination', 'N/A')}")
            print(f"   Peso: {tracking_info.get('weight', 'N/A')}")
            print(f"   Piezas: {tracking_info.get('pieces', 'N/A')}")
            print(f"   Fecha envío: {tracking_info.get('shipment_date', 'N/A')}")
            
            # Detalles de piezas
            piece_details = result.get('piece_details', [])
            if piece_details:
                print(f"\n📦 DETALLES DE PIEZAS ({len(piece_details)} piezas):")
                for i, piece in enumerate(piece_details):
                    print(f"   Pieza {i+1}:")
                    print(f"     - Número: {piece.get('piece_number', 'N/A')}")
                    print(f"     - License Plate: {piece.get('license_plate', 'N/A')}")
                    print(f"     - Peso real: {piece.get('actual_weight', 'N/A')} {piece.get('weight_unit', 'N/A')}")
                    print(f"     - Dimensiones reales: {piece.get('actual_length', 'N/A')} x {piece.get('actual_width', 'N/A')} x {piece.get('actual_height', 'N/A')}")
                    print(f"     - Peso dimensional: {piece.get('dim_weight', 'N/A')} {piece.get('weight_unit', 'N/A')}")
                    print(f"     - Tipo: {piece.get('package_type', 'N/A')}")
            
            # Hacer cotización con los datos obtenidos
            test_rate_quote_with_tracking_data(result)
            
        else:
            print(f"\n❌ Error: {result.get('message', 'Error desconocido')}")
            
    except Exception as e:
        print(f"❌ Error al ejecutar: {str(e)}")

if __name__ == "__main__":
    test_tracking_and_quote()
