/**
 * Componente para inputs numéricos con validación DHL
 * Maneja peso, dimensiones, cantidades y valores monetarios
 */

import React, { useState, useEffect } from 'react';
import { validateWeightAndDimensions, DHL_LIMITS } from '../utils/dhlValidations';

const ValidationNumberInput = ({
  value,
  onChange,
  field,
  label,
  placeholder,
  required = false,
  unit = '',
  min,
  max,
  step = 'any',
  className = '',
  disabled = false,
  relatedValues = {}, // Para validaciones cruzadas (peso vs dimensiones)
  ...props
}) => {
  const [localValue, setLocalValue] = useState(value || '');
  const [validationError, setValidationError] = useState('');
  const [warning, setWarning] = useState('');

  // Determinar límites según el campo
  const getFieldLimits = (fieldName) => {
    const limits = {
      'weight': { min: DHL_LIMITS.MIN_WEIGHT, max: DHL_LIMITS.MAX_WEIGHT },
      'length': { min: DHL_LIMITS.MIN_DIMENSION, max: DHL_LIMITS.MAX_DIMENSION },
      'width': { min: DHL_LIMITS.MIN_DIMENSION, max: DHL_LIMITS.MAX_DIMENSION },
      'height': { min: DHL_LIMITS.MIN_DIMENSION, max: DHL_LIMITS.MAX_DIMENSION },
      'quantity': { min: DHL_LIMITS.MIN_QUANTITY, max: DHL_LIMITS.MAX_QUANTITY },
      'unit_price': { min: 0.01, max: 999999.99 },
      'customs_value': { min: DHL_LIMITS.MIN_CUSTOMS_VALUE, max: DHL_LIMITS.MAX_CUSTOMS_VALUE }
    };
    
    return limits[fieldName] || { min: 0, max: 999999999 };
  };

  const fieldLimits = getFieldLimits(field);
  const minValue = min !== undefined ? min : fieldLimits.min;
  const maxValue = max !== undefined ? max : fieldLimits.max;

  // Actualizar valor local cuando cambie el prop
  useEffect(() => {
    setLocalValue(value || '');
  }, [value]);

  // Validar el valor actual
  useEffect(() => {
    if (localValue !== '' && localValue !== null && localValue !== undefined) {
      const numValue = parseFloat(localValue);
      
      if (isNaN(numValue)) {
        setValidationError('Debe ser un número válido');
        setWarning('');
        return;
      }
      
      if (numValue < minValue) {
        setValidationError(`Valor mínimo: ${minValue}${unit}`);
        setWarning('');
        return;
      }
      
      if (numValue > maxValue) {
        setValidationError(`Valor máximo: ${maxValue}${unit}`);
        setWarning('');
        return;
      }
      
      setValidationError('');
      
      // Validaciones específicas y warnings
      if (field === 'weight' && relatedValues.dimensions) {
        const dimensionValidation = validateWeightAndDimensions(numValue, relatedValues.dimensions);
        if (dimensionValidation.warnings.length > 0) {
          setWarning(dimensionValidation.warnings[0]);
        } else {
          setWarning('');
        }
      }
      
      // Warning para valores inusuales
      if (field === 'weight') {
        if (numValue > 1000) {
          setWarning('Peso muy alto - Verificar unidades (kg)');
        } else if (numValue < 0.1) {
          setWarning('Peso muy bajo - Verificar unidades (kg)');
        }
      }
      
      if (['length', 'width', 'height'].includes(field)) {
        if (numValue > 200) {
          setWarning('Dimensión muy grande - Verificar unidades (cm)');
        } else if (numValue < 1) {
          setWarning('Dimensión muy pequeña - Verificar unidades (cm)');
        }
      }
      
      if (field === 'customs_value' && relatedValues.unit_price && relatedValues.quantity) {
        const totalPrice = relatedValues.unit_price * relatedValues.quantity;
        const difference = Math.abs(totalPrice - numValue) / totalPrice;
        
        if (difference > 0.2) {
          setWarning(`Valor aduanero (${numValue}) difiere del precio total (${totalPrice.toFixed(2)})`);
        }
      }
      
    } else {
      setValidationError('');
      setWarning('');
    }
  }, [localValue, minValue, maxValue, unit, field, relatedValues]);

  const handleChange = (e) => {
    const newValue = e.target.value;
    setLocalValue(newValue);
    
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
    
    if (warning) {
      return `${baseClasses} border-yellow-500 focus:border-yellow-500 focus:ring-yellow-500 bg-yellow-50`;
    }
    
    if (localValue && !validationError && !warning) {
      return `${baseClasses} border-green-500 focus:border-green-500 focus:ring-green-500 bg-green-50`;
    }
    
    return `${baseClasses} border-gray-300 focus:border-dhl-red focus:ring-dhl-red`;
  };

  // Formatear valor para mostrar
  const getDisplayValue = () => {
    if (field === 'unit_price' || field === 'customs_value') {
      const num = parseFloat(localValue);
      if (!isNaN(num) && localValue !== '') {
        return num.toFixed(2);
      }
    }
    return localValue;
  };

  return (
    <div className={`validation-number-input ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
          {unit && <span className="text-gray-500 ml-1">({unit})</span>}
        </label>
      )}
      
      <div className="relative">
        <input
          type="number"
          value={localValue}
          onChange={handleChange}
          placeholder={placeholder}
          className={getInputClasses()}
          disabled={disabled}
          min={minValue}
          max={maxValue}
          step={step}
          {...props}
        />
        
        {/* Indicador de validación */}
        {localValue && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">
            {validationError ? (
              <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            ) : warning ? (
              <svg className="h-5 w-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            )}
          </div>
        )}
        
        {/* Unidad de medida */}
        {unit && localValue && (
          <div className="absolute inset-y-0 right-8 flex items-center pr-3 text-gray-500 text-sm pointer-events-none">
            {unit}
          </div>
        )}
      </div>
      
      {/* Mensajes de validación */}
      <div className="mt-1">
        {validationError && (
          <p className="text-sm text-red-600">{validationError}</p>
        )}
        {!validationError && warning && (
          <p className="text-sm text-yellow-600">⚠️ {warning}</p>
        )}
      </div>
      
      {/* Información de límites */}
      <div className="text-xs text-gray-500 mt-1">
        Rango: {minValue} - {maxValue} {unit}
      </div>
    </div>
  );
};

export default ValidationNumberInput;
