import React from 'react';
import PropTypes from 'prop-types';
import useFormValidation from '../../hooks/useFormValidation';
import FormValidationStatus from '../FormValidationStatus';

/**
 * Componente para la pestaña ePOD (Proof of Delivery)
 */
const EpodTab = ({
  epodTrackingNumber,
  setEpodTrackingNumber,
  handleEpod,
  epodLoading,
  epodError,
  epodResult,
  selectedAccount,
  downloadDocument,
  resetEpodState
}) => {
  // ✅ Usar hook de validación para epod
  const validation = useFormValidation({ tracking_number: epodTrackingNumber }, 'epod');

  // ✅ Manejar envío con validación
  const handleSubmit = () => {
    if (validation.validate()) {
      handleEpod();
    }
  };

  return (
  <div className="space-y-6">
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        ePOD - Comprobante Electrónico de Entrega
      </h2>
      
      <p className="text-gray-600 mb-6">
        Descarga el comprobante electrónico de entrega (ePOD) en formato PDF para envíos ya entregados.
      </p>

      {/* Formulario de ePOD */}
      <div className="space-y-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Número de Tracking (Envío Entregado)
          </label>
          <div className="flex space-x-2">
            <input
              type="text"
              value={epodTrackingNumber}
              onChange={(e) => setEpodTrackingNumber(e.target.value)}
              className={validation.getFieldClass('tracking_number', 'flex-1 px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
              placeholder="Ej: 1234567890"
              onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
            />
            <button
              onClick={handleSubmit}
              disabled={epodLoading || !validation.canSubmit}
              className={`py-2 px-6 rounded-md font-semibold transition-all duration-200 ${
                validation.canSubmit && !epodLoading
                  ? 'bg-dhl-red text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-dhl-red focus:ring-offset-2'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
              title={!validation.canSubmit ? 'Ingrese un número de tracking válido' : ''}
            >
              {epodLoading ? 'Obteniendo...' : validation.canSubmit ? '📄 Obtener ePOD' : '⚠️ Campo requerido'}
            </button>
          </div>

          {/* Estado de validación */}
          {!validation.isValid && (
            <FormValidationStatus
              isValid={validation.isValid}
              className="mt-4"
            />
          )}
          <p className="text-sm text-gray-500 mt-1">
            ⚠️ El ePOD solo está disponible para envíos que ya han sido entregados.
          </p>
          
          {/* Información de cuenta utilizada */}
          <div className="mt-2 p-3 bg-blue-50 rounded border border-blue-200">
            <div className="flex items-center text-sm">
              <svg className="w-4 h-4 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-blue-700">
                <strong>Cuenta DHL a utilizar:</strong>
                <span className="font-mono ml-2">
                  {selectedAccount || '706014493 (cuenta por defecto)'}
                </span>
              </span>
            </div>
            {!selectedAccount && (
              <div className="text-xs text-blue-600 mt-1 ml-6">
                💡 Selecciona una cuenta específica en el dropdown superior si necesitas usar una cuenta diferente.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mostrar errores de ePOD - Versión Simplificada */}
      {epodError && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-red-800">No se pudo obtener el ePOD</h3>
              <div className="mt-2 text-sm text-red-700">
                {epodError}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mostrar resultados de ePOD - Versión Ultra Simplificada */}
      {epodResult && epodResult.success && (
        <div className="space-y-6">
          {/* Vista del PDF embebido */}
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h5 className="font-medium text-gray-900 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-dhl-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  Comprobante de Entrega - {epodTrackingNumber}
                </h5>
                <button
                  onClick={() => {
                    const pdfData = epodResult.epod_data?.pdf_data || epodResult.pdf_data;
                    downloadDocument(pdfData, `ePOD_${epodTrackingNumber}.pdf`);
                  }}
                  className="inline-flex items-center px-4 py-2 bg-dhl-red text-white rounded-md hover:bg-red-700 transition-colors"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Descargar PDF
                </button>
              </div>
            </div>
            <div className="p-4">
              {(() => {
                const pdfData = epodResult.epod_data?.pdf_data || epodResult.pdf_data;
                if (pdfData) {
                  const pdfUrl = `data:application/pdf;base64,${pdfData.replace(/^data:application\/pdf;base64,/, '')}`;
                  return (
                    <iframe
                      src={pdfUrl}
                      className="w-full border border-gray-300 rounded"
                      title={`ePOD - ${epodTrackingNumber}`}
                      style={{ height: '600px' }}
                    />
                  );
                } else {
                  return (
                    <div className="text-center py-8">
                      <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                      <p className="text-gray-500 mb-4">No se pudo cargar la vista previa</p>
                      <button
                        onClick={() => {
                          const pdfData = epodResult.epod_data?.pdf_data || epodResult.pdf_data;
                          downloadDocument(pdfData, `ePOD_${epodTrackingNumber}.pdf`);
                        }}
                        className="inline-flex items-center px-4 py-2 bg-dhl-red text-white rounded-md hover:bg-red-700 transition-colors"
                      >
                        Descargar PDF
                      </button>
                    </div>
                  );
                }
              })()}
            </div>
          </div>

          {/* Botón para nueva consulta */}
          <div className="text-center">
            <button
              onClick={resetEpodState}
              className="inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Nueva Consulta
            </button>
          </div>
        </div>
      )}

      {/* Mensaje cuando no se encuentra ePOD */}
      {epodResult && !epodResult.success && (
        <div className="text-center py-8">
          <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No se encontró el ePOD</h3>
          <p className="text-gray-600 mb-4">
            El comprobante de entrega no está disponible para este envío.
          </p>
          <button
            onClick={resetEpodState}
            className="inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
          >
            Intentar con otro número
          </button>
        </div>
      )}
    </div>
  </div>
  );
};

EpodTab.propTypes = {
  epodTrackingNumber: PropTypes.string.isRequired,
  setEpodTrackingNumber: PropTypes.func.isRequired,
  handleEpod: PropTypes.func.isRequired,
  epodLoading: PropTypes.bool.isRequired,
  epodError: PropTypes.string,
  epodResult: PropTypes.object,
  selectedAccount: PropTypes.string,
  downloadDocument: PropTypes.func.isRequired,
  resetEpodState: PropTypes.func.isRequired
};

EpodTab.defaultProps = {
  epodError: null,
  epodResult: null,
  selectedAccount: null
};

export default EpodTab;
