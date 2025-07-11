#!/usr/bin/env python
"""
Script para probar las credenciales DHL y analizar las respuestas
"""

import requests
import xml.etree.ElementTree as ET
import base64
from datetime import datetime
import json

class DHLCredentialTester:
    def __init__(self):
        # Credenciales del archivo .env
        self.username = "apO3fS5mJ8zT7h"
        self.password = "J^4oF@1qW!0qS!5b"
        self.base_url = "https://wsbexpress.dhl.com"
        
        # Endpoints para pruebas
        self.endpoints = {
            "getePOD": "https://wsbexpress.dhl.com/gbl/getePOD",
            "rate": "https://wsbexpress.dhl.com/sndpt/expressRateBook",
            "tracking": "https://wsbexpress.dhl.com/gbl/glDHLExpressTrack",
            "shipment": "https://wsbexpress.dhl.com/sndpt/expressRateBook"
        }
    
    def get_auth_header(self):
        """Genera header de autenticación WS-Security"""
        return f"""
        <wsse:Security SOAP-ENV:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
            <wsse:UsernameToken>
                <wsse:Username>{self.username}</wsse:Username>
                <wsse:Password>{self.password}</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
        """
    
    def get_basic_auth_header(self):
        """Genera header de autenticación Basic"""
        credentials = f"{self.username}:{self.password}"
        auth_header = base64.b64encode(credentials.encode()).decode()
        return f"Basic {auth_header}"
    
    def test_epod_service(self):
        """Prueba el servicio ePOD"""
        print("=== Probando servicio ePOD ===")
        
        # Usar un shipment ID de prueba conocido
        test_shipment_id = "2287013540"
        
        soap_body = f"""
<SOAP-ENV:Envelope xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="glDHLExpressePOD/providers/DocumentRetrieve" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
    <SOAP-ENV:Header>
        <wsse:Security SOAP-ENV:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
            <wsse:UsernameToken>
                <wsse:Username>{self.username}</wsse:Username>
                <wsse:Password>{self.password}</wsse:Password>
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
                    <Shp Id="{test_shipment_id}">
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
        
        headers = {
            'Content-Type': 'text/xml',
            'SOAPAction': 'euExpressRateBook_providerServices_ShipmentHandlingServices_Binder_createShipmentRequest',
            'Authorization': self.get_basic_auth_header(),
            'Cookie': 'BIGipServer~WSB~pl_wsb-express-ash.dhl.com_443=1566607772.64288.0000'
        }
        
        try:
            response = requests.post(
                self.endpoints["getePOD"],
                headers=headers,
                data=soap_body,
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Response Length: {len(response.text)}")
            print(f"First 500 chars: {response.text[:500]}")
            
            if response.status_code == 200:
                return self.analyze_epod_response(response.text)
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "response": response.text
                }
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def test_tracking_service(self):
        """Prueba el servicio de tracking"""
        print("\n=== Probando servicio de Tracking ===")
        
        # Usar un número de tracking de prueba
        test_tracking = "1234567890"
        
        soap_body = f"""
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:trac="http://scxgxtt.phx-dc.dhl.com/glDHLExpressTrack/providers/services/trackShipment" xmlns:dhl="http://www.dhl.com">
    <soapenv:Header>
        {self.get_auth_header()}
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
                        <ArrayOfAWBNumberItem>{test_tracking}</ArrayOfAWBNumberItem>
                    </AWBNumber>
                    <LevelOfDetails>ALL_CHECK_POINTS</LevelOfDetails>
                    <PiecesEnabled>B</PiecesEnabled>
                </dhl:TrackingRequest>
            </trackingRequest>
        </trac:trackShipmentRequest>
    </soapenv:Body>
</soapenv:Envelope>"""
        
        headers = {
            'Content-Type': 'text/xml',
            'SOAPAction': 'glDHLExpressTrack_providers_services_trackShipment_Binder_trackShipmentRequest'
        }
        
        try:
            response = requests.post(
                self.endpoints["tracking"],
                headers=headers,
                data=soap_body,
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Length: {len(response.text)}")
            print(f"First 500 chars: {response.text[:500]}")
            
            if response.status_code == 200:
                return self.analyze_tracking_response(response.text)
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "response": response.text
                }
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def test_rate_service(self):
        """Prueba el servicio de cotización"""
        print("\n=== Probando servicio de Rate ===")
        
        soap_body = f"""
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:rat="http://scxgxtt.phx-dc.dhl.com/euExpressRateBook/RateMsgRequest">
    <soapenv:Header>
        {self.get_auth_header()}
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
                        <StreetLines>Test Address</StreetLines>
                        <City>Test City</City>
                        <StateOrProvinceCode>XX</StateOrProvinceCode>
                        <PostalCode>12345</PostalCode>
                        <CountryCode>US</CountryCode>
                    </Shipper>
                    <Recipient>
                        <StreetLines>Test Address</StreetLines>
                        <City>Test City</City>
                        <PostalCode>54321</PostalCode>
                        <CountryCode>US</CountryCode>
                    </Recipient>
                </Ship>
                <Packages>
                    <RequestedPackages number="1">
                        <Weight>
                            <Value>1.5</Value>
                        </Weight>
                        <Dimensions>
                            <Length>10</Length>
                            <Width>10</Width>
                            <Height>10</Height>
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
</soapenv:Envelope>"""
        
        headers = {
            'Content-Type': 'text/xml',
            'SOAPAction': 'euExpressRateBook_providerServices_ShipmentHandlingServices_Binder_getRateRequest'
        }
        
        try:
            response = requests.post(
                self.endpoints["rate"],
                headers=headers,
                data=soap_body,
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Length: {len(response.text)}")
            print(f"First 500 chars: {response.text[:500]}")
            
            if response.status_code == 200:
                return self.analyze_rate_response(response.text)
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "response": response.text
                }
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def analyze_epod_response(self, response_text):
        """Analiza la respuesta del servicio ePOD"""
        try:
            root = ET.fromstring(response_text)
            
            # Buscar diferentes elementos en la respuesta
            analysis = {
                "has_fault": "fault" in response_text.lower(),
                "has_error": "error" in response_text.lower(),
                "has_pdf_data": False,
                "namespaces": [],
                "elements": []
            }
            
            # Obtener namespaces
            for elem in root.iter():
                if elem.tag.startswith('{'):
                    namespace = elem.tag.split('}')[0] + '}'
                    if namespace not in analysis["namespaces"]:
                        analysis["namespaces"].append(namespace)
            
            # Buscar elementos importantes
            for elem in root.iter():
                tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                analysis["elements"].append({
                    "tag": tag_name,
                    "text": elem.text[:100] if elem.text else None,
                    "attributes": dict(elem.attrib)
                })
                
                # Buscar datos PDF
                if elem.get('Img') or (elem.text and len(elem.text) > 100 and elem.text.startswith('JVBERi')):
                    analysis["has_pdf_data"] = True
            
            return analysis
            
        except ET.ParseError as e:
            return {
                "success": False,
                "error": f"XML Parse Error: {str(e)}",
                "response_preview": response_text[:1000]
            }
    
    def analyze_tracking_response(self, response_text):
        """Analiza la respuesta del servicio de tracking"""
        try:
            root = ET.fromstring(response_text)
            
            analysis = {
                "has_fault": "fault" in response_text.lower(),
                "has_error": "error" in response_text.lower(),
                "tracking_events": [],
                "shipment_info": {},
                "elements": []
            }
            
            # Buscar elementos de tracking
            for elem in root.iter():
                tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                analysis["elements"].append({
                    "tag": tag_name,
                    "text": elem.text[:100] if elem.text else None,
                    "attributes": dict(elem.attrib)
                })
            
            return analysis
            
        except ET.ParseError as e:
            return {
                "success": False,
                "error": f"XML Parse Error: {str(e)}",
                "response_preview": response_text[:1000]
            }
    
    def analyze_rate_response(self, response_text):
        """Analiza la respuesta del servicio de cotización"""
        try:
            root = ET.fromstring(response_text)
            
            analysis = {
                "has_fault": "fault" in response_text.lower(),
                "has_error": "error" in response_text.lower(),
                "rates_found": [],
                "elements": []
            }
            
            # Buscar elementos de cotización
            for elem in root.iter():
                tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                analysis["elements"].append({
                    "tag": tag_name,
                    "text": elem.text[:100] if elem.text else None,
                    "attributes": dict(elem.attrib)
                })
            
            return analysis
            
        except ET.ParseError as e:
            return {
                "success": False,
                "error": f"XML Parse Error: {str(e)}",
                "response_preview": response_text[:1000]
            }
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas"""
        results = {}
        
        print("Iniciando pruebas con credenciales DHL...")
        print(f"Username: {self.username}")
        print(f"Password: {self.password}")
        print(f"Base URL: {self.base_url}")
        
        # Probar ePOD
        results["epod"] = self.test_epod_service()
        
        # Probar Tracking
        results["tracking"] = self.test_tracking_service()
        
        # Probar Rate
        results["rate"] = self.test_rate_service()
        
        # Guardar resultados
        with open('/Users/noelsantamaria/Develop/dhl-front-client/test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print("\n=== RESUMEN DE RESULTADOS ===")
        for service, result in results.items():
            print(f"{service.upper()}: {'✓' if result.get('success') != False else '✗'}")
            if result.get('error'):
                print(f"  Error: {result['error']}")
        
        return results

if __name__ == "__main__":
    tester = DHLCredentialTester()
    tester.run_all_tests()
