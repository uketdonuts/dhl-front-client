/**
 * Hook personalizado para validación de formularios DHL
 * Asegura que todos los campos requeridos estén completados antes de permitir el envío
 * Incluye validaciones avanzadas según documentación DHL API
 */

import { useState, useEffect, useMemo, useRef } from 'react';
import { validateDHLRequest, validateTextLength, validateAccountNumber, validateWeightAndDimensions, validatePostalCode, formatPostalCode, DHL_LIMITS } from '../utils/dhlValidations';

// Configuración de campos requeridos por tipo de formulario
const REQUIRED_FIELDS = {
  rate: {
    'origin.city': 'Ciudad de origen',
    'origin.country': 'País de origen',
    'destination.city': 'Ciudad de destino',
    'destination.country': 'País de destino',
    'weight': 'Peso del paquete',
    'dimensions.length': 'Longitud del paquete',
    'dimensions.width': 'Ancho del paquete',
    'dimensions.height': 'Alto del paquete'
  },
  landedCost: {
    'origin.city': 'Ciudad de origen',
    'origin.country': 'País de origen',
    'destination.city': 'Ciudad de destino',
    'destination.country': 'País de destino',
    'weight': 'Peso del paquete',
    'dimensions.length': 'Longitud del paquete',
    'dimensions.width': 'Ancho del paquete',
    'dimensions.height': 'Alto del paquete',
    'currency_code': 'Código de moneda',
    'items[0].name': 'Nombre del producto',
    'items[0].description': 'Descripción del producto',
    'items[0].manufacturer_country': 'País de fabricación',
    'items[0].quantity': 'Cantidad',
    'items[0].unit_price': 'Precio unitario',
    'items[0].customs_value': 'Valor aduanero',
    'items[0].commodity_code': 'Código HS'
  },
  shipment: {
    'shipper.city': 'Ciudad de origen',
    'shipper.country': 'País de origen',
    'recipient.city': 'Ciudad de destino',
    'recipient.country': 'País de destino',
    'package.weight': 'Peso del paquete',
    'package.length': 'Longitud del paquete',
    'package.width': 'Ancho del paquete',
    'package.height': 'Alto del paquete',
    'shipper.name': 'Nombre del remitente',
    'shipper.email': 'Email del remitente',
    'shipper.phone': 'Teléfono del remitente',
    'recipient.name': 'Nombre del destinatario',
    'recipient.email': 'Email del destinatario',
    'recipient.phone': 'Teléfono del destinatario'
  },
  tracking: {
    'tracking_number': 'Número de guía'
  },
  epod: {
    'shipment_id': 'Número de envío'
  }
};

/**
 * Obtiene el valor de un campo anidado usando notación de puntos
 * @param {Object} obj - Objeto donde buscar
 * @param {string} path - Ruta del campo (ej: "origin.city", "items[0].name")
 * @returns {*} Valor del campo o undefined
 */
const getNestedValue = (obj, path) => {
  return path.split(/[\.\[\]]/).filter(Boolean).reduce((current, key) => {
    return current && current[key] !== undefined ? current[key] : undefined;
  }, obj);
};

/**
 * Verifica si un valor está vacío o es inválido
 * @param {*} value - Valor a verificar
 * @param {string} fieldPath - Ruta del campo para validaciones específicas
 * @returns {boolean} true si está vacío
 */
const isEmpty = (value, fieldPath = '') => {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim() === '';
  
  // Para campos de precio y valor aduanero, 0 es considerado vacío (deben ser > 0)
  if (fieldPath.includes('unit_price') || fieldPath.includes('customs_value')) {
    return value <= 0 || isNaN(value);
  }
  
  // Para campos de peso y dimensiones, 0 es considerado vacío
  if (fieldPath === 'weight' || fieldPath.includes('dimensions.')) {
    return value <= 0 || isNaN(value);
  }
  
  // Para cantidad, debe ser >= 1
  if (fieldPath.includes('quantity')) {
    return value < 1 || isNaN(value);
  }
  
  // Para otros campos numéricos, solo NaN es inválido
  if (typeof value === 'number') return isNaN(value);
  if (Array.isArray(value)) return value.length === 0;
  return false;
};

/**
 * Hook para validación de formularios DHL
 * @param {Object} formData - Datos del formulario
 * @param {string} formType - Tipo de formulario ('rate', 'landedCost', 'shipment', etc.)
 * @param {Object} customRules - Reglas de validación personalizadas
 * @returns {Object} Estado de validación y métodos
 */
export const useFormValidation = (formData, formType = 'rate', customRules = {}) => {
  const [validationErrors, setValidationErrors] = useState({});
  const [hasValidated, setHasValidated] = useState(false);
  const previousErrorsRef = useRef({});

  // Obtener campos requeridos para el tipo de formulario
  const requiredFields = useMemo(() => {
    return { ...REQUIRED_FIELDS[formType], ...customRules };
  }, [formType, customRules]);

  // Validar todos los campos requeridos
  const validateForm = useMemo(() => {
    const errors = {};
    const missingFields = [];
    const warnings = [];

    // Validaciones básicas de campos requeridos
    Object.entries(requiredFields).forEach(([fieldPath, fieldLabel]) => {
      const value = getNestedValue(formData, fieldPath);
      
      if (isEmpty(value, fieldPath)) {
        errors[fieldPath] = `${fieldLabel} es obligatorio`;
        missingFields.push(fieldLabel);
      }
    });

    // Validaciones avanzadas usando el nuevo sistema - excluyendo códigos postales y commodity codes
    const dhlValidation = validateDHLRequest(formData, formType);
    
    // Filtrar errores de códigos postales y commodity codes ya que los manejamos como advertencias
    const dhlErrors = dhlValidation.errors.filter(error => 
      !error.includes('código postal') && 
      !error.includes('postal code') &&
      !error.includes('Código postal') &&
      !error.includes('Código HS') &&
      !error.includes('commodity code')
    );
    
    // Agregar errores de validación DHL (sin códigos postales ni commodity codes)
    if (dhlErrors.length > 0) {
      errors['dhl_validation'] = dhlErrors.join('; ');
    }

    // Almacenar warnings para mostrar al usuario (incluyendo códigos postales y commodity codes)
    warnings.push(...dhlValidation.warnings);

    // Validaciones específicas adicionales por tipo de formulario
    if (formType === 'landedCost' || formType === 'rate') {
      
      // Validar peso y dimensiones con límites DHL
      if (formData.weight && formData.dimensions) {
        const weightDimValidation = validateWeightAndDimensions(formData.weight, formData.dimensions);
        weightDimValidation.errors.forEach(error => {
          errors['weight_dimensions'] = errors['weight_dimensions'] ? 
            `${errors['weight_dimensions']}; ${error}` : error;
        });
        warnings.push(...weightDimValidation.warnings);
      }

      // Validar códigos postales - usar "0" por defecto en lugar de bloquear
      if (formData.origin?.postal_code && formData.origin?.country) {
        const originPostalValidation = validatePostalCode(formData.origin.postal_code, formData.origin.country);
        if (originPostalValidation.errors.length > 0) {
          // Solo advertencia, no error bloqueante
          warnings.push(`Código postal de origen: ${originPostalValidation.errors[0]} - Se usará "0" por defecto`);
        }
      }

      if (formData.destination?.postal_code && formData.destination?.country) {
        const destPostalValidation = validatePostalCode(formData.destination.postal_code, formData.destination.country);
        if (destPostalValidation.errors.length > 0) {
          // Solo advertencia, no error bloqueante
          warnings.push(`Código postal de destino: ${destPostalValidation.errors[0]} - Se usará "0" por defecto`);
        }
      }

      // Validar longitudes de campos de texto
      if (formData.origin?.city) {
        const cityErrors = validateTextLength(formData.origin.city, DHL_LIMITS.MAX_CITY_NAME_LENGTH, 'Ciudad de origen');
        if (cityErrors.length > 0) {
          errors['origin.city'] = cityErrors[0];
        }
      }

      if (formData.destination?.city) {
        const cityErrors = validateTextLength(formData.destination.city, DHL_LIMITS.MAX_CITY_NAME_LENGTH, 'Ciudad de destino');
        if (cityErrors.length > 0) {
          errors['destination.city'] = cityErrors[0];
        }
      }

      // Validar número de cuenta DHL si está presente
      if (formData.account_number) {
        const accountErrors = validateAccountNumber(formData.account_number);
        if (accountErrors.length > 0) {
          // Como warning en lugar de error bloqueante
          warnings.push(accountErrors[0]);
        }
      }
    }

    // Para landed cost, validar múltiples items con validaciones avanzadas
    if (formType === 'landedCost' && formData.items) {
      formData.items.forEach((item, index) => {
        const itemRequiredFields = [
          'name', 'description', 'manufacturer_country', 
          'quantity', 'unit_price', 'customs_value', 'commodity_code'
        ];

        itemRequiredFields.forEach(field => {
          const value = item[field];
          if (isEmpty(value, `items[${index}].${field}`)) {
            const fieldKey = `items[${index}].${field}`;
            errors[fieldKey] = `${field} del producto ${index + 1} es obligatorio`;
            missingFields.push(`${field} del producto ${index + 1}`);
          }
        });

        // Validaciones específicas para productos
        if (item.name) {
          const nameErrors = validateTextLength(item.name, DHL_LIMITS.MAX_NAME_LENGTH, `Nombre del producto ${index + 1}`);
          if (nameErrors.length > 0) {
            errors[`items[${index}].name`] = nameErrors[0];
          }
        }

        if (item.description) {
          const descErrors = validateTextLength(item.description, DHL_LIMITS.MAX_DESCRIPTION_LENGTH, `Descripción del producto ${index + 1}`);
          if (descErrors.length > 0) {
            errors[`items[${index}].description`] = descErrors[0];
          }
        }

        // Validar cantidades y valores dentro de límites DHL
        if (item.quantity) {
          const qty = parseFloat(item.quantity);
          if (qty < DHL_LIMITS.MIN_QUANTITY || qty > DHL_LIMITS.MAX_QUANTITY) {
            errors[`items[${index}].quantity`] = `Cantidad debe estar entre ${DHL_LIMITS.MIN_QUANTITY} y ${DHL_LIMITS.MAX_QUANTITY}`;
          }
        }

        if (item.customs_value) {
          const value = parseFloat(item.customs_value);
          if (value < DHL_LIMITS.MIN_CUSTOMS_VALUE || value > DHL_LIMITS.MAX_CUSTOMS_VALUE) {
            errors[`items[${index}].customs_value`] = `Valor aduanero debe estar entre ${DHL_LIMITS.MIN_CUSTOMS_VALUE} y ${DHL_LIMITS.MAX_CUSTOMS_VALUE}`;
          }
        }
      });
    }

    return {
      errors,
      isValid: Object.keys(errors).length === 0,
      missingFields,
      missingCount: missingFields.length,
      warnings,
      warningCount: warnings.length
    };
  }, [formData, requiredFields, formType]); // Depender de formData y requiredFields para actualizarse

  // Actualizar errores cuando cambie la validación
  useEffect(() => {
    if (hasValidated) {
      setValidationErrors(validateForm.errors);
    }
  }, [hasValidated, validateForm.errors]); // Depender de los errores también

  // Método para forzar validación (llamar antes de enviar)
  const validate = () => {
    setHasValidated(true);
    setValidationErrors(validateForm.errors);
    return validateForm.isValid;
  };

  // Método para limpiar validación
  const clearValidation = () => {
    setHasValidated(false);
    setValidationErrors({});
  };

  // Verificar si un campo específico tiene error
  const hasFieldError = (fieldPath) => {
    return hasValidated && !!validationErrors[fieldPath];
  };

  // Obtener mensaje de error de un campo específico
  const getFieldError = (fieldPath) => {
    return validationErrors[fieldPath] || '';
  };

  // Obtener clase CSS para el campo (con error o sin error)
  const getFieldClass = (fieldPath, baseClass = '') => {
    const errorClass = hasFieldError(fieldPath) 
      ? 'border-red-500 focus:border-red-500 focus:ring-red-500' 
      : 'border-gray-300 focus:border-dhl-red focus:ring-dhl-red';
    
    return `${baseClass} ${errorClass}`;
  };

  return {
    // Estado de validación
    isValid: validateForm.isValid,
    errors: validationErrors,
    missingFields: validateForm.missingFields,
    missingCount: validateForm.missingCount,
    warnings: validateForm.warnings || [],
    warningCount: validateForm.warningCount || 0,
    hasValidated,

    // Métodos
    validate,
    clearValidation,
    hasFieldError,
    getFieldError,
    getFieldClass,

    // Información para mostrar al usuario
    canSubmit: validateForm.isValid,
    summary: validateForm.isValid 
      ? (validateForm.warningCount > 0 
          ? `⚠️ Formulario completo con ${validateForm.warningCount} advertencias`
          : '✅ Formulario completo')
      : `❌ Formulario incompleto (${validateForm.missingCount} campos faltantes)`,
    
    // Lista de campos faltantes para mostrar en la UI
    missingFieldsList: validateForm.missingFields,
    warningsList: validateForm.warnings || []
  };
};

export default useFormValidation;
