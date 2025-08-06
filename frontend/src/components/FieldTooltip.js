import React, { useState } from 'react';
import { getFieldInfo } from '../constants/fieldInfo';

/**
 * Componente Tooltip que muestra información de ayuda al pasar el mouse sobre un campo
 * @param {string} fieldPath - Ruta del campo (ej: 'items.name', 'origin.country')
 * @param {string} position - Posición del tooltip: 'top', 'bottom', 'left', 'right'
 * @param {React.ReactNode} children - Elemento que activa el tooltip (opcional, usa icono por defecto)
 */
const FieldTooltip = ({ 
  fieldPath, 
  position = 'top', 
  children, 
  className = '',
  disabled = false 
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const fieldInfo = getFieldInfo(fieldPath);

  // Si no hay información del campo o está deshabilitado, no mostrar nada
  if (!fieldInfo || disabled) {
    return null;
  }

  const showTooltip = () => setIsVisible(true);
  const hideTooltip = () => setIsVisible(false);

  // Icono por defecto si no se proporciona children
  const defaultIcon = (
    <div className="ml-2 flex items-center justify-center w-5 h-5 bg-blue-500 text-white rounded-full cursor-help hover:bg-blue-600 transition-colors duration-200 text-xs font-bold shadow-md">
      ?
    </div>
  );

  // Clases de posicionamiento del tooltip
  const positionClasses = {
    top: 'bottom-full left-1/2 transform -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 transform -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 transform -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 transform -translate-y-1/2 ml-2'
  };

  // Clases de la flecha del tooltip
  const arrowClasses = {
    top: 'top-full left-1/2 transform -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent border-t-gray-900',
    bottom: 'bottom-full left-1/2 transform -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent border-b-gray-900',
    left: 'left-full top-1/2 transform -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent border-l-gray-900',
    right: 'right-full top-1/2 transform -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent border-r-gray-900'
  };

  return (
    <div 
      className={`relative inline-block ${className}`}
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
    >
      {children || defaultIcon}
      
      {isVisible && (
        <div 
          className={`absolute z-50 ${positionClasses[position]} animate-fade-in`}
          style={{ zIndex: 9999 }}
        >
          {/* Contenido del tooltip */}
          <div className="bg-gray-900 text-white text-sm rounded-lg p-4 shadow-xl max-w-sm w-max border border-gray-700">
            {/* Título del campo */}
            <div className="font-semibold text-orange-300 mb-3 flex items-center">
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              {fieldPath.split('.').pop().toUpperCase()}
              {fieldInfo.required && (
                <span className="text-red-400 ml-2 text-xs font-bold">REQUERIDO</span>
              )}
            </div>
            
            {/* Descripción */}
            <div className="text-gray-200 mb-3 leading-relaxed">
              {fieldInfo.description}
            </div>
            
            {/* Ejemplo */}
            <div className="mb-3">
              <span className="font-medium text-green-300 flex items-center mb-1">
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Ejemplo:
              </span>
              <div className="text-gray-300 text-xs bg-gray-800 px-2 py-1 rounded font-mono">
                {fieldInfo.example}
              </div>
            </div>
            
            {/* Límites */}
            <div className="mb-3">
              <span className="font-medium text-blue-300 flex items-center mb-1">
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                </svg>
                Límite:
              </span>
              <div className="text-gray-300 text-xs">
                {fieldInfo.limit}
              </div>
            </div>
            
            {/* Validación adicional */}
            {fieldInfo.validation && (
              <div>
                <span className="font-medium text-purple-300 flex items-center mb-1">
                  <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  Nota:
                </span>
                <div className="text-gray-300 text-xs">
                  {fieldInfo.validation}
                </div>
              </div>
            )}
            
            {/* Flecha del tooltip */}
            <div className={`absolute w-0 h-0 border-4 ${arrowClasses[position]}`}></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FieldTooltip;
