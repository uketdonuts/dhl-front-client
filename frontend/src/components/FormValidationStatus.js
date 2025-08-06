import React from 'react';
import PropTypes from 'prop-types';

/**
 * Componente que muestra el estado de validación del formulario
 * Indica si se pueden enviar los datos con mensajes concisos
 */
const FormValidationStatus = ({ 
  isValid, 
  className = ''
}) => {
  if (isValid) {
    return (
      <div className={`bg-green-50 border border-green-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-green-800">
              ✅ Formulario completo
            </h3>
            <p className="text-sm text-green-700 mt-1">
              Listo para enviar
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
      <div className="flex">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-red-800">
            Formulario incompleto
          </h3>
          <p className="text-sm text-red-700 mt-1">
            Completa todos los campos marcados con * para continuar
          </p>
        </div>
      </div>
    </div>
  );
};

FormValidationStatus.propTypes = {
  isValid: PropTypes.bool.isRequired,
  className: PropTypes.string,
};

export default FormValidationStatus;
