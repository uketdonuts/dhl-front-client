import requests
import base64
from datetime import datetime, timedelta
import os
import logging
import pytz
import re
import uuid
import json
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Q
from .models import CountryISO

logger = logging.getLogger(__name__)

class DHLService:
    def __init__(self, username, password, base_url, environment="production"):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.environment = environment
        # Lazy country map cache
        self._country_map_loaded = False
        self._country_name_to_code = {}
        self._country_codes_set = set()

        logger.info(f"Initializing DHLService with environment: {self.environment}")
        logger.info(f"Base URL: {self.base_url}")

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

    def _normalize_str(self, text: str) -> str:
        """Normaliza strings a MAYÚSCULAS sin acentos ni caracteres especiales."""
        if not text:
            return ""
        try:
            s = str(text).strip().upper()
            s = unicodedata.normalize('NFKD', s)
            s = ''.join(c for c in s if not unicodedata.combining(c))
            s = re.sub(r'[^A-Z ]', ' ', s)
            s = re.sub(r'\s+', ' ', s).strip()
            return s
        except Exception:
            # Fallback simple
            return str(text).strip().upper()

    def _load_country_map(self):
        """Carga countries.json una sola vez para mapear NOMBRE → ISO alpha-2."""
        if self._country_map_loaded:
            return
        try:
            project_root = os.path.dirname(os.path.dirname(__file__))
            countries_path = os.path.join(project_root, 'countries.json')
            with open(countries_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            items = data.get('data', []) if isinstance(data, dict) else []
            for item in items:
                code = str(item.get('country_code', '')).upper().strip()
                name = self._normalize_str(item.get('country_name', ''))
                if code and len(code) == 2:
                    self._country_codes_set.add(code)
                if name and code:
                    self._country_name_to_code[name] = code
            # Sinónimos comunes (ES/EN/alpha-3 frecuentes)
            synonyms = {
                'UNITED STATES': 'US',
                'UNITED STATES OF AMERICA': 'US',
                'USA': 'US',
                'COLOMBIA': 'CO',
                'COL': 'CO',
                'PANAMA': 'PA',
                'PANAMA CITY': 'PA',
                'MEXICO': 'MX',
                'MEXICO CITY': 'MX',
                'CANADA': 'CA',
                'CANADA (CA)': 'CA',
            }
            for k, v in synonyms.items():
                self._country_name_to_code[self._normalize_str(k)] = v
                self._country_codes_set.add(v)
            self._country_map_loaded = True
            logger.info(f"Country map loaded: {len(self._country_name_to_code)} names, {len(self._country_codes_set)} codes")
        except Exception as e:
            logger.warning(f"Could not load countries.json for normalization: {str(e)}")
            self._country_map_loaded = True  # Evitar reintentos en caliente

    def _normalize_country_code(self, value, default: str | None = None) -> str:
        """Normaliza countryCode a ISO-3166-1 alpha-2 (2 letras) priorizando DB (CountryISO).

        Orden de resolución:
        1) DB CountryISO: code (ISO-2) exacto.
        2) DB CountryISO: alt_code (alpha-3) exacto.
        3) DB CountryISO: nombres exactos (iso_short_name, iso_full_name, dhl_short_name) case-insensitive.
        4) Fallback local: countries.json + sinónimos comunes.
        5) Heurística: primeras 2 letras si son ISO-2 conocidas del catálogo local.
        6) default o valor original en mayúsculas.
        """
        try:
            if not value:
                return default or value
            raw = str(value).strip().upper()
            norm = self._normalize_str(raw)

            # 1) DB: code exacto (ISO-2)
            try:
                if len(raw) == 2 and CountryISO.objects.filter(code=raw).exists():
                    return raw
            except Exception:
                pass

            # 2) DB: alt_code (alpha-3)
            try:
                if len(raw) == 3:
                    obj = CountryISO.objects.filter(alt_code=raw).only('code').first()
                    if obj and obj.code:
                        return obj.code.upper()
            except Exception:
                pass

            # 3) DB: por nombres exactos (case-insensitive)
            try:
                obj = CountryISO.objects.filter(
                    Q(iso_short_name__iexact=value) |
                    Q(iso_full_name__iexact=value) |
                    Q(dhl_short_name__iexact=value)
                ).only('code').first()
                if obj and obj.code:
                    return obj.code.upper()
            except Exception:
                pass

            # 4) Fallback local: countries.json + sinónimos
            self._load_country_map()

            # Ya es ISO-2 válido en catálogo local
            if len(raw) == 2 and raw in self._country_codes_set:
                return raw
            if len(norm) == 2 and norm in self._country_codes_set:
                return norm

            # Alpha-3 comunes locales
            alpha3_map = {
                'USA': 'US', 'COL': 'CO', 'MEX': 'MX', 'PAN': 'PA', 'CAN': 'CA',
                'ARG': 'AR', 'BRA': 'BR', 'PER': 'PE', 'CHL': 'CL', 'ECU': 'EC',
                'VEN': 'VE', 'URY': 'UY', 'PRY': 'PY', 'BOL': 'BO'
            }
            if raw in alpha3_map:
                return alpha3_map[raw]
            if norm in alpha3_map:
                return alpha3_map[norm]

            # Por nombre en catálogo local
            if norm in self._country_name_to_code:
                return self._country_name_to_code[norm]

            # 5) Heurística por primeras 2 letras si están en catálogo local
            maybe = norm[:2]
            if len(maybe) == 2 and maybe in self._country_codes_set:
                return maybe

            # 6) default u original
            return default or raw
        except Exception:
            return default or (str(value).strip().upper() if value else value)

    def _round_half_up(self, value, ndigits: int = 2) -> float:
        """Redondeo consistente HALF_UP (2 decimales por defecto).

        DHL y la UI esperan 2 decimales con redondeo estándar (0.5 hacia arriba).
        Python round usa banker’s rounding; por eso usamos Decimal.
        """
        try:
            q = '0.' + ('0' * (ndigits - 1)) + '1' if ndigits > 0 else '1'
            return float(Decimal(str(value)).quantize(Decimal(q), rounding=ROUND_HALF_UP))
        except Exception:
            # Fallback seguro si algo raro ocurre
            return round(float(value), ndigits)

    def _to_float_weight(self, value) -> float:
        """Convierte un campo de peso (número, string o dict con 'value') a float seguro."""
        try:
            if value is None:
                return 0.0
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                return float(value.strip()) if value.strip() else 0.0
            if isinstance(value, dict):
                # Formatos comunes: { value: 12.34, unitText: 'kg' }
                if 'value' in value:
                    return float(value.get('value') or 0.0)
                # A veces viene { totalWeight: { value: X } } ya cubierto antes
                # Cualquier otro formato no soportado: retornar 0
                return 0.0
        except Exception:
            return 0.0

    def _get_rest_headers(self):
        """Genera headers para requests REST JSON"""
        import base64
        credentials = f"{self.username}:{self.password}"
        auth_header = base64.b64encode(credentials.encode()).decode()
        
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {auth_header}'
        }
    
    def _get_epod_headers(self):
        """Genera headers específicos para requests ePOD con todos los headers recomendados"""
        from datetime import datetime
        import uuid
        
        credentials = f"{self.username}:{self.password}"
        auth_header = base64.b64encode(credentials.encode()).decode()
        
        # Generar valores para headers requeridos según documentación DHL
        current_time = datetime.utcnow()
        message_ref = str(uuid.uuid4())[:32]  # UUID truncado para Message-Reference
        date_rfc2822 = current_time.strftime('%a, %d %b %Y %H:%M:%S GMT')  # RFC 2822 format
        
        return {
            'Accept': 'application/json',
            'Authorization': f'Basic {auth_header}',
            'Message-Reference': message_ref,
            'Message-Reference-Date': date_rfc2822,
            'Plugin-Name': 'DHL-Front-Client',
            'Plugin-Version': '1.0.0',
            'Shipping-System-Platform-Name': 'Django',
            'Shipping-System-Platform-Version': '4.2',
            'Webstore-Platform-Name': 'React',
            'Webstore-Platform-Version': '18.0',
            'x-version': '3.0.0'
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
            
            # Headers específicos para ePOD con todos los headers recomendados por DHL
            headers = self._get_epod_headers()
            
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
                
                # Para debugging, loggear respuesta completa si es exitosa
                if response.status_code in [200, 201]:
                    logger.info(f"ePOD response (full): {response.text}")
                else:
                    logger.debug(f"ePOD response: {response.text[:500]}")
                
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
                    "message": "Ha ocurrido un error",
                    "error_code": "CONNECTION_ERROR",
                    "suggestion": "Verificar conexión a internet y reintentar"
                }
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error for ePOD {shipment_id}: {str(e)}")
                return {
                    "success": False,
                    "message": "Ha ocurrido un error",
                    "error_code": "REQUEST_ERROR",
                    "suggestion": "Reintentar más tarde"
                }
            
        except Exception as e:
            logger.exception(f"Error in get_ePOD for {shipment_id}")
            return {
                "success": False, 
                "message": "Ha ocurrido un error",
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
            
            # Limpiar y preparar datos - soportar tanto 'country' como 'countryCode'
            origin_city = self._clean_text(origin.get('city', origin.get('cityName', 'Panama')))
            origin_postal = origin.get('postal_code', origin.get('postalCode', '0'))
            origin_country = origin.get('country', origin.get('countryCode', 'PA'))
            origin_state = origin.get('state', 'PA')
            
            dest_city = self._clean_text(destination.get('city', destination.get('cityName', 'MIA')))
            dest_postal = destination.get('postal_code', destination.get('postalCode', '25134'))
            dest_country = destination.get('country', destination.get('countryCode', 'CO'))  # Cambiar default de US a CO

            # Normalizar countryCode a ISO-2 sin cambiar la estructura del payload
            normalized_origin_country = self._normalize_country_code(origin_country, default='PA')
            normalized_dest_country = self._normalize_country_code(dest_country, default='CO')
            if normalized_origin_country != origin_country or normalized_dest_country != dest_country:
                logger.info(
                    f"Normalizing country codes for Rate: origin {origin_country} -> {normalized_origin_country}, "
                    f"destination {dest_country} -> {normalized_dest_country}"
                )
            origin_country = normalized_origin_country
            dest_country = normalized_dest_country
            
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
            
            # Para debugging, loggear respuesta completa (temporalmente para desarrollo)
            if response.status_code >= 400:
                logger.error(f"DHL API Error {response.status_code} - Response preview: {response.text[:500]}")
            else:
                logger.info(f"Rate response (full): {response.text}")
                logger.debug(f"Rate response: {response.text[:200]}...")
            
            result = self._parse_rest_response(response, "Rate")
            
            # Agregar información del peso facturable a la respuesta
            if result.get('success') and 'rates' in result:
                # Nuestros cálculos originales
                our_dimensional_weight = self._calculate_dimensional_weight(dimensions)
                our_chargeable_weight = chargeable_weight
                
                weight_breakdown = {
                    # Lo que nosotros calculamos
                    'our_actual_weight': weight,
                    'our_dimensional_weight': our_dimensional_weight,
                    'our_declared_weight': declared_weight or 0.0,
                    'our_chargeable_weight': our_chargeable_weight,
                    
                    # Lo que DHL calculó (del weight_info)
                    'dhl_weight_info': result.get('weight_breakdown', {}),
                    
                    # Para compatibilidad
                    'actual_weight': weight,
                    'dimensional_weight': our_dimensional_weight,
                    'declared_weight': declared_weight or 0.0,
                    'chargeable_weight': chargeable_weight
                }
                
                # Comparar nuestros cálculos con los de DHL
                dhl_weights = result.get('weight_breakdown', {})
                if dhl_weights:
                    logger.info(f"Weight comparison:")
                    logger.info(f"  Our dimensional: {our_dimensional_weight:.2f}kg vs DHL: {dhl_weights.get('dhl_volumetric_weight', 0):.2f}kg")
                    logger.info(f"  Our chargeable: {our_chargeable_weight:.2f}kg vs DHL: {dhl_weights.get('dhl_chargeable_weight', 0):.2f}kg")
                
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
                'message': 'Ha ocurrido un error'
            }
        except Exception as e:
            logger.error(f"Error inesperado en get_rate: {str(e)}")
            return {
                'success': False,
                'error_type': 'unexpected_error',
                'message': 'Ha ocurrido un error'
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
            
            # Parámetros de query para API REST
            params = {
                "trackingView": "all-checkpoints",  # Valor válido según API 
                "levelOfDetail": "all"  # Valor válido: shipment, piece, all
            }
            
            logger.info(f"Using params: {params}")
            
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
                
                # Para debugging, loggear respuesta completa si es exitosa
                if response.status_code in [200, 201]:
                    logger.info(f"Tracking response (full): {response.text}")
                else:
                    logger.debug(f"Tracking response: {response.text[:500]}")
                
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
                    "message": "Ha ocurrido un error",
                    "error_code": "CONNECTION_ERROR",
                    "suggestion": "Verificar conexión a internet y reintentar"
                }
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error for tracking {tracking_number}: {str(e)}")
                return {
                    "success": False,
                    "message": "Ha ocurrido un error",
                    "error_code": "REQUEST_ERROR",
                    "suggestion": "Reintentar más tarde"
                }
            
        except Exception as e:
            logger.exception(f"Error in get_tracking for {tracking_number}")
            return {
                "success": False, 
                "message": "Ha ocurrido un error",
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
            
            # Almacenar datos para uso en mensajes de error
            self._last_shipment_data = shipment_data
            
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
            
            # Determinar cuenta a usar según país de origen
            account_number = self._get_account_for_country(
                shipper.get('country', 'PA'), 
                shipment_data.get('account_number')
            )
            
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
            
            # Actualizar valor total declarado - DHL requiere mínimo 0.001
            if total_value <= 0:
                total_value = 0.01  # Valor mínimo por defecto
                logger.warning(f"Valor declarado era 0 o menor, usando valor mínimo: {total_value}")
            elif total_value < 0.001:
                total_value = 0.001  # Valor mínimo requerido por DHL
                logger.warning(f"Valor declarado menor al mínimo DHL, ajustando a: {total_value}")
            
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
            
            # Para debugging, loggear respuesta completa si es exitosa
            if response.status_code in [200, 201]:
                logger.info(f"Shipment response (full): {response.text}")
            elif response.status_code >= 400:
                logger.error(f"Shipment API Error {response.status_code} - Response: {response.text[:500]}")
            
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
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Error de conexión en create_shipment: {str(e)}")
            return {
                'success': False,
                'error': 'Error de conexión con DHL API. Verifique su conexión a internet y vuelva a intentar.',
                'error_code': 'CONNECTION_ERROR',
                'details': str(e)
            }
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout en create_shipment: {str(e)}")
            return {
                'success': False,
                'error': 'Timeout en la conexión con DHL API. Vuelva a intentar en unos momentos.',
                'error_code': 'TIMEOUT_ERROR',
                'details': str(e)
            }
        except Exception as e:
            logger.error(f"Error en create_shipment: {str(e)}")
            return {
                "success": False,
                "message": "Ha ocurrido un error",
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
            
            logger.info(f"Account validation response status: {response.status_code}")
            if response.status_code != 200:
                logger.debug(f"Account validation response: {response.text[:300]}")
            
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
                        "message": "Ha ocurrido un error",
                        "raw_response": response.text[:500]
                    }
                
                # Parse específico por tipo y adjuntar metadatos HTTP/headers
                if service_type == "Rate":
                    parsed = self._parse_rest_rate_response(data)
                elif service_type == "Tracking":
                    parsed = self._parse_rest_tracking_response(data)
                elif service_type == "ePOD":
                    parsed = self._parse_rest_epod_response(data)
                elif service_type == "Shipment":
                    # Para shipments exitosos, extraer el tracking number
                    parsed = {
                        "success": True,
                        "tracking_number": data.get('shipmentTrackingNumber', ''),
                        "shipment_data": data,
                        "message": "Envío creado exitosamente"
                    }
                else:
                    parsed = {
                        "success": True,
                        "data": data,
                        "message": "Respuesta procesada exitosamente"
                    }

                # Adjuntar metadatos de HTTP para diagnósticos completos
                try:
                    parsed['http_status'] = response.status_code
                    parsed['response_headers'] = dict(response.headers)
                except Exception:
                    pass
                return parsed
            
            elif response.status_code >= 400:
                # Mensaje genérico para todos los errores, incluyendo un preview de la respuesta cruda
                raw_preview = None
                try:
                    raw_text = response.text or ""
                    raw_preview = raw_text[:1500]
                except Exception:
                    raw_preview = None
                return {
                    "success": False,
                    "error_code": str(response.status_code),
                    "message": "Ha ocurrido un error",
                    "http_status": response.status_code,
                    "raw_response": raw_preview
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
                "message": "Ha ocurrido un error",
                "raw_response": response.text[:500] if response else "No response"
            }
    
    def _extract_location_info(self, location_details):
        """Extrae información de ubicación de diferentes formatos"""
        try:
            if not location_details:
                return "Unknown"
            
            # Para shipperDetails/receiverDetails - Priorizar serviceArea sobre postalAddress
            if 'serviceArea' in location_details and location_details['serviceArea']:
                # serviceArea contiene la información real en formato "Ciudad-CÓDIGO"
                service_area = location_details['serviceArea'][0]  # Primer elemento
                return service_area.get('description', 'Unknown')
            
            # Fallback: Para shipperDetails/receiverDetails con postalAddress (generalmente vacío)
            elif 'postalAddress' in location_details:
                postal = location_details['postalAddress']
                city = postal.get('cityName', '')
                country = postal.get('countryCode', '')
                
                # Si cityName está vacío, usar serviceArea si está disponible
                if not city and 'serviceArea' in location_details and location_details['serviceArea']:
                    return location_details['serviceArea'][0].get('description', f"{city}, {country}".strip(', '))
                
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
                    "message": "Ha ocurrido un error",
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
                    "message": "Ha ocurrido un error",
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
            
            # Determinar el estado real basado en el último evento
            real_status = status_desc
            tracking_events = shipment.get('events', [])
            if tracking_events:
                last_event = tracking_events[-1]  # Último evento
                last_event_desc = last_event.get('description', '')
                last_event_type = last_event.get('typeCode', '')
                
                # Mapear códigos de tipo a estados más descriptivos
                if last_event_type == 'OK':
                    real_status = 'Delivered'
                elif last_event_type == 'WC':
                    real_status = 'Out for Delivery'
                elif last_event_type == 'PU':
                    real_status = 'Pickup'
                elif last_event_type in ['AF', 'AR']:
                    real_status = 'In Transit'
                elif last_event_type == 'PL':
                    real_status = 'Processed'
                elif last_event_type == 'DF':
                    real_status = 'In Transit'
                else:
                    # Usar la descripción del evento si no hay mapeo
                    real_status = last_event_desc
            
            # Información básica del envío con repesaje
            shipment_info = {
                'tracking_number': shipment.get('shipmentTrackingNumber', shipment.get('id', '')),
                'status': status_code,
                'status_description': real_status,  # Usar el estado real del último evento
                'service': shipment.get('productCode', shipment.get('service', 'Unknown')),
                'description': shipment.get('description', 'Unknown'),
                'shipment_timestamp': shipment.get('shipmentTimestamp', ''),
                'origin': self._extract_location_info(shipment.get('shipperDetails', {})),
                'destination': self._extract_location_info(shipment.get('receiverDetails', {})),
                'total_weight': shipment.get('totalWeight', shipment.get('details', {}).get('totalWeight', {}).get('value', 0) if isinstance(shipment.get('details', {}).get('totalWeight', {}), dict) else shipment.get('details', {}).get('totalWeight', 0)),
                'weight_unit': shipment.get('unitOfMeasurements', shipment.get('details', {}).get('totalWeight', {}).get('unitText', 'kg') if isinstance(shipment.get('details', {}).get('totalWeight', {}), dict) else 'kg'),
                'number_of_pieces': shipment.get('numberOfPieces', shipment.get('details', {}).get('numberOfPieces', 0))
            }

            # Volumetric/dimensional weight a nivel envío si DHL lo provee
            try:
                dhl_total_dim = None
                # Posibles ubicaciones
                candidates = [
                    shipment.get('volumetricWeight'),
                    shipment.get('dimensionalWeight'),
                    shipment.get('details', {}).get('volumetricWeight') if isinstance(shipment.get('details', {}), dict) else None,
                    shipment.get('details', {}).get('dimensionalWeight') if isinstance(shipment.get('details', {}), dict) else None,
                ]
                for c in candidates:
                    if c is None:
                        continue
                    if isinstance(c, dict):
                        v = c.get('value')
                    else:
                        v = c
                    if v is not None:
                        dhl_total_dim = self._to_float_weight(v)
                        break
                if dhl_total_dim is not None:
                    shipment_info['dhl_total_dimensional_weight'] = self._round_half_up(dhl_total_dim, 2)
            except Exception:
                pass

            # Normalizar unidad y redondear total_weight
            try:
                shipment_info['total_weight'] = self._round_half_up(self._to_float_weight(shipment_info.get('total_weight', 0)), 2)
                unit = str(shipment_info.get('weight_unit', 'kg')).lower()
                if unit in ('metric', 'kg', 'kilogram', 'kilograms', 'kilos'):
                    shipment_info['weight_unit'] = 'kg'
            except Exception:
                pass
            
            # Eventos de tracking
            events = []
            tracking_events = shipment.get('events', [])
            for event in tracking_events:
                # Combinar fecha y hora si están separadas
                date_part = event.get('date', '')
                time_part = event.get('time', '')
                timestamp = f"{date_part}T{time_part}" if date_part and time_part else event.get('timestamp', '')
                
                # Extraer ubicación de serviceArea
                location = "Unknown"
                service_areas = event.get('serviceArea', [])
                if service_areas and len(service_areas) > 0:
                    location = service_areas[0].get('description', 'Unknown')
                elif event.get('location'):
                    location = self._extract_location_info(event.get('location', {}))
                
                event_data = {
                    'timestamp': timestamp,
                    'location': location,
                    'status': event.get('description', 'Unknown'),
                    'next_steps': event.get('nextSteps', ''),
                    'type_code': event.get('typeCode', ''),
                    'date': date_part,
                    'time': time_part
                }
                events.append(event_data)
            
            # Detalles de piezas con información de repesaje
            pieces = []
            piece_details = shipment.get('pieces', [])
            for piece in piece_details:
                # Extraer peso declarado y repesaje
                peso_declarado = self._to_float_weight(piece.get('weight', 0))
                peso_repesaje = self._to_float_weight(piece.get('actualWeight', 0))
                # Extraer peso dimensional/volumétrico provisto por DHL si existe
                dhl_dim_weight = None
                try:
                    # Claves posibles según variantes del API
                    candidates = [
                        piece.get('dimensionalWeight'),
                        piece.get('volumetricWeight'),
                        piece.get('dimWeight'),
                    ]
                    # Algunos endpoints anidan como { dimensionalWeight: { value: X } }
                    for c in candidates:
                        if c is None:
                            continue
                        if isinstance(c, dict):
                            v = c.get('value')
                        else:
                            v = c
                        if v is not None:
                            dhl_dim_weight = self._to_float_weight(v)
                            break
                except Exception:
                    dhl_dim_weight = None
                
                piece_data = {
                    'piece_id': piece.get('trackingNumber', piece.get('number', '')),
                    'description': piece.get('description', ''),
                    'peso_declarado': self._round_half_up(peso_declarado, 2) if peso_declarado else 0,
                    'repesaje': self._round_half_up(peso_repesaje, 2) if peso_repesaje else 0,
                    'weight': self._round_half_up(peso_repesaje, 2) if peso_repesaje else self._round_half_up(peso_declarado, 2) if peso_declarado else 0,
                    'weight_unit': piece.get('unitOfMeasurements', 'kg'),
                    'dimensions': piece.get('dimensions', {}),
                    'type_code': piece.get('typeCode', ''),
                    'package_type': piece.get('packageType', ''),
                    # Peso dimensional según DHL si está disponible
                    'dhl_dimensional_weight': self._round_half_up(dhl_dim_weight, 2) if dhl_dim_weight else 0,
                    # Información adicional de peso para compatibilidad
                    'weight_info': {
                        'declared_weight': float(peso_declarado) if peso_declarado else 0,
                        'actual_weight_reweigh': float(peso_repesaje) if peso_repesaje else 0,
                        'chargeable_weight': float(peso_repesaje) if peso_repesaje else float(peso_declarado) if peso_declarado else 0,
                        'unit': piece.get('unitOfMeasurements', 'kg'),
                        'dhl_dimensional_weight': float(dhl_dim_weight) if dhl_dim_weight else 0
                    }
                }
                pieces.append(piece_data)

            # Corrección del total_weight: usar el MAYOR peso entre las piezas con redondeo HALF_UP
            # Contexto: algunos envíos multi-pieza devuelven totalWeight con 1 decimal (p.ej. 148.4),
            # mientras que el negocio requiere mostrar el mayor de las 3 piezas (p.ej. 148.85).
            try:
                piece_weights = [float(p.get('weight') or 0) if p.get('weight') is not None else 0 for p in pieces]
                if piece_weights:
                    max_piece_weight = max(piece_weights)
                    max_piece_weight = self._round_half_up(max_piece_weight, 2)
                    # Tomar el máximo entre lo que vino en shipment y el mayor de piezas (ambos redondeados)
                    original_total = self._round_half_up(shipment_info.get('total_weight', 0), 2)
                    corrected_total = max(original_total, max_piece_weight)
                    shipment_info['total_weight'] = corrected_total
                    # Anotar fuente para debugging sin romper compatibilidad
                    shipment_info['weight_source'] = 'max_piece_weight'
                    shipment_info['original_total_weight'] = original_total
            except Exception as _e:
                logger.debug(f"Weight correction skipped: {_e}")
            
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
                        "date": event['date'],
                        "time": event['time'],
                        "location": event['location'],
                        "additional_info": event.get('next_steps', ''),
                        "type_code": event.get('type_code', '')
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
                "message": "Ha ocurrido un error",
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
                
                # Obtener información de peso de DHL para este producto
                dhl_weight_data = product.get('weight', {})
                dhl_provided_weight = float(dhl_weight_data.get('provided', 0))
                dhl_volumetric_weight = float(dhl_weight_data.get('volumetric', 0))
                dhl_chargeable_weight = max(dhl_provided_weight, dhl_volumetric_weight)
                
                # Agregar información de peso a cada rate
                rate['weight_info'] = {
                    'provided_weight': dhl_provided_weight,
                    'volumetric_weight': dhl_volumetric_weight, 
                    'chargeable_weight': dhl_chargeable_weight,
                    'unit': dhl_weight_data.get('unitOfMeasurement', 'metric')
                }
                
                logger.debug(f"DHL Weight calculation for {rate['service_code']}: "
                           f"provided={dhl_provided_weight}kg, volumetric={dhl_volumetric_weight}kg, "
                           f"chargeable={dhl_chargeable_weight}kg")
                
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
            
            # Calcular información de peso comparando nuestros cálculos con los de DHL
            weight_info = {}
            if products:
                first_product = products[0]
                dhl_weight_data = first_product.get('weight', {})
                
                # Pesos de DHL
                dhl_provided = float(dhl_weight_data.get('provided', 0))
                dhl_volumetric = float(dhl_weight_data.get('volumetric', 0))
                dhl_chargeable = max(dhl_provided, dhl_volumetric)
                
                weight_info = {
                    # Información original enviada
                    'sent_actual_weight': dhl_provided,  # Lo que enviamos a DHL
                    
                    # Cálculos de DHL (los oficiales)
                    'dhl_provided_weight': dhl_provided,
                    'dhl_volumetric_weight': dhl_volumetric,
                    'dhl_chargeable_weight': dhl_chargeable,
                    
                    # Para compatibilidad con código existente
                    'actual_weight': dhl_provided,
                    'dimensional_weight': dhl_volumetric,
                    'declared_weight': dhl_provided,
                    'chargeable_weight': dhl_chargeable,
                    
                    'unit_of_measurement': dhl_weight_data.get('unitOfMeasurement', 'metric')
                }
                
                logger.info(f"Weight comparison - DHL calculated: provided={dhl_provided}kg, "
                          f"volumetric={dhl_volumetric}kg, chargeable={dhl_chargeable}kg")
            
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
                "message": "Ha ocurrido un error",
                "raw_data": data
            }

    def _parse_rest_epod_response(self, data):
        """
        Parsea la respuesta JSON de ePOD de la API REST de DHL
        
        Estructura esperada según documentación oficial DHL:
        {
          "documents": [
            {
              "encodingFormat": "PDF",
              "content": "base64 encoded content", 
              "typeCode": "POD"
            }
          ]
        }
        """
        try:
            logger.info("Parsing ePOD response from DHL API")
            
            # Validar que data sea un diccionario
            if not isinstance(data, dict):
                logger.error(f"ePOD response data is not a dict: {type(data)}")
                return {
                    "success": False,
                    "message": "Respuesta ePOD inválida: formato no reconocido",
                    "error_code": "INVALID_FORMAT",
                    "suggestion": "Contactar soporte técnico - formato de respuesta inesperado",
                    "raw_data": str(data)[:500]
                }
            
            # Extraer documentos de la respuesta
            documents = data.get('documents', [])
            
            # Validar que haya documentos
            if not documents or not isinstance(documents, list):
                logger.warning("No documents found in ePOD response")
                return {
                    "success": False,
                    "message": "No se encontraron documentos ePOD para este envío",
                    "error_code": "NO_DOCUMENTS",
                    "suggestion": "Verificar que el envío haya sido entregado y tenga ePOD disponible",
                    "total_documents": 0,
                    "documents": [],
                    "raw_data": data
                }
            
            logger.info(f"Found {len(documents)} document(s) in ePOD response")
            
            # Procesar cada documento
            processed_documents = []
            main_document = None
            
            for i, doc in enumerate(documents):
                if not isinstance(doc, dict):
                    logger.warning(f"Document {i} is not a dict, skipping")
                    continue
                
                # Extraer campos según estructura oficial DHL
                type_code = doc.get('typeCode', 'POD')
                encoding_format = doc.get('encodingFormat', 'PDF')
                content = doc.get('content', '')
                
                # Validar contenido base64
                is_valid_base64 = self._validate_base64_content(content)
                content_size = len(content) if content else 0
                
                # Crear documento procesado
                processed_doc = {
                    'index': i,
                    'type_code': type_code,
                    'encoding_format': encoding_format.upper(),
                    'content': content,
                    'content_size_bytes': content_size,
                    'content_size_mb': round(content_size / (1024 * 1024), 2) if content_size > 0 else 0,
                    'is_valid_base64': is_valid_base64,
                    'is_pdf': encoding_format.upper() == 'PDF',
                    'has_content': bool(content and content.strip())
                }
                
                processed_documents.append(processed_doc)
                
                # Usar el primer documento válido como principal
                if not main_document and processed_doc['has_content'] and processed_doc['is_valid_base64']:
                    main_document = processed_doc
                    logger.info(f"Selected document {i} as main document (type: {type_code}, format: {encoding_format}, size: {content_size} bytes)")
            
            # Estadísticas de documentos
            valid_documents = [d for d in processed_documents if d['has_content'] and d['is_valid_base64']]
            invalid_documents = [d for d in processed_documents if not d['has_content'] or not d['is_valid_base64']]
            
            logger.info(f"Document processing summary: {len(valid_documents)} valid, {len(invalid_documents)} invalid")
            
            # Verificar si hay al menos un documento válido
            if not main_document:
                logger.error("No valid documents found in ePOD response")
                return {
                    "success": False,
                    "message": "Documentos ePOD encontrados pero ninguno tiene contenido válido",
                    "error_code": "INVALID_DOCUMENTS",
                    "suggestion": "Los documentos no contienen datos válidos en base64",
                    "total_documents": len(processed_documents),
                    "valid_documents": len(valid_documents),
                    "invalid_documents": len(invalid_documents),
                    "documents": processed_documents,
                    "raw_data": data
                }
            
            # Respuesta exitosa con documento principal
            response = {
                "success": True,
                "message": f"ePOD obtenido exitosamente - {len(valid_documents)} documento(s) válido(s)",
                
                # Información del documento principal
                "pdf_data": main_document['content'],
                "format": main_document['encoding_format'],
                "type_code": main_document['type_code'],
                "size_bytes": main_document['content_size_bytes'],
                "size_mb": main_document['content_size_mb'],
                "is_base64": main_document['is_valid_base64'],
                "is_pdf": main_document['is_pdf'],
                
                # Estadísticas generales
                "total_documents": len(processed_documents),
                "valid_documents": len(valid_documents),
                "invalid_documents": len(invalid_documents),
                
                # Todos los documentos procesados
                "all_documents": processed_documents,
                
                # Información adicional para debugging
                "main_document_index": main_document['index'],
                "processing_summary": {
                    "total_found": len(documents),
                    "successfully_processed": len(processed_documents),
                    "with_valid_content": len(valid_documents),
                    "largest_document_mb": max([d['content_size_mb'] for d in processed_documents], default=0)
                },
                
                # Datos raw para debugging si es necesario
                "raw_data": data
            }
            
            logger.info(f"ePOD parsing successful: main document {main_document['content_size_mb']}MB, format: {main_document['encoding_format']}")
            return response
            
        except Exception as e:
            logger.exception(f"Error parsing REST ePOD response: {str(e)}")
            return {
                "success": False,
                "error_type": "parse_error",
                "message": "Ha ocurrido un error",
                "error_code": "PARSE_ERROR",
                "suggestion": "Contactar soporte técnico - error de procesamiento interno",
                "raw_data": str(data)[:500] if data else "No data available"
            }
    
    def _validate_base64_content(self, content):
        """
        Valida si el contenido es base64 válido
        
        Args:
            content (str): Contenido a validar
            
        Returns:
            bool: True si es base64 válido, False en caso contrario
        """
        try:
            if not content or not isinstance(content, str):
                return False
            
            # Verificar que la longitud sea múltiplo de 4 (después de padding)
            if len(content) % 4 != 0:
                return False
            
            # Verificar caracteres válidos de base64
            import re
            if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', content):
                return False
            
            # Intentar decodificar
            import base64
            base64.b64decode(content, validate=True)
            return True
            
        except Exception as e:
            logger.debug(f"Base64 validation failed: {str(e)}")
            return False

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

    def get_landed_cost(self, origin, destination, weight, dimensions, currency_code='USD',
                       is_customs_declarable=True, get_cost_breakdown=True,
                       items=None, account_number=None, service='P'):
        """
        Calcula el landed cost (costo total de importación) incluyendo 
        shipping, duties, taxes, fees usando el endpoint /landed-cost de DHL.
        
        Args:
            origin (dict): Dirección de origen
            destination (dict): Dirección de destino  
            weight (float): Peso en kg
            dimensions (dict): Dimensiones en cm
            currency_code (str): Código de moneda
            is_customs_declarable (bool): Si requiere declaración aduanera
            get_cost_breakdown (bool): Si se quiere desglose de costos
            items (list): Lista de productos con detalles aduaneros
            account_number (str): Número de cuenta DHL (REQUERIDO)
            service (str): Tipo de servicio - 'P' para Express Worldwide
            
        Returns:
            dict: Respuesta con landed cost calculado
        """
        try:
            logger.info(f"=== DHL LANDED COST REQUEST ===")
            logger.info(f"Origin: {origin}")
            logger.info(f"Destination: {destination}")
            logger.info(f"Weight: {weight}kg")
            logger.info(f"Currency: {currency_code}")
            logger.info(f"Account: {account_number}")
            logger.info(f"Items count: {len(items) if items else 0}")
            
            # ✅ VALIDACIÓN OBLIGATORIA: account_number
            if not account_number:
                return {
                    'success': False,
                    'message': 'Número de cuenta DHL es obligatorio para calcular landed cost',
                    'error_code': 'MISSING_ACCOUNT_NUMBER'
                }
            
            # Validar que tengamos items para el cálculo
            if not items or len(items) == 0:
                return {
                    'success': False,
                    'message': 'Se requiere al menos un producto para calcular landed cost',
                    'error_code': 'MISSING_ITEMS'
                }
            
            # ✅ PAYLOAD SIMPLIFICADO QUE FUNCIONA
            payload = {
                "customerDetails": {
                    "shipperDetails": {
                        "postalCode": origin.get('postal_code', ''),
                        "cityName": origin.get('city', ''),
                        "countryCode": origin.get('country', '')
                    },
                    "receiverDetails": {
                        "postalCode": destination.get('postal_code', ''),
                        "cityName": destination.get('city', ''),
                        "countryCode": destination.get('country', '')
                    }
                },
                "productCode": service,
                "localProductCode": service,
                "unitOfMeasurement": "metric",
                "currencyCode": currency_code,
                "isCustomsDeclarable": is_customs_declarable,
                "getCostBreakdown": get_cost_breakdown,  # ✅ CAMPO OBLIGATORIO
                "packages": [
                    {
                        "typeCode": "3BX",
                        "weight": weight,
                        "dimensions": {
                            "length": dimensions.get('length', 10),
                            "width": dimensions.get('width', 10),
                            "height": dimensions.get('height', 10)
                        }
                    }
                ],
                "items": [],
                # ✅ CAMPO OBLIGATORIO - cuenta real
                "accounts": [
                    {
                        "typeCode": "shipper",
                        "number": str(account_number)
                    }
                ]
            }
            
            # ✅ Procesar items con formato simplificado que funciona
            for idx, item in enumerate(items):
                # Solo valores válidos para quantityType: "prt" o "box"
                quantity_type = item.get('quantity_type', 'pcs')
                valid_quantity_types = {
                    'pcs': 'prt', 'piece': 'prt', 'pieces': 'prt', 'each': 'prt',
                    'unit': 'prt', 'units': 'prt', 'part': 'prt', 'parts': 'prt', 'prt': 'prt',
                    'box': 'box', 'boxes': 'box', 'caja': 'box', 'cajas': 'box'
                }
                dhl_quantity_type = valid_quantity_types.get(quantity_type.lower(), 'prt')
                
                dhl_item = {
                    "number": idx + 1,
                    "name": item.get('name', 'Product'),
                    "description": item.get('description', 'No description'),
                    "manufacturerCountry": item.get('manufacturer_country', 'US'),
                    "quantity": item.get('quantity', 1),
                    "quantityType": dhl_quantity_type,  # ✅ Solo "prt" o "box"
                    "unitPrice": float(item.get('unit_price', 0)),
                    "unitPriceCurrencyCode": item.get('unit_price_currency_code', currency_code),
                    "customsValue": float(item.get('customs_value', item.get('unit_price', 0))),
                    "customsValueCurrencyCode": item.get('customs_value_currency_code', currency_code),
                    "commodityCode": str(item.get('commodity_code', '150420')),  # ✅ Código válido por defecto
                    "weight": float(item.get('weight', weight / len(items)))
                }
                
                payload["items"].append(dhl_item)
            
            logger.info(f"DHL Landed Cost Payload: {payload}")
            
            # Hacer la llamada a DHL landed-cost API
            url = "https://express.api.dhl.com/mydhlapi/landed-cost"
            headers = self._get_rest_headers()
            
            response = requests.post(url, json=payload, headers=headers, verify=False, timeout=30)
            
            logger.info(f"DHL Landed Cost Response Status: {response.status_code}")
            logger.info(f"DHL Landed Cost Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_landed_cost_response(data, currency_code)
            else:
                error_data = {}
                try:
                    error_data = response.json()
                except:
                    pass
                
                return {
                    'success': False,
                    'message': 'Ha ocurrido un error',
                    'error_code': 'DHL_API_ERROR',
                    'raw_response': response.text,
                    'error_details': error_data
                }
                
        except Exception as e:
            logger.error(f"Error in get_landed_cost: {str(e)}")
            return {
                'success': False,
                'message': 'Ha ocurrido un error',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def _parse_landed_cost_response(self, data, currency_code):
        """
        Parsea la respuesta del endpoint landed-cost de DHL con formato actualizado
        """
        try:
            products = data.get('products', [])
            if not products:
                return {
                    'success': False,
                    'message': 'No se encontraron productos en la respuesta',
                    'error_code': 'NO_PRODUCTS'
                }
            
            product = products[0]  # Tomar el primer producto
            total_price_list = product.get('totalPrice', [])
            breakdown_list = product.get('detailedPriceBreakdown', [])
            items_breakdown = product.get('items', [])
            warnings = data.get('warnings', [])
            
            # ✅ Extraer precio total (totalPrice es una lista)
            total_cost = 0
            total_currency = currency_code
            if total_price_list:
                total_price_obj = total_price_list[0]
                total_cost = float(total_price_obj.get('price', 0))
                total_currency = total_price_obj.get('priceCurrency', currency_code)
            
            # Inicializar componentes de costo
            shipping_cost = 0
            duties_total = 0
            taxes_total = 0
            fees_total = 0
            insurance_cost = 0
            
            # ✅ Procesar breakdown detallado
            breakdown_items = []
            if breakdown_list:
                breakdown = breakdown_list[0].get('breakdown', [])
                
                for item in breakdown:
                    name = item.get('name', '')
                    type_code = item.get('typeCode', '')
                    price = float(item.get('price', 0))
                    service_code = item.get('serviceCode', '')
                    
                    breakdown_items.append({
                        'name': name,
                        'type_code': type_code,
                        'service_code': service_code,
                        'price': price,
                        'currency': item.get('priceCurrency', currency_code),
                        'description': self._get_breakdown_description(name, type_code, service_code)
                    })
                    
                    # ✅ Categorizar costos según nombres reales de DHL
                    if type_code == 'DUTY' or name == 'TOTAL DUTIES':
                        duties_total += price
                    elif type_code == 'TAX' or name == 'TOTAL TAXES' or name == 'VAT':
                        taxes_total += price
                    elif type_code == 'FEE' or name == 'TOTAL FEES':
                        fees_total += price
                    elif name in ['SINSV']:  # Insurance
                        insurance_cost += price
                    elif name in ['SPRQN', 'STSCH', 'SCUSV'] or service_code in ['FF']:  # Shipping
                        shipping_cost += price
            
            # ✅ Procesar breakdown por item
            items_detail = []
            for item in items_breakdown:
                item_breakdown = item.get('breakdown', [])
                item_detail = {
                    'item_number': item.get('number', 0),
                    'breakdown': []
                }
                
                for breakdown_item in item_breakdown:
                    item_detail['breakdown'].append({
                        'name': breakdown_item.get('name', ''),
                        'type_code': breakdown_item.get('typeCode', ''),
                        'price': float(breakdown_item.get('price', 0)),
                        'currency': breakdown_item.get('priceCurrency', currency_code),
                        'formula': breakdown_item.get('tariffRateFormula', '')
                    })
                
                items_detail.append(item_detail)
            
            return {
                'success': True,
                'landed_cost': {
                    'total_cost': total_cost,
                    'currency': total_currency,
                    'shipping_cost': shipping_cost,
                    'duties': duties_total,
                    'taxes': taxes_total,
                    'fees': fees_total,
                    'insurance': insurance_cost,
                    'breakdown': breakdown_items
                },
                'items_breakdown': items_detail,
                'warnings': warnings,
                'raw_response': data  # Para debugging
            }
            
        except Exception as e:
            logger.error(f"Error parsing landed cost response: {str(e)}")
            return {
                'success': False,
                'message': 'Ha ocurrido un error',
                'error_code': 'PARSE_ERROR'
            }
    
    def _get_breakdown_description(self, name, type_code, service_code):
        """
        Obtiene descripción legible para los elementos del breakdown
        """
        descriptions = {
            'SPRQN': 'Costo de envío DHL',
            'STSCH': 'Servicios adicionales DHL',
            'SINSV': 'Valor del seguro',
            'SCUSV': 'Valor declarado para aduanas',
            'MACHG': 'Cargos adicionales del comerciante',
            'MFCHG': 'Cargos de flete del comerciante',
            'FF': 'Recargo de combustible',
            'CR': 'Recargo de situación de emergencia',
            'DD': 'Impuestos y aranceles pagados',
            'DUTY': 'Aranceles de importación',
            'TAX': 'Impuestos de importación',
            'FEE': 'Tasas y cargos',
            'IMPORT_PROCESSING_CHARGE': 'Cargo por procesamiento de importación',
            'IDCA': 'Cargo de declaración de importación',
            'GST': 'Impuesto sobre bienes y servicios',
            'CIF': 'Valor CIF (Costo + Seguro + Flete)'
        }
        
        return descriptions.get(name, descriptions.get(type_code, f'Cargo: {name or type_code}'))
    
    def _get_account_for_country(self, origin_country, requested_account=None):
        """
        Determina qué cuenta DHL usar según el país de origen del envío
        
        Args:
            origin_country (str): Código de país de origen (ej: 'PA', 'CO', 'US')
            requested_account (str): Cuenta específica solicitada (opcional)
            
        Returns:
            str: Número de cuenta DHL a usar
        """
        # Para envíos internacionales, usar siempre la cuenta IMPEX
        # La cuenta 706014493 es una cuenta IMPEX que puede manejar envíos internacionales
        impex_account = '706014493'
        
        # Si se especifica una cuenta específica, verificar si es válida para envíos internacionales
        if requested_account:
            # Si la cuenta solicitada es la canadiense, usar IMPEX en su lugar
            if requested_account == '706065602':
                logger.warning(f"Cuenta canadiense {requested_account} no válida para envíos internacionales, usando cuenta IMPEX: {impex_account}")
                return impex_account
            else:
                logger.info(f"Usando cuenta específica solicitada: {requested_account}")
                return requested_account
        
        # Para todos los países, usar la cuenta IMPEX que permite envíos internacionales
        logger.info(f"País origen: {origin_country} -> Cuenta DHL IMPEX: {impex_account}")
        
        return impex_account
