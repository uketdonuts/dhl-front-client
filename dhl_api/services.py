import requests
import xml.etree.ElementTree as ET
import base64
from datetime import datetime, timedelta
import os
import logging
import pytz
import re

logger = logging.getLogger(__name__)

class DHLService:
    def __init__(self, username, password, base_url, environment="production"):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.environment = environment
        
        logger.info(f"Initializing DHLService with environment: {environment}")
        logger.info(f"Base URL: {base_url}")
        
        # Configuración de endpoints DHL
        self.endpoints = {
            "getePOD": "https://wsbexpress.dhl.com:443/gbl/getePOD",
            "rate": "https://wsbexpress.dhl.com:443/sndpt/expressRateBook",
            "tracking": "https://wsbexpress.dhl.com:443/gbl/glDHLExpressTrack",
            "shipment": "https://wsbexpress.dhl.com:443/sndpt/expressRateBook"
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
        </tns:shipmentDocumentRetrieveReq>        </SOAP-ENV:Body>
        </SOAP-ENV:Envelope>"""
            
            response = requests.post(
                self.endpoints["getePOD"],
                headers=self._get_headers(soap_action),
                data=soap_body
            )
            
            return self._parse_response(response, response.text, "ePOD")
            
        except Exception as e:
            return {"success": False, "message": f"Error en get_ePOD: {str(e)}"}

    def _calculate_dimensional_weight(self, dimensions):
        """
        Calcula el peso dimensional según la fórmula de DHL
        Peso dimensional = (Largo × Ancho × Alto) / 5000
        """
        try:
            length = float(dimensions.get('length', 0))
            width = float(dimensions.get('width', 0))
            height = float(dimensions.get('height', 0))
            
            if length <= 0 or width <= 0 or height <= 0:
                return 0.0
            
            # Fórmula DHL: (L × W × H) / 5000
            dimensional_weight = (length * width * height) / 5000
            
            logger.debug(f"Calculated dimensional weight: {dimensional_weight:.2f} kg (L:{length} × W:{width} × H:{height})")
            return round(dimensional_weight, 2)
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculating dimensional weight: {str(e)}")
            return 0.0
    
    def _calculate_chargeable_weight(self, actual_weight, dimensions, declared_weight=None):
        """
        Calcula el peso facturable (el más alto entre peso real, dimensional y declarado)
        Este es el peso que DHL usa para calcular la tarifa
        """
        try:
            actual_weight = float(actual_weight) if actual_weight else 0.0
            declared_weight = float(declared_weight) if declared_weight else 0.0
            
            # Calcular peso dimensional
            dimensional_weight = self._calculate_dimensional_weight(dimensions)
            
            # Encontrar el peso más alto
            chargeable_weight = max(actual_weight, dimensional_weight, declared_weight)
            
            # Log detallado para debugging
            logger.info(f"Weight calculation details:")
            logger.info(f"  - Actual weight: {actual_weight:.2f} kg")
            logger.info(f"  - Dimensional weight: {dimensional_weight:.2f} kg")
            logger.info(f"  - Declared weight: {declared_weight:.2f} kg")
            logger.info(f"  - Chargeable weight (highest): {chargeable_weight:.2f} kg")
            
            return round(chargeable_weight, 2)
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculating chargeable weight: {str(e)}")
            return float(actual_weight) if actual_weight else 0.0

    def get_rate(self, origin, destination, weight, dimensions, declared_weight=None, content_type="P", account_number=None):
        """
        Obtiene cotización de tarifas usando el formato exacto que funciona con DHL
        
        Args:
            origin: Información del origen
            destination: Información del destino
            weight: Peso del paquete
            dimensions: Dimensiones del paquete
            declared_weight: Peso declarado (opcional)
            content_type: Tipo de contenido - "P" para NON_DOCUMENTS, "D" para DOCUMENTS
        """
        try:
            # Validar tipo de contenido
            if content_type not in ["P", "D"]:
                content_type = "P"  # Default a NON_DOCUMENTS
            
            # Mapear tipo de contenido a XML
            # P = NON_DOCUMENTS (paquetes con productos)
            # D = DOCUMENTS (solo documentos)
            content_xml = "NON_DOCUMENTS" if content_type == "P" else "DOCUMENTS"
            
            logger.info(f"Using content type: {content_type} ({content_xml})")
            
            # Calcular peso facturable
            chargeable_weight = self._calculate_chargeable_weight(
                actual_weight=weight,
                dimensions=dimensions,
                declared_weight=declared_weight
            )
            
            # Usar el peso facturable para las cotizaciones
            weight_to_use = chargeable_weight
            
            # Determinar número de cuenta para la cotización
            account_to_use = account_number if account_number else '706014493'
            logger.info(f"Using account number for rate: {account_to_use}")
            # Payload SOAP exacto con account_number y SCDtl dinámicos
            soap_body = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:rat="http://scxgxtt.phx-dc.dhl.com/euExpressRateBook/RateMsgRequest">
    <soapenv:Header>
        {self._get_auth_header()}
    </soapenv:Header>
    <soapenv:Body>
        <rat:RateRequest>
            <ClientDetail>
                <SCDtl AccNo="{account_number or os.getenv('DHL_ACCOUNT_NUMBER', '706014493')}" CRlTyCd="{content_xml}"/>
            </ClientDetail>
            <RequestedShipment>
                <DropOffType>REQUEST_COURIER</DropOffType>
                <NextBusinessDay>N</NextBusinessDay>
                <Ship>
                    <Shipper>
                        <StreetLines>{self._clean_text(origin.get('address', 'River House'))}</StreetLines>
                        <StreetLines2>{self._clean_text(origin.get('address2', '1'))}</StreetLines2>
                        <StreetLines3>{self._clean_text(origin.get('address3', '1'))}</StreetLines3>
                        <StreetName>{self._clean_text(origin.get('street', 'Eas Wall road'))}</StreetName>
                        <StreetNumber>{self._clean_text(origin.get('street_number', '1'))}</StreetNumber>
                        <City>{self._clean_text(origin.get('city', 'Panama'))}</City>
                        <StateOrProvinceCode>{origin.get('state', 'PA')}</StateOrProvinceCode>
                        <PostalCode>{origin.get('postal_code', '0')}</PostalCode>
                        <CountryCode>{origin.get('country', 'PA')}</CountryCode>
                    </Shipper>
                    <Recipient>
                        <StreetLines>{self._clean_text(destination.get('address', 'River House'))}</StreetLines>
                        <StreetLines2>{self._clean_text(destination.get('address2', '1'))}</StreetLines2>
                        <StreetLines3>{self._clean_text(destination.get('address3', '1'))}</StreetLines3>
                        <StreetName>{self._clean_text(destination.get('street', 'Eas Wall road'))}</StreetName>
                        <StreetNumber>{self._clean_text(destination.get('street_number', '1'))}</StreetNumber>
                        <City>{self._clean_text(destination.get('city', 'MIA'))}</City>
                        <PostalCode>{destination.get('postal_code', '25134')}</PostalCode>
                        <CountryCode>{destination.get('country', 'US')}</CountryCode>
                    </Recipient>
                </Ship>
                <Packages>
                    <RequestedPackages number="1">
                        <Weight>
                            <Value>{weight_to_use}</Value>
                        </Weight>
                        <Dimensions>
                            <Length>{dimensions.get('length', 1)}</Length>
                            <Width>{dimensions.get('width', 1)}</Width>
                            <Height>{dimensions.get('height', 1)}</Height>
                        </Dimensions>
                    </RequestedPackages>
                </Packages>
                <UnitOfMeasurement>SI</UnitOfMeasurement>
                <Content>{content_xml}</Content>
                <PaymentInfo>DDU</PaymentInfo>
                <Account>{account_number or os.getenv('DHL_ACCOUNT_NUMBER', '706014493')}</Account>
            </RequestedShipment>
        </rat:RateRequest>
    </soapenv:Body>
</soapenv:Envelope>"""
            
            # Headers específicos para rate request (incluye Authorization)
            headers = self._get_headers('euExpressRateBook_providerServices_ShipmentHandlingServices_Binder_getRateRequest')
            # Asegurar charset en Content-Type
            headers['Content-Type'] = 'text/xml; charset=utf-8'
            
            logger.info(f"Making rate request to: {self.endpoints['rate']}")
            logger.debug(f"Request body: {soap_body}")
            
            response = requests.post(
                self.endpoints["rate"],
                headers=headers,
                data=soap_body,
                verify=False,
                timeout=30
            )
            
            logger.info(f"Rate response status: {response.status_code}")
            logger.debug(f"Rate response: {response.text}")
            
            result = self._parse_response(response, response.text, "Rate")
            
            # Agregar información del peso facturable a la respuesta
            if result.get('success') and 'rates' in result:
                weight_breakdown = {
                    'actual_weight': weight,
                    'dimensional_weight': self._calculate_dimensional_weight(dimensions),
                    'declared_weight': declared_weight or 0.0,
                    'chargeable_weight': chargeable_weight
                }
                
                content_info = {
                    'content_type': content_type,
                    'content_xml': content_xml,
                    'description': 'Paquetes con productos' if content_type == 'P' else 'Solo documentos'
                }
                
                for rate in result['rates']:
                    rate['weight_breakdown'] = weight_breakdown
                    rate['content_info'] = content_info
                
                result['weight_breakdown'] = weight_breakdown
                result['content_info'] = content_info
            
            return result
            
        except Exception as e:
            logger.exception(f"Error in get_rate: {str(e)}")
            return {"success": False, "message": f"Error en get_rate: {str(e)}"}
    
    def get_tracking(self, tracking_number):
        """Obtiene información de seguimiento usando el formato exacto de DHL"""
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
            
            # Usar el formato exacto del ejemplo que funciona con credenciales correctas
            soap_body = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:trac="http://scxgxtt.phx-dc.dhl.com/glDHLExpressTrack/providers/services/trackShipment" xmlns:dhl="http://www.dhl.com">
    <soapenv:Header>
        <wsse:Security soapenv:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
            <wsse:UsernameToken>
                <wsse:Username>apO3fS5mJ8zT7h</wsse:Username>
                <wsse:Password>J^4oF@1qW!0qS!5b</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </soapenv:Header>
    <soapenv:Body>
        <trac:trackShipmentRequest>
            <trackingRequest>
                <dhl:TrackingRequest>
                    <Request>
                        <ServiceHeader>
                            <MessageTime>{datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}Z</MessageTime>
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
            
            # Headers específicos para tracking
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'glDHLExpressTrack_providers_services_trackShipment_Binder_trackShipmentRequest'
            }
            
            logger.debug(f"Request Headers: {headers}")
            logger.debug(f"Request Body: {soap_body}")
            
            # Hacer la petición a DHL usando la URL exacta
            endpoint_url = "https://wsbexpress.dhl.com:443/gbl/glDHLExpressTrack"
            logger.info(f"Making request to: {endpoint_url}")
            
            try:
                response = requests.post(
                    endpoint_url,
                    headers=headers,
                    data=soap_body,
                    verify=False,
                    timeout=30
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
                        "error_code": "XML_PARSE_ERROR",
                        "raw_response": response.text[:500]
                    }
                    
            except requests.exceptions.Timeout:
                logger.error(f"Timeout error for tracking {tracking_number}")
                return {
                    "success": False,
                    "message": "Timeout al conectar con DHL. Intenta más tarde.",
                    "error_code": "TIMEOUT_ERROR",
                    "suggestion": "Reintentar en unos minutos"
                }
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error for tracking {tracking_number}")
                return {
                    "success": False,
                    "message": "Error de conexión con DHL. Verifica tu conexión a internet.",
                    "error_code": "CONNECTION_ERROR",
                    "suggestion": "Verificar conexión a internet y reintentar"
                }
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error for tracking {tracking_number}: {str(e)}")
                return {
                    "success": False,
                    "message": f"Error en la petición a DHL: {str(e)}",
                    "error_code": "REQUEST_ERROR",
                    "suggestion": "Reintentar más tarde"
                }
            
        except Exception as e:
            logger.exception(f"Error in get_tracking for {tracking_number}")
            return {
                "success": False, 
                "message": f"Error en get_tracking: {str(e)}",
                "error_code": "GENERAL_ERROR",
                "suggestion": "Contactar soporte técnico"
            }

    def create_shipment(self, shipment_data, content_type="P"):
        """
        Crea un nuevo envío usando el formato exacto que funciona
        
        Args:
            shipment_data: Datos del envío
            content_type: Tipo de contenido - "P" para NON_DOCUMENTS, "D" para DOCUMENTS
        """
        try:
            # Validar tipo de contenido
            if content_type not in ["P", "D"]:
                content_type = "P"  # Default a NON_DOCUMENTS
            
            # Mapear tipo de contenido a XML
            # P = NON_DOCUMENTS (paquetes con productos)
            # D = DOCUMENTS (solo documentos)
            content_xml = "NON_DOCUMENTS" if content_type == "P" else "DOCUMENTS"
            
            logger.info(f"Creating shipment with content type: {content_type} ({content_xml})")
            
            # Usar el endpoint real con formato exacto del ejemplo
            soap_action = "euExpressRateBook_providerServices_ShipmentHandlingServices_Binder_createShipmentRequest"
            # Extraer datos del formulario
            shipper = shipment_data.get('shipper', {})
            recipient = shipment_data.get('recipient', {})
            package = shipment_data.get('package', {})
            packages = shipment_data.get('packages', [])  # Support multiple packages
            service_type = shipment_data.get('service', 'P')
            payment_type = shipment_data.get('payment', 'S')
            account_number = shipment_data.get('account_number', '706065602')  # Usar la cuenta seleccionada o cuenta principal
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
            <PickupLocation>{self._clean_text(shipper.get('address', 'Dirección de Recolección'))}</PickupLocation>
            <PaymentInfo>DDP</PaymentInfo>
            <InternationalDetail>
               <Commodities>
                  <Description>{self._clean_text(package.get('description', 'General Merchandise'))}</Description>
                  <CustomsValue>{package.get('value', 100)}</CustomsValue>
               </Commodities>
               <Content>{content_xml}</Content>
            </InternationalDetail>
            <Ship>
               <Shipper>
                  <Contact>
                     <PersonName>{self._clean_text(shipper.get('name', 'Remitente'))}</PersonName>
                     <CompanyName>{self._clean_text(shipper.get('company', 'Empresa Remitente'))}</CompanyName>
                     <PhoneNumber>{self._clean_phone(shipper.get('phone', '507431-2600'))}</PhoneNumber>
                     <EmailAddress>{shipper.get('email', 'remitente@empresa.com')}</EmailAddress>
                     <MobilePhoneNumber>{self._clean_phone(shipper.get('phone', '507431-2600'))}</MobilePhoneNumber>
                  </Contact>
                  <Address>
                     <StreetLines>{self._clean_text(shipper.get('address', 'Dirección del Remitente'))}</StreetLines>
                     <StreetName>{self._clean_text(shipper.get('address', 'Calle del Remitente'))}</StreetName>
                     <StreetNumber>{self._clean_text(shipper.get('address2', 'Building 1'))}</StreetNumber>
                     <StreetLines2>.</StreetLines2>
                     <StreetLines3>{self._clean_text(shipper.get('address3', 'Floor 1'))}</StreetLines3>
                     <City>{self._clean_text(shipper.get('city', 'Ciudad del Remitente'))}</City>
                     <StateOrProvinceCode>{self._clean_text(shipper.get('state', 'XX'))}</StateOrProvinceCode>
                     <PostalCode>{shipper.get('postalCode', '0')}</PostalCode>
                     <CountryCode>{shipper.get('country', 'US')}</CountryCode>
                  </Address>
               </Shipper>
               <Recipient>
                  <Contact>
                     <PersonName>{self._clean_text(recipient.get('name', 'Destinatario'))}</PersonName>
                     <CompanyName>{self._clean_text(recipient.get('company', 'Empresa Destinatario'))}</CompanyName>
                     <PhoneNumber>{self._clean_phone(recipient.get('phone', '1234567890'))}</PhoneNumber>
                     <EmailAddress>{recipient.get('email', 'destinatario@empresa.com')}</EmailAddress>
                     <MobilePhoneNumber>{self._clean_phone(recipient.get('phone', '1234567890'))}</MobilePhoneNumber>
                  </Contact>
                  <Address>
                     <StreetLines>{self._clean_text(recipient.get('address', 'Dirección del Destinatario'))}</StreetLines>
                     <StreetName>{self._clean_text(recipient.get('address', 'Calle del Destinatario'))}</StreetName>
                     <StreetLines2>{self._clean_text(recipient.get('address2', 'Apt 1'))}</StreetLines2>
                     <City>{self._clean_text(recipient.get('city', 'Ciudad del Destinatario'))}</City>
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
</soapenv:Envelope>"""            # Usar la URL exacta del ejemplo
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
            
            result = self._parse_response(response, response.text, "Shipment")
            
            # Agregar información del tipo de contenido a la respuesta
            if result.get('success'):
                content_info = {
                    'content_type': content_type,
                    'content_xml': content_xml,
                    'description': 'Paquetes con productos' if content_type == 'P' else 'Solo documentos'
                }
                result['content_info'] = content_info
                
                # Agregar información adicional del envío
                if 'shipment_info' in result:
                    result['shipment_info']['content_info'] = content_info
            
            return result
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
    
    def _parse_response(self, response, response_text, service_type):
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
                    return self._parse_epod_response(root, response_text)
                elif service_type == "Rate":
                    return self._parse_rate_response(root, response_text)
                elif service_type == "Tracking":
                    return self._parse_tracking_response(root, response_text)
                elif service_type == "Shipment":
                    return self._parse_shipment_response(root, response_text)
                else:
                    return {
                        "success": True,
                        "raw_response": response_text,
                        "message": "Respuesta procesada"
                    }
            
            else:
                return self._handle_http_error(response)
                
        except ET.ParseError as e:
            return {
                "success": False,
                "error_type": "xml_parse_error",
                "message": f"Error parseando XML: {str(e)}",
                "raw_response": response_text[:500]
            }
        except Exception as e:
            return {
                "success": False,
                "error_type": "unknown_error",
                "message": f"Error procesando respuesta: {str(e)}",
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
        """Parser mejorado para respuestas de cotización basado en estructura real de DHL"""
        rates = []
        
        # Buscar Provider con código DHL
        provider_elements = root.findall('.//Provider[@code="DHL"]')
        if not provider_elements:
            # Fallback: buscar cualquier Provider
            provider_elements = root.findall('.//Provider')
        
        if not provider_elements:
            return {
                "success": False,
                "message": "No se encontró información de proveedor en la respuesta",
                "raw_response": response_text[:500]
            }
        
        provider = provider_elements[0]
        
        # Verificar notificaciones de error
        notification_elements = provider.findall('.//Notification')
        for notification in notification_elements:
            code = notification.get('code')
            message_elem = notification.find('Message')
            
            if code and code != '0':  # Código 0 es éxito
                error_message = message_elem.text if message_elem is not None else f"Error código {code}"
                return {
                    "success": False,
                    "error_code": code,
                    "message": f"Error DHL: {error_message}",
                    "raw_response": response_text[:500]
                }
        
        # Buscar servicios disponibles
        service_elements = provider.findall('.//Service')
        
        for service_elem in service_elements:
            rate = {}
            
            # Obtener tipo de servicio
            service_type = service_elem.get('type')
            if service_type:
                rate['service_code'] = service_type
                
                # Mapear códigos de servicio a nombres descriptivos
                service_names = {
                    'D': 'EXPRESS WORLDWIDE DOC',
                    'P': 'EXPRESS WORLDWIDE',
                    'U': 'EXPRESS WORLDWIDE',
                    'K': 'EXPRESS 9:00',
                    'L': 'EXPRESS 10:30',
                    'G': 'DOMESTIC EXPRESS',
                    'W': 'ECONOMY SELECT',
                    'I': 'BREAK BULK EXPRESS',
                    'N': 'DOMESTIC EXPRESS',
                    'O': 'DOMESTIC EXPRESS'
                }
                rate['service_name'] = service_names.get(service_type, f"DHL Service {service_type}")
                
                # Agregar información sobre compatibilidad de contenido
                content_compatibility = self.get_service_content_compatibility(service_type)
                rate['content_compatibility'] = content_compatibility
            
            # Obtener información financiera
            total_net_elem = service_elem.find('TotalNet')
            if total_net_elem is not None:
                currency_elem = total_net_elem.find('Currency')
                amount_elem = total_net_elem.find('Amount')
                
                if currency_elem is not None and currency_elem.text:
                    rate['currency'] = currency_elem.text
                
                if amount_elem is not None and amount_elem.text:
                    try:
                        rate['total_charge'] = float(amount_elem.text)
                    except ValueError:
                        rate['total_charge'] = 0.0
            
            # Obtener desglose de cargos
            charges_elem = service_elem.find('Charges')
            if charges_elem is not None:
                charges = []
                charge_elements = charges_elem.findall('Charge')
                
                for charge_elem in charge_elements:
                    charge = {}
                    
                    # Código del cargo
                    charge_code_elem = charge_elem.find('ChargeCode')
                    if charge_code_elem is not None and charge_code_elem.text:
                        charge['code'] = charge_code_elem.text
                    
                    # Tipo de cargo
                    charge_type_elem = charge_elem.find('ChargeType')
                    if charge_type_elem is not None and charge_type_elem.text:
                        charge['description'] = charge_type_elem.text
                    
                    # Monto del cargo
                    charge_amount_elem = charge_elem.find('ChargeAmount')
                    if charge_amount_elem is not None and charge_amount_elem.text:
                        try:
                            charge['amount'] = float(charge_amount_elem.text)
                        except ValueError:
                            charge['amount'] = 0.0
                    
                    if charge.get('description') or charge.get('amount'):
                        charges.append(charge)
                
                rate['charges'] = charges
            
            # Obtener tiempo de entrega
            delivery_time_elem = service_elem.find('DeliveryTime')
            if delivery_time_elem is not None and delivery_time_elem.text:
                # Parsear fecha/hora de entrega
                try:
                    from datetime import datetime
                    delivery_datetime = datetime.fromisoformat(delivery_time_elem.text.replace('Z', '+00:00'))
                    rate['delivery_time'] = delivery_datetime.strftime('%Y-%m-%d %H:%M')
                    rate['delivery_date'] = delivery_datetime.strftime('%Y-%m-%d')
                except:
                    rate['delivery_time'] = delivery_time_elem.text
            
            # Obtener tiempo de corte
            cutoff_time_elem = service_elem.find('CutoffTime')
            if cutoff_time_elem is not None and cutoff_time_elem.text:
                try:
                    from datetime import datetime
                    cutoff_datetime = datetime.fromisoformat(cutoff_time_elem.text.replace('Z', '+00:00'))
                    rate['cutoff_time'] = cutoff_datetime.strftime('%Y-%m-%d %H:%M')
                except:
                    rate['cutoff_time'] = cutoff_time_elem.text
            
            # Indicador de siguiente día hábil
            next_business_day_elem = service_elem.find('NextBusinessDayInd')
            if next_business_day_elem is not None and next_business_day_elem.text:
                rate['next_business_day'] = next_business_day_elem.text == 'Y'
            
            # Asegurar valores por defecto
            rate.setdefault('service_name', f"DHL Service {rate.get('service_code', 'Unknown')}")
            rate.setdefault('total_charge', 0.0)
            rate.setdefault('currency', 'USD')
            rate.setdefault('delivery_time', 'Unknown')
            rate.setdefault('charges', [])
            
            if rate.get('service_code'):
                rates.append(rate)
        
        if not rates:
            return {
                "success": False,
                "message": "No se encontraron tarifas disponibles en la respuesta",
                "raw_response": response_text[:500]
            }
        
        return {
            "success": True,
            "rates": rates,
            "total_rates": len(rates),
            "message": f"Se encontraron {len(rates)} tarifas disponibles",
            "provider": "DHL"
        }

    def _parse_tracking_response(self, root, response_text):
        """Parser para la respuesta real de DHL tracking basado en la estructura XML proporcionada"""
        try:
            logger.info(f"Parsing tracking response with root tag: {root.tag}")
            
            # Buscar información básica del envío
            shipment_info = {}
            events = []
            
            # Buscar AWBInfo en la estructura real de DHL
            awb_info_items = root.findall('.//AWBInfo/ArrayOfAWBInfoItem')
            if not awb_info_items:
                return {
                    "success": False,
                    "message": "No se encontró información AWB en la respuesta",
                    "raw_response": response_text[:500]
                }
            
            # Usar el primer AWBInfoItem
            awb_info = awb_info_items[0]
            
            # Obtener AWB Number
            awb_number_elem = awb_info.find('.//AWBNumber')
            if awb_number_elem is not None and awb_number_elem.text:
                shipment_info['awb_number'] = awb_number_elem.text
                shipment_info['tracking_number'] = awb_number_elem.text
                logger.info(f"Found AWB Number: {awb_number_elem.text}")
            
            # Obtener estado del envío
            status_elem = awb_info.find('.//Status/ActionStatus')
            if status_elem is not None and status_elem.text:
                shipment_info['status'] = status_elem.text
                logger.info(f"Found Status: {status_elem.text}")
            
            # Buscar información del envío
            shipment_info_elem = awb_info.find('.//ShipmentInfo')
            if shipment_info_elem is not None:
                # Origen
                origin_elem = shipment_info_elem.find('.//OriginServiceArea/Description')
                if origin_elem is not None and origin_elem.text:
                    shipment_info['origin'] = origin_elem.text
                    logger.info(f"Found Origin: {origin_elem.text}")
                
                # Destino
                dest_elem = shipment_info_elem.find('.//DestinationServiceArea/Description')
                if dest_elem is not None and dest_elem.text:
                    shipment_info['destination'] = dest_elem.text
                    logger.info(f"Found Destination: {dest_elem.text}")
                
                # Peso
                weight_elem = shipment_info_elem.find('.//Weight')
                if weight_elem is not None and weight_elem.text:
                    weight_unit_elem = shipment_info_elem.find('.//WeightUnit')
                    unit = weight_unit_elem.text if weight_unit_elem is not None else 'K'
                    shipment_info['weight'] = f"{weight_elem.text} {unit}"
                    logger.info(f"Found Weight: {weight_elem.text} {unit}")
                
                # Piezas
                pieces_elem = shipment_info_elem.find('.//Pieces')
                if pieces_elem is not None and pieces_elem.text:
                    shipment_info['pieces'] = int(pieces_elem.text)
                    logger.info(f"Found Pieces: {pieces_elem.text}")
                
                # Fecha de envío
                shipment_date_elem = shipment_info_elem.find('.//ShipmentDate')
                if shipment_date_elem is not None and shipment_date_elem.text:
                    shipment_info['shipment_date'] = shipment_date_elem.text.split('T')[0]  # Solo la fecha
                    logger.info(f"Found Shipment Date: {shipment_info['shipment_date']}")
            
            # Buscar detalles de piezas individuales
            piece_details = []
            piece_info_items = awb_info.findall('.//Pieces/PieceInfo/ArrayOfPieceInfoItem')
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
                            piece_detail['actual_length'] = actual_depth.text  # DHL usa depth como length
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
                            piece_detail['declared_length'] = depth.text
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
                    
                    # Procesar eventos de la pieza
                    piece_events = piece_item.findall('.//PieceEvent/ArrayOfPieceEventItem')
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
                        
                        # Agregar evento solo si tiene información útil
                        if event.get('code') and event.get('timestamp'):
                            # Crear clave única para evitar duplicados
                            event_key = f"{event['timestamp']}_{event['code']}_{event.get('location', '')}"
                            
                            # Verificar si ya existe este evento
                            if not any(e.get('_key') == event_key for e in events):
                                event['_key'] = event_key  # Clave interna para deduplicación
                                events.append(event)
                                logger.info(f"Added unique event: {event.get('code', 'N/A')} - {event.get('description', 'N/A')}")
                    
                    if piece_detail:
                        piece_details.append(piece_detail)
                        logger.info(f"Parsed piece detail: Piece {piece_detail.get('piece_number', 'N/A')} - {piece_detail.get('license_plate', 'N/A')}")
            
            # Si no hay eventos de piezas, buscar eventos de envío generales
            if not events:
                shipment_events = awb_info.findall('.//ShipmentEvent/ArrayOfShipmentEventItem')
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
                        
                        # Firmante (para entregas)
                        signatory = event_elem.find('.//Signatory')
                        if signatory is not None and signatory.text:
                            event['signatory'] = signatory.text
                        
                        # Agregar evento solo si tiene información útil
                        if event.get('code') and event.get('timestamp'):
                            # Crear clave única para evitar duplicados
                            event_key = f"{event['timestamp']}_{event['code']}_{event.get('location', '')}"
                            
                            # Verificar si ya existe este evento
                            if not any(e.get('_key') == event_key for e in events):
                                event['_key'] = event_key  # Clave interna para deduplicación
                                events.append(event)
                                logger.info(f"Added unique shipment event: {event.get('code', 'N/A')} - {event.get('description', 'N/A')}")
            
            # Limpiar claves internas antes de devolver
            for event in events:
                event.pop('_key', None)
            
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
            
            # Validar que tenemos información básica
            if not shipment_info.get('awb_number') and not shipment_info.get('tracking_number'):
                logger.warning("No se encontró información básica de tracking")
                return {
                    "success": False,
                    "message": "No se encontró información de tracking válida en la respuesta",
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
    
    def get_content_types(self):
        """
        Obtiene los tipos de contenido disponibles para DHL
        
        Returns:
            list: Lista de tipos de contenido con información detallada
        """
        return [
            {
                'code': 'P',
                'name': 'NON_DOCUMENTS',
                'description': 'Paquetes con productos',
                'xml_value': 'NON_DOCUMENTS',
                'restrictions': [
                    'Productos con valor comercial',
                    'Requiere declaración de valor',
                    'Sujeto a aranceles e impuestos'
                ],
                'typical_services': ['P', 'U', 'K', 'L', 'G', 'W', 'I', 'N', 'O']
            },
            {
                'code': 'D',
                'name': 'DOCUMENTS',
                'description': 'Solo documentos',
                'xml_value': 'DOCUMENTS',
                'restrictions': [
                    'Solo documentos sin valor comercial',
                    'Peso máximo típico: 2 kg',
                    'Sin declaración de valor'
                ],
                'typical_services': ['D']
            }
        ]

    def get_service_content_compatibility(self, service_code):
        """
        Verifica qué tipos de contenido son compatibles con un servicio específico
        
        Args:
            service_code (str): Código del servicio DHL
            
        Returns:
            dict: Información de compatibilidad
        """
        # Servicios que solo manejan documentos
        document_only_services = ['D']
        
        # Servicios que manejan paquetes (NON_DOCUMENTS)
        package_services = ['P', 'U', 'K', 'L', 'G', 'W', 'I', 'N', 'O']
        
        if service_code in document_only_services:
            return {
                'service_code': service_code,
                'supported_content_types': ['D'],
                'default_content_type': 'D',
                'restrictions': 'Solo documentos'
            }
        elif service_code in package_services:
            return {
                'service_code': service_code,
                'supported_content_types': ['P', 'D'],
                'default_content_type': 'P',
                'restrictions': 'Paquetes y documentos'
            }
        else:
            return {
                'service_code': service_code,
                'supported_content_types': ['P'],
                'default_content_type': 'P',
                'restrictions': 'Servicio desconocido, asumiendo paquetes'
            }
    
    def get_content_type_comparison(self):
        """
        Obtiene una comparación detallada entre tipos de contenido DHL
        
        Returns:
            dict: Comparación entre DOCUMENTS y NON_DOCUMENTS
        """
        return {
            'comparison': {
                'DOCUMENTS': {
                    'code': 'D',
                    'xml_value': 'DOCUMENTS',
                    'description': 'Solo documentos sin valor comercial',
                    'characteristics': [
                        'Peso máximo típico: 2 kg',
                        'Sin declaración de valor comercial',
                        'Proceso de aduana simplificado',
                        'Tarifas generalmente más bajas',
                        'Tiempos de tránsito más rápidos'
                    ],
                    'restrictions': [
                        'No puede contener productos físicos',
                        'No puede tener valor comercial',
                        'Limitaciones de peso y tamaño'
                    ],
                    'examples': [
                        'Contratos',
                        'Facturas',
                        'Certificados',
                        'Correspondencia',
                        'Documentos legales'
                    ]
                },
                'NON_DOCUMENTS': {
                    'code': 'P',
                    'xml_value': 'NON_DOCUMENTS',
                    'description': 'Paquetes con productos físicos',
                    'characteristics': [
                        'Productos con valor comercial',
                        'Requiere declaración de valor',
                        'Proceso de aduana completo',
                        'Sujeto a aranceles e impuestos',
                        'Mayor flexibilidad en peso y tamaño'
                    ],
                    'restrictions': [
                        'Productos prohibidos por país',
                        'Restricciones de materiales peligrosos',
                        'Requisitos de empaque especiales'
                    ],
                    'examples': [
                        'Productos manufacturados',
                        'Muestras comerciales',
                        'Repuestos',
                        'Regalos',
                        'Mercancía general'
                    ]
                }
            },
            'response_differences': {
                'DOCUMENTS': {
                    'typical_services': ['D'],
                    'pricing_factors': ['Peso', 'Destino', 'Urgencia'],
                    'customs_processing': 'Simplificado',
                    'transit_time': 'Más rápido'
                },
                'NON_DOCUMENTS': {
                    'typical_services': ['P', 'U', 'K', 'L', 'G', 'W', 'I', 'N', 'O'],
                    'pricing_factors': ['Peso', 'Destino', 'Urgencia', 'Valor declarado', 'Peso dimensional'],
                    'customs_processing': 'Completo',
                    'transit_time': 'Estándar'
                }
            },
            'api_response_differences': {
                'rate_calculation': {
                    'DOCUMENTS': 'Basado principalmente en peso y destino',
                    'NON_DOCUMENTS': 'Incluye peso dimensional y valor declarado'
                },
                'available_services': {
                    'DOCUMENTS': 'Limitado a servicios de documentos',
                    'NON_DOCUMENTS': 'Acceso a todos los servicios DHL'
                },
                'additional_charges': {
                    'DOCUMENTS': 'Menos cargos adicionales',
                    'NON_DOCUMENTS': 'Puede incluir cargos por valor, combustible, zona remota'
                }
            }
        }

    def validate_content_type_for_service(self, service_code, content_type):
        """
        Valida si un tipo de contenido es compatible con un servicio específico
        
        Args:
            service_code (str): Código del servicio DHL
            content_type (str): Tipo de contenido ('P' o 'D')
            
        Returns:
            dict: Resultado de la validación
        """
        compatibility = self.get_service_content_compatibility(service_code)
        
        if content_type in compatibility['supported_content_types']:
            return {
                'valid': True,
                'service_code': service_code,
                'content_type': content_type,
                'message': f"Tipo de contenido {content_type} es compatible con servicio {service_code}"
            }
        else:
            return {
                'valid': False,
                'service_code': service_code,
                'content_type': content_type,
                'message': f"Tipo de contenido {content_type} NO es compatible con servicio {service_code}",
                'supported_types': compatibility['supported_content_types'],
                'suggestion': f"Use tipo de contenido {compatibility['default_content_type']} para este servicio"
            }
    
    def suggest_content_type(self, shipment_description, shipment_value=None, weight=None):
        """
        Sugiere el tipo de contenido basado en la descripción y características del envío
        
        Args:
            shipment_description (str): Descripción del contenido del envío
            shipment_value (float): Valor declarado del envío (opcional)
            weight (float): Peso del envío en kg (opcional)
            
        Returns:
            dict: Sugerencia de tipo de contenido
        """
        description_lower = shipment_description.lower() if shipment_description else ""
        
        # Palabras clave que indican documentos
        document_keywords = [
            'documento', 'document', 'contract', 'contrato', 'invoice', 'factura',
            'certificate', 'certificado', 'letter', 'carta', 'correspondence',
            'correspondencia', 'legal', 'paper', 'papel', 'form', 'formulario',
            'statement', 'declaración', 'report', 'reporte', 'manual'
        ]
        
        # Palabras clave que indican productos
        product_keywords = [
            'product', 'producto', 'merchandise', 'mercancía', 'goods', 'bienes',
            'sample', 'muestra', 'part', 'repuesto', 'component', 'componente',
            'equipment', 'equipo', 'device', 'dispositivo', 'tool', 'herramienta',
            'gift', 'regalo', 'clothing', 'ropa', 'electronics', 'electrónicos'
        ]
        
        # Verificar palabras clave
        has_document_keywords = any(keyword in description_lower for keyword in document_keywords)
        has_product_keywords = any(keyword in description_lower for keyword in product_keywords)
        
        # Factores que sugieren NON_DOCUMENTS
        suggests_non_documents = False
        reasons = []
        
        if shipment_value and shipment_value > 0:
            suggests_non_documents = True
            reasons.append(f"Valor declarado: ${shipment_value}")
        
        if weight and weight > 2:
            suggests_non_documents = True
            reasons.append(f"Peso: {weight} kg (típico para paquetes)")
        
        if has_product_keywords:
            suggests_non_documents = True
            reasons.append("Descripción indica productos físicos")
        
        # Determinar sugerencia
        if has_document_keywords and not suggests_non_documents:
            suggested_type = 'D'
            confidence = 'high'
            reasoning = "Descripción indica documentos sin valor comercial"
        elif suggests_non_documents:
            suggested_type = 'P'
            confidence = 'high' if len(reasons) > 1 else 'medium'
            reasoning = f"Factores que indican productos: {', '.join(reasons)}"
        else:
            suggested_type = 'P'  # Default seguro
            confidence = 'low'
            reasoning = "No hay indicadores claros, usando NON_DOCUMENTS por seguridad"
        
        return {
            'suggested_type': suggested_type,
            'suggested_xml': 'DOCUMENTS' if suggested_type == 'D' else 'NON_DOCUMENTS',
            'confidence': confidence,
            'reasoning': reasoning,
            'factors_analyzed': {
                'description': shipment_description,
                'value': shipment_value,
                'weight': weight,
                'has_document_keywords': has_document_keywords,
                'has_product_keywords': has_product_keywords
            },
            'alternatives': {
                'D': {
                    'suitable_if': 'Solo documentos sin valor comercial',
                    'restrictions': 'Peso máximo ~2kg, sin valor comercial'
                },
                'P': {
                    'suitable_if': 'Cualquier producto físico con valor',
                    'restrictions': 'Requiere declaración de valor y proceso aduanero'
                }
            }
        }