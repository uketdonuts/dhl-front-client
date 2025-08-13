/**
 * Componente de input con validación en tiempo real según estándares DHL
 * Incluye límites de caracteres, formateo automático y indicadores visuales
 */

import React, { useState, useEffect } from 'react';
import { validateTextLength, DHL_LIMITS, formatPostalCode } from '../utils/dhlValidations';

const ValidationInput = ({
  value,
  onChange,
  type = 'text',
  field,
  label,
  placeholder,
  required = false,
  countryCode = null,
  className = '',
  disabled = false,
  ...props
}) => {
  const [localValue, setLocalValue] = useState(value || '');
  const [validationError, setValidationError] = useState('');
  const [characterCount, setCharacterCount] = useState(0);

  // Determinar límite de caracteres según el campo
  const getFieldLimit = (fieldName) => {
    const limits = {
      'name': DHL_LIMITS.MAX_NAME_LENGTH,
      'description': DHL_LIMITS.MAX_DESCRIPTION_LENGTH,
      'city': DHL_LIMITS.MAX_CITY_NAME_LENGTH,
      'address': DHL_LIMITS.MAX_ADDRESS_LINE_LENGTH,
      'county': DHL_LIMITS.MAX_COUNTY_NAME_LENGTH,
      'province': DHL_LIMITS.MAX_PROVINCE_CODE_LENGTH,
      'postal_code': DHL_LIMITS.MAX_POSTAL_CODE_LENGTH,
      'account_number': DHL_LIMITS.MAX_ACCOUNT_NUMBER_LENGTH,
      'commodity_code': DHL_LIMITS.MAX_COMMODITY_CODE_LENGTH,
      'category': DHL_LIMITS.MAX_CATEGORY_LENGTH,
      'brand': DHL_LIMITS.MAX_BRAND_LENGTH,
      'part_number': DHL_LIMITS.MAX_PART_NUMBER_LENGTH
    };
    
    return limits[fieldName] || 255; // Default 255 caracteres
  };

  const maxLength = getFieldLimit(field);

  // Actualizar valor local cuando cambie el prop
  useEffect(() => {
    setLocalValue(value || '');
    setCharacterCount((value || '').length);
  }, [value]);

  // Validar el valor actual
  useEffect(() => {
    if (localValue) {
      const errors = validateTextLength(localValue, maxLength, label);
      setValidationError(errors[0] || '');
    } else {
      setValidationError('');
    }
  }, [localValue, maxLength, label]);

  const handleChange = (e) => {
    let newValue = e.target.value;
    
    // Formateo específico por tipo de campo
    if (field === 'postal_code' && countryCode) {
      newValue = formatPostalCode(newValue, countryCode);
    }
    
    // Límite de caracteres hard (evitar que excedan)
    if (newValue.length > maxLength) {
      newValue = newValue.substring(0, maxLength);
    }
    
    setLocalValue(newValue);
    setCharacterCount(newValue.length);
    
    // Llamar onChange del parent
    if (onChange) {
      onChange(newValue);
    }
  };

  // Determinar clases CSS según estado de validación
  const getInputClasses = () => {
    const baseClasses = 'w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2';
    
    if (disabled) {
      return `${baseClasses} bg-gray-100 text-gray-500 border-gray-200`;
    }
    
    if (validationError) {
      return `${baseClasses} border-red-500 focus:border-red-500 focus:ring-red-500 bg-red-50`;
    }
    
    if (localValue && !validationError) {
      return `${baseClasses} border-green-500 focus:border-green-500 focus:ring-green-500 bg-green-50`;
    }
    
    return `${baseClasses} border-gray-300 focus:border-dhl-red focus:ring-dhl-red`;
  };

  // Determinar color del contador de caracteres
  const getCounterColor = () => {
    const percentage = (characterCount / maxLength) * 100;
    
    if (percentage >= 100) return 'text-red-600';
    if (percentage >= 85) return 'text-yellow-600';
    if (percentage >= 70) return 'text-yellow-500';
    return 'text-gray-500';
  };

  return (
    <div className={`validation-input ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      <div className="relative">
        <input
          type={type}
          value={localValue}
          onChange={handleChange}
          placeholder={placeholder}
          className={getInputClasses()}
          disabled={disabled}
          maxLength={maxLength}
          {...props}
        />
        
        {/* Indicador de validación */}
        {localValue && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">
            {validationError ? (
              <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            )}
          </div>
        )}
      </div>
      
      {/* Contador de caracteres */}
      <div className="flex justify-between items-center mt-1">
        <div className="flex-1">
          {validationError && (
            <p className="text-sm text-red-600">{validationError}</p>
          )}
        </div>
        
        <div className={`text-xs ${getCounterColor()}`}>
          {characterCount}/{maxLength}
        </div>
      </div>
      
      {/* Información adicional según el campo */}
      {field === 'postal_code' && countryCode && (
        <p className="text-xs text-gray-500 mt-1">
          {countryCode === 'CA' && 'Formato: A9A 9A9 (ej: K1A 0A6)'}
          {countryCode === 'US' && 'Formato: 12345 o 12345-6789'}
          {countryCode === 'GB' && 'Formato: SW1A 1AA'}
          {!['CA', 'US', 'GB'].includes(countryCode) && 'Use "0" si no aplica código postal'}
        </p>
      )}
      
      {field === 'commodity_code' && (
        <p className="text-xs text-gray-500 mt-1">
          Código HS: 6-10 dígitos. Mínimo 8 recomendado para cálculo preciso de aranceles.
        </p>
      )}
      
      {field === 'account_number' && (
        <p className="text-xs text-gray-500 mt-1">
          Número de cuenta DHL: 9-12 dígitos (ej: 706014493)
        </p>
      )}
    </div>
  );
};

export default ValidationInput;
