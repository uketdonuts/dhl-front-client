#!/usr/bin/env python3
"""
Script simple para probar el formato SOAP de DHL directamente
sin dependencias de Django.
"""

import requests
from datetime import datetime, timedelta

def test_dhl_soap_direct():
    """Probar el SOAP request directamente"""
    
    print("=== PRUEBA DIRECTA DEL SOAP REQUEST DHL ===")
    print()
    
    # Generar MessageReference único
    message_ref = f"JCAIN{int(datetime.now().timestamp())}"
    print(f"MessageReference: {message_ref}")
    
    # SOAP request usando el formato exacto del ejemplo
    soap_body = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ship="http://scxgxtt.phx-dc.dhl.com/euExpressRateBook/ShipmentMsgRequest">
   <soapenv:Header>
      <wsse:Security soapenv:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
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
               <ServiceType>P</ServiceType>
               <Billing>
                  <ShipperAccountNumber>706065602</ShipperAccountNumber>
                  <ShippingPaymentType>S</ShippingPaymentType>
                  <DutyAndTaxPayerAccountNumber>706065602</DutyAndTaxPayerAccountNumber>
               </Billing>
               <SpecialServices>
                  <Service>
                     <ServiceType>DD</ServiceType>
                  </Service>
               </SpecialServices>
               <Currency>USD</Currency>
               <UnitOfMeasurement>SU</UnitOfMeasurement>
               <LabelType>ZPL</LabelType>
               <LabelTemplate>ECOM26_84_001</LabelTemplate>
               <ArchiveLabelTemplate>ARCH_8x4</ArchiveLabelTemplate>
            </ShipmentInfo>
            <ShipTimestamp>{(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SGMT+00:00')}</ShipTimestamp>
            <PickupLocationCloseTime>18:00</PickupLocationCloseTime>
            <SpecialPickupInstruction>I DECLARE ALL INFORMATION TRUE And CORRECT</SpecialPickupInstruction>
            <PickupLocation>Test Location</PickupLocation>
            <PaymentInfo>DDP</PaymentInfo>
            <InternationalDetail>
               <Commodities>
                  <Description>Test Package - Electronic Components</Description>
                  <CustomsValue>54.87</CustomsValue>
               </Commodities>
               <Content>NON_DOCUMENTS</Content>
            </InternationalDetail>
            <Ship>
               <Shipper>
                  <Contact>
                     <PersonName>Test Shipper</PersonName>
                     <CompanyName>Test Company LATINOAMERICA</CompanyName>
                     <PhoneNumber>507431-2600</PhoneNumber>
                     <EmailAddress>shipper_test@dhl.com</EmailAddress>
                     <MobilePhoneNumber>507431-2600</MobilePhoneNumber>
                  </Contact>
                  <Address>
                     <StreetLines>Test Address, Building 1</StreetLines>
                     <StreetName>Test Street</StreetName>
                     <StreetNumber>Building 1</StreetNumber>
                     <StreetLines2>.</StreetLines2>
                     <StreetLines3>Floor 1</StreetLines3>
                     <City>Test City</City>
                     <StateOrProvinceCode>XX</StateOrProvinceCode>
                     <PostalCode>0</PostalCode>
                     <CountryCode>US</CountryCode>
                  </Address>
               </Shipper>
               <Recipient>
                  <Contact>
                     <PersonName>Test Recipient Company</PersonName>
                     <CompanyName>Test Recipient Company</CompanyName>
                     <PhoneNumber>1234567890</PhoneNumber>
                     <EmailAddress>recipient_test@example.com</EmailAddress>
                     <MobilePhoneNumber>1234567890</MobilePhoneNumber>
                  </Contact>
                  <Address>
                     <StreetLines>Test Recipient Address</StreetLines>
                     <StreetName>Test Street</StreetName>
                     <StreetLines2>Apt 1</StreetLines2>
                     <City>Test City</City>
                     <PostalCode>0</PostalCode>
                     <CountryCode>US</CountryCode>
                  </Address>
                  <RegistrationNumbers>
                     <RegistrationNumber>
                        <Number>123456789</Number>
                        <NumberTypeCode>VAT</NumberTypeCode>
                        <NumberIssuerCountryCode>US</NumberIssuerCountryCode>
                     </RegistrationNumber>
                  </RegistrationNumbers>
               </Recipient>
            </Ship>
            <Packages>
               <RequestedPackages number="1">
                  <Weight>0.3</Weight>
                  <Dimensions>
                     <Length>21</Length>
                     <Width>16</Width>
                     <Height>11</Height>
                  </Dimensions>
                  <CustomerReferences>{message_ref}</CustomerReferences>
                  <CustomerReferenceType>SH</CustomerReferenceType>
               </RequestedPackages>
            </Packages>
         </RequestedShipment>
      </ship:ShipmentRequest>
   </soapenv:Body>
</soapenv:Envelope>"""
    
    # Headers
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'euExpressRateBook_providerServices_ShipmentHandlingServices_Binder_createShipmentRequest'
    }
    
    # URL del endpoint
    url = "https://wsbexpress.dhl.com:443/sndpt/expressRateBook"
    
    print("Enviando request a:", url)
    print("Content-Type:", headers['Content-Type'])
    print("SOAPAction:", headers['SOAPAction'])
    print()
    
    try:
        print("Realizando request...")
        response = requests.post(url, headers=headers, data=soap_body, timeout=30)
        
        print("=== RESPUESTA ===")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            print("✅ Request exitoso!")
            print("Respuesta XML:")
            print(response.text[:1000])  # Primeros 1000 caracteres
            print("...")
            print()
            
            # Intentar parsear la respuesta
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                
                # Buscar número de tracking
                tracking_elements = root.findall('.//AWBNumber') + root.findall('.//*[contains(local-name(), "AWBNumber")]')
                if tracking_elements:
                    print(f"🎉 ¡Número de tracking encontrado!: {tracking_elements[0].text}")
                
                # Buscar errores
                fault_elements = root.findall('.//{http://schemas.xmlsoap.org/soap/envelope/}Fault')
                if fault_elements:
                    print("❌ Se encontraron errores SOAP:")
                    for fault in fault_elements:
                        fault_code = fault.find('.//{http://schemas.xmlsoap.org/soap/envelope/}faultcode')
                        fault_string = fault.find('.//{http://schemas.xmlsoap.org/soap/envelope/}faultstring')
                        if fault_code is not None:
                            print(f"  Fault Code: {fault_code.text}")
                        if fault_string is not None:
                            print(f"  Fault String: {fault_string.text}")
                
            except Exception as e:
                print(f"Error parseando XML: {str(e)}")
                
        else:
            print(f"❌ Request falló con código {response.status_code}")
            print("Respuesta:")
            print(response.text[:1000])
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error en el request: {str(e)}")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dhl_soap_direct()
