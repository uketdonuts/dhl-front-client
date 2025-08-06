/**
 * Información de campos y tooltips para formularios DHL
 * Contiene descripciones, ejemplos y límites según la documentación oficial de DHL API
 */

export const FIELD_LIMITS = {
  // Pesos y dimensiones
  min_weight: 0.01,
  max_weight: 1000.0,
  min_dimension: 1,
  max_dimension: 270,
  min_customs_value: 0.01,
  max_customs_value: 50000.00,
  min_quantity: 1,
  max_quantity: 999999999999,
  
  // Longitudes de campos de texto
  max_name_length: 512,
  max_description_length: 255,
  max_category_length: 50,
  max_brand_length: 50,
  max_part_number_length: 35,
  max_commodity_code_length: 18,
  
  // Límites de envío
  max_items_per_shipment: 1000,
  max_packages_per_shipment: 999,
  max_charges_per_shipment: 20,
  
  // Dimensiones de paquetes
  min_weight_package: 0.001,
  max_weight_package: 999999999999,
  min_dimension_package: 0.001,
  max_dimension_package: 9999999,
  
  // Direcciones
  max_postal_code_length: 12,
  max_city_name_length: 45,
  max_address_line_length: 45,
  max_county_name_length: 45,
  max_province_code_length: 35,
  
  // Cuentas
  max_account_number_length: 12,
  min_account_number_length: 1,
};

export const FIELD_INFO = {
  // === INFORMACIÓN DE ORIGEN Y DESTINO ===
  'origin.country': {
    description: 'Código ISO de 2 letras del país de origen',
    example: 'PA (Panamá), US (Estados Unidos), ES (España)',
    limit: 'Exactamente 2 caracteres',
    required: true,
    validation: 'Debe ser un código ISO válido'
  },
  
  'origin.city': {
    description: 'Nombre de la ciudad de origen',
    example: 'Ciudad de Panamá, Miami, Madrid',
    limit: `Máximo ${FIELD_LIMITS.max_city_name_length} caracteres`,
    required: true,
    validation: 'Solo letras, espacios y caracteres especiales básicos'
  },
  
  'origin.postal_code': {
    description: 'Código postal del origen (opcional si no existe)',
    example: '0816 (Panamá), 33101 (Miami), 28001 (Madrid)',
    limit: `Máximo ${FIELD_LIMITS.max_postal_code_length} caracteres`,
    required: false,
    validation: 'Puede estar vacío si el país no usa códigos postales'
  },
  
  'destination.country': {
    description: 'Código ISO de 2 letras del país de destino',
    example: 'US (Estados Unidos), GB (Reino Unido), DE (Alemania)',
    limit: 'Exactamente 2 caracteres',
    required: true,
    validation: 'Debe ser un código ISO válido soportado por DHL'
  },
  
  'destination.city': {
    description: 'Nombre de la ciudad de destino',
    example: 'New York, London, Berlin',
    limit: `Máximo ${FIELD_LIMITS.max_city_name_length} caracteres`,
    required: true,
    validation: 'Solo letras, espacios y caracteres especiales básicos'
  },
  
  'destination.postal_code': {
    description: 'Código postal del destino',
    example: '10001 (New York), SW1A 1AA (London), 10115 (Berlin)',
    limit: `Máximo ${FIELD_LIMITS.max_postal_code_length} caracteres`,
    required: true,
    validation: 'Formato según las reglas del país de destino'
  },
  
  // === INFORMACIÓN DEL PAQUETE ===
  'weight': {
    description: 'Peso total del envío en kilogramos',
    example: '2.5 kg, 10.3 kg, 0.25 kg',
    limit: `Entre ${FIELD_LIMITS.min_weight} y ${FIELD_LIMITS.max_weight} kg`,
    required: true,
    validation: 'Debe ser un número decimal positivo'
  },
  
  'dimensions.length': {
    description: 'Largo del paquete en centímetros',
    example: '30 cm, 45.5 cm, 120 cm',
    limit: `Entre ${FIELD_LIMITS.min_dimension} y ${FIELD_LIMITS.max_dimension} cm`,
    required: true,
    validation: 'Debe ser un número decimal positivo'
  },
  
  'dimensions.width': {
    description: 'Ancho del paquete en centímetros',
    example: '20 cm, 30.5 cm, 80 cm',
    limit: `Entre ${FIELD_LIMITS.min_dimension} y ${FIELD_LIMITS.max_dimension} cm`,
    required: true,
    validation: 'Debe ser un número decimal positivo'
  },
  
  'dimensions.height': {
    description: 'Alto del paquete en centímetros',
    example: '15 cm, 25.3 cm, 60 cm',
    limit: `Entre ${FIELD_LIMITS.min_dimension} y ${FIELD_LIMITS.max_dimension} cm`,
    required: true,
    validation: 'Debe ser un número decimal positivo'
  },
  
  // === INFORMACIÓN DE PRODUCTOS ===
  'items.name': {
    description: 'Nombre corto del producto',
    example: 'iPhone 15, Zapatos Deportivos, Camiseta Algodón',
    limit: `Máximo ${FIELD_LIMITS.max_name_length} caracteres`,
    required: true,
    validation: 'Descripción clara y concisa del producto'
  },
  
  'items.description': {
    description: 'Descripción completa del producto para aduanas',
    example: 'Smartphone Apple iPhone 15 Pro 256GB Color Azul Titanio con Cargador',
    limit: `Máximo ${FIELD_LIMITS.max_description_length} caracteres`,
    required: true,
    validation: 'Debe ser detallada para facilitar el proceso aduanero'
  },
  
  'items.manufacturer_country': {
    description: 'País donde se fabricó el producto (código ISO)',
    example: 'CN (China), US (Estados Unidos), DE (Alemania)',
    limit: 'Exactamente 2 caracteres',
    required: true,
    validation: 'Debe ser el país real de manufactura, no de la marca'
  },
  
  'items.quantity': {
    description: 'Cantidad de unidades del producto',
    example: '1 unidad, 5 piezas, 12 cajas',
    limit: `Entre ${FIELD_LIMITS.min_quantity} y ${FIELD_LIMITS.max_quantity}`,
    required: true,
    validation: 'Debe ser un número entero positivo'
  },
  
  'items.unit_price': {
    description: 'Precio unitario del producto en la moneda especificada',
    example: '$150.00, €89.99, £45.50',
    limit: 'Debe ser mayor a 0',
    required: true,
    validation: 'Precio real de venta o valor comercial'
  },
  
  'items.customs_value': {
    description: 'Valor declarado para aduanas por unidad',
    example: '$150.00, €89.99, £45.50',
    limit: `Entre $${FIELD_LIMITS.min_customs_value} y $${FIELD_LIMITS.max_customs_value}`,
    required: true,
    validation: 'Debe coincidir con el valor real del producto'
  },
  
  'items.commodity_code': {
    description: 'Código HS (Sistema Armonizado) para clasificación aduanera',
    example: '851712 (smartphones), 640319 (zapatos), 610910 (camisetas)',
    limit: `Máximo ${FIELD_LIMITS.max_commodity_code_length} dígitos`,
    required: true,
    validation: 'Use código específico de 8-10 dígitos para cálculo preciso de aranceles'
  },
  
  'items.part_number': {
    description: 'Número de parte o SKU del producto (opcional)',
    example: 'SKU-12345, MODEL-ABC123, REF-789XYZ',
    limit: `Máximo ${FIELD_LIMITS.max_part_number_length} caracteres`,
    required: false,
    validation: 'Código interno del producto para identificación'
  },
  
  'items.category': {
    description: 'Código de categoría del producto según clasificación DHL',
    example: '201 (Sneakers), 1205 (Computing), 1601 (Toys & Games)',
    limit: `Máximo ${FIELD_LIMITS.max_category_length} caracteres - Solo códigos válidos de DHL`,
    required: false,
    validation: 'Debe ser un código de categoría válido de DHL'
  },

  // === INFORMACIÓN PARA COTIZACIÓN DE TARIFAS ===
  'rate.origin.postal_code': {
    description: 'Código postal del lugar de origen del envío',
    example: '0000 (Panamá), 33101 (Miami), 28001 (Madrid)',
    limit: `Máximo ${FIELD_LIMITS.max_postal_code_length} caracteres`,
    required: false,
    validation: 'Puede estar vacío si el país no usa códigos postales'
  },

  'rate.origin.city': {
    description: 'Ciudad de origen del envío',
    example: 'Ciudad de Panamá, Miami, Madrid',
    limit: `Máximo ${FIELD_LIMITS.max_city_name_length} caracteres`,
    required: true,
    validation: 'Nombre oficial de la ciudad'
  },

  'rate.origin.state': {
    description: 'Estado o provincia de origen (si aplica)',
    example: 'FL (Florida), CA (California), MD (Madrid)',
    limit: `Máximo ${FIELD_LIMITS.max_province_code_length} caracteres`,
    required: false,
    validation: 'Código o nombre del estado/provincia'
  },

  'rate.origin.country': {
    description: 'Código ISO de 2 letras del país de origen',
    example: 'PA (Panamá), US (Estados Unidos), ES (España)',
    limit: 'Exactamente 2 caracteres',
    required: true,
    validation: 'Debe ser un código ISO válido'
  },

  'rate.destination.postal_code': {
    description: 'Código postal del lugar de destino del envío',
    example: '10001 (New York), SW1A 1AA (London), 10115 (Berlin)',
    limit: `Máximo ${FIELD_LIMITS.max_postal_code_length} caracteres`,
    required: true,
    validation: 'Formato según las reglas del país de destino'
  },

  'rate.destination.city': {
    description: 'Ciudad de destino del envío',
    example: 'New York, London, Berlin',
    limit: `Máximo ${FIELD_LIMITS.max_city_name_length} caracteres`,
    required: true,
    validation: 'Nombre oficial de la ciudad'
  },

  'rate.destination.state': {
    description: 'Estado o provincia de destino (si aplica)',
    example: 'NY (New York), CA (California), LND (London)',
    limit: `Máximo ${FIELD_LIMITS.max_province_code_length} caracteres`,
    required: false,
    validation: 'Código o nombre del estado/provincia'
  },

  'rate.destination.country': {
    description: 'Código ISO de 2 letras del país de destino',
    example: 'US (Estados Unidos), GB (Reino Unido), DE (Alemania)',
    limit: 'Exactamente 2 caracteres',
    required: true,
    validation: 'Debe ser un código ISO válido soportado por DHL'
  },

  'rate.weight': {
    description: 'Peso total del envío en kilogramos para cálculo de tarifa',
    example: '2.5 kg, 10.3 kg, 0.25 kg',
    limit: `Entre ${FIELD_LIMITS.min_weight} y ${FIELD_LIMITS.max_weight} kg`,
    required: true,
    validation: 'Debe ser un número decimal positivo. DHL cobra por peso o volumen, lo que sea mayor'
  },

  'rate.service': {
    description: 'Tipo de contenido del envío que afecta las tarifas',
    example: 'P (Paquetes/Mercancías), D (Documentos)',
    limit: 'P o D únicamente',
    required: true,
    validation: 'Los documentos tienen tarifas diferentes a los paquetes'
  },

  'rate.account_number': {
    description: 'Número de cuenta DHL para tarifas preferenciales',
    example: '706014493, 123456789, 987654321',
    limit: `Entre ${FIELD_LIMITS.min_account_number_length} y ${FIELD_LIMITS.max_account_number_length} caracteres`,
    required: false,
    validation: 'Usar cuenta activa para obtener mejores tarifas. Sin cuenta se usan tarifas públicas'
  },

  'rate.dimensions.length': {
    description: 'Largo del paquete en centímetros para cálculo volumétrico',
    example: '30 cm, 45.5 cm, 120 cm',
    limit: `Entre ${FIELD_LIMITS.min_dimension} y ${FIELD_LIMITS.max_dimension} cm`,
    required: true,
    validation: 'Dimensión más larga del paquete. Afecta el peso volumétrico (L×W×H÷5000)'
  },

  'rate.dimensions.width': {
    description: 'Ancho del paquete en centímetros para cálculo volumétrico',
    example: '20 cm, 30.5 cm, 80 cm',
    limit: `Entre ${FIELD_LIMITS.min_dimension} y ${FIELD_LIMITS.max_dimension} cm`,
    required: true,
    validation: 'Segunda dimensión del paquete. Se usa en la fórmula L×W×H÷5000 para peso volumétrico'
  },

  'rate.dimensions.height': {
    description: 'Alto del paquete en centímetros para cálculo volumétrico',
    example: '15 cm, 25.3 cm, 60 cm',
    limit: `Entre ${FIELD_LIMITS.min_dimension} y ${FIELD_LIMITS.max_dimension} cm`,
    required: true,
    validation: 'Tercera dimensión del paquete. DHL cobra por el mayor entre peso real y volumétrico'
  },

  // === INFORMACIÓN DE MARCAS Y VALIDACIONES ADICIONALES ===
  'items.brand': {
    description: 'Marca del producto',
    example: 'Apple, Nike, Samsung, Zara',
    limit: `Máximo ${FIELD_LIMITS.max_brand_length} caracteres`,
    required: false,
    validation: 'Marca reconocida del producto'
  },
  
  // === CONFIGURACIÓN DEL ENVÍO ===
  'currency_code': {
    description: 'Moneda para el cálculo de costos',
    example: 'USD (Dólares), EUR (Euros), GBP (Libras)',
    limit: 'Exactamente 3 caracteres',
    required: true,
    validation: 'Debe ser una moneda soportada por DHL'
  },
  
  'is_customs_declarable': {
    description: 'Indica si el envío contiene productos declarables en aduanas',
    example: 'true (productos comerciales), false (documentos)',
    limit: 'Valor booleano',
    required: true,
    validation: 'true para productos con valor comercial'
  },
  
  'is_dtp_requested': {
    description: 'DTP: DHL paga aranceles e impuestos en destino',
    example: 'true (DHL paga), false (destinatario paga)',
    limit: 'Valor booleano',
    required: false,
    validation: 'Servicio premium que simplifica la entrega'
  },
  
  'is_insurance_requested': {
    description: 'Seguro adicional para el envío',
    example: 'true (con seguro), false (sin seguro)',
    limit: 'Valor booleano',
    required: false,
    validation: 'Recomendado para envíos de alto valor'
  },
  
  'shipment_purpose': {
    description: 'Propósito del envío',
    example: 'commercial (B2B), personal (B2C)',
    limit: 'commercial o personal',
    required: true,
    validation: 'Afecta el proceso aduanero y los aranceles'
  },
  
  'service': {
    description: 'Tipo de servicio DHL',
    example: 'P (Packages - paquetes), D (Documents - documentos)',
    limit: 'P o D',
    required: true,
    validation: 'P para productos físicos, D para documentos'
  },
  
  'account_number': {
    description: 'Número de cuenta DHL Express',
    example: '706014493, 123456789',
    limit: `Entre ${FIELD_LIMITS.min_account_number_length} y ${FIELD_LIMITS.max_account_number_length} dígitos`,
    required: true,
    validation: 'Cuenta DHL válida y activa'
  },
  
  // === OPCIONES AVANZADAS ===
  'get_cost_breakdown': {
    description: 'Solicitar desglose detallado de costos',
    example: 'true (mostrar detalles), false (solo total)',
    limit: 'Valor booleano',
    required: false,
    validation: 'Útil para entender todos los cargos aplicados'
  },
  
  'charges': {
    description: 'Cargos adicionales al envío',
    example: 'Seguro: $25.00, Combustible: $15.50',
    limit: `Máximo ${FIELD_LIMITS.max_charges_per_shipment} cargos`,
    required: false,
    validation: 'Cargos extras que se suman al costo base'
  },
  
  'transport_mode': {
    description: 'Modo de transporte',
    example: 'air (aéreo), ocean (marítimo), ground (terrestre)',
    limit: 'air, ocean, o ground',
    required: false,
    validation: 'DHL Express usa principalmente transporte aéreo'
  }
};

/**
 * Obtiene la información de un campo específico
 * @param {string} fieldPath - Ruta del campo (ej: 'items.name', 'origin.country')
 * @returns {object|null} - Información del campo o null si no existe
 */
export const getFieldInfo = (fieldPath) => {
  return FIELD_INFO[fieldPath] || null;
};

/**
 * Obtiene el límite de un campo específico
 * @param {string} limitKey - Clave del límite (ej: 'max_name_length')
 * @returns {number|null} - Valor del límite o null si no existe
 */
export const getFieldLimit = (limitKey) => {
  return FIELD_LIMITS[limitKey] || null;
};

/**
 * Valida si un valor cumple con los límites del campo
 * @param {string} fieldPath - Ruta del campo
 * @param {any} value - Valor a validar
 * @returns {object} - {isValid: boolean, message: string}
 */
export const validateField = (fieldPath, value) => {
  const info = getFieldInfo(fieldPath);
  if (!info) {
    return { isValid: true, message: '' };
  }
  
  // Validación básica según el tipo de campo
  if (info.required && (!value || value.toString().trim() === '')) {
    return { isValid: false, message: 'Este campo es obligatorio' };
  }
  
  // Validación de longitud para strings
  if (typeof value === 'string') {
    if (fieldPath.includes('country') && value.length !== 2) {
      return { isValid: false, message: 'Debe ser exactamente 2 caracteres (código ISO)' };
    }
    
    if (fieldPath.includes('currency') && value.length !== 3) {
      return { isValid: false, message: 'Debe ser exactamente 3 caracteres (código ISO)' };
    }
    
    // Verificar límites de longitud
    const lengthLimits = {
      'name': FIELD_LIMITS.max_name_length,
      'description': FIELD_LIMITS.max_description_length,
      'city': FIELD_LIMITS.max_city_name_length,
      'postal_code': FIELD_LIMITS.max_postal_code_length,
      'part_number': FIELD_LIMITS.max_part_number_length,
      'category': FIELD_LIMITS.max_category_length,
      'brand': FIELD_LIMITS.max_brand_length,
      'commodity_code': FIELD_LIMITS.max_commodity_code_length,
      'account_number': FIELD_LIMITS.max_account_number_length
    };
    
    for (const [key, limit] of Object.entries(lengthLimits)) {
      if (fieldPath.includes(key) && value.length > limit) {
        return { isValid: false, message: `Máximo ${limit} caracteres` };
      }
    }
  }
  
  // Validación de números
  if (typeof value === 'number') {
    if (fieldPath.includes('weight')) {
      if (value < FIELD_LIMITS.min_weight || value > FIELD_LIMITS.max_weight) {
        return { 
          isValid: false, 
          message: `Debe estar entre ${FIELD_LIMITS.min_weight} y ${FIELD_LIMITS.max_weight} kg` 
        };
      }
    }
    
    if (fieldPath.includes('dimension')) {
      if (value < FIELD_LIMITS.min_dimension || value > FIELD_LIMITS.max_dimension) {
        return { 
          isValid: false, 
          message: `Debe estar entre ${FIELD_LIMITS.min_dimension} y ${FIELD_LIMITS.max_dimension} cm` 
        };
      }
    }
    
    if (fieldPath.includes('quantity') && (value < FIELD_LIMITS.min_quantity || value > FIELD_LIMITS.max_quantity)) {
      return { 
        isValid: false, 
        message: `Debe estar entre ${FIELD_LIMITS.min_quantity} y ${FIELD_LIMITS.max_quantity}` 
      };
    }
    
    if (fieldPath.includes('customs_value')) {
      if (value < FIELD_LIMITS.min_customs_value || value > FIELD_LIMITS.max_customs_value) {
        return { 
          isValid: false, 
          message: `Debe estar entre $${FIELD_LIMITS.min_customs_value} y $${FIELD_LIMITS.max_customs_value}` 
        };
      }
    }
  }
  
  return { isValid: true, message: 'Válido' };
};

const fieldInfoModule = {
  FIELD_INFO,
  FIELD_LIMITS,
  getFieldInfo,
  getFieldLimit,
  validateField
};

export default fieldInfoModule;
