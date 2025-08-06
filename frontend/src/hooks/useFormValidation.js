/**
 * Hook personalizado para validación de formularios DHL
 * Asegura que todos los campos requeridos estén completados antes de permitir el envío
 */

import { useState, useEffect, useMemo } from 'react';

// Configuración de campos requeridos por tipo de formulario
const REQUIRED_FIELDS = {
  rate: {
    'origin.postal_code': 'Código postal de origen',
    'origin.city': 'Ciudad de origen',
    'origin.country': 'País de origen',
    'destination.postal_code': 'Código postal de destino',
    'destination.city': 'Ciudad de destino',
    'destination.country': 'País de destino',
    'weight': 'Peso del paquete',
    'dimensions.length': 'Longitud del paquete',
    'dimensions.width': 'Ancho del paquete',
    'dimensions.height': 'Alto del paquete'
  },
  landedCost: {
    'origin.postal_code': 'Código postal de origen',
    'origin.city': 'Ciudad de origen',
    'origin.country': 'País de origen',
    'destination.postal_code': 'Código postal de destino',
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
    'origin.postal_code': 'Código postal de origen',
    'origin.city': 'Ciudad de origen',
    'origin.country': 'País de origen',
    'destination.postal_code': 'Código postal de destino',
    'destination.city': 'Ciudad de destino',
    'destination.country': 'País de destino',
    'weight': 'Peso del paquete',
    'dimensions.length': 'Longitud del paquete',
    'dimensions.width': 'Ancho del paquete',
    'dimensions.height': 'Alto del paquete',
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
    'tracking_number': 'Número de guía'
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
 * @returns {boolean} true si está vacío
 */
const isEmpty = (value) => {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim() === '';
  if (typeof value === 'number') return value === 0 || isNaN(value);
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

  // Obtener campos requeridos para el tipo de formulario
  const requiredFields = useMemo(() => {
    return { ...REQUIRED_FIELDS[formType], ...customRules };
  }, [formType, customRules]);

  // Validar todos los campos requeridos
  const validateForm = useMemo(() => {
    const errors = {};
    const missingFields = [];

    Object.entries(requiredFields).forEach(([fieldPath, fieldLabel]) => {
      const value = getNestedValue(formData, fieldPath);
      
      if (isEmpty(value)) {
        errors[fieldPath] = `${fieldLabel} es obligatorio`;
        missingFields.push(fieldLabel);
      }
    });

    // Validaciones específicas adicionales
    if (formType === 'landedCost' || formType === 'rate') {
      // Validar que las dimensiones sean positivas
      const dimensions = formData.dimensions || {};
      ['length', 'width', 'height'].forEach(dim => {
        if (dimensions[dim] && dimensions[dim] <= 0) {
          errors[`dimensions.${dim}`] = `${dim.charAt(0).toUpperCase() + dim.slice(1)} debe ser mayor a 0`;
          missingFields.push(`${dim.charAt(0).toUpperCase() + dim.slice(1)} válida`);
        }
      });

      // Validar peso positivo
      if (formData.weight && formData.weight <= 0) {
        errors['weight'] = 'El peso debe ser mayor a 0';
        missingFields.push('Peso válido');
      }
    }

    // Para landed cost, validar múltiples items
    if (formType === 'landedCost' && formData.items) {
      formData.items.forEach((item, index) => {
        const itemRequiredFields = [
          'name', 'description', 'manufacturer_country', 
          'quantity', 'unit_price', 'customs_value', 'commodity_code'
        ];

        itemRequiredFields.forEach(field => {
          const value = item[field];
          if (isEmpty(value)) {
            const fieldKey = `items[${index}].${field}`;
            errors[fieldKey] = `${field} del producto ${index + 1} es obligatorio`;
            missingFields.push(`${field} del producto ${index + 1}`);
          }
        });

        // Validar valores numéricos positivos
        ['quantity', 'unit_price', 'customs_value'].forEach(field => {
          if (item[field] && item[field] <= 0) {
            const fieldKey = `items[${index}].${field}`;
            errors[fieldKey] = `${field} del producto ${index + 1} debe ser mayor a 0`;
            missingFields.push(`${field} válido del producto ${index + 1}`);
          }
        });
      });
    }

    return {
      errors,
      isValid: Object.keys(errors).length === 0,
      missingFields,
      missingCount: missingFields.length
    };
  }, [formData, requiredFields, formType]);

  // Actualizar errores cuando cambie la validación
  useEffect(() => {
    if (hasValidated) {
      setValidationErrors(validateForm.errors);
    }
  }, [validateForm.errors, hasValidated]);

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
      ? '✅ Formulario completo'
      : '❌ Formulario incompleto',
    
    // Lista de campos faltantes para mostrar en la UI
    missingFieldsList: validateForm.missingFields
  };
};

export default useFormValidation;
