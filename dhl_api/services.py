import requests
import xml.etree.ElementTree as ET
import base64
from datetime import datetime, timedelta
import os

class DHLService:
    def __init__(self, username, password, base_url, environment="sandbox"):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.environment = environment
        
        # Configuración por entorno
        if environment == "sandbox":
            # Para sandbox, usar endpoints de prueba específicos
            self.endpoints = {
                "getePOD": "https://wsbexpress.dhl.com/gbl/getePOD",
                "rate": "https://wsbexpress.dhl.com/sndpt/expressRateBook",
                "tracking": "https://wsbexpress.dhl.com/gbl/glDHLExpressTrack",
                "shipment": "https://wsbexpress.dhl.com/sndpt/expressRateBook"
            }
            # Datos de prueba específicos del sandbox
            self.sandbox_data = {
                "account_number": "123456789",
                "test_tracking": "1234567890",
                "test_shipment_id": "2287013540",
                "test_origin": {
                    "postal_code": "12345",
                    "city": "Test City",
                    "country_code": "US"
                },
                "test_destination": {
                    "postal_code": "54321", 
                    "city": "Destination City",
                    "country_code": "US"
                },
                "test_weight": 1.5,
                "test_dimensions": {
                    "length": 10,
                    "width": 10,
                    "height": 10
                }
            }
        elif environment == "development":
            # Configuración para desarrollo local
            self.endpoints = {
                "getePOD": f"{base_url}/gbl/getePOD",
                "rate": f"{base_url}/sndpt/expressRateBook",
                "tracking": f"{base_url}/gbl/glDHLExpressTrack",
                "shipment": f"{base_url}/sndpt/expressRateBook"
            }
            self.sandbox_data = {
                "account_number": "706014493",
                "test_tracking": "5339266472",
                "test_shipment_id": "2287013540"
            }
        else:
            # URLs de producción
            self.endpoints = {
                "getePOD": f"{base_url}/gbl/getePOD",
                "rate": f"{base_url}/sndpt/expressRateBook",
                "tracking": f"{base_url}/gbl/glDHLExpressTrack",
                "shipment": f"{base_url}/sndpt/expressRateBook"
            }
            self.sandbox_data = {
                "account_number": "TU_ACCOUNT_NUMBER",
                "test_tracking": "TU_TRACKING_NUMBER",
                "test_shipment_id": "TU_SHIPMENT_ID"
            }

    def _get_headers(self, soap_action):
        """Genera headers para requests SOAP"""
        import base64
        
        # Crear header Authorization Basic para ePOD
        if "getePOD" in soap_action or "createShipmentRequest" in soap_action:
            credentials = "apO3fS5mJ8zT7h:J^4oF@1qW!0qS!5b"
            auth_header = base64.b64encode(credentials.encode()).decode()
            return {
                'Content-Type': 'text/xml',
                'SOAPAction': soap_action,
                'Authorization': f'Basic {auth_header}',
                'Cookie': 'BIGipServer~WSB~pl_wsb-express-ash.dhl.com_443=1566607772.64288.0000'
            }
        else:
            return {
                'Content-Type': 'text/xml',
                'SOAPAction': soap_action
            }

    def _get_auth_header(self, endpoint_type=None):
        """Genera header de autenticación WS-Security con credenciales específicas por endpoint"""
        # Usar credenciales específicas según el endpoint
        if endpoint_type == "getePOD":
            username = "apO3fS5mJ8zT7h"
            password = "J^4oF@1qW!0qS!5b"
        elif endpoint_type == "rate":
            username = "USCIM"
            password = "B#9pC^2fU#0d"
        elif endpoint_type == "tracking":
            username = "mydhlapicert"
            password = "X!9tA@2xU^1n"
        else:
            username = self.username
            password = self.password
            
        return f"""
        <wsse:Security SOAP-ENV:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
            <wsse:UsernameToken>
                <wsse:Username>{username}</wsse:Username>
                <wsse:Password>{password}</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
        """
    
    def _clean_text(self, text):
        """Limpia el texto para evitar problemas con caracteres especiales"""
        if not text:
            return text
        
        # Reemplazar caracteres especiales problemáticos
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ç': 'c', 'ü': 'u',
            'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
            'Ñ': 'N', 'Ç': 'C', 'Ü': 'U'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _clean_phone(self, phone):
        """Limpia el número de teléfono para DHL"""
        if not phone:
            return phone
        
        # Remover caracteres especiales excepto números, + y espacios
        import re
        cleaned = re.sub(r'[^\d\+\s\-\(\)]', '', phone)
        
        # Limitar longitud a 15 caracteres
        return cleaned[:15]

    def get_ePOD(self, shipment_id):
        """Obtiene comprobante de entrega electrónico"""
        try:
            soap_action = "euExpressRateBook_providerServices_ShipmentHandlingServices_Binder_createShipmentRequest"
            
            # Usar exactamente el mismo SOAP request que funciona
            soap_body = f"""
<SOAP-ENV:Envelope xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="glDHLExpressePOD/providers/DocumentRetrieve" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
	<SOAP-ENV:Header>
		<wsse:Security SOAP-ENV:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
			<wsse:UsernameToken>
				<wsse:Username>apO3fS5mJ8zT7h</wsse:Username>
				<wsse:Password>J^4oF@1qW!0qS!5b</wsse:Password>
			</wsse:UsernameToken>
		</wsse:Security>
	</SOAP-ENV:Header>
	<SOAP-ENV:Body>
		<tns:shipmentDocumentRetrieveReq>
			<MSG>
				<Hdr Dtm="2018-08-06T08:08:41.914+02:00" Id="1533535721914" Ver="1.038">
					<Sndr AppCd="GloWS" AppNm="GloWS"/>
				</Hdr>
				<Bd>
					<Shp Id="{shipment_id}">
						<ShpTr>
							<SCDtl AccNo="706014493" CRlTyCd="PY"/>
						</ShpTr>
						<ShpInDoc>
							<SDoc DocTyCd="POD"/>
						</ShpInDoc>
					</Shp>
					<GenrcRq>
						<GenrcRqCritr TyCd="IMG_CONTENT" Val="epod-detail"/>
						<GenrcRqCritr TyCd="IMG_FORMAT" Val="PDF"/>
						<GenrcRqCritr TyCd="DOC_RND_REQ" Val="true"/>
						<GenrcRqCritr TyCd="EXT_REQ" Val="true"/>
						<GenrcRqCritr TyCd="DUPL_HANDL" Val="CORE_WB_NO"/>
						<GenrcRqCritr TyCd="SORT_BY" Val="$INGEST_DATE,D"/>
						<GenrcRqCritr TyCd="LANGUAGE" Val="es"/>
					</GenrcRq>
				</Bd>
			</MSG>
		</tns:shipmentDocumentRetrieveReq>
	</SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
            
            response = requests.post(
                self.endpoints["getePOD"],
                headers=self._get_headers(soap_action),
                data=soap_body
            )
            
            return self._parse_response(response, "ePOD")
            
        except Exception as e:
            return {"success": False, "message": f"Error en get_ePOD: {str(e)}"}

    def get_rate(self, origin, destination, weight, dimensions):
        """Obtiene cotización de tarifas"""
        try:
            # Para desarrollo/sandbox, simular la cotización de tarifas
            if self.environment in ["sandbox", "development"]:
                # Generar tarifas simuladas basadas en el peso y distancia
                import random
                
                # Calcular distancia aproximada (simplificado)
                origin_country = origin.get('country', 'US')
                dest_country = destination.get('country', 'US')
                
                # Tarifas base por servicio
                services = {
                    'P': {'name': 'Priority', 'base_rate': 45.00, 'multiplier': 2.5},
                    'K': {'name': 'Economy', 'base_rate': 35.00, 'multiplier': 2.0},
                    'U': {'name': 'Express', 'base_rate': 55.00, 'multiplier': 3.0},
                    'Y': {'name': 'Same Day', 'base_rate': 85.00, 'multiplier': 4.0}
                }
                
                # Calcular tarifa basada en peso y distancia
                weight_factor = weight * 2.5
                distance_factor = 1.0
                
                if origin_country != dest_country:
                    distance_factor = 3.0  # Internacional
                elif origin.get('state') != destination.get('state'):
                    distance_factor = 1.5  # Nacional entre estados
                
                rates = []
                for service_code, service_info in services.items():
                    total_rate = service_info['base_rate'] + (weight_factor * service_info['multiplier'] * distance_factor)
                    # Agregar variación aleatoria
                    total_rate += random.uniform(-5, 5)
                    total_rate = round(total_rate, 2)
                    
                    # Calcular tiempo de entrega estimado
                    if service_code == 'P':
                        delivery_time = "1-2 días hábiles"
                    elif service_code == 'K':
                        delivery_time = "3-5 días hábiles"
                    elif service_code == 'U':
                        delivery_time = "1 día hábil"
                    else:
                        delivery_time = "Mismo día"
                    
                    rates.append({
                        'service_code': service_code,
                        'service_name': service_info['name'],
                        'total_charge': total_rate,
                        'currency': 'USD',
                        'delivery_time': delivery_time,
                        'weight': weight,
                        'dimensions': dimensions
                    })
                
                return {
                    "success": True,
                    "rates": rates,
                    "origin": origin,
                    "destination": destination,
                    "message": "Cotización generada exitosamente (modo sandbox)"
                }
            
            # Para producción, usar el endpoint real
            soap_action = "euExpressRateBook_providerServices_ShipmentHandlingServices_Binder_getRateRequest"
            
            soap_body = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:rat="http://scxgxtt.phx-dc.dhl.com/euExpressRateBook/RateMsgRequest">
                <soapenv:Header>
                    {self._get_auth_header(endpoint_type="rate")}
                </soapenv:Header>
                <soapenv:Body>
                    <rat:RateRequest>
                        <ClientDetail>
                            <sso>testsso</sso>
                            <plant>testplant</plant>
                        </ClientDetail>
                        <RequestedShipment>
                            <DropOffType>REGULAR_PICKUP</DropOffType>
                            <NextBusinessDay>N</NextBusinessDay>
                            <Ship>
                                <Shipper>
                                    <StreetLines>{origin.get('address', 'Test Address')}</StreetLines>
                                    <City>{origin.get('city', 'Test City')}</City>
                                    <StateOrProvinceCode>{origin.get('state', 'XX')}</StateOrProvinceCode>
                                    <PostalCode>{origin.get('postal_code', '00000')}</PostalCode>
                                    <CountryCode>{origin.get('country', 'US')}</CountryCode>
                                </Shipper>
                                <Recipient>
                                    <StreetLines>{destination.get('address', 'Test Address')}</StreetLines>
                                    <City>{destination.get('city', 'Test City')}</City>
                                    <PostalCode>{destination.get('postal_code', '00000')}</PostalCode>
                                    <CountryCode>{destination.get('country', 'US')}</CountryCode>
                                </Recipient>
                            </Ship>
                            <Packages>
                                <RequestedPackages number="1">
                                    <Weight>
                                        <Value>{weight}</Value>
                                    </Weight>
                                    <Dimensions>
                                        <Length>{dimensions.get('length', 10)}</Length>
                                        <Width>{dimensions.get('width', 10)}</Width>
                                        <Height>{dimensions.get('height', 10)}</Height>
                                    </Dimensions>
                                </RequestedPackages>
                            </Packages>
                            <ShipTimestamp>{datetime.now().strftime('%Y-%m-%dT%H:%M:%SGMT+00:00')}</ShipTimestamp>
                            <UnitOfMeasurement>SU</UnitOfMeasurement>
                            <Content>NON_DOCUMENTS</Content>
                            <PaymentInfo>DDU</PaymentInfo>
                            <Account>803921577</Account>
                        </RequestedShipment>
                    </rat:RateRequest>
                </soapenv:Body>
            </soapenv:Envelope>
            """
            
            response = requests.post(
                self.endpoints["rate"],
                headers=self._get_headers(soap_action),
                data=soap_body
            )
            
            return self._parse_response(response, "Rate")
            
        except Exception as e:
            return {"success": False, "message": f"Error en get_rate: {str(e)}"}

    def get_tracking(self, tracking_number):
        """Obtiene información de seguimiento"""
        try:
            # Para desarrollo/sandbox, simular el seguimiento
            if self.environment in ["sandbox", "development"]:
                import random
                
                # Generar eventos de seguimiento simulados
                events = []
                current_time = datetime.now()
                
                # Eventos típicos de DHL
                event_types = [
                    {
                        "code": "PU",
                        "description": "Picked up by DHL",
                        "location": "Madrid, Spain",
                        "timestamp": current_time - timedelta(days=2, hours=3)
                    },
                    {
                        "code": "TR",
                        "description": "In transit to destination",
                        "location": "Madrid, Spain",
                        "timestamp": current_time - timedelta(days=2, hours=1)
                    },
                    {
                        "code": "AR",
                        "description": "Arrived at destination facility",
                        "location": "New York, USA",
                        "timestamp": current_time - timedelta(days=1, hours=6)
                    },
                    {
                        "code": "OFD",
                        "description": "Out for delivery",
                        "location": "New York, USA",
                        "timestamp": current_time - timedelta(hours=2)
                    }
                ]
                
                # Agregar evento de entrega si el envío está "completado"
                if random.choice([True, False]):
                    events.append({
                        "code": "DL",
                        "description": "Delivered",
                        "location": "New York, USA",
                        "timestamp": current_time - timedelta(hours=1)
                    })
                    status = "Delivered"
                else:
                    status = "In Transit"
                
                # Agregar eventos en orden cronológico
                for event in event_types:
                    events.append(event)
                
                # Ordenar por timestamp
                events.sort(key=lambda x: x["timestamp"])
                
                # Información del envío
                shipment_info = {
                    "awb_number": tracking_number,
                    "status": status,
                    "service": "DHL Express Worldwide",
                    "origin": "Madrid, Spain",
                    "destination": "New York, USA",
                    "estimated_delivery": (current_time + timedelta(days=1)).strftime("%Y-%m-%d"),
                    "weight": "2.5 kg",
                    "pieces": "1"
                }
                
                return {
                    "success": True,
                    "tracking_info": shipment_info,
                    "events": events,
                    "message": "Información de seguimiento obtenida (modo sandbox)"
                }
            
            # Para producción, usar el endpoint real
            soap_action = "glDHLExpressTrack_providers_services_trackShipment_Binder_trackShipmentRequest"
            
            soap_body = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:trac="http://scxgxtt.phx-dc.dhl.com/glDHLExpressTrack/providers/services/trackShipment" xmlns:dhl="http://www.dhl.com">
                <soapenv:Header>
                    {self._get_auth_header(endpoint_type="tracking")}
                </soapenv:Header>
                <soapenv:Body>
                    <trac:trackShipmentRequest>
                        <trackingRequest>
                            <dhl:TrackingRequest>
                                <Request>
                                    <ServiceHeader>
                                        <MessageTime>{datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3]}Z</MessageTime>
                                        <MessageReference>123456789123456789123456789123</MessageReference>
                                    </ServiceHeader>
                                </Request>
                                <AWBNumber>
                                    <ArrayOfAWBNumberItem>{tracking_number}</ArrayOfAWBNumberItem>
                                </AWBNumber>
                                <LevelOfDetails>ALL_CHECK_POINTS</LevelOfDetails>
                                <PiecesEnabled>B</PiecesEnabled>
                            </dhl:TrackingRequest>
                        </trackingRequest>
                    </trac:trackShipmentRequest>
                </soapenv:Body>
            </soapenv:Envelope>
            """
            
            response = requests.post(
                self.endpoints["tracking"],
                headers=self._get_headers(soap_action),
                data=soap_body
            )
            
            return self._parse_response(response, "Tracking")
            
        except Exception as e:
            return {"success": False, "message": f"Error en get_tracking: {str(e)}"}

    def create_shipment(self, shipment_data):
        """Crea un nuevo envío"""
        try:
            # Para desarrollo/sandbox, simular la creación de envío
            if self.environment in ["sandbox", "development"]:
                # Generar un número de tracking simulado
                import random
                tracking_number = f"{random.randint(1000000000, 9999999999)}"
                
                return {
                    "success": True,
                    "tracking_number": tracking_number,
                    "message": "Envío creado exitosamente (modo sandbox)",
                    "shipment_data": {
                        "shipper": shipment_data.get('shipper', {}),
                        "recipient": shipment_data.get('recipient', {}),
                        "package": shipment_data.get('package', {}),
                        "service": shipment_data.get('service', 'P'),
                        "payment": shipment_data.get('payment', 'S')
                    },
                    "estimated_delivery": "3-5 días hábiles",
                    "cost": "Calculado según tarifas DHL"
                }
            
            # Para producción, usar el endpoint real
            soap_action = "euExpressRateBook_providerServices_ShipmentHandlingServices_Binder_createShipmentRequest"
            
            # Extraer datos del formulario
            shipper = shipment_data.get('shipper', {})
            recipient = shipment_data.get('recipient', {})
            package = shipment_data.get('package', {})
            service_type = shipment_data.get('service', 'P')
            payment_type = shipment_data.get('payment', 'S')
            
            # Fecha futura para evitar errores - formato correcto para DHL
            future_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.000+00:00')
            
            soap_body = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ship="http://scxgxtt.phx-dc.dhl.com/euExpressRateBook/ShipmentMsgRequest">
                <soapenv:Header>
                    {self._get_auth_header()}
                </soapenv:Header>
                <soapenv:Body>
                    <ship:ShipmentRequest>
                        <Request>
                            <ServiceHeader>
                                <MessageTime>{datetime.now().strftime('%Y-%m-%dT%H:%M:%S-05:00')}</MessageTime>
                                <MessageReference>SHIP{int(datetime.now().timestamp())}</MessageReference>
                                <WebstorePlatform>DHL_API_CLIENT</WebstorePlatform>
                                <WebstorePlatformVersion>1.0</WebstorePlatformVersion>
                                <ShippingSystemPlatform>DHL_EXPRESS</ShippingSystemPlatform>
                                <ShippingSystemPlatformVersion>1.0</ShippingSystemPlatformVersion>
                                <PlugIn>FLASK_API</PlugIn>
                                <PlugInVersion>1.0</PlugInVersion>
                            </ServiceHeader>
                        </Request>
                        <RequestedShipment>
                            <ShipmentInfo>
                                <DropOffType>REGULAR_PICKUP</DropOffType>
                                <ServiceType>{service_type}</ServiceType>
                                <Billing>
                                    <ShipperAccountNumber>706014493</ShipperAccountNumber>
                                    <ShippingPaymentType>{payment_type}</ShippingPaymentType>
                                    <DutyAndTaxPayerAccountNumber>706014493</DutyAndTaxPayerAccountNumber>
                                </Billing>
                                <Currency>{package.get('currency', 'USD')}</Currency>
                                <UnitOfMeasurement>SU</UnitOfMeasurement>
                                <LabelType>PDF</LabelType>
                                <LabelTemplate>ECOM26_84_001</LabelTemplate>
                                <ArchiveLabelTemplate>ARCH_8x4</ArchiveLabelTemplate>
                            </ShipmentInfo>
                            <ShipTimestamp>{future_date}</ShipTimestamp>
                            <PaymentInfo>DDP</PaymentInfo>
                            <InternationalDetail>
                                <Commodities>
                                    <Description>{self._clean_text(package.get('description', 'General Merchandise'))}</Description>
                                    <CustomsValue>{package.get('value', 100)}</CustomsValue>
                                </Commodities>
                                <Content>NON_DOCUMENTS</Content>
                            </InternationalDetail>
                            <Ship>
                                <Shipper>
                                    <Contact>
                                        <PersonName>{self._clean_text(shipper.get('name', 'Test Shipper'))}</PersonName>
                                        <CompanyName>{self._clean_text(shipper.get('company', 'Company Name'))}</CompanyName>
                                        <PhoneNumber>{self._clean_phone(shipper.get('phone', '1234567890'))}</PhoneNumber>
                                        <EmailAddress>{shipper.get('email', 'test@example.com')}</EmailAddress>
                                    </Contact>
                                    <Address>
                                        <StreetLines>{self._clean_text(shipper.get('address', '123 Test Street'))}</StreetLines>
                                        <City>{self._clean_text(shipper.get('city', 'Test City'))}</City>
                                        <StateOrProvinceCode>{self._clean_text(shipper.get('state', 'XX'))}</StateOrProvinceCode>
                                        <PostalCode>{shipper.get('postalCode', '12345')}</PostalCode>
                                        <CountryCode>{shipper.get('country', 'US')}</CountryCode>
                                    </Address>
                                </Shipper>
                                <Recipient>
                                    <Contact>
                                        <PersonName>{self._clean_text(recipient.get('name', 'Test Recipient'))}</PersonName>
                                        <CompanyName>{self._clean_text(recipient.get('company', 'Company Name'))}</CompanyName>
                                        <PhoneNumber>{self._clean_phone(recipient.get('phone', '1234567890'))}</PhoneNumber>
                                        <EmailAddress>{recipient.get('email', 'test@example.com')}</EmailAddress>
                                    </Contact>
                                    <Address>
                                        <StreetLines>{self._clean_text(recipient.get('address', '456 Test Street'))}</StreetLines>
                                        <City>{self._clean_text(recipient.get('city', 'Test City'))}</City>
                                        <StateOrProvinceCode>{self._clean_text(recipient.get('state', 'XX'))}</StateOrProvinceCode>
                                        <PostalCode>{recipient.get('postalCode', '54321')}</PostalCode>
                                        <CountryCode>{recipient.get('country', 'US')}</CountryCode>
                                    </Address>
                                </Recipient>
                            </Ship>
                            <Packages>
                                <RequestedPackages number="1">
                                    <Weight>{package.get('weight', 1.0)}</Weight>
                                    <Dimensions>
                                        <Length>{package.get('length', 10)}</Length>
                                        <Width>{package.get('width', 10)}</Width>
                                        <Height>{package.get('height', 10)}</Height>
                                    </Dimensions>
                                    <CustomerReferences>SHIP{int(datetime.now().timestamp())}</CustomerReferences>
                                    <CustomerReferenceType>SH</CustomerReferenceType>
                                </RequestedPackages>
                            </Packages>
                        </RequestedShipment>
                    </ship:ShipmentRequest>
                </soapenv:Body>
            </soapenv:Envelope>
            """
            
            response = requests.post(
                self.endpoints["shipment"],
                headers=self._get_headers(soap_action),
                data=soap_body
            )
            
            return self._parse_response(response, "Shipment")
            
        except Exception as e:
            return {"success": False, "message": f"Error en create_shipment: {str(e)}"}

    def _parse_response(self, response, service_type):
        """Parsea la respuesta XML de DHL"""
        try:
            if response.status_code == 200:
                # Parsear XML
                root = ET.fromstring(response.text)
                
                # Buscar elementos específicos según el tipo de servicio
                if service_type == "ePOD":
                    # Buscar datos PDF en la respuesta usando múltiples enfoques
                    pdf_data = None
                    
                    # Método 1: Usar namespace-aware search
                    for elem in root.iter():
                        if elem.tag.endswith('Img') and elem.get('Img'):
                            pdf_data = elem.get('Img')
                            break
                    
                    # Método 2: Si no se encontró, buscar directamente en el texto
                    if not pdf_data and 'Img="' in response.text:
                        import re
                        match = re.search(r'Img="([^"]+)"', response.text)
                        if match:
                            pdf_data = match.group(1)
                    
                    if pdf_data:
                        return {
                            "success": True,
                            "pdf_data": pdf_data,
                            "message": "PDF obtenido exitosamente"
                        }
                    else:
                        return {
                            "success": False,
                            "message": "No se encontró PDF en la respuesta",
                            "raw_response": response.text[:1000]  # Primeros 1000 chars para debug
                        }
                
                elif service_type == "Rate":
                    # Buscar tarifas en la respuesta
                    rates = []
                    rate_elements = root.findall(".//Rate")
                    for rate in rate_elements:
                        service_name_elem = rate.find("ServiceName")
                        total_net_elem = rate.find("TotalNet")
                        currency_elem = rate.find("CurrencyCode")
                        delivery_time_elem = rate.find("DeliveryTime")
                        
                        rates.append({
                            "service": service_name_elem.text if service_name_elem is not None else "Unknown",
                            "price": total_net_elem.text if total_net_elem is not None else "0",
                            "currency": currency_elem.text if currency_elem is not None else "USD",
                            "delivery_time": delivery_time_elem.text if delivery_time_elem is not None else "Unknown"
                        })
                    
                    return {
                        "success": True,
                        "rates": rates,
                        "message": f"Se encontraron {len(rates)} tarifas disponibles"
                    }
                
                elif service_type == "Tracking":
                    # Buscar información de seguimiento
                    events = []
                    event_elements = root.findall(".//ArrayOfShipmentEventItem")
                    for event in event_elements:
                        date_elem = event.find("Date")
                        time_elem = event.find("Time")
                        desc_elem = event.find(".//Description")
                        
                        events.append({
                            "date": date_elem.text if date_elem is not None else "",
                            "time": time_elem.text if time_elem is not None else "",
                            "location": desc_elem.text if desc_elem is not None else "",
                            "description": desc_elem.text if desc_elem is not None else ""
                        })
                    
                    awb_elem = root.find(".//AWBNumber")
                    return {
                        "success": True,
                        "tracking": {
                            "tracking_number": awb_elem.text if awb_elem is not None else "",
                            "status": "Delivered" if events else "In Transit",
                            "events": events
                        },
                        "message": "Información de seguimiento obtenida"
                    }
                
                elif service_type == "Shipment":
                    # Buscar número de tracking en la respuesta
                    tracking_number = root.find(".//AWBNumber")
                    if tracking_number is not None:
                        return {
                            "success": True,
                            "tracking_number": tracking_number.text,
                            "message": "Envío creado exitosamente"
                        }
                    else:
                        return {
                            "success": False,
                            "message": "No se pudo obtener el número de tracking"
                        }
                
                else:
                    return {
                        "success": True,
                        "raw_response": response.text,
                        "message": "Respuesta procesada"
                    }
            
            else:
                return {
                    "success": False,
                    "message": f"Error HTTP {response.status_code}: {response.text}"
                }
                
        except ET.ParseError as e:
            return {
                "success": False,
                "message": f"Error parseando XML: {str(e)}",
                "raw_response": response.text
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error procesando respuesta: {str(e)}",
                "raw_response": response.text
            }
