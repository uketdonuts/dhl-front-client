import requests
import xml.etree.ElementTree as ET
import base64
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)

class DHLService:
    def __init__(self, username, password, base_url, environment="production"):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.environment = environment
        
        logger.info(f"Initializing DHLService with environment: {environment}")
        logger.info(f"Base URL: {base_url}")
        
        # Configuración por entorno
        if environment == "sandbox":
            # Para sandbox, usar endpoints de prueba específicos
            self.endpoints = {
                "getePOD": "https://wsbexpress.dhl.com:443/gbl/getePOD",
                "rate": "https://wsbexpress.dhl.com:443/sndpt/expressRateBook",
                "tracking": "https://wsbexpress.dhl.com:443/gbl/glDHLExpressTrack",
                "shipment": "https://wsbexpress.dhl.com:443/sndpt/expressRateBook"
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
            # URLs de producción - usar endpoints exactos que funcionan
            self.endpoints = {
                "getePOD": "https://wsbexpress.dhl.com:443/gbl/getePOD",
                "rate": "https://wsbexpress.dhl.com:443/sndpt/expressRateBook",
                "tracking": "https://wsbexpress.dhl.com:443/gbl/glDHLExpressTrack",
                "shipment": "https://wsbexpress.dhl.com:443/sndpt/expressRateBook"
            }
            self.sandbox_data = {
                "account_number": "706065602",  # Usar el número real
                "test_tracking": "TU_TRACKING_NUMBER",
                "test_shipment_id": "TU_SHIPMENT_ID"
            }
        
        logger.info(f"Endpoints configured: {self.endpoints}")

    def _get_headers(self, soap_action):
        """Genera headers para requests SOAP"""
        import base64
        
        # Crear header Authorization Basic para todas las peticiones
        credentials = "apO3fS5mJ8zT7h:J^4oF@1qW!0qS!5b"
        auth_header = base64.b64encode(credentials.encode()).decode()
        
        # Headers base que se usan en todas las peticiones
        headers = {
            'Content-Type': 'text/xml',
            'Authorization': f'Basic {auth_header}'
        }
        
        # Agregar SOAPAction si se proporciona
        if soap_action:
            headers['SOAPAction'] = soap_action
        
        # Agregar Cookie para ePOD
        if "getePOD" in soap_action or "createShipmentRequest" in soap_action:
            headers['Cookie'] = 'BIGipServer~WSB~pl_wsb-express-ash.dhl.com_443=1566607772.64288.0000'
        
        return headers

    def _get_auth_header(self, endpoint_type=None):
        """Genera header de autenticación WS-Security con credenciales específicas por endpoint"""
        # Usar las credenciales reales del ejemplo que funciona
        username = "apO3fS5mJ8zT7h"
        password = "J^4oF@1qW!0qS!5b"
            
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
        """Obtiene información de seguimiento con validación mejorada"""
        try:
            logger.info(f"Starting tracking request for {tracking_number}")
            logger.info(f"Environment: {self.environment}")
            logger.info(f"Endpoint: {self.endpoints['tracking']}")
            
            # Validar formato del número de tracking
            if not tracking_number or not str(tracking_number).strip():
                logger.error("Empty tracking number")
                return {"success": False, "message": "Número de tracking requerido"}
            
            # Limpiar el número de tracking
            tracking_number = str(tracking_number).strip()
            
            # Validar que sea numérico y tenga al menos 9 dígitos
            if not tracking_number.isdigit() or len(tracking_number) < 9:
                logger.error(f"Invalid tracking number format: {tracking_number}")
                return {"success": False, "message": "Número de tracking inválido. Debe contener al menos 9 dígitos numéricos"}
            
            # Usar el formato exacto del ejemplo que funciona
            soap_body = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:trac="http://scxgxtt.phx-dc.dhl.com/glDHLExpressTrack/providers/services/trackShipment" xmlns:dhl="http://www.dhl.com">
    <soapenv:Header>
        <wsse:Security soapenv:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
            <wsse:UsernameToken>
                <wsse:Username>{self.username}</wsse:Username>
                <wsse:Password>{self.password}</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </soapenv:Header>
    <soapenv:Body>
        <trac:trackShipmentRequest>
            <trackingRequest>
                <dhl:TrackingRequest>
                    <Request>
                        <ServiceHeader>
                            <MessageTime>2014-07-01T13:39:57.938Z</MessageTime>
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
</soapenv:Envelope>"""
            
            # Obtener headers
            headers = self._get_headers("")
            logger.debug(f"Request Headers: {headers}")
            logger.debug(f"Request Body: {soap_body}")
            
            # Hacer la petición a DHL
            logger.info("Making request to DHL API...")
            response = requests.post(
                self.endpoints["tracking"],
                headers=headers,
                data=soap_body,
                verify=False
            )
            
            # Log de la respuesta para debugging
            logger.info(f"Response Status: {response.status_code}")
            logger.debug(f"Response Headers: {dict(response.headers)}")
            logger.debug(f"Response Content Length: {len(response.text)}")
            logger.debug(f"Response Content: {response.text}")
            
            # Verificar si la respuesta es válida
            if response.status_code != 200:
                logger.error(f"HTTP Error: {response.status_code}")
                return self._handle_http_error(response)
            
            # Parsear la respuesta
            try:
                root = ET.fromstring(response.content)
                logger.info(f"XML Root Tag: {root.tag}")
                result = self._parse_tracking_response(root, response.text)
                logger.info(f"Parse Result: {result}")
                return result
            except ET.ParseError as e:
                logger.error(f"XML Parse Error: {str(e)}")
                return {
                    "success": False,
                    "message": f"Error parseando XML de DHL: {str(e)}",
                    "raw_response": response.text[:500]
                }
            
        except Exception as e:
            logger.exception(f"Error in get_tracking for {tracking_number}")
            return {"success": False, "message": f"Error en get_tracking: {str(e)}"}

    def create_shipment(self, shipment_data):
        """Crea un nuevo envío usando el formato exacto que funciona"""
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
            
            # Para producción, usar el endpoint real con formato exacto del ejemplo
            soap_action = "euExpressRateBook_providerServices_ShipmentHandlingServices_Binder_createShipmentRequest"
            # Extraer datos del formulario
            shipper = shipment_data.get('shipper', {})
            recipient = shipment_data.get('recipient', {})
            package = shipment_data.get('package', {})
            packages = shipment_data.get('packages', [])  # Support multiple packages
            service_type = shipment_data.get('service', 'P')
            payment_type = shipment_data.get('payment', 'S')
            account_number = shipment_data.get('account_number', '706065602')  # Usar la cuenta seleccionada o default
            # Generar MessageReference único
            message_ref = f"JCAIN{int(datetime.now().timestamp())}"
            # Usar formato exacto del ejemplo que funciona
            soap_body = f"""<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:ship=\"http://scxgxtt.phx-dc.dhl.com/euExpressRateBook/ShipmentMsgRequest\">
   <soapenv:Header>
      <wsse:Security soapenv:mustUnderstand=\"1\" xmlns:wsse=\"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd\">
         <wsse:UsernameToken>
            <wsse:Username>apO3fS5mJ8zT7h</wsse:Username>
            <wsse:Password>J^4oF@1qW!0qS!5b</wsse:Password>
         </wsse:UsernameToken>
      </wsse:Security>
   </soapenv:Header>
   <soapenv:Body>
      <ship:ShipmentRequest>
         <Request>
            <ServiceHeader>
               <MessageTime>{datetime.now().strftime('%Y-%m-%dT%H:%M:%S-05:00')}</MessageTime>
               <MessageReference>{message_ref}</MessageReference>
               <WebstorePlatform>3PV</WebstorePlatform>
               <WebstorePlatformVersion>10.0</WebstorePlatformVersion>
               <ShippingSystemPlatform>Platform</ShippingSystemPlatform>
               <ShippingSystemPlatformVersion>5</ShippingSystemPlatformVersion>
               <PlugIn>plugin</PlugIn>
               <PlugInVersion>4</PlugInVersion>
            </ServiceHeader>
         </Request>
         <RequestedShipment>
            <ShipmentInfo>
               <DropOffType>REGULAR_PICKUP</DropOffType>
               <ServiceType>{service_type}</ServiceType>
               <Billing>
                  <ShipperAccountNumber>{account_number}</ShipperAccountNumber>
                  <ShippingPaymentType>{payment_type}</ShippingPaymentType>
                  <DutyAndTaxPayerAccountNumber>{account_number}</DutyAndTaxPayerAccountNumber>
               </Billing>
               <SpecialServices>
                  <Service>
                     <ServiceType>DD</ServiceType>
                  </Service>
               </SpecialServices>
               <Currency>{package.get('currency', 'USD')}</Currency>
               <UnitOfMeasurement>SU</UnitOfMeasurement>
               <LabelType>ZPL</LabelType>
               <LabelTemplate>ECOM26_84_001</LabelTemplate>
               <ArchiveLabelTemplate>ARCH_8x4</ArchiveLabelTemplate>
            </ShipmentInfo>
            <ShipTimestamp>{self._get_valid_ship_timestamp()}</ShipTimestamp>
            <PickupLocationCloseTime>18:00</PickupLocationCloseTime>
            <SpecialPickupInstruction>I DECLARE ALL INFORMATION TRUE And CORRECT</SpecialPickupInstruction>
            <PickupLocation>{self._clean_text(shipper.get('address', 'Test Location'))}</PickupLocation>
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
                     <CompanyName>{self._clean_text(shipper.get('company', 'Test Company'))}</CompanyName>
                     <PhoneNumber>{self._clean_phone(shipper.get('phone', '507431-2600'))}</PhoneNumber>
                     <EmailAddress>{shipper.get('email', 'shipper_test@dhl.com')}</EmailAddress>
                     <MobilePhoneNumber>{self._clean_phone(shipper.get('phone', '507431-2600'))}</MobilePhoneNumber>
                  </Contact>
                  <Address>
                     <StreetLines>{self._clean_text(shipper.get('address', 'Test Address'))}</StreetLines>
                     <StreetName>{self._clean_text(shipper.get('address', 'Test Street'))}</StreetName>
                     <StreetNumber>{self._clean_text(shipper.get('address2', 'Building 1'))}</StreetNumber>
                     <StreetLines2>.</StreetLines2>
                     <StreetLines3>{self._clean_text(shipper.get('address3', 'Floor 1'))}</StreetLines3>
                     <City>{self._clean_text(shipper.get('city', 'Test City'))}</City>
                     <StateOrProvinceCode>{self._clean_text(shipper.get('state', 'XX'))}</StateOrProvinceCode>
                     <PostalCode>{shipper.get('postalCode', '0')}</PostalCode>
                     <CountryCode>{shipper.get('country', 'US')}</CountryCode>
                  </Address>
               </Shipper>
               <Recipient>
                  <Contact>
                     <PersonName>{self._clean_text(recipient.get('name', 'Test Recipient'))}</PersonName>
                     <CompanyName>{self._clean_text(recipient.get('company', 'Test Company'))}</CompanyName>
                     <PhoneNumber>{self._clean_phone(recipient.get('phone', '1234567890'))}</PhoneNumber>
                     <EmailAddress>{recipient.get('email', 'recipient_test@example.com')}</EmailAddress>
                     <MobilePhoneNumber>{self._clean_phone(recipient.get('phone', '1234567890'))}</MobilePhoneNumber>
                  </Contact>
                  <Address>
                     <StreetLines>{self._clean_text(recipient.get('address', 'Test Address'))}</StreetLines>
                     <StreetName>{self._clean_text(recipient.get('address', 'Test Street'))}</StreetName>
                     <StreetLines2>{self._clean_text(recipient.get('address2', 'Apt 1'))}</StreetLines2>
                     <City>{self._clean_text(recipient.get('city', 'Test City'))}</City>
                     <PostalCode>{recipient.get('postalCode', '0')}</PostalCode>
                     <CountryCode>{recipient.get('country', 'US')}</CountryCode>
                  </Address>
                  <RegistrationNumbers>
                     <RegistrationNumber>
                        <Number>{recipient.get('vat', '123456789')}</Number>
                        <NumberTypeCode>VAT</NumberTypeCode>
                        <NumberIssuerCountryCode>{recipient.get('country', 'US')}</NumberIssuerCountryCode>
                     </RegistrationNumber>
                  </RegistrationNumbers>
               </Recipient>
            </Ship>
            <Packages>{self._generate_packages_xml(packages if packages else [package], message_ref)}
            </Packages>
         </RequestedShipment>
      </ship:ShipmentRequest>
   </soapenv:Body>
</soapenv:Envelope>"""
            # Usar la URL exacta del ejemplo
            endpoint_url = "https://wsbexpress.dhl.com:443/sndpt/expressRateBook"
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': soap_action
            }
            response = requests.post(
                endpoint_url,
                headers=headers,
                data=soap_body
            )
            return self._parse_response(response, "Shipment")
        except Exception as e:
            return {"success": False, "message": f"Error en create_shipment: {str(e)}"}

    def validate_account(self, account_number):
        """
        Valida si una cuenta DHL existe y está activa
        
        Args:
            account_number (str): Número de cuenta DHL a validar
            
        Returns:
            bool: True si la cuenta es válida, False en caso contrario
        """
        try:
            # Construir el XML para validar la cuenta
            xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
            <soapenv:Envelope 
                xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                xmlns:ship="http://scxgxtt.phx-dc.dhl.com/euExpressRateBook/ShipmentMsgRequest">
                <soapenv:Header>
                    <wsse:Security soapenv:mustUnderstand="1" 
                        xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
                        <wsse:UsernameToken>
                            <wsse:Username>{self.username}</wsse:Username>
                            <wsse:Password>{self.password}</wsse:Password>
                        </wsse:UsernameToken>
                    </wsse:Security>
                </soapenv:Header>
                <soapenv:Body>
                    <ship:ShipmentRequest>
                        <Request>
                            <ServiceHeader>
                                <MessageTime>{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}</MessageTime>
                                <MessageReference>VALIDATE_ACCOUNT_{account_number}</MessageReference>
                            </ServiceHeader>
                        </Request>
                        <RequestedShipment>
                            <ShipmentInfo>
                                <DropOffType>REGULAR_PICKUP</DropOffType>
                                <ServiceType>P</ServiceType>
                                <Billing>
                                    <ShipperAccountNumber>{account_number}</ShipperAccountNumber>
                                    <ShippingPaymentType>S</ShippingPaymentType>
                                </Billing>
                            </ShipmentInfo>
                        </RequestedShipment>
                    </ship:ShipmentRequest>
                </soapenv:Body>
            </soapenv:Envelope>"""
            
            # Hacer la petición a DHL
            response = requests.post(
                self.base_url,
                data=xml_request,
                headers={'Content-Type': 'text/xml'},
                verify=False
            )
            
            # Parsear la respuesta
            root = ET.fromstring(response.content)
            
            # Buscar errores específicos de cuenta inválida
            notification_elements = root.findall('.//*[contains(local-name(), "Notification")]')
            for notification in notification_elements:
                code = notification.get('code')
                if code in ['1001', '1002', '1003']:  # Códigos de error relacionados con cuentas
                    return False
            
            return True
            
        except Exception as e:
            # Assuming 'logger' is defined elsewhere or will be added.
            # For now, just print the error.
            print(f"Error validando cuenta DHL {account_number}: {str(e)}")
            return False

    def _parse_response(self, response, service_type):
        """Parsea la respuesta XML de DHL con manejo mejorado"""
        try:
            if response.status_code == 200:
                # Parsear XML
                root = ET.fromstring(response.text)
                
                # Verificar si es un fault response
                if self._is_fault_response(root):
                    return self._parse_fault_response(root)
                
                # Buscar elementos específicos según el tipo de servicio
                if service_type == "ePOD":
                    return self._parse_epod_response(root, response.text)
                elif service_type == "Rate":
                    return self._parse_rate_response(root, response.text)
                elif service_type == "Tracking":
                    return self._parse_tracking_response(root, response.text)
                elif service_type == "Shipment":
                    return self._parse_shipment_response(root, response.text)
                else:
                    return {
                        "success": True,
                        "raw_response": response.text,
                        "message": "Respuesta procesada"
                    }
            
            else:
                return self._handle_http_error(response)
                
        except ET.ParseError as e:
            return {
                "success": False,
                "error_type": "xml_parse_error",
                "message": f"Error parseando XML: {str(e)}",
                "raw_response": response.text[:500]
            }
        except Exception as e:
            return {
                "success": False,
                "error_type": "unknown_error",
                "message": f"Error procesando respuesta: {str(e)}",
                "raw_response": response.text[:500]
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
    
    def _parse_epod_response(self, root, response_text):
        """Parser mejorado para respuestas ePOD"""
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
            import re
            pdf_match = re.search(r'Img="([^"]*JVBERi[^"]*)"', response_text)
            if pdf_match:
                pdf_data = pdf_match.group(1)
        
        if pdf_data:
            # Validar que sea base64 válido
            try:
                import base64
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
                
    def _parse_rate_response(self, root, response_text):
        """Parser mejorado para respuestas de cotización"""
        rates = []
        
        # Buscar servicios usando múltiples estrategias
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
                            try:
                                rate['total_charge'] = float(net_child.text) if net_child.text else 0
                            except ValueError:
                                rate['total_charge'] = 0
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

    def _parse_tracking_response(self, root, response_text):
        """Parser para la respuesta real de DHL tracking basado en la estructura XML proporcionada"""
        try:
            logger.info(f"Parsing tracking response with root tag: {root.tag}")
            
            # Buscar información básica del envío
            shipment_info = {}
            events = []
            
            # Buscar AWB Number en la estructura real de DHL
            awb_elements = root.findall('.//AWBNumber')
            if awb_elements:
                shipment_info['awb_number'] = awb_elements[0].text
                shipment_info['tracking_number'] = awb_elements[0].text
                logger.info(f"Found AWB Number: {awb_elements[0].text}")
            
            # Buscar estado del envío
            status_elements = root.findall('.//Status')
            for status_elem in status_elements:
                action_status = status_elem.find('.//ActionStatus')
                if action_status is not None and action_status.text:
                    shipment_info['status'] = action_status.text
                    logger.info(f"Found Status: {action_status.text}")
                    break
            
            # Buscar información del envío
            shipment_info_elem = root.find('.//ShipmentInfo')
            if shipment_info_elem is not None:
                # Origen
                origin_elem = shipment_info_elem.find('.//OriginServiceArea')
                if origin_elem is not None:
                    description = origin_elem.find('.//Description')
                    if description is not None and description.text:
                        shipment_info['origin'] = description.text
                        logger.info(f"Found Origin: {description.text}")
                
                # Destino
                dest_elem = shipment_info_elem.find('.//DestinationServiceArea')
                if dest_elem is not None:
                    description = dest_elem.find('.//Description')
                    if description is not None and description.text:
                        shipment_info['destination'] = description.text
                        logger.info(f"Found Destination: {description.text}")
                
                # Peso
                weight_elem = shipment_info_elem.find('.//Weight')
                if weight_elem is not None and weight_elem.text:
                    weight_unit = shipment_info_elem.find('.//WeightUnit')
                    unit = weight_unit.text if weight_unit is not None else 'K'
                    shipment_info['weight'] = f"{weight_elem.text} {unit}"
                    logger.info(f"Found Weight: {weight_elem.text} {unit}")
                
                # Piezas
                pieces_elem = shipment_info_elem.find('.//Pieces')
                if pieces_elem is not None and pieces_elem.text:
                    shipment_info['pieces'] = int(pieces_elem.text)
                    logger.info(f"Found Pieces: {pieces_elem.text}")
                
                # Fecha de envío
                shipment_date = shipment_info_elem.find('.//ShipmentDate')
                if shipment_date is not None and shipment_date.text:
                    shipment_info['shipment_date'] = shipment_date.text
                    logger.info(f"Found Shipment Date: {shipment_date.text}")
            
            # Buscar detalles de piezas individuales
            piece_details = []
            piece_info_items = root.findall('.//PieceInfo/ArrayOfPieceInfoItem')
            if piece_info_items:
                logger.info(f"Found {len(piece_info_items)} piece info items")
                for piece_item in piece_info_items:
                    piece_detail = {}
                    
                    # Detalles básicos de la pieza
                    piece_details_elem = piece_item.find('.//PieceDetails')
                    if piece_details_elem is not None:
                        # Número de pieza
                        piece_num = piece_details_elem.find('.//PieceNumber')
                        if piece_num is not None and piece_num.text:
                            piece_detail['piece_number'] = piece_num.text
                        
                        # License Plate
                        license_plate = piece_details_elem.find('.//LicensePlate')
                        if license_plate is not None and license_plate.text:
                            piece_detail['license_plate'] = license_plate.text
                        
                        # Dimensiones reales
                        actual_depth = piece_details_elem.find('.//ActualDepth')
                        actual_width = piece_details_elem.find('.//ActualWidth')
                        actual_height = piece_details_elem.find('.//ActualHeight')
                        if actual_depth is not None and actual_depth.text:
                            piece_detail['actual_depth'] = actual_depth.text
                        if actual_width is not None and actual_width.text:
                            piece_detail['actual_width'] = actual_width.text
                        if actual_height is not None and actual_height.text:
                            piece_detail['actual_height'] = actual_height.text
                        
                        # Peso real
                        actual_weight = piece_details_elem.find('.//ActualWeight')
                        if actual_weight is not None and actual_weight.text:
                            piece_detail['actual_weight'] = actual_weight.text
                        
                        # Dimensiones declaradas
                        depth = piece_details_elem.find('.//Depth')
                        width = piece_details_elem.find('.//Width')
                        height = piece_details_elem.find('.//Height')
                        if depth is not None and depth.text:
                            piece_detail['declared_depth'] = depth.text
                        if width is not None and width.text:
                            piece_detail['declared_width'] = width.text
                        if height is not None and height.text:
                            piece_detail['declared_height'] = height.text
                        
                        # Peso declarado
                        weight = piece_details_elem.find('.//Weight')
                        if weight is not None and weight.text:
                            piece_detail['declared_weight'] = weight.text
                        
                        # Tipo de paquete
                        package_type = piece_details_elem.find('.//PackageType')
                        if package_type is not None and package_type.text:
                            piece_detail['package_type'] = package_type.text
                        
                        # Peso dimensional
                        dim_weight = piece_details_elem.find('.//DimWeight')
                        if dim_weight is not None and dim_weight.text:
                            piece_detail['dim_weight'] = dim_weight.text
                        
                        # Unidad de peso
                        weight_unit = piece_details_elem.find('.//WeightUnit')
                        if weight_unit is not None and weight_unit.text:
                            piece_detail['weight_unit'] = weight_unit.text
                        
                        # Convertir a formato más legible
                        if piece_detail.get('actual_depth') and piece_detail.get('actual_width') and piece_detail.get('actual_height'):
                            piece_detail['actual_length'] = piece_detail['actual_depth']  # DHL usa depth como length
                    
                    if piece_detail:
                        piece_details.append(piece_detail)
                        logger.info(f"Parsed piece detail: Piece {piece_detail.get('piece_number', 'N/A')} - {piece_detail.get('license_plate', 'N/A')}")
            
            # Buscar eventos de tracking en la estructura real de DHL
            piece_events = root.findall('.//PieceEvent/ArrayOfPieceEventItem')
            if piece_events:
                logger.info(f"Found {len(piece_events)} piece events")
                for event_elem in piece_events:
                    event = {}
                    
                    # Fecha y hora
                    date_elem = event_elem.find('.//Date')
                    time_elem = event_elem.find('.//Time')
                    if date_elem is not None and time_elem is not None:
                        event['date'] = date_elem.text
                        event['time'] = time_elem.text
                        event['timestamp'] = f"{date_elem.text} {time_elem.text}"
                    
                    # Código y descripción del evento
                    service_event = event_elem.find('.//ServiceEvent')
                    if service_event is not None:
                        event_code = service_event.find('.//EventCode')
                        event_desc = service_event.find('.//Description')
                        if event_code is not None and event_code.text:
                            event['code'] = event_code.text
                        if event_desc is not None and event_desc.text:
                            event['description'] = event_desc.text
                    
                    # Ubicación
                    service_area = event_elem.find('.//ServiceArea')
                    if service_area is not None:
                        description = service_area.find('.//Description')
                        if description is not None and description.text:
                            event['location'] = description.text
                    
                    # Firmante (para entregas)
                    signatory = event_elem.find('.//Signatory')
                    if signatory is not None and signatory.text:
                        event['signatory'] = signatory.text
                    
                    if event:
                        events.append(event)
                        logger.info(f"Parsed event: {event.get('code', 'N/A')} - {event.get('description', 'N/A')}")
            
            # Si no se encontraron eventos de piezas, buscar eventos de envío generales
            if not events:
                shipment_events = root.findall('.//ShipmentEvent/ArrayOfShipmentEventItem')
                if shipment_events:
                    logger.info(f"Found {len(shipment_events)} shipment events")
                    for event_elem in shipment_events:
                        event = {}
                        
                        # Fecha y hora
                        date_elem = event_elem.find('.//Date')
                        time_elem = event_elem.find('.//Time')
                        if date_elem is not None and time_elem is not None:
                            event['date'] = date_elem.text
                            event['time'] = time_elem.text
                            event['timestamp'] = f"{date_elem.text} {time_elem.text}"
                        
                        # Código y descripción del evento
                        service_event = event_elem.find('.//ServiceEvent')
                        if service_event is not None:
                            event_code = service_event.find('.//EventCode')
                            event_desc = service_event.find('.//Description')
                            if event_code is not None and event_code.text:
                                event['code'] = event_code.text
                            if event_desc is not None and event_desc.text:
                                event['description'] = event_desc.text
                        
                        # Ubicación
                        service_area = event_elem.find('.//ServiceArea')
                        if service_area is not None:
                            description = service_area.find('.//Description')
                            if description is not None and description.text:
                                event['location'] = description.text
                        
                        if event:
                            events.append(event)
                            logger.info(f"Parsed shipment event: {event.get('code', 'N/A')} - {event.get('description', 'N/A')}")
            
            # Ordenar eventos por fecha y hora
            events.sort(key=lambda x: f"{x.get('date', '')} {x.get('time', '')}")
            
            # Determinar estado final basado en eventos
            if events:
                last_event = events[-1]
                if last_event.get('code') == 'OK':
                    shipment_info['status'] = 'Delivered'
                elif last_event.get('code') in ['PU', 'AF', 'PL', 'DF', 'CR', 'CC']:
                    shipment_info['status'] = 'In Transit'
                else:
                    shipment_info['status'] = 'Processing'
            
            # Si no se encontró información básica, puede ser un error
            if not shipment_info.get('awb_number') and not shipment_info.get('tracking_number'):
                logger.warning("No se encontró información básica de tracking")
                return {
                    "success": False,
                    "message": "No se encontró información de tracking válida",
                    "elements_found": self._get_element_summary(root),
                    "raw_response": response_text[:500] + "..." if len(response_text) > 500 else response_text
                }
            
            logger.info(f"Successfully parsed tracking info: {shipment_info}")
            logger.info(f"Found {len(events)} events")
            logger.info(f"Found {len(piece_details)} piece details")
            
            return {
                "success": True,
                "tracking_info": shipment_info,
                "events": events,
                "piece_details": piece_details,
                "total_events": len(events),
                "total_pieces": len(piece_details),
                "message": "Información de seguimiento obtenida exitosamente de DHL"
            }
            
        except Exception as e:
            logger.exception(f"Error parsing tracking response: {str(e)}")
            return {
                "success": False,
                "message": f"Error al procesar respuesta de tracking: {str(e)}",
                "raw_response": response_text[:500] + "..." if len(response_text) > 500 else response_text
            }

    def _parse_shipment_response(self, root, response_text):
        """Parser mejorado para respuestas de creación de envío"""
        # Check for notification errors first
        notification_elements = root.findall('.//*[contains(local-name(), "Notification")]')
        errors = []
        
        for notification in notification_elements:
            code = notification.get('code')
            message_elem = notification.find('.//*[contains(local-name(), "Message")]')
            if message_elem is not None and message_elem.text:
                error_info = {
                    'code': code,
                    'message': message_elem.text
                }
                
                # Agregar información específica para errores comunes
                if code == '998':
                    error_info['error_type'] = 'INVALID_DATE'
                    error_info['suggestion'] = 'Verificar que la fecha de envío sea futura y no más de 10 días adelante'
                elif code == '999':
                    error_info['error_type'] = 'PROCESS_FAILURE'
                    error_info['suggestion'] = 'Error interno del sistema. Reintentar o contactar soporte técnico'
                elif code in ['400', '401', '402', '403']:
                    error_info['error_type'] = 'VALIDATION_ERROR'
                    error_info['suggestion'] = 'Verificar datos del envío (direcciones, pesos, dimensiones)'
                else:
                    error_info['error_type'] = 'UNKNOWN_ERROR'
                    error_info['suggestion'] = 'Verificar datos del envío y reintentar'
                
                errors.append(error_info)
        
        if errors:
            # Crear mensaje detallado
            error_messages = []
            for error in errors:
                error_messages.append(f"Error {error['code']}: {error['message']}")
            
            return {
                "success": False,
                "errors": errors,
                "message": f"Error en creación de envío: {'; '.join(error_messages)}",
                "error_summary": f"Se encontraron {len(errors)} errores en la solicitud de envío",
                "next_steps": "Revise los datos del envío y las sugerencias para cada error"
            }
        
        # Buscar número de tracking
        tracking_elements = root.findall('.//AWBNumber') + root.findall('.//*[contains(local-name(), "AWBNumber")]')
        
        if tracking_elements:
            return {
                "success": True,
                "tracking_number": tracking_elements[0].text,
                "message": "Envío creado exitosamente"
            }
        else:
            # Buscar otros posibles elementos de éxito
            success_elements = root.findall('.//*[contains(local-name(), "ShipmentIdentificationNumber")]')
            if success_elements:
                return {
                    "success": True,
                    "tracking_number": success_elements[0].text,
                    "message": "Envío creado exitosamente (usando ShipmentIdentificationNumber)"
                }
            
            return {
                "success": False,
                "message": "No se pudo obtener el número de tracking",
                "elements_found": self._get_element_summary(root),
                "raw_response": response_text[:500] + "..." if len(response_text) > 500 else response_text
            }

    def _handle_http_error(self, response):
        """Maneja errores HTTP de manera mejorada"""
        if response.status_code == 401:
            return {
                "success": False,
                "error_code": "AUTH_ERROR",
                "message": "Credenciales inválidas. Verificar username/password.",
                "suggestion": "Contactar con DHL para verificar credenciales"
            }
        elif response.status_code == 403:
            return {
                "success": False,
                "error_code": "ACCESS_DENIED",
                "message": "Acceso denegado. Cuenta sin permisos suficientes.",
                "suggestion": "Verificar permisos de la cuenta DHL"
            }
        elif response.status_code == 404:
            return {
                "success": False,
                "error_code": "ENDPOINT_NOT_FOUND",
                "message": "Endpoint no encontrado.",
                "suggestion": "Verificar URL del endpoint"
            }
        elif response.status_code == 500:
            return {
                "success": False,
                "error_code": "SERVER_ERROR",
                "message": "Error interno del servidor DHL.",
                "suggestion": "Reintentar más tarde"
            }
        else:
            return {
                "success": False,
                "error_code": "HTTP_ERROR",
                "message": f"Error HTTP {response.status_code}",
                "response": response.text[:200]
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
    
    def _generate_packages_xml(self, packages, message_ref):
        """Generate packages XML for multiple packages"""
        if not packages:
            # Single package default
            return f"""
               <RequestedPackages number="1">
                  <Weight>0.3</Weight>
                  <Dimensions>
                     <Length>21</Length>
                     <Width>16</Width>
                     <Height>11</Height>
                  </Dimensions>
                  <CustomerReferences>{message_ref}</CustomerReferences>
                  <CustomerReferenceType>SH</CustomerReferenceType>
               </RequestedPackages>"""
        
        packages_xml = ""
        for i, package in enumerate(packages, 1):
            packages_xml += f"""
               <RequestedPackages number="{i}">
                  <Weight>{package.get('weight', 0.3)}</Weight>
                  <Dimensions>
                     <Length>{package.get('length', 21)}</Length>
                     <Width>{package.get('width', 16)}</Width>
                     <Height>{package.get('height', 11)}</Height>
                  </Dimensions>
                  <CustomerReferences>{package.get('reference', message_ref)}</CustomerReferences>
                  <CustomerReferenceType>SH</CustomerReferenceType>
               </RequestedPackages>"""
        
        return packages_xml
    
    def _get_valid_ship_timestamp(self, requested_date=None):
        """Get a valid ship timestamp within DHL's requirements (not in past, not more than 10 days future)"""
        from datetime import datetime, timedelta
        import pytz
        
        # Usar UTC para consistencia
        now = datetime.now(pytz.UTC)
        
        if requested_date:
            try:
                # Parse the requested date
                if isinstance(requested_date, str):
                    # Manejar diferentes formatos de fecha
                    if 'GMT' in requested_date:
                        requested_date = requested_date.replace('GMT+00:00', '+00:00')
                    requested_date = datetime.fromisoformat(requested_date.replace('Z', '+00:00'))
                    if requested_date.tzinfo is None:
                        requested_date = requested_date.replace(tzinfo=pytz.UTC)
                elif isinstance(requested_date, datetime):
                    if requested_date.tzinfo is None:
                        requested_date = requested_date.replace(tzinfo=pytz.UTC)
                else:
                    raise ValueError("Invalid date format")
                
                # Check if it's within valid range (not in past, not more than 10 days future)
                # Agregar un margen de 1 hora para evitar problemas de zona horaria
                if requested_date <= now + timedelta(hours=1):
                    # If in past or too close, use tomorrow at 10 AM
                    ship_date = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
                elif requested_date > now + timedelta(days=9):  # Usar 9 días para ser más conservador
                    # If more than 9 days future, use 9 days from now
                    ship_date = (now + timedelta(days=9)).replace(hour=10, minute=0, second=0, microsecond=0)
                else:
                    # Date is valid, but ensure it's at least 1 hour from now
                    ship_date = max(requested_date, now + timedelta(hours=1))
                    
            except (ValueError, TypeError) as e:
                # Invalid date format, use default
                ship_date = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        else:
            # No date provided, use tomorrow at 10 AM
            ship_date = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        
        # Formatear según lo que espera DHL
        return ship_date.strftime('%Y-%m-%dT%H:%M:%S') + 'GMT+00:00'
