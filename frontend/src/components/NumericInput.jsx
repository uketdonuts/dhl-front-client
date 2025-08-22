import React, { useEffect, useRef, useState } from 'react';

/**
 * Componente de input numérico optimizado para dispositivos móviles
 * 
 * Soluciona problemas comunes con type="number" en móviles:
 * - Ceros iniciales que no se pueden borrar
 * - Comportamiento inconsistente del teclado
 * - Validación incorrecta
 * 
 * @param {Object} props - Propiedades del componente
 * @param {string|number} props.value - Valor actual del input
 * @param {Function} props.onChange - Función callback para cambios de valor
 * @param {string} props.placeholder - Texto placeholder
 * @param {number} props.min - Valor mínimo permitido
 * @param {number} props.max - Valor máximo permitido
 * @param {number} props.step - Incremento para decimales
 * @param {boolean} props.allowDecimals - Permitir números decimales (default: true)
 * @param {number} props.decimals - Número máximo de decimales (default: 2)
 * @param {string} props.className - Clases CSS adicionales
 * @param {boolean} props.disabled - Estado deshabilitado
 * @param {string} props.id - ID del input
 * @param {string} props.name - Nombre del input
 */
const NumericInput = ({
  value = '',
  onChange,
  placeholder = '',
  min,
  max,
  step = 0.01,
  allowDecimals = true,
  decimals = 2,
  className = '',
  disabled = false,
  id,
  name,
  ...props
}) => {
  // Estado interno para prevenir que el valor del padre sobrescriba mientras el usuario escribe (ej. "0.")
  const [displayValue, setDisplayValue] = useState('');
  const isFocusedRef = useRef(false);

  // Inicializar/sincronizar displayValue cuando no está enfocado
  useEffect(() => {
    if (!isFocusedRef.current) {
      setDisplayValue(formatDisplayValue(value));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);
  
  /**
   * Formatea el valor para mostrar en el input
   */
  const formatDisplayValue = (val) => {
    if (val === '' || val === null || val === undefined) {
      return '';
    }
    
    // Convertir a string y limpiar
    let strVal = String(val);
    
    // NO ocultar valores como 0.5, solo ocultar el 0 exacto
    if (parseFloat(strVal) === 0 && strVal !== '0.') {
      return '';
    }
    
    return strVal;
  };

  /**
   * Valida y limpia el input del usuario
   */
  const cleanInput = (inputValue) => {
    if (!inputValue || inputValue === '') {
      return '';
    }

    // Remover caracteres no válidos
    let cleaned = inputValue.replace(/[^0-9.,]/g, '');
    
    // Reemplazar comas por puntos (para usuarios que usan coma como decimal)
    cleaned = cleaned.replace(/,/g, '.');
    
    // Permitir solo un punto decimal
    const parts = cleaned.split('.');
    if (parts.length > 2) {
      cleaned = parts[0] + '.' + parts.slice(1).join('');
    }
    
    // Limitar decimales si está especificado
    if (!allowDecimals) {
      cleaned = cleaned.split('.')[0];
    } else if (parts.length === 2 && decimals > 0) {
      cleaned = parts[0] + '.' + parts[1].substring(0, decimals);
    }
    
    // Manejar ceros iniciales de forma inteligente
    cleaned = handleLeadingZeros(cleaned);
    
    return cleaned;
  };

  /**
   * Maneja ceros iniciales de forma inteligente
   * Permite: "0.5", "0.", "0" pero evita: "01", "02", etc.
   */
  const handleLeadingZeros = (value) => {
    if (!value) return value;
    
    // Si tiene punto decimal, permitir ceros iniciales (0.5, 0.123, etc.)
    if (value.includes('.')) {
      return value;
    }
    
    // Si es solo "0", permitir
    if (value === '0') {
      return value;
    }
    
    // Si empieza con 0 y tiene más dígitos sin punto decimal, remover ceros iniciales
    // Esto evita "01", "02", "001" etc. pero permite "0.5"
    if (value.startsWith('0') && value.length > 1) {
      return value.replace(/^0+/, '') || '0';
    }
    
    return value;
  };

  /**
   * Valida el rango del valor
   */
  const validateRange = (val) => {
    const numVal = parseFloat(val);
    
    if (isNaN(numVal)) {
      return true; // Permitir valores vacíos o inválidos para que el usuario pueda escribir
    }
    
    // Durante la escritura, permitir valores fuera del rango
    // La validación final se hará en onBlur
    if (max !== undefined && numVal > max) {
      return false; // Solo bloquear valores excesivamente altos
    }
    
    return true;
  };

  /**
   * Maneja el cambio de valor
   */
  const handleChange = (e) => {
    const inputValue = e.target.value;
    
    // Limpiar el input
    const cleanedValue = cleanInput(inputValue);
  // Actualizar display inmediatamente para no depender del valor del padre mientras escribe
  setDisplayValue(cleanedValue);
    
    // Si está vacío, pasar string vacío
    if (cleanedValue === '') {
      onChange(e, '');
      return;
    }
    
    // Validar rango
    if (!validateRange(cleanedValue)) {
      return; // No actualizar si está fuera del rango
    }
    
    // Pasar el valor limpio
    onChange(e, cleanedValue);
  };

  /**
   * Maneja el evento onBlur para formatear el valor final
   */
  const handleBlur = (e) => {
    const currentValue = e.target.value;
    isFocusedRef.current = false;
    
    if (currentValue === '') {
      return;
    }
    
    const numValue = parseFloat(currentValue);
    
    if (!isNaN(numValue)) {
      // Aplicar min/max si están definidos
      let finalValue = numValue;
      
      if (min !== undefined && finalValue < min) {
        finalValue = min;
      }
      
      if (max !== undefined && finalValue > max) {
        finalValue = max;
      }
      
      // Si cambió el valor, notificar
      if (finalValue !== numValue) {
        const syntheticEvent = {
          ...e,
          target: {
            ...e.target,
            value: finalValue.toString()
          }
        };
        onChange(syntheticEvent, finalValue.toString());
        setDisplayValue(finalValue.toString());
      } else {
        // Mantener formato consistente tras blur
        setDisplayValue(finalValue.toString());
      }
    }
    
    // Llamar onBlur original si existe
    if (props.onBlur) {
      props.onBlur(e);
    }
  };

  const handleFocus = () => {
    isFocusedRef.current = true;
  };

  // Construir pattern para validación HTML5
  const getPattern = () => {
    if (!allowDecimals) {
      return '[0-9]*';
    }
    // Aceptar punto o coma como separador decimal (mejor UX móvil en distintos locales)
    return '[0-9]*([\\.,][0-9]*)?';
  };

  return (
    <input
      type="text"
      inputMode="decimal"
      pattern={getPattern()}
      value={displayValue}
      onChange={handleChange}
      onFocus={handleFocus}
      onBlur={handleBlur}
      placeholder={placeholder}
      className={className}
      disabled={disabled}
      id={id}
      name={name}
      autoComplete="off"
      {...props}
    />
  );
};

export default NumericInput;
