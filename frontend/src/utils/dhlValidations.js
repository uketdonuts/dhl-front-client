/**
 * Validaciones completas para DHL API según documentación oficial
 * Incluye límites de campos, formatos y reglas de negocio
 */

// Límites y configuraciones según documentación DHL API
export const DHL_LIMITS = {
  // Peso y dimensiones
  MIN_WEIGHT: 0.001,
  MAX_WEIGHT: 999999999999,
  MIN_DIMENSION: 0.001,
  MAX_DIMENSION: 9999999,
  
  // Valores aduaneros
  MIN_CUSTOMS_VALUE: 0.01,
  MAX_CUSTOMS_VALUE: 50000.00,
  MIN_QUANTITY: 1,
  MAX_QUANTITY: 9999,
  
  // Longitudes de campos de texto
  MAX_NAME_LENGTH: 512,
  MAX_DESCRIPTION_LENGTH: 255,
  MAX_CATEGORY_LENGTH: 50,
  MAX_BRAND_LENGTH: 50,
  MAX_PART_NUMBER_LENGTH: 35,
  MAX_COMMODITY_CODE_LENGTH: 18,
  MAX_POSTAL_CODE_LENGTH: 12,
  MAX_CITY_NAME_LENGTH: 45,
  MAX_ADDRESS_LINE_LENGTH: 45,
  MAX_COUNTY_NAME_LENGTH: 45,
  MAX_PROVINCE_CODE_LENGTH: 35,
  MAX_ACCOUNT_NUMBER_LENGTH: 12,
  MIN_ACCOUNT_NUMBER_LENGTH: 9,
  
  // Límites de elementos
  MAX_ITEMS_PER_SHIPMENT: 1000,
  MAX_PACKAGES_PER_SHIPMENT: 999,
  MAX_CHARGES_PER_SHIPMENT: 20
};

// Expresiones regulares para validación
export const DHL_PATTERNS = {
  ACCOUNT_NUMBER: /^\d{9,12}$/,
  COMMODITY_CODE: /^\d{6,10}$/,
  POSTAL_CODE_CANADA: /^[A-Z]\d[A-Z]\s?\d[A-Z]\d$/i,
  POSTAL_CODE_US: /^\d{5}(-\d{4})?$/,
  POSTAL_CODE_UK: /^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$/i,
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PHONE: /^[\+]?[\d\s\-\(\)]{7,20}$/,
  BASE64: /^[A-Za-z0-9+/]*={0,2}$/
};

// Tipos de contenido válidos por servicio DHL
export const SERVICE_CONTENT_COMPATIBILITY = {
  'P': { documents: true, packages: true, description: 'Packages - Paquetes y documentos' },
  'D': { documents: true, packages: false, description: 'Documents - Solo documentos' },
  'N': { documents: true, packages: true, description: 'Express Worldwide - Paquetes y documentos' },
  'T': { documents: true, packages: true, description: 'Express 9:00 - Paquetes y documentos' },
  'Y': { documents: true, packages: true, description: 'Express 10:30 - Paquetes y documentos' },
  'U': { documents: true, packages: true, description: 'Express Worldwide - Paquetes y documentos' },
  'K': { documents: false, packages: true, description: 'Express Easy - Solo paquetes' },
  'L': { documents: false, packages: true, description: 'Logistics Services - Solo paquetes' }
};

// Tipos de cantidad válidos
export const VALID_QUANTITY_TYPES = ['pcs', 'kg', 'cm', 'sqm', 'cbm', 'ltr', 'pkg', 'prt', 'box'];

// Monedas soportadas
export const VALID_CURRENCIES = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CNY', 'MXN', 'BRL', 'SGD'];

/**
 * Validador principal para campos de texto con límite de caracteres
 */
export const validateTextLength = (value, maxLength, fieldName) => {
  const errors = [];
  
  if (!value) return errors;
  
  const text = String(value).trim();
  if (text.length > maxLength) {
    errors.push(`${fieldName} no puede exceder ${maxLength} caracteres (actual: ${text.length})`);
  }
  
  return errors;
};

/**
 * Validador para números de cuenta DHL
 */
export const validateAccountNumber = (accountNumber) => {
  const errors = [];
  
  if (!accountNumber) {
    errors.push('Número de cuenta DHL es requerido para cálculos precisos');
    return errors;
  }
  
  const account = String(accountNumber).trim();
  
  if (!DHL_PATTERNS.ACCOUNT_NUMBER.test(account)) {
    errors.push('Número de cuenta DHL debe tener entre 9-12 dígitos');
  }
  
  return errors;
};

/**
 * Validador para peso y dimensiones
 */
export const validateWeightAndDimensions = (weight, dimensions) => {
  const errors = [];
  const warnings = [];
  
  // Validar peso
  if (!weight || weight <= 0) {
    errors.push('El peso debe ser mayor que 0');
  } else {
    if (weight < DHL_LIMITS.MIN_WEIGHT) {
      errors.push(`Peso mínimo permitido: ${DHL_LIMITS.MIN_WEIGHT} kg`);
    }
    if (weight > DHL_LIMITS.MAX_WEIGHT) {
      errors.push(`Peso máximo permitido: ${DHL_LIMITS.MAX_WEIGHT} kg`);
    }
  }
  
  // Validar dimensiones
  if (!dimensions || typeof dimensions !== 'object') {
    errors.push('Las dimensiones son requeridas');
    return { errors, warnings };
  }
  
  const { length, width, height } = dimensions;
  
  ['length', 'width', 'height'].forEach(dim => {
    const value = dimensions[dim];
    if (!value || value <= 0) {
      errors.push(`${dim} debe ser mayor que 0`);
    } else {
      if (value < DHL_LIMITS.MIN_DIMENSION) {
        errors.push(`${dim} mínima permitida: ${DHL_LIMITS.MIN_DIMENSION} cm`);
      }
      if (value > DHL_LIMITS.MAX_DIMENSION) {
        errors.push(`${dim} máxima permitida: ${DHL_LIMITS.MAX_DIMENSION} cm`);
      }
    }
  });
  
  // Validar coherencia peso vs volumen
  if (length && width && height && weight) {
    const volume = length * width * height; // cm³
    const volumeInM3 = volume / 1000000; // m³
    const weightDensity = weight / volumeInM3; // kg/m³
    
    // Alertas por densidad inusual
    if (weightDensity > 1000) {
      warnings.push('Densidad muy alta - Verificar peso vs dimensiones');
    }
    if (weightDensity < 0.1) {
      warnings.push('Densidad muy baja - Verificar peso vs dimensiones');
    }
  }
  
  return { errors, warnings };
};

/**
 * Validador para códigos HS/Commodity
 */
export const validateCommodityCode = (commodityCode, itemName = 'Producto') => {
  const errors = [];
  const warnings = [];
  
  if (!commodityCode) {
    errors.push(`${itemName}: Código HS/Commodity es requerido`);
    return { errors, warnings };
  }
  
  const code = String(commodityCode).trim();
  
  // Validar formato básico - convertir errores en advertencias para ser menos estrictos
  if (!DHL_PATTERNS.COMMODITY_CODE.test(code)) {
    warnings.push(`${itemName}: Código HS debe tener entre 6-10 dígitos (actual: ${code}). Se procesará como está.`);
  }
  // Códigos cortos generan advertencias
  else if (code.length < 8) {
    warnings.push(`${itemName}: Código HS corto (${code.length} dígitos). Para mejor precisión, use mínimo 8 dígitos`);
  }
  
  return { errors, warnings };
};

/**
 * Validador para códigos postales por país
 */
export const validatePostalCode = (postalCode, countryCode) => {
  const errors = [];
  
  // Si no hay código postal, usar "0" por defecto
  if (!postalCode || postalCode.trim() === '') {
    return { errors, postalCode: "0" };
  }
  
  const code = String(postalCode).trim().toUpperCase();
  
  // Validaciones específicas por país (solo para países que sí requieren formato específico)
  switch (countryCode?.toUpperCase()) {
    case 'CA':
      if (!DHL_PATTERNS.POSTAL_CODE_CANADA.test(code)) {
        errors.push('Código postal canadiense debe seguir formato A9A 9A9 (ej: K1A 0A6)');
      }
      break;
    case 'US':
      if (!DHL_PATTERNS.POSTAL_CODE_US.test(code)) {
        errors.push('Código postal estadounidense debe seguir formato 12345 o 12345-6789');
      }
      break;
    case 'GB':
      if (!DHL_PATTERNS.POSTAL_CODE_UK.test(code)) {
        errors.push('Código postal del Reino Unido debe seguir formato válido (ej: SW1A 1AA)');
      }
      break;
    default:
      // Para otros países, aceptar cualquier código o "0"
      if (code.length > DHL_LIMITS.MAX_POSTAL_CODE_LENGTH) {
        errors.push(`Código postal no puede exceder ${DHL_LIMITS.MAX_POSTAL_CODE_LENGTH} caracteres`);
      }
  }
  
  return { errors, postalCode: code };
};

/**
 * Validador para fechas de envío
 */
export const validateShipmentDate = (shipmentDate) => {
  const errors = [];
  const warnings = [];
  
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const maxDate = new Date(today);
  maxDate.setDate(maxDate.getDate() + 10); // Máximo 10 días en el futuro
  
  let validatedDate = shipmentDate;
  
  if (!shipmentDate) {
    // Usar mañana como fecha por defecto
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    validatedDate = tomorrow.toISOString().split('T')[0];
    warnings.push('No se proporcionó fecha de envío, usando mañana como fecha por defecto');
  } else {
    const requestedDate = new Date(shipmentDate);
    
    if (isNaN(requestedDate.getTime())) {
      errors.push('Formato de fecha inválido');
      return { errors, warnings, validatedDate: null };
    }
    
    if (requestedDate < today) {
      errors.push('La fecha de envío no puede ser en el pasado');
    }
    
    if (requestedDate > maxDate) {
      errors.push('La fecha de envío no puede ser más de 10 días en el futuro');
    }
  }
  
  return { errors, warnings, validatedDate };
};

/**
 * Validador para compatibilidad de servicio vs contenido
 */
export const validateServiceContentCompatibility = (serviceCode, items = []) => {
  const errors = [];
  const warnings = [];
  
  if (!serviceCode) {
    warnings.push('No se especificó tipo de servicio, usando "P" (Packages) por defecto');
    return { errors, warnings, recommendedService: 'P' };
  }
  
  const service = SERVICE_CONTENT_COMPATIBILITY[serviceCode];
  
  if (!service) {
    errors.push(`Código de servicio "${serviceCode}" no es válido`);
    return { errors, warnings };
  }
  
  // Verificar compatibilidad con items
  const hasCommercialValue = items.some(item => 
    item.customs_value && parseFloat(item.customs_value) > 0
  );
  
  if (serviceCode === 'D' && hasCommercialValue) {
    warnings.push('Servicio "Documents" seleccionado pero hay productos con valor comercial. ¿Debería ser "Packages"?');
    return { errors, warnings, recommendedService: 'P' };
  }
  
  if (!service.packages && hasCommercialValue) {
    errors.push(`Servicio "${serviceCode}" no soporta paquetes con valor comercial`);
  }
  
  return { errors, warnings };
};

/**
 * Validador para productos/items de Landed Cost
 */
export const validateLandedCostItems = (items) => {
  const errors = [];
  const warnings = [];
  
  if (!items || !Array.isArray(items) || items.length === 0) {
    errors.push('Se requiere al menos un producto para calcular Landed Cost');
    return { errors, warnings };
  }
  
  if (items.length > DHL_LIMITS.MAX_ITEMS_PER_SHIPMENT) {
    errors.push(`Máximo ${DHL_LIMITS.MAX_ITEMS_PER_SHIPMENT} productos por envío`);
  }
  
  items.forEach((item, index) => {
    const itemPrefix = `Producto ${index + 1}:`;
    
    // Validar campos requeridos
    const requiredFields = ['name', 'description', 'manufacturer_country', 'quantity', 'unit_price', 'customs_value', 'commodity_code'];
    requiredFields.forEach(field => {
      if (!item[field]) {
        errors.push(`${itemPrefix} ${field} es requerido`);
      }
    });
    
    // Validar longitudes de texto
    if (item.name) {
      const nameErrors = validateTextLength(item.name, DHL_LIMITS.MAX_NAME_LENGTH, `${itemPrefix} Nombre`);
      errors.push(...nameErrors);
    }
    
    if (item.description) {
      const descErrors = validateTextLength(item.description, DHL_LIMITS.MAX_DESCRIPTION_LENGTH, `${itemPrefix} Descripción`);
      errors.push(...descErrors);
    }
    
    // Validar cantidades y valores
    if (item.quantity) {
      const qty = parseFloat(item.quantity);
      if (qty < DHL_LIMITS.MIN_QUANTITY || qty > DHL_LIMITS.MAX_QUANTITY) {
        errors.push(`${itemPrefix} Cantidad debe estar entre ${DHL_LIMITS.MIN_QUANTITY} y ${DHL_LIMITS.MAX_QUANTITY}`);
      }
    }
    
    if (item.customs_value) {
      const value = parseFloat(item.customs_value);
      if (value < DHL_LIMITS.MIN_CUSTOMS_VALUE || value > DHL_LIMITS.MAX_CUSTOMS_VALUE) {
        errors.push(`${itemPrefix} Valor aduanero debe estar entre ${DHL_LIMITS.MIN_CUSTOMS_VALUE} y ${DHL_LIMITS.MAX_CUSTOMS_VALUE}`);
      }
    }
    
    // Validar código HS (simple)
    const commodityValidation = validateCommodityCode(item.commodity_code, itemPrefix);
    errors.push(...commodityValidation.errors);
    warnings.push(...commodityValidation.warnings);
  });
  
  return { errors, warnings };
};

/**
 * Validador maestro para requests completos
 */
export const validateDHLRequest = (requestData, requestType = 'rate') => {
  const errors = [];
  const warnings = [];
  
  // Validar origen y destino
  if (requestData.origin) {
    const originErrors = validateTextLength(requestData.origin.city, DHL_LIMITS.MAX_CITY_NAME_LENGTH, 'Ciudad de origen');
    errors.push(...originErrors);
    
    // Validar código postal de origen - usar "0" como fallback
    if (requestData.origin.postal_code) {
      const postalValidation = validatePostalCode(requestData.origin.postal_code, requestData.origin.country);
      if (postalValidation.errors.length > 0) {
        warnings.push(`Código postal de origen inválido, se usará "0": ${postalValidation.errors[0]}`);
      }
    }
  }
  
  if (requestData.destination) {
    const destErrors = validateTextLength(requestData.destination.city, DHL_LIMITS.MAX_CITY_NAME_LENGTH, 'Ciudad de destino');
    errors.push(...destErrors);
    
    // Validar código postal de destino - usar "0" como fallback
    if (requestData.destination.postal_code) {
      const postalValidation = validatePostalCode(requestData.destination.postal_code, requestData.destination.country);
      if (postalValidation.errors.length > 0) {
        warnings.push(`Código postal de destino inválido, se usará "0": ${postalValidation.errors[0]}`);
      }
    }
  }
  
  // Validar peso y dimensiones
  if (requestData.weight && requestData.dimensions) {
    const weightDimValidation = validateWeightAndDimensions(requestData.weight, requestData.dimensions);
    errors.push(...weightDimValidation.errors);
    warnings.push(...weightDimValidation.warnings);
  }
  
  // Validar número de cuenta si está presente
  if (requestData.account_number) {
    const accountErrors = validateAccountNumber(requestData.account_number);
    warnings.push(...accountErrors); // Como warning en lugar de error
  }
  
  // Validar fecha de envío
  if (requestData.shipment_date) {
    const dateValidation = validateShipmentDate(requestData.shipment_date);
    errors.push(...dateValidation.errors);
    warnings.push(...dateValidation.warnings);
  }
  
  // Validaciones específicas por tipo de request
  if (requestType === 'landedCost' && requestData.items) {
    const itemsValidation = validateLandedCostItems(requestData.items);
    errors.push(...itemsValidation.errors);
    warnings.push(...itemsValidation.warnings);
    
    // Validar compatibilidad de servicio
    const serviceValidation = validateServiceContentCompatibility(requestData.service, requestData.items);
    errors.push(...serviceValidation.errors);
    warnings.push(...serviceValidation.warnings);
  }
  
  return {
    isValid: errors.length === 0,
    errors: errors.filter(Boolean),
    warnings: warnings.filter(Boolean),
    summary: `${errors.length} errores, ${warnings.length} advertencias`
  };
};

// Función helper para formatear códigos postales
export const formatPostalCode = (postalCode, countryCode) => {
  if (!postalCode || postalCode === "0") return postalCode;
  
  // Normalizar: quitar espacios y guiones para un formato compacto
  const code = String(postalCode).trim().toUpperCase().replace(/\s|-/g, '');

  switch (countryCode?.toUpperCase()) {
    case 'CA':
      // Canadá: devolver compacto A9A9A9 (sin espacio)
      return code;
    case 'US':
      // Estados Unidos: devolver 12345 o 123456789 (sin guión)
      return code;
    default:
      return code;
  }
};

// Normalizadores de campos de ubicación
export const normalizeCountryCode = (country) => (country || '').toString().trim().toUpperCase();
export const normalizeStateCode = (state) => (state || '').toString().trim().toUpperCase();
// Limpia sufijos comunes en nombres de ciudad: " - CODE", códigos postales al final, y paréntesis
export const cleanFriendlyCity = (city) => {
  let s = (city || '').toString().trim();
  // Sufijo " - CODE" (2-4 alfanuméricos)
  s = s.replace(/\s+-\s+[A-Z0-9]{2,4}$/i, '');
  // Códigos postales al final (CA: A9A9A9)
  s = s.replace(/\s+[A-Z]\d[A-Z]\d[A-Z]\d$/i, '');
  // Códigos postales US al final: 12345 o 123456789
  s = s.replace(/\s+\d{5}(?:\d{4})?$/, '');
  // Quitar información entre paréntesis al final
  s = s.replace(/\s+\([^)]*\)$/, '');
  return s;
};

export const normalizeCityName = (city) => cleanFriendlyCity(city).toUpperCase();

// Normaliza un objeto de ubicación (acepta postal_code o postalCode)
export const normalizeLocation = (loc = {}) => {
  const country = normalizeCountryCode(loc.country);
  const state = normalizeStateCode(loc.state);
  const cityRaw = loc.cityName || loc.city;
  const city = normalizeCityName(cityRaw);
  const postalRaw = loc.postal_code ?? loc.postalCode ?? '';
  const postal_code = formatPostalCode(postalRaw, country) || (country ? '0' : '');
  return {
    ...loc,
    country,
    state,
    city,
    cityName: city,
    postal_code,
    postalCode: postal_code
  };
};

// Aplica normalización a claves tipo 'origin' y 'destination' en un payload
export const normalizePayloadLocations = (payload = {}, keys = ['origin', 'destination']) => {
  try {
    const cloned = JSON.parse(JSON.stringify(payload));
    keys.forEach(k => {
      if (cloned[k]) cloned[k] = normalizeLocation(cloned[k]);
    });
    return cloned;
  } catch (_) {
    return payload;
  }
};

// Aplica normalización a 'shipper' y 'recipient' en payload de shipment
export const normalizeShipmentParties = (payload = {}) => {
  try {
    const cloned = JSON.parse(JSON.stringify(payload));
    ['shipper', 'recipient'].forEach(k => {
      if (cloned[k]) cloned[k] = normalizeLocation(cloned[k]);
    });
    return cloned;
  } catch (_) {
    return payload;
  }
};

export default {
  DHL_LIMITS,
  DHL_PATTERNS,
  validateTextLength,
  validateAccountNumber,
  validateWeightAndDimensions,
  validateCommodityCode,
  validatePostalCode,
  validateShipmentDate,
  validateServiceContentCompatibility,
  validateLandedCostItems,
  validateDHLRequest,
  formatPostalCode,
  cleanFriendlyCity,
  normalizeCountryCode,
  normalizeStateCode,
  normalizeCityName,
  normalizeLocation,
  normalizePayloadLocations,
  normalizeShipmentParties
};
