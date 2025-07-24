import requests
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
        
        # Configuración de endpoints DHL - API REST moderna (solo JSON)
        # Solo endpoints de producción
        self.endpoints = {
            "rate": "https://express.api.dhl.com/mydhlapi/rates",
            "tracking": "https://express.api.dhl.com/mydhlapi/shipments/{}/tracking", 
            "shipment": "https://express.api.dhl.com/mydhlapi/shipments",
            "pickup": "https://express.api.dhl.com/mydhlapi/pickups",
            "products": "https://express.api.dhl.com/mydhlapi/products",
            "address": "https://express.api.dhl.com/mydhlapi/address-validate",
            "epod": "https://express.api.dhl.com/mydhlapi/shipments/{}/proof-of-delivery"
        }
        
        logger.info(f"REST Endpoints configured: {self.endpoints}")

    def _get_rest_headers(self):
        """Genera headers para requests REST JSON"""
        import base64
        credentials = f"{self.username}:{self.password}"
        auth_header = base64.b64encode(credentials.encode()).decode()
        
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {auth_header}'
        }
    
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

    def get_ePOD(self, shipment_id, account_number=None, content_type="epod-summary"):
        """
        Obtiene comprobante de entrega electrónico usando la API REST moderna de DHL
        
        Args:
            shipment_id (str): Número de tracking del envío
            account_number (str): Número de cuenta del shipper (opcional)
            content_type (str): Tipo de contenido ePOD según documentación oficial DHL:
                               - "epod-detail": Detalle completo
                               - "epod-summary": Resumen (default)
                               - "epod-detail-esig": Detalle con firma electrónica
                               - "epod-summary-esig": Resumen con firma electrónica
                               - "epod-table": Formato tabla
                               - "epod-table-detail": Tabla con detalle
                               - "epod-table-esig": Tabla con firma electrónica
        """
        try:
            logger.info(f"Getting ePOD for shipment: {shipment_id} with content type: {content_type}")
            
            # Validar parámetros
            if not shipment_id or not str(shipment_id).strip():
                return {"success": False, "message": "Número de tracking requerido"}
            
            # Validar tipo de contenido según documentación oficial
            valid_content_types = [
                "epod-detail", "epod-summary", "epod-detail-esig", 
                "epod-summary-esig", "epod-table", "epod-table-detail", "epod-table-esig"
            ]
            if content_type not in valid_content_types:
                logger.warning(f"Invalid content type {content_type}, using default 'epod-summary'")
                content_type = "epod-summary"
            
            # Limpiar el número de tracking
            shipment_id = str(shipment_id).strip()
            
            # Usar cuenta por defecto si no se proporciona
            account_to_use = account_number if account_number else '706014493'
            logger.info(f"ePOD: Using account_number={account_number}, final account_to_use={account_to_use}")
            
            # Formatear la URL con el número de tracking
            endpoint_url = self.endpoints["epod"].format(shipment_id)
            logger.info(f"Making ePOD request to: {endpoint_url}")
            
            # Headers para API REST
            headers = self._get_rest_headers()
            
            # Parámetros de query
            params = {
                "shipperAccountNumber": account_to_use,
                "content": content_type
            }
            
            logger.debug(f"Request Headers: {headers}")
            logger.debug(f"Request Params: {params}")
            
            try:
                response = requests.get(
                    endpoint_url,
                    headers=headers,
                    params=params,
                    verify=False,
                    timeout=30
                )
                
                logger.info(f"Response Status: {response.status_code}")
                logger.debug(f"Response Headers: {dict(response.headers)}")
                
                # Parsear la respuesta REST
                result = self._parse_rest_response(response, "ePOD")
                logger.info(f"Parse Result success: {result.get('success', False)}")
                return result
                    
            except requests.exceptions.Timeout:
                logger.error(f"Timeout error for ePOD {shipment_id}")
                return {
                    "success": False,
                    "message": "Timeout al conectar con DHL. Intenta más tarde.",
                    "error_code": "TIMEOUT_ERROR",
                    "suggestion": "Reintentar en unos minutos"
                }
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error for ePOD {shipment_id}")
                return {
                    "success": False,
                    "message": "Error de conexión con DHL. Verifica tu conexión a internet.",
                    "error_code": "CONNECTION_ERROR",
                    "suggestion": "Verificar conexión a internet y reintentar"
                }
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error for ePOD {shipment_id}: {str(e)}")
                return {
                    "success": False,
                    "message": f"Error en la petición a DHL: {str(e)}",
                    "error_code": "REQUEST_ERROR",
                    "suggestion": "Reintentar más tarde"
                }
            
        except Exception as e:
            logger.exception(f"Error in get_ePOD for {shipment_id}")
            return {
                "success": False, 
                "message": f"Error en get_ePOD: {str(e)}",
                "error_code": "GENERAL_ERROR",
                "suggestion": "Contactar soporte técnico"
            }

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
        Obtiene cotización de tarifas usando la API REST moderna de DHL
        
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
            
            # Determinar si es declarable a aduana
            is_customs_declarable = content_type == "P"  # NON_DOCUMENTS requiere declaración
            
            logger.info(f"Using content type: {content_type} (customs declarable: {is_customs_declarable})")
            
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
            
            # Limpiar y preparar datos
            origin_city = self._clean_text(origin.get('city', 'Panama'))
            origin_postal = origin.get('postal_code', '0')
            origin_country = origin.get('country', 'PA')
            origin_state = origin.get('state', 'PA')
            
            dest_city = self._clean_text(destination.get('city', 'MIA'))
            dest_postal = destination.get('postal_code', '25134')
            dest_country = destination.get('country', 'CO')  # Cambiar default de US a CO
            
            # Preparar datos para API REST
            import base64
            credentials = f"{self.username}:{self.password}"
            auth_header = base64.b64encode(credentials.encode()).decode()
            
            # Headers para API REST
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Basic {auth_header}'
            }
            
            # Estructura de datos para API REST de DHL
            # Calcular fecha de envío (próximo día laboral para asegurar disponibilidad)
            from datetime import datetime, timedelta
            
            # Encontrar el próximo día laboral (lunes a viernes)
            current_date = datetime.now()
            days_ahead = 1
            
            # Si es viernes, sábado o domingo, ir al próximo lunes
            while True:
                next_date = current_date + timedelta(days=days_ahead)
                if next_date.weekday() < 5:  # 0=Monday, 6=Sunday (0-4 son días laborales)
                    break
                days_ahead += 1
            
            shipping_date = next_date.strftime('%Y-%m-%dT13:00:00GMT+00:00')
            logger.info(f"Using shipping date: {shipping_date} (weekday: {next_date.strftime('%A')}) - weekday number: {next_date.weekday()}")
            
            request_data = {
                "customerDetails": {
                    "shipperDetails": {
                        "postalCode": origin_postal,
                        "cityName": origin_city,
                        "countryCode": origin_country
                    },
                    "receiverDetails": {
                        "postalCode": dest_postal,
                        "cityName": dest_city,
                        "countryCode": dest_country
                    }
                },
                "accounts": [
                    {
                        "typeCode": "shipper",
                        "number": account_to_use
                    }
                ],
                "plannedShippingDateAndTime": shipping_date,
                "unitOfMeasurement": "metric",
                "isCustomsDeclarable": is_customs_declarable,
                "packages": [
                    {
                        "typeCode": "3BX",
                        "weight": weight_to_use,
                        "dimensions": {
                            "length": dimensions.get('length', 1),
                            "width": dimensions.get('width', 1),
                            "height": dimensions.get('height', 1)
                        }
                    }
                ]
            }
            
            logger.info(f"Making rate request to: {self.endpoints['rate']}")
            logger.info(f"DEBUGGING - Origin country: {origin_country}")
            logger.info(f"DEBUGGING - Destination country: {dest_country}")
            logger.info(f"DEBUGGING - Request data receiverDetails countryCode: {request_data['customerDetails']['receiverDetails']['countryCode']}")
            logger.debug(f"Request data: {request_data}")
            
            response = requests.post(
                self.endpoints["rate"],
                headers=headers,
                json=request_data,
                verify=False,
                timeout=30
            )
            
            logger.info(f"Rate response status: {response.status_code}")
            
            # Para debugging, solo loggear los primeros 500 caracteres si es error
            if response.status_code >= 400:
                logger.error(f"DHL API Error {response.status_code} - Response preview: {response.text[:500]}")
            else:
                logger.debug(f"Rate response: {response.text[:200]}...")
            
            result = self._parse_rest_response(response, "Rate")
            
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
                    'is_customs_declarable': is_customs_declarable,
                    'account_number': account_to_use
                }
                
                result['weight_breakdown'] = weight_breakdown
                result['content_info'] = content_info
                
                logger.info(f"Rate calculation successful: {len(result['rates'])} rates found")
                for rate in result['rates']:
                    logger.info(f"  - {rate.get('service_name', 'Unknown')}: {rate.get('currency', 'USD')} {rate.get('total_charge', 0)}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión en get_rate: {str(e)}")
            return {
                'success': False,
                'error_type': 'connection_error',
                'message': f'Error de conexión: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error inesperado en get_rate: {str(e)}")
            return {
                'success': False,
                'error_type': 'unexpected_error',
                'message': f'Error inesperado: {str(e)}'
            }
    
    def get_tracking(self, tracking_number):
        """Obtiene información de seguimiento usando la API REST de DHL"""
        try:
            logger.info(f"Starting tracking request for {tracking_number}")
            logger.info(f"Environment: {self.environment}")
            
            # Validar formato del número de tracking
            if not tracking_number or not str(tracking_number).strip():
                logger.error("Empty tracking number")
                return {"success": False, "message": "Número de tracking requerido"}
            
            # Limpiar el número de tracking
            tracking_number = str(tracking_number).strip()
            
            # Formatear la URL con el número de tracking
            endpoint_url = self.endpoints["tracking"].format(tracking_number)
            logger.info(f"Making tracking request to: {endpoint_url}")
            
            # Headers para API REST
            headers = self._get_rest_headers()
            
            # Parámetros de query opcionales - TEST VERSION - usando valores válidos
            params = {
                "trackingView": "all-checkpoints",  # Valor válido según API 
                "levelOfDetail": "all"  # Valor válido: shipment, piece, all - UPDATED
            }
            
            logger.info(f"TRACKING DEBUG: Using params: {params}")  # Debug adicional
            
            logger.debug(f"Request Headers: {headers}")
            logger.debug(f"Request Params: {params}")
            
            try:
                response = requests.get(
                    endpoint_url,
                    headers=headers,
                    params=params,
                    verify=False,
                    timeout=30
                )
                
                logger.info(f"Response Status: {response.status_code}")
                logger.debug(f"Response Headers: {dict(response.headers)}")
                logger.debug(f"Response Content: {response.text}")
                
                # Parsear la respuesta REST
                result = self._parse_rest_response(response, "Tracking")
                logger.info(f"Parse Result: {result}")
                return result
                    
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
        Crea un nuevo envío usando la API REST de DHL
        
        Args:
            shipment_data: Datos del envío
            content_type: Tipo de contenido - "P" para NON_DOCUMENTS, "D" para DOCUMENTS
        """
        try:
            logger.info(f"Creating shipment with content type: {content_type}")
            
            # Validar tipo de contenido
            if content_type not in ["P", "D"]:
                content_type = "P"  # Default a NON_DOCUMENTS
            
            # Determinar si es declarable a aduana
            is_customs_declarable = content_type == "P"
            
            # Extraer datos del formulario
            shipper = shipment_data.get('shipper', {})
            recipient = shipment_data.get('recipient', {})
            packages = shipment_data.get('packages', [])
            service_type = shipment_data.get('service', 'P')
            account_number = shipment_data.get('account_number', '706014493')
            
            # Validar que haya al menos un paquete
            if not packages or len(packages) == 0:
                return {
                    "success": False,
                    "message": "Debe incluir al menos un paquete en el envío",
                    "error_type": "validation_error",
                    "error_code": "NO_PACKAGES"
                }
            
            # Validar que todos los paquetes tengan peso válido
            for i, package in enumerate(packages):
                weight = package.get('weight', 0)
                if not weight or float(weight) <= 0:
                    return {
                        "success": False,
                        "message": f"El paquete {i+1} debe tener un peso mayor que 0",
                        "error_type": "validation_error",
                        "error_code": "INVALID_WEIGHT"
                    }
            
            # Calcular fecha de envío (mañana para asegurar disponibilidad)
            from datetime import datetime, timedelta
            tomorrow = datetime.now() + timedelta(days=1)
            shipping_date = tomorrow.strftime('%Y-%m-%dT13:00:00GMT+00:00')
            
            # Preparar el payload para la API REST
            shipment_payload = {
                "plannedShippingDateAndTime": shipping_date,
                "pickup": {
                    "isRequested": False
                },
                "productCode": service_type,
                "accounts": [
                    {
                        "typeCode": "shipper",
                        "number": account_number
                    }
                ],
                "customerDetails": {
                    "shipperDetails": {
                        "postalAddress": {
                            "postalCode": shipper.get('postalCode', '0'),
                            "cityName": self._clean_text(shipper.get('city', 'Ciudad')),
                            "countryCode": shipper.get('country', 'PA'),
                            "addressLine1": self._clean_text(shipper.get('address', 'Dirección'))
                        },
                        "contactInformation": {
                            "phone": self._clean_phone(shipper.get('phone', '50712345678')),
                            "companyName": self._clean_text(shipper.get('company', 'Empresa')),
                            "fullName": self._clean_text(shipper.get('name', 'Nombre')),
                            "email": shipper.get('email', 'shipper@example.com')
                        }
                    },
                    "receiverDetails": {
                        "postalAddress": {
                            "postalCode": recipient.get('postalCode', '0'),
                            "cityName": self._clean_text(recipient.get('city', 'Ciudad')),
                            "countryCode": recipient.get('country', 'CO'),
                            "addressLine1": self._clean_text(recipient.get('address', 'Dirección'))
                        },
                        "contactInformation": {
                            "phone": self._clean_phone(recipient.get('phone', '12345678901')),
                            "companyName": self._clean_text(recipient.get('company', 'Empresa')),
                            "fullName": self._clean_text(recipient.get('name', 'Nombre')),
                            "email": recipient.get('email', 'recipient@example.com')
                        }
                    }
                },
                "content": {
                    "packages": [],
                    "isCustomsDeclarable": is_customs_declarable,
                    "declaredValue": 0,
                    "declaredValueCurrency": "USD",
                    "description": "General Merchandise",
                    "unitOfMeasurement": "metric"
                }
            }
            
            # Agregar incoterm si es declarable
            if is_customs_declarable:
                shipment_payload["content"]["incoterm"] = "DAP"  # Delivered At Place - el más común
            
            # Agregar paquetes
            total_value = 0
            for i, package in enumerate(packages):
                package_data = {
                    "typeCode": "3BX",
                    "weight": float(package.get('weight', 1)),
                    "dimensions": {
                        "length": float(package.get('length', 10)),
                        "width": float(package.get('width', 10)),
                        "height": float(package.get('height', 10))
                    }
                }
                
                # Agregar valor declarado si es customs declarable
                if is_customs_declarable:
                    package_value = float(package.get('value', 100))
                    total_value += package_value
                    package_data["customerReferences"] = [
                        {
                            "value": f"Package {i+1}",
                            "typeCode": "CU"
                        }
                    ]
                
                shipment_payload["content"]["packages"].append(package_data)
            
            # Actualizar valor total declarado
            shipment_payload["content"]["declaredValue"] = total_value
            
            # Si es customs declarable, agregar detalles de commodities
            if is_customs_declarable:
                shipment_payload["content"]["exportDeclaration"] = {
                    "lineItems": [
                        {
                            "number": 1,
                            "description": "General Merchandise",
                            "price": total_value,
                            "quantity": {
                                "value": max(1, len(packages)),  # Asegurar que sea >= 1
                                "unitOfMeasurement": "PCS"
                            },
                            "commodityCodes": [
                                {
                                    "typeCode": "outbound",
                                    "value": "999999"
                                }
                            ],
                            "exportReasonType": "permanent",
                            "manufacturerCountry": shipper.get('country', 'PA'),
                            "weight": {
                                "netValue": sum(float(p.get('weight', 1)) for p in packages),
                                "grossValue": sum(float(p.get('weight', 1)) for p in packages)
                            }
                        }
                    ],
                    "invoice": {
                        "number": f"INV-{int(datetime.now().timestamp())}",
                        "date": datetime.now().strftime('%Y-%m-%d'),
                        "totalNetWeight": sum(float(p.get('weight', 1)) for p in packages),
                        "totalGrossWeight": sum(float(p.get('weight', 1)) for p in packages),
                        "customerReferences": [
                            {
                                "value": f"REF-{int(datetime.now().timestamp())}",
                                "typeCode": "CU"
                            }
                        ]
                    }
                }
            
            # Headers para API REST
            headers = self._get_rest_headers()
            
            logger.info(f"Making shipment request to: {self.endpoints['shipment']}")
            logger.debug(f"Request payload: {shipment_payload}")
            
            response = requests.post(
                self.endpoints["shipment"],
                headers=headers,
                json=shipment_payload,
                verify=False,
                timeout=30
            )
            
            logger.info(f"Shipment response status: {response.status_code}")
            
            result = self._parse_rest_response(response, "Shipment")
            
            # Agregar información del tipo de contenido a la respuesta
            if result.get('success'):
                content_info = {
                    'content_type': content_type,
                    'is_customs_declarable': is_customs_declarable,
                    'description': 'Paquetes con productos' if content_type == 'P' else 'Solo documentos'
                }
                result['content_info'] = content_info
            
            return result
            
        except Exception as e:
            logger.error(f"Error en create_shipment: {str(e)}")
            return {
                "success": False,
                "message": f"Error en create_shipment: {str(e)}",
                "error_type": "unexpected_error"
            }

    def validate_account(self, account_number):
        """
        Valida si una cuenta DHL existe y está activa usando la API REST
        
        Args:
            account_number (str): Número de cuenta DHL a validar
            
        Returns:
            bool: True si la cuenta es válida, False en caso contrario
        """
        try:
            # Hacer una petición simple de productos para validar la cuenta
            headers = self._get_rest_headers()
            
            # Parámetros mínimos para validar cuenta
            params = {
                'accountNumber': account_number,
                'originCountryCode': 'PA',
                'destinationCountryCode': 'CO',
                'weight': 1,
                'length': 10,
                'width': 10,
                'height': 10,
                'plannedShippingDate': datetime.now().strftime('%Y-%m-%d'),
                'isCustomsDeclarable': False,
                'unitOfMeasurement': 'metric'
            }
            
            response = requests.get(
                self.endpoints['products'],
                headers=headers,
                params=params,
                verify=False,
                timeout=10
            )
            
            # Si no hay error de autorización o cuenta inválida, la cuenta es válida
            if response.status_code == 200:
                return True
            elif response.status_code == 400:
                # Revisar el mensaje de error
                try:
                    error_data = response.json()
                    error_message = error_data.get('detail', '').lower()
                    if 'account' in error_message and ('invalid' in error_message or 'not found' in error_message):
                        return False
                except:
                    pass
                return True  # Otros errores 400 no necesariamente significan cuenta inválida
            else:
                # Para otros códigos de error, asumir que la cuenta es válida
                return True
            
        except Exception as e:
            logger.error(f"Error validando cuenta DHL {account_number}: {str(e)}")
            return False
    
    def _parse_rest_response(self, response, service_type):
        """Parsea la respuesta JSON de la API REST de DHL"""
        try:
            if response.status_code in [200, 201]:  # 200 = OK, 201 = Created
                try:
                    data = response.json()
                except ValueError as e:
                    logger.error(f"Invalid JSON in successful response: {str(e)}")
                    return {
                        "success": False,
                        "error_type": "json_parse_error",
                        "message": "Respuesta exitosa pero JSON inválido",
                        "raw_response": response.text[:500]
                    }
                
                if service_type == "Rate":
                    return self._parse_rest_rate_response(data)
                elif service_type == "Tracking":
                    return self._parse_rest_tracking_response(data)
                elif service_type == "ePOD":
                    return self._parse_rest_epod_response(data)
                elif service_type == "Shipment":
                    # Para shipments exitosos, extraer el tracking number
                    return {
                        "success": True,
                        "tracking_number": data.get('shipmentTrackingNumber', ''),
                        "shipment_data": data,
                        "message": "Envío creado exitosamente"
                    }
                else:
                    return {
                        "success": True,
                        "data": data,
                        "message": "Respuesta procesada exitosamente"
                    }
            
            elif response.status_code >= 400:
                # Intentar parsear error JSON
                try:
                    error_data = response.json()
                    error_message = error_data.get('detail', error_data.get('message', 'Error desconocido'))
                    
                    # Manejo específico para tracking 404 - No data found
                    if response.status_code == 404 and service_type == "Tracking":
                        return {
                            "success": False,
                            "tracking_info": {},
                            "events": [],
                            "piece_details": [],
                            "total_events": 0,
                            "total_pieces": 0,
                            "message": "Error DHL API: No data found",
                            "error_code": "404",
                            "suggestion": "Reintentar más tarde",
                            "raw_response": response.text[:500]
                        }
                    
                    # Manejo específico para errores 422 (Validation Error)
                    if response.status_code == 422:
                        additional_details = error_data.get('additionalDetails', [])
                        if additional_details:
                            # Mejorar los mensajes de error para que sean más comprensibles
                            friendly_messages = []
                            for detail in additional_details:
                                if 'pickup' in detail and 'isRequested' in detail:
                                    friendly_messages.append("Configuración de pickup inválida")
                                elif 'pickup' in detail and 'accountNumber' in detail:
                                    friendly_messages.append("Número de cuenta en pickup no permitido")
                                elif 'pickup' in detail and 'typeCode' in detail:
                                    friendly_messages.append("Tipo de pickup inválido")
                                elif 'quantity/value' in detail and 'not greater or equal to 1' in detail:
                                    friendly_messages.append("La cantidad debe ser mayor o igual a 1")
                                elif 'packages' in detail and 'expected minimum item count: 1' in detail:
                                    friendly_messages.append("Debe incluir al menos un paquete")
                                else:
                                    friendly_messages.append(detail)
                            
                            error_message = f"Errores de validación: {'; '.join(friendly_messages)}"
                    
                    return {
                        "success": False,
                        "error_code": str(response.status_code),
                        "message": f"Error DHL API: {error_message}",
                        "http_status": response.status_code,
                        "error_data": error_data
                    }
                except ValueError as json_error:
                    logger.error(f"Invalid JSON in error response: {str(json_error)}")
                    return {
                        "success": False,
                        "error_code": str(response.status_code),
                        "message": f"Error HTTP {response.status_code}",
                        "http_status": response.status_code,
                        "raw_response": response.text[:500]
                    }
            
            else:
                return {
                    "success": False,
                    "error_code": str(response.status_code),
                    "message": f"Respuesta inesperada: {response.status_code}",
                    "http_status": response.status_code
                }
                
        except Exception as e:
            logger.error(f"Error parsing REST response: {str(e)}")
            return {
                "success": False,
                "error_type": "parse_error",
                "message": f"Error procesando respuesta: {str(e)}",
                "raw_response": response.text[:500] if response else "No response"
            }
    
    def _extract_location_info(self, location_details):
        """Extrae información de ubicación de diferentes formatos"""
        try:
            if not location_details:
                return "Unknown"
            
            # Para shipperDetails/receiverDetails
            if 'postalAddress' in location_details:
                postal = location_details['postalAddress']
                city = postal.get('cityName', '')
                country = postal.get('countryCode', '')
                service_areas = location_details.get('serviceArea', [])
                
                if service_areas and len(service_areas) > 0:
                    return service_areas[0].get('description', f"{city}, {country}".strip(', '))
                return f"{city}, {country}".strip(', ') or "Unknown"
            
            # Para eventos de tracking con location/address
            elif 'address' in location_details:
                address = location_details['address']
                return address.get('addressLocality', 'Unknown')
            
            # Otros formatos
            else:
                return str(location_details) if location_details else "Unknown"
                
        except Exception as e:
            logger.error(f"Error extracting location info: {str(e)}")
            return "Unknown"
    
    def _parse_rest_tracking_response(self, data):
        """Parsea la respuesta JSON de tracking de la API REST"""
        try:
            # Validar que data sea un diccionario
            if not isinstance(data, dict):
                logger.error(f"Tracking response data is not a dict: {type(data)}")
                return {
                    "success": False,
                    "tracking_info": {},
                    "events": [],
                    "piece_details": [],
                    "total_events": 0,
                    "total_pieces": 0,
                    "message": "Error DHL API: Formato de respuesta inválido",
                    "error_code": "INVALID_FORMAT",
                    "suggestion": "Reintentar más tarde",
                    "raw_response": str(data)[:500]
                }
            
            # Estructura de respuesta de tracking de DHL REST API
            shipments = data.get('shipments', [])
            if not shipments:
                return {
                    "success": False,
                    "tracking_info": {},
                    "events": [],
                    "piece_details": [],
                    "total_events": 0,
                    "total_pieces": 0,
                    "message": "Error DHL API: No se encontró información de tracking",
                    "error_code": "NO_DATA",
                    "suggestion": "Verificar número de tracking",
                    "raw_response": str(data)[:500]
                }
            
            # Usar el primer envío
            shipment = shipments[0]
            
            # Manejar status como string o como objeto
            status = shipment.get('status', 'Unknown')
            if isinstance(status, dict):
                status_code = status.get('statusCode', 'Unknown')
                status_desc = status.get('description', 'Unknown')
            else:
                status_code = str(status)
                status_desc = str(status)
            
            # Información básica del envío
            shipment_info = {
                'tracking_number': shipment.get('shipmentTrackingNumber', shipment.get('id', '')),
                'status': status_code,
                'status_description': status_desc,
                'service': shipment.get('productCode', shipment.get('service', 'Unknown')),
                'description': shipment.get('description', 'Unknown'),
                'shipment_timestamp': shipment.get('shipmentTimestamp', ''),
                'origin': self._extract_location_info(shipment.get('shipperDetails', {})),
                'destination': self._extract_location_info(shipment.get('receiverDetails', {})),
                'total_weight': shipment.get('details', {}).get('totalWeight', {}).get('value', 0),
                'weight_unit': shipment.get('details', {}).get('totalWeight', {}).get('unitText', 'kg'),
                'number_of_pieces': shipment.get('details', {}).get('numberOfPieces', 0)
            }
            
            # Eventos de tracking
            events = []
            tracking_events = shipment.get('events', [])
            for event in tracking_events:
                event_data = {
                    'timestamp': event.get('timestamp', ''),
                    'location': self._extract_location_info(event.get('location', {})),
                    'status': event.get('description', 'Unknown'),
                    'next_steps': event.get('nextSteps', '')
                }
                events.append(event_data)
            
            # Detalles de piezas
            pieces = []
            piece_details = shipment.get('pieces', [])
            for piece in piece_details:
                piece_data = {
                    'piece_id': piece.get('id', ''),
                    'description': piece.get('description', ''),
                    'weight': piece.get('weight', {}).get('value', 0),
                    'weight_unit': piece.get('weight', {}).get('unitText', 'kg'),
                    'dimensions': piece.get('dimensions', {})
                }
                pieces.append(piece_data)
            
            return {
                "success": True,
                "tracking_number": shipment_info['tracking_number'],
                "status": shipment_info['status_description'],
                "shipment_info": {
                    "tracking_number": shipment_info['tracking_number'],
                    "status": shipment_info['status'],
                    "status_description": shipment_info['status_description'],
                    "origin": shipment_info['origin'],
                    "destination": shipment_info['destination'],
                    "service_type": shipment_info['service'],
                    "description": shipment_info['description'],
                    "shipment_timestamp": shipment_info['shipment_timestamp'],
                    "estimated_delivery": shipment_info.get('estimated_delivery', 'No disponible'),
                    "total_weight": shipment_info['total_weight'],
                    "weight_unit": shipment_info['weight_unit'],
                    "number_of_pieces": shipment_info['number_of_pieces']
                },
                "events": [
                    {
                        "description": event['status'],
                        "date": event['timestamp'].split('T')[0] if 'T' in event['timestamp'] else event['timestamp'],
                        "time": event['timestamp'].split('T')[1] if 'T' in event['timestamp'] else '',
                        "location": event['location'],
                        "additional_info": event.get('next_steps', '')
                    } for event in events
                ],
                "piece_details": pieces,
                "total_events": len(events),
                "total_pieces": len(pieces),
                "message": f"Tracking encontrado: {len(events)} eventos, {len(pieces)} piezas",
                "additional_info": {
                    "product_code": shipment_info['service'],
                    "description": shipment_info['description'],
                    "timestamp": shipment_info['shipment_timestamp']
                },
                "raw_data": data
            }
            
        except Exception as e:
            logger.error(f"Error parsing REST tracking response: {str(e)}")
            return {
                "success": False,
                "tracking_info": {},
                "events": [],
                "piece_details": [],
                "total_events": 0,
                "total_pieces": 0,
                "message": f"Error procesando respuesta de tracking: {str(e)}",
                "error_code": "PARSE_ERROR",
                "suggestion": "Reintentar más tarde",
                "raw_response": str(data)[:500] if data else "No data"
            }

    def _parse_rest_rate_response(self, data):
        """Parsea la respuesta JSON de cotización de la API REST"""
        try:
            rates = []
            
            # Verificar si hay productos disponibles
            products = data.get('products', [])
            if not products:
                return {
                    "success": False,
                    "message": "No se encontraron productos/tarifas disponibles",
                    "data": data
                }
            
            for product in products:
                rate = {}
                
                # Información del servicio
                rate['service_code'] = product.get('productCode', 'Unknown')
                rate['service_name'] = product.get('productName', f"DHL Service {product.get('productCode', 'Unknown')}")
                
                # Información financiera - usar BILLC (USD en factura)
                total_price = product.get('totalPrice', [])
                billc_price = None
                for price in total_price:
                    if price.get('currencyType') == 'BILLC':
                        billc_price = price
                        break
                
                if billc_price:
                    rate['total_charge'] = float(billc_price.get('price', 0))
                    rate['currency'] = billc_price.get('priceCurrency', 'USD')  # Usar priceCurrency no currencyType
                else:
                    rate['total_charge'] = 0.0
                    rate['currency'] = 'USD'
                
                # Desglose detallado de precios
                detailed_breakdown = product.get('detailedPriceBreakdown', [])
                charges = []
                
                # Buscar el desglose BILLC
                billc_breakdown = None
                for breakdown in detailed_breakdown:
                    if breakdown.get('currencyType') == 'BILLC':
                        billc_breakdown = breakdown
                        break
                
                if billc_breakdown:
                    for charge in billc_breakdown.get('breakdown', []):
                        charges.append({
                            'code': charge.get('serviceCode', charge.get('name', 'Unknown')),
                            'description': charge.get('name', 'Concepto'),
                            'amount': float(charge.get('price', 0))
                        })
                
                rate['charges'] = charges
                
                # Información de tiempo de entrega
                delivery_capabilities = product.get('deliveryCapabilities', {})
                pickup_capabilities = product.get('pickupCapabilities', {})
                
                if delivery_capabilities:
                    # Fecha y hora estimada de entrega
                    delivery_datetime = delivery_capabilities.get('estimatedDeliveryDateAndTime')
                    if delivery_datetime:
                        rate['delivery_date'] = delivery_datetime
                        # Extraer solo la hora si es necesario
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(delivery_datetime.replace('Z', '+00:00'))
                            rate['delivery_time'] = dt.strftime('%H:%M')
                        except:
                            rate['delivery_time'] = "Durante horario comercial"
                    
                    rate['total_transit_days'] = delivery_capabilities.get('totalTransitDays', 0)
                
                if pickup_capabilities:
                    rate['next_business_day'] = pickup_capabilities.get('nextBusinessDay', False)
                    
                    # Hora límite de recolección
                    cutoff_datetime = pickup_capabilities.get('localCutoffDateAndTime')
                    if cutoff_datetime:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(cutoff_datetime.replace('Z', '+00:00'))
                            rate['cutoff_time'] = dt.strftime('%H:%M')
                        except:
                            rate['cutoff_time'] = pickup_capabilities.get('GMTCutoffTime', 'No disponible')
                
                # Información de compatibilidad de contenido
                rate['content_compatibility'] = self.get_service_content_compatibility(rate['service_code'])
                
                rates.append(rate)
            
            # Calcular información de peso
            weight_info = {}
            if products:
                first_product = products[0]
                weight_data = first_product.get('weight', {})
                weight_info = {
                    'actual_weight': float(weight_data.get('provided', 0)),
                    'dimensional_weight': float(weight_data.get('volumetric', 0)),
                    'declared_weight': float(weight_data.get('provided', 0)),  # Asumimos que provided es el declarado
                    'chargeable_weight': max(float(weight_data.get('provided', 0)), float(weight_data.get('volumetric', 0)))
                }
            
            return {
                "success": True,
                "rates": rates,
                "total_rates": len(rates),
                "message": f"Se encontraron {len(rates)} tarifas disponibles",
                "provider": "DHL",
                "raw_data": data,
                "weight_breakdown": weight_info
            }
            
        except Exception as e:
            logger.error(f"Error parsing REST rate response: {str(e)}")
            return {
                "success": False,
                "error_type": "parse_error",
                "message": f"Error procesando respuesta de cotización: {str(e)}",
                "raw_data": data
            }

    def _parse_rest_epod_response(self, data):
        """Parsea la respuesta JSON de ePOD de la API REST"""
        try:
            # Estructura de respuesta de ePOD de DHL REST API
            documents = data.get('documents', [])
            if not documents:
                return {
                    "success": False,
                    "message": "No se encontraron documentos ePOD",
                    "data": data
                }
            
            # Procesar documentos encontrados
            processed_documents = []
            for doc in documents:
                doc_data = {
                    'type_code': doc.get('typeCode', 'POD'),
                    'encoding_format': doc.get('encodingFormat', 'PDF'),
                    'content': doc.get('content', ''),
                    'size': len(doc.get('content', '')),
                    'is_base64': True if doc.get('content', '').startswith('JVBERi') else False
                }
                processed_documents.append(doc_data)
            
            # Usar el primer documento como principal
            main_document = processed_documents[0] if processed_documents else None
            
            if main_document and main_document['content']:
                return {
                    "success": True,
                    "pdf_data": main_document['content'],
                    "format": main_document['encoding_format'],
                    "type_code": main_document['type_code'],
                    "size": main_document['size'],
                    "is_base64": main_document['is_base64'],
                    "total_documents": len(processed_documents),
                    "all_documents": processed_documents,
                    "message": f"ePOD obtenido exitosamente: {len(processed_documents)} documento(s)",
                    "raw_data": data
                }
            else:
                return {
                    "success": False,
                    "message": "Documento ePOD encontrado pero sin contenido",
                    "total_documents": len(processed_documents),
                    "all_documents": processed_documents,
                    "raw_data": data
                }
            
        except Exception as e:
            logger.error(f"Error parsing REST ePOD response: {str(e)}")
            return {
                "success": False,
                "error_type": "parse_error",
                "message": f"Error procesando respuesta de ePOD: {str(e)}",
                "raw_data": data
            }

    def get_service_content_compatibility(self, service_code):
        """
        Obtiene información sobre la compatibilidad de contenido para un servicio específico
        
        Args:
            service_code (str): Código del servicio DHL
            
        Returns:
            dict: Información sobre tipos de contenido soportados
        """
        # Mapeo de servicios DHL reales y su compatibilidad con tipos de contenido
        service_compatibility = {
            # Servicios Express principales
            'N': {
                'service_code': 'N',
                'supported_content_types': ['P', 'D'],
                'default_content_type': 'P',
                'restrictions': 'Express Worldwide - Paquetes y documentos',
                'documents': True,
                'packages': True,
                'pallets': False
            },
            'P': {
                'service_code': 'P',
                'supported_content_types': ['P', 'D'],
                'default_content_type': 'P',
                'restrictions': 'Express 12:00 - Paquetes y documentos',
                'documents': True,
                'packages': True,
                'pallets': False
            },
            'T': {
                'service_code': 'T',
                'supported_content_types': ['P', 'D'],
                'default_content_type': 'P',
                'restrictions': 'Express 9:00 - Paquetes y documentos',
                'documents': True,
                'packages': True,
                'pallets': False
            },
            'Y': {
                'service_code': 'Y',
                'supported_content_types': ['P', 'D'],
                'default_content_type': 'P',
                'restrictions': 'Express 10:30 - Paquetes y documentos',
                'documents': True,
                'packages': True,
                'pallets': False
            },
            'U': {
                'service_code': 'U',
                'supported_content_types': ['P', 'D'],
                'default_content_type': 'P',
                'restrictions': 'Express Worldwide - Paquetes y documentos',
                'documents': True,
                'packages': True,
                'pallets': False
            },
            'K': {
                'service_code': 'K',
                'supported_content_types': ['P'],
                'default_content_type': 'P',
                'restrictions': 'Express Easy - Solo paquetes',
                'documents': False,
                'packages': True,
                'pallets': False
            },
            'L': {
                'service_code': 'L',
                'supported_content_types': ['P'],
                'default_content_type': 'P',
                'restrictions': 'Logistics Services - Solo paquetes',
                'documents': False,
                'packages': True,
                'pallets': True
            },
            'Q': {
                'service_code': 'Q',
                'supported_content_types': ['P'],
                'default_content_type': 'P',
                'restrictions': 'Medical Express - Solo paquetes médicos',
                'documents': False,
                'packages': True,
                'pallets': False
            },
            # Servicios solo documentos
            'D': {
                'service_code': 'D',
                'supported_content_types': ['D'],
                'default_content_type': 'D',
                'restrictions': 'Express Documents - Solo documentos',
                'documents': True,
                'packages': False,
                'pallets': False
            },
            'W': {
                'service_code': 'W',
                'supported_content_types': ['D'],
                'default_content_type': 'D',
                'restrictions': 'Jetline - Solo documentos',
                'documents': True,
                'packages': False,
                'pallets': False
            }
        }
        
        # Si no encontramos el código específico, crear una respuesta genérica
        if service_code not in service_compatibility:
            return {
                'service_code': service_code,
                'supported_content_types': ['P', 'D'],
                'default_content_type': 'P',
                'restrictions': f'Servicio DHL {service_code} - Compatible con paquetes y documentos',
                'documents': True,
                'packages': True,
                'pallets': False
            }
        
        return service_compatibility[service_code]
