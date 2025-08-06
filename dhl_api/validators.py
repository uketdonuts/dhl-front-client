"""
Sistema de validación y avisos para usuarios del endpoint Landed Cost
"""

from django.core.exceptions import ValidationError
import re
import logging

logger = logging.getLogger(__name__)

class LandedCostValidator:
    """
    Validador completo para requests de Landed Cost con avisos específicos al usuario
    """
    
    # Configuración de límites de producción
    LIMITS = {
        'min_weight': 0.01,
        'max_weight': 1000.0,
        'min_dimension': 1,
        'max_dimension': 270,
        'min_customs_value': 0.01,
        'max_customs_value': 50000.00,
        'min_quantity': 1,
        'max_quantity': 9999,
        'max_name_length': 512,  # Según documentación DHL API
        'max_description_length': 255,  # Corregido según documentación DHL API
        'max_category_length': 50,  # Según documentación DHL API
        'max_brand_length': 50,  # Según documentación DHL API
        'max_part_number_length': 35,  # Según documentación DHL API
        'max_commodity_code_length': 18,  # Según documentación DHL API
        'max_items_per_shipment': 1000,  # Según documentación DHL API
        'max_packages_per_shipment': 999,  # Según documentación DHL API
        'max_charges_per_shipment': 20,  # Según documentación DHL API
        'min_weight_package': 0.001,  # Según documentación DHL API
        'max_weight_package': 999999999999,  # Según documentación DHL API
        'min_dimension_package': 0.001,  # Según documentación DHL API
        'max_dimension_package': 9999999,  # Según documentación DHL API
        'max_postal_code_length': 12,  # Según documentación DHL API
        'max_city_name_length': 45,  # Según documentación DHL API
        'max_address_line_length': 45,  # Según documentación DHL API
        'max_county_name_length': 45,  # Según documentación DHL API
        'max_province_code_length': 35,  # Según documentación DHL API
        'max_account_number_length': 12,  # Según documentación DHL API
        'min_account_number_length': 1,  # Según documentación DHL API
    }
    
    # Información de ayuda para cada campo (tooltips)
    FIELD_INFO = {
        'origin': {
            'description': 'Dirección de origen del envío',
            'example': '{"country": "PA", "city": "Panama City", "postal_code": "0816"}'
        },
        'destination': {
            'description': 'Dirección de destino del envío',
            'example': '{"country": "US", "city": "New York", "postal_code": "10001"}'
        },
        'weight': {
            'description': 'Peso total del paquete en kg (sistema métrico) o lb (imperial)',
            'example': '2.5 kg para un paquete de 2.5 kilos'
        },
        'dimensions': {
            'description': 'Dimensiones del paquete en cm (métrico) o in (imperial)',
            'example': '{"length": 30, "width": 20, "height": 15} para 30x20x15 cm'
        },
        'currency_code': {
            'description': 'Código de moneda ISO 3166 para el cálculo de costos',
            'example': 'USD, EUR, GBP, CAD, etc.'
        },
        'is_customs_declarable': {
            'description': 'Indica si el envío contiene productos declarables en aduana',
            'example': 'true para productos comerciales, false para documentos'
        },
        'is_dtp_requested': {
            'description': 'DHL paga aranceles e impuestos en destino (DTP - Duties & Taxes Paid)',
            'example': 'true para incluir DTP, false para pago en destino'
        },
        'is_insurance_requested': {
            'description': 'Solicitar seguro DHL para el envío',
            'example': 'true para activar seguro, false para envío sin seguro'
        },
        'get_cost_breakdown': {
            'description': 'Recibir desglose detallado de todos los costos',
            'example': 'true para ver costos detallados, false para total simple'
        },
        'shipment_purpose': {
            'description': 'Propósito del envío: comercial (B2B) o personal (B2C)',
            'example': 'commercial para negocios, personal para uso personal'
        },
        'service': {
            'description': 'Tipo de servicio DHL: P (Packages) o D (Documents)',
            'example': 'P para paquetes con valor, D para documentos'
        },
        'account_number': {
            'description': 'Número de cuenta DHL Express (9-12 dígitos)',
            'example': '706014493 - Tu número de cuenta DHL'
        },
        'transportation_mode': {
            'description': 'Modo de transporte para el envío',
            'example': 'air (aéreo), ocean (marítimo), ground (terrestre)'
        },
        'charges': {
            'description': 'Cargos adicionales a incluir en el cálculo',
            'example': '[{"typeCode": "insurance", "amount": 50, "currencyCode": "USD"}]'
        },
        'packages': {
            'description': 'Información detallada de cada paquete del envío',
            'example': '[{"weight": 2.5, "dimensions": {"length": 30, "width": 20, "height": 15}}]'
        },
        'items': {
            'description': 'Lista de productos/artículos en el envío para cálculo de aranceles',
            'example': 'Cada item debe incluir nombre, descripción, código HS, valor, etc.'
        },
        # Campos específicos de items
        'item_name': {
            'description': 'Nombre corto del producto (máximo 512 caracteres)',
            'example': 'KNITWEAR COTTON - Nombre descriptivo del producto'
        },
        'item_description': {
            'description': 'Descripción completa del producto (máximo 255 caracteres)',
            'example': 'KNITWEAR 100% COTTON REDUCTION PRICE FALL COLLECTION'
        },
        'manufacturer_country': {
            'description': 'Código ISO del país donde se fabricó el producto',
            'example': 'CN (China), US (Estados Unidos), DE (Alemania)'
        },
        'part_number': {
            'description': 'Número de parte o SKU del producto (máximo 35 caracteres)',
            'example': 'SKU-12345, PART-ABC-001'
        },
        'quantity': {
            'description': 'Cantidad total del artículo a enviar',
            'example': '2 para dos unidades del producto'
        },
        'quantity_type': {
            'description': 'Tipo de unidad de medida para la cantidad',
            'example': 'prt (partes), box (cajas), pcs (piezas)'
        },
        'unit_price': {
            'description': 'Precio unitario del producto en la moneda especificada',
            'example': '120.50 para $120.50 por unidad'
        },
        'unit_price_currency_code': {
            'description': 'Código de moneda del precio unitario',
            'example': 'USD, EUR, GBP según la moneda del precio'
        },
        'customs_value': {
            'description': 'Valor aduanero del producto para cálculo de aranceles',
            'example': '240.00 para declarar $240.00 en aduana'
        },
        'customs_value_currency_code': {
            'description': 'Código de moneda del valor aduanero',
            'example': 'USD para valor en dólares americanos'
        },
        'commodity_code': {
            'description': 'Código HS (Harmonized System) del producto (6-18 dígitos)',
            'example': '611020 para suéteres de punto, 851713 para teléfonos móviles'
        },
        'category': {
            'description': 'Categoría del producto según clasificación DHL (máximo 50 caracteres)',
            'example': '109 para Jerseys/Sweatshirts, 204 para Calzado textil'
        },
        'brand': {
            'description': 'Marca del producto (máximo 50 caracteres)',
            'example': 'Nike, Apple, Samsung, etc.'
        },
        'weight_item': {
            'description': 'Peso individual del artículo en kg o lb',
            'example': '0.5 para 500 gramos por unidad'
        },
        'weight_unit_of_measurement': {
            'description': 'Sistema de medida para peso: métrico o imperial',
            'example': 'metric (kg/cm), imperial (lb/in)'
        },
        'estimated_tariff_rate_type': {
            'description': 'Tipo de tarifa estimada para cálculo de aranceles',
            'example': 'default_rate (estándar), preferential_rate (preferencial)'
        },
        # Campos de dirección
        'postal_code': {
            'description': 'Código postal de la dirección (máximo 12 caracteres)',
            'example': '10001 (NY), 0816 (Panamá), SW1A 1AA (Londres)'
        },
        'city_name': {
            'description': 'Nombre de la ciudad (máximo 45 caracteres)',
            'example': 'Panama City, New York, London'
        },
        'country_code': {
            'description': 'Código ISO de país de 2 letras',
            'example': 'PA (Panamá), US (Estados Unidos), GB (Reino Unido)'
        },
        'province_code': {
            'description': 'Código de provincia o estado (máximo 35 caracteres)',
            'example': 'NY (New York), CA (California), ON (Ontario)'
        },
        'address_line1': {
            'description': 'Primera línea de dirección (máximo 45 caracteres)',
            'example': '123 Main Street, Calle 50 Este'
        },
        'address_line2': {
            'description': 'Segunda línea de dirección (máximo 45 caracteres)',
            'example': 'Apt 4B, Edificio Torre Global'
        },
        'address_line3': {
            'description': 'Tercera línea de dirección (máximo 45 caracteres)',
            'example': 'Piso 15, Oficina 1501'
        },
        'county_name': {
            'description': 'Nombre del condado o distrito (máximo 45 caracteres)',
            'example': 'Manhattan, Distrito de Panamá'
        }
    }
    
    # Valores válidos según DHL API
    VALID_VALUES = {
        'quantity_types': ['pcs', 'kg', 'cm', 'sqm', 'cbm', 'ltr', 'pkg'],
        'currencies': ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CNY', 'MXN', 'BRL', 'SGD'],
        'shipment_purposes': ['commercial', 'personal'],
        'transport_modes': ['air', 'ocean', 'ground'],
        'service_types': ['P', 'D'],
        'charge_types': ['freight', 'additional', 'insurance'],
        'tariff_rate_types': ['default_rate', 'derived_rate', 'highest_rate', 'center_rate', 'lowest_rate', 'preferential_rate'],
        'supported_countries': {
            # América del Norte
            'US', 'CA', 'MX',
            # Centroamérica y Caribe (Panamá es HUB principal de DHL)
            'PA', 'CR', 'GT', 'SV', 'HN', 'NI', 'BZ',
            'DO', 'JM', 'TT', 'BB', 'BS', 'CU',
            # América del Sur
            'BR', 'AR', 'CL', 'CO', 'PE', 'VE', 'EC', 'UY', 'PY', 'BO', 'GY', 'SR',
            # Europa
            'GB', 'DE', 'FR', 'ES', 'IT', 'NL', 'BE', 'CH', 'AT', 'SE', 'DK', 'NO', 'FI',
            'PT', 'IE', 'PL', 'CZ', 'HU', 'GR', 'RO', 'BG', 'HR', 'SI', 'SK', 'LT', 'LV', 'EE',
            # Asia-Pacífico
            'CN', 'JP', 'KR', 'IN', 'SG', 'TH', 'MY', 'ID', 'PH', 'VN', 'AU', 'NZ', 'HK', 'TW',
            # Medio Oriente y África
            'AE', 'SA', 'QA', 'KW', 'BH', 'OM', 'IL', 'EG', 'ZA', 'KE', 'NG', 'MA', 'GH',
            # Otros importantes
            'RU', 'TR', 'UA', 'BY', 'MD', 'GE', 'AM', 'AZ', 'KZ', 'UZ'
        }
    }
    
    @classmethod
    def get_field_info(cls, field_name):
        """
        Obtiene información de tooltip para un campo específico
        
        Args:
            field_name (str): Nombre del campo
            
        Returns:
            dict: {"description": str, "example": str} o None si no existe
        """
        return cls.FIELD_INFO.get(field_name)
    
    @classmethod
    def get_all_field_info(cls):
        """
        Obtiene toda la información de tooltips para el frontend
        
        Returns:
            dict: Diccionario completo de información de campos
        """
        return cls.FIELD_INFO
    
    @classmethod
    def get_field_limits(cls):
        """
        Obtiene todos los límites de validación para el frontend
        
        Returns:
            dict: Diccionario completo de límites
        """
        return cls.LIMITS
    
    @classmethod
    def get_valid_values(cls):
        """
        Obtiene todos los valores válidos para campos con opciones
        
        Returns:
            dict: Diccionario completo de valores válidos
        """
        return cls.VALID_VALUES

    @classmethod
    def validate_request(cls, data):
        """
        Valida una request completa de landed cost
        Retorna: (is_valid, errors, warnings, recommendations)
        """
        errors = []
        warnings = []
        recommendations = []
        
        try:
            # 1. Validaciones críticas (bloquean el cálculo)
            cls._validate_critical_fields(data, errors)
            cls._validate_origin_destination(data, errors)
            cls._validate_weight_dimensions(data, errors, warnings)
            cls._validate_items(data, errors, warnings, recommendations)
            cls._validate_business_rules(data, errors, warnings)
            cls._validate_price_affecting_options(data, errors, warnings)
            
            # 2. Advertencias (permiten continuar)
            cls._validate_warnings(data, warnings)
            
            # 3. Recomendaciones (informativos)
            cls._generate_recommendations(data, recommendations)
            
            is_valid = len(errors) == 0
            
            return is_valid, errors, warnings, recommendations
            
        except Exception as e:
            logger.error(f"Error en validación de landed cost: {str(e)}")
            errors.append("Error interno en validación. Contacte soporte técnico.")
            return False, errors, warnings, recommendations
    
    @classmethod
    def _validate_critical_fields(cls, data, errors):
        """Validaciones críticas que bloquean el cálculo"""
        
        # Campos obligatorios
        required_fields = ['origin', 'destination', 'weight', 'dimensions', 'items']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"❌ Campo obligatorio faltante: '{field}'")
        
        # Validar estructura de origin/destination
        for location_type in ['origin', 'destination']:
            if location_type in data:
                location = data[location_type]
                
                # ✅ Validar country y city (obligatorios)
                required_location_fields = ['country', 'city']
                for field in required_location_fields:
                    if field not in location or not location[field]:
                        errors.append(f"❌ {location_type}.{field} es obligatorio")
                
                # ✅ Postal code: usar "0" como default si está vacío (igual que endpoint rate)
                if 'postal_code' not in location or not location['postal_code']:
                    # Aplicar el mismo comportamiento que el endpoint rate
                    location['postal_code'] = "0"
                    logger.info(f"Applied default postal_code '0' for {location_type}")
        
        # Validar items no vacío
        if 'items' in data and not data['items']:
            errors.append("❌ Se requiere al menos un producto para calcular landed cost")
    
    @classmethod
    def _validate_origin_destination(cls, data, errors):
        """Validar países soportados"""
        
        for location_type in ['origin', 'destination']:
            if location_type in data:
                country = data[location_type].get('country', '').upper()
                if country and country not in cls.VALID_VALUES['supported_countries']:
                    errors.append(
                        f"❌ País {location_type} '{country}' no está soportado por DHL Express. "
                        f"Países soportados: {', '.join(sorted(cls.VALID_VALUES['supported_countries']))}"
                    )
    
    @classmethod
    def _validate_weight_dimensions(cls, data, errors, warnings):
        """Validar peso y dimensiones"""
        
        # Validar peso
        weight = data.get('weight', 0)
        if weight < cls.LIMITS['min_weight']:
            errors.append(f"❌ Peso mínimo: {cls.LIMITS['min_weight']} kg")
        elif weight > cls.LIMITS['max_weight']:
            errors.append(f"❌ Peso máximo: {cls.LIMITS['max_weight']} kg")
        elif weight > 100:
            warnings.append(f"⚠️ Peso elevado ({weight} kg). Verificar si es correcto.")
        
        # Validar dimensiones
        dimensions = data.get('dimensions', {})
        for dim_name in ['length', 'width', 'height']:
            dim_value = dimensions.get(dim_name, 0)
            if dim_value < cls.LIMITS['min_dimension']:
                errors.append(f"❌ {dim_name} mínimo: {cls.LIMITS['min_dimension']} cm")
            elif dim_value > cls.LIMITS['max_dimension']:
                errors.append(f"❌ {dim_name} máximo: {cls.LIMITS['max_dimension']} cm")
    
    @classmethod
    def _validate_items(cls, data, errors, warnings, recommendations):
        """Validar productos"""
        
        items = data.get('items', [])
        
        # Límite de productos
        if len(items) > cls.LIMITS['max_items_per_shipment']:
            errors.append(f"❌ Máximo {cls.LIMITS['max_items_per_shipment']} productos por envío")
        
        for idx, item in enumerate(items):
            item_prefix = f"Producto {idx + 1}:"
            
            # Campos obligatorios por item
            required_item_fields = [
                'name', 'description', 'manufacturer_country', 
                'quantity', 'unit_price', 'customs_value', 'commodity_code'
            ]
            
            for field in required_item_fields:
                if field not in item or not item[field]:
                    errors.append(f"❌ {item_prefix} Campo '{field}' es obligatorio")
            
            # Validar quantity_type
            quantity_type = item.get('quantity_type', '').lower()
            if quantity_type and quantity_type not in cls.VALID_VALUES['quantity_types']:
                errors.append(
                    f"❌ {item_prefix} quantity_type '{quantity_type}' no válido. "
                    f"Valores válidos: {', '.join(cls.VALID_VALUES['quantity_types'])}"
                )
            
            # Validar límites de cantidad y valores
            quantity = item.get('quantity', 0)
            if quantity < cls.LIMITS['min_quantity'] or quantity > cls.LIMITS['max_quantity']:
                errors.append(f"❌ {item_prefix} Cantidad debe estar entre {cls.LIMITS['min_quantity']} y {cls.LIMITS['max_quantity']}")
            
            customs_value = item.get('customs_value', 0)
            if customs_value < cls.LIMITS['min_customs_value']:
                errors.append(f"❌ {item_prefix} Valor mínimo: ${cls.LIMITS['min_customs_value']}")
            elif customs_value > cls.LIMITS['max_customs_value']:
                errors.append(f"❌ {item_prefix} Valor máximo: ${cls.LIMITS['max_customs_value']}")
            
            # Validar longitud de campos de texto
            text_fields = {
                'name': cls.LIMITS['max_name_length'],
                'description': cls.LIMITS['max_description_length'],
                'category': cls.LIMITS['max_category_length'],
                'brand': cls.LIMITS['max_brand_length']
            }
            
            for field, max_length in text_fields.items():
                if field in item and len(str(item[field])) > max_length:
                    errors.append(f"❌ {item_prefix} {field} máximo {max_length} caracteres")
            
            # Validar commodity code (HS Code)
            commodity_code = str(item.get('commodity_code', ''))
            if commodity_code == '999999':
                warnings.append(f"⚠️ {item_prefix} Usando código genérico 999999. Recomendamos usar código HS específico.")
                warnings.append(f"🚫 {item_prefix} DHL Warning 200200: Cálculo de aranceles no posible sin código HS completo.")
            elif not re.match(r'^\d{6,10}$', commodity_code):
                warnings.append(f"⚠️ {item_prefix} Código commodity '{commodity_code}' no parece válido (debe ser 6-10 dígitos)")
                warnings.append(f"🚫 {item_prefix} DHL Warning 200200: Cálculo de aranceles no posible sin código HS completo.")
            elif len(commodity_code) < 8:
                warnings.append(f"⚠️ {item_prefix} Código HS '{commodity_code}' muy corto. Para cálculo preciso de aranceles, use mínimo 8 dígitos.")
                warnings.append(f"🚫 {item_prefix} DHL Warning 200200: Cálculo de aranceles limitado con código HS incompleto.")
            
            # Validar coherencia precio vs valor
            unit_price = item.get('unit_price', 0)
            if customs_value > 0 and unit_price > 0:
                price_diff = abs(customs_value - unit_price) / unit_price
                if price_diff > 0.5:  # Más de 50% diferencia
                    warnings.append(f"⚠️ {item_prefix} Gran diferencia entre precio (${unit_price}) y valor declarado (${customs_value})")
    
    @classmethod
    def _validate_business_rules(cls, data, errors, warnings):
        """Validaciones de reglas de negocio"""
        
        # Validar moneda
        currency_code = data.get('currency_code', 'USD').upper()
        if currency_code not in cls.VALID_VALUES['currencies']:
            errors.append(f"❌ Moneda '{currency_code}' no soportada. Válidas: {', '.join(cls.VALID_VALUES['currencies'])}")
        
        # Validar service type
        service = data.get('service', 'P').upper()
        if service not in cls.VALID_VALUES['service_types']:
            errors.append(f"❌ Tipo de servicio '{service}' no válido. Válidos: P (Packages), D (Documents)")
        
        # Validar coherencia service vs items
        if service == 'D':  # Documents
            items = data.get('items', [])
            for item in items:
                customs_value = item.get('customs_value', 0)
                if customs_value > 0:
                    warnings.append("⚠️ Servicio 'Documents' seleccionado pero hay productos con valor comercial. ¿Debería ser 'Packages'?")
                    break
        
        # Validar número de cuenta para producción
        account_number = data.get('account_number')
        if not account_number:
            warnings.append("⚠️ Sin número de cuenta DHL. Requerido para cálculos precisos en producción.")
        elif not re.match(r'^\d{9,12}$', str(account_number)):
            warnings.append("⚠️ Formato de cuenta DHL inusual. Verificar que sea correcto.")
    
    @classmethod
    def _validate_price_affecting_options(cls, data, errors, warnings):
        """Validar opciones que afectan el precio del envío"""
        
        # Validar DTP (Duties & Taxes Paid)
        is_dtp_requested = data.get('is_dtp_requested', False)
        if is_dtp_requested:
            # DTP solo está disponible para ciertos países
            dest_country = data.get('destination', {}).get('country', '').upper()
            if dest_country in ['US', 'GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AU']:
                total_value = sum([item.get('customs_value', 0) * item.get('quantity', 1) 
                                  for item in data.get('items', [])])
                estimated_dtp_cost = total_value * 0.20  # Estimación 20% del valor
                warnings.append(f"💰 DTP activado: Aranceles e impuestos incluidos (~${estimated_dtp_cost:.2f} estimado).")
            else:
                warnings.append(f"⚠️ DTP solicitado para {dest_country}. Verificar disponibilidad en destino.")
        
        # Validar seguro
        is_insurance_requested = data.get('is_insurance_requested', False)
        if is_insurance_requested:
            total_value = sum([item.get('customs_value', 0) * item.get('quantity', 1) 
                              for item in data.get('items', [])])
            if total_value > 0:
                # Estimación de costo de seguro (típicamente 0.5-2% del valor)
                insurance_estimate = total_value * 0.01  # 1% estimado
                warnings.append(f"💰 Seguro solicitado: Costo estimado ~${insurance_estimate:.2f} (1% del valor ${total_value:.2f})")
            else:
                warnings.append("⚠️ Seguro solicitado pero no hay valor declarado en productos.")
        
        # Validar cargos adicionales
        charges = data.get('charges', [])
        if charges:
            total_additional_charges = 0
            for charge in charges:
                charge_type = charge.get('typeCode', '').lower()
                amount = charge.get('amount', 0)
                currency = charge.get('currencyCode', 'USD')
                
                # Validar tipo de cargo
                if charge_type not in cls.VALID_VALUES['charge_types']:
                    errors.append(f"❌ Tipo de cargo '{charge_type}' no válido. "
                                f"Válidos: {', '.join(cls.VALID_VALUES['charge_types'])}")
                
                # Validar monto
                if amount <= 0:
                    errors.append("❌ Monto de cargo adicional debe ser mayor a 0")
                elif amount > 999999:
                    errors.append("❌ Monto de cargo adicional excede el límite (999,999)")
                
                total_additional_charges += amount
            
            if total_additional_charges > 0:
                warnings.append(f"💰 Cargos adicionales: ${total_additional_charges:.2f} se sumarán al costo total")
        
        # Validar coherencia entre DTP y tipo de envío
        shipment_purpose = data.get('shipment_purpose', '').lower()
        if is_dtp_requested and shipment_purpose == 'personal':
            warnings.append("⚠️ DTP solicitado para envío personal. Normalmente se usa para envíos comerciales.")
        
        # Validar estimatedTariffRateType que afecta cálculo de aranceles
        for item in data.get('items', []):
            tariff_rate_type = item.get('estimated_tariff_rate_type', '').lower()
            if tariff_rate_type and tariff_rate_type not in cls.VALID_VALUES['tariff_rate_types']:
                errors.append(f"❌ Tipo de tarifa '{tariff_rate_type}' no válido. "
                            f"Válidos: {', '.join(cls.VALID_VALUES['tariff_rate_types'])}")
            elif tariff_rate_type == 'preferential_rate':
                warnings.append("💰 Tarifa preferencial solicitada: Puede reducir aranceles si cumple requisitos de origen.")
            elif tariff_rate_type in ['highest_rate', 'lowest_rate']:
                warnings.append(f"💰 Usando '{tariff_rate_type}': Estimación de rango para cálculo de aranceles.")
    
    @classmethod
    def _validate_warnings(cls, data, warnings):
        """Generar advertencias adicionales"""
        
        # Verificar si es envío de alto valor
        total_value = sum([item.get('customs_value', 0) * item.get('quantity', 1) for item in data.get('items', [])])
        if total_value > 5000:
            warnings.append(f"⚠️ Envío de alto valor (${total_value:,.2f}). Considere seguro adicional.")
        
        # Verificar DTP para envíos comerciales
        if data.get('shipment_purpose') == 'commercial' and not data.get('is_dtp_requested'):
            dest_country = data.get('destination', {}).get('country', '').upper()
            if dest_country in ['US', 'GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AU']:
                warnings.append("⚠️ Para envíos comerciales a este destino, considere activar DTP (Duties & Taxes Paid) para simplificar el proceso.")
    
    @classmethod
    def _generate_recommendations(cls, data, recommendations):
        """Generar recomendaciones útiles"""
        
        items = data.get('items', [])
        
        # Recomendar consolidación
        if len(items) > 10:
            recommendations.append("💡 Considere consolidar productos similares para optimizar costos.")
        
        # Recomendar documentación
        if data.get('shipment_purpose') == 'commercial':
            recommendations.append("💡 Asegúrese de tener factura comercial y documentos aduaneros completos.")
        
        # Recomendar verificación de restricciones
        dest_country = data.get('destination', {}).get('country', '')
        if dest_country in ['CN', 'IN', 'BR']:
            recommendations.append(f"💡 Verificar restricciones específicas para importaciones a {dest_country}.")
        
        # Recomendar optimización de embalaje
        weight = data.get('weight', 0)
        dimensions = data.get('dimensions', {})
        volume = dimensions.get('length', 1) * dimensions.get('width', 1) * dimensions.get('height', 1) / 1000000  # m³
        if volume > 0 and weight / volume < 100:  # Densidad baja
            recommendations.append("💡 Embalaje con baja densidad. Considere optimizar para reducir costos volumétricos.")
        
        # Recomendar opciones de precio
        total_value = sum([item.get('customs_value', 0) * item.get('quantity', 1) for item in data.get('items', [])])
        if total_value > 1000 and not data.get('is_insurance_requested'):
            recommendations.append("💡 Considere activar seguro DHL para proteger su envío de alto valor.")
        
        if data.get('shipment_purpose') == 'commercial' and not data.get('is_dtp_requested'):
            recommendations.append("💡 DTP (Duties & Taxes Paid) simplifica el proceso aduanero y puede acelerar la entrega.")
        
        if data.get('get_cost_breakdown', False):
            recommendations.append("💡 Desglose de costos activado: Recibirá información detallada de todos los cargos.")

    @classmethod
    def format_validation_response(cls, is_valid, errors, warnings, recommendations):
        """
        Formatea la respuesta de validación para el usuario
        """
        response = {
            'is_valid': is_valid,
            'can_proceed': is_valid,
            'summary': cls._get_validation_summary(is_valid, errors, warnings, recommendations)
        }
        
        if errors:
            response['errors'] = {
                'count': len(errors),
                'items': errors,
                'action_required': 'Corrija los errores antes de continuar'
            }
        
        if warnings:
            response['warnings'] = {
                'count': len(warnings),
                'items': warnings,
                'action_required': 'Revise las advertencias. Puede continuar si está seguro.'
            }
        
        if recommendations:
            response['recommendations'] = {
                'count': len(recommendations),
                'items': recommendations,
                'action_required': 'Sugerencias para optimizar su envío'
            }
        
        return response
    
    @classmethod
    def _get_validation_summary(cls, is_valid, errors, warnings, recommendations):
        """Genera resumen de validación"""
        if is_valid:
            if warnings or recommendations:
                return "✅ Datos válidos con sugerencias de mejora"
            else:
                return "✅ Datos completamente válidos"
        else:
            return f"❌ {len(errors)} error(es) encontrado(s). Corrección requerida."
