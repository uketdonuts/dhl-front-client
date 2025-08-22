import React from 'react';
import PropTypes from 'prop-types';
import useFormValidation from '../../hooks/useFormValidation';
import FormValidationStatus from '../FormValidationStatus';
import { mapCountryNameToCode, mapCodeToCountryName } from '../../utils/countryMappingService';

/**
 * Componente para la pestaña de Rastreo con funcionalidad completa
 */
const TrackingTab = ({
  trackingNumber,
  setTrackingNumber,
  handleTracking,
  trackingLoading,
  trackingError,
  trackingResult,
  translateStatus,
  onNavigateToRate,
  updateRateData,
  updateAddress,
  setNotification,
  onQuoteClick,
  quoteBusy,
  quoteStatus
}) => {
  // ✅ Usar hook de validación para tracking
  const validation = useFormValidation({ tracking_number: trackingNumber }, 'tracking');

  // ✅ Manejar envío con validación
  const handleSubmit = () => {
    if (validation.validate()) {
      handleTracking();
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Rastreo de Envíos DHL Express
        </h2>
        
        <p className="text-gray-600 mb-6">
          Ingresa el número de tracking para obtener información detallada sobre el estado de tu envío.
        </p>

        {/* Formulario de tracking */}
        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Número de Tracking
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={trackingNumber}
                onChange={(e) => setTrackingNumber(e.target.value)}
                className={validation.getFieldClass('tracking_number', 'flex-1 px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
                placeholder="Ej: 1234567890"
                onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
              />
              {validation.hasFieldError('tracking_number') && (
                <p className="mt-1 text-sm text-red-600">{validation.getFieldError('tracking_number')}</p>
              )}
              <button
                onClick={handleSubmit}
                disabled={trackingLoading || !validation.canSubmit}
                className={`py-2 px-6 rounded-md font-semibold transition-all duration-200 ${
                  validation.canSubmit && !trackingLoading
                    ? 'bg-dhl-red text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-dhl-red focus:ring-offset-2'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
                title={!validation.canSubmit ? 'Ingrese un número de tracking válido' : ''}
              >
                {trackingLoading ? 'Rastreando...' : validation.canSubmit ? '🔍 Rastrear' : '⚠️ Campo requerido'}
              </button>
            </div>
          </div>

          {/* Estado de validación - Comentado para tracking */}
          {/* {!validation.isValid && (
            <FormValidationStatus
              isValid={validation.isValid}
              className="mt-4"
            />
          )} */}
        </div>

        {/* Mostrar errores de tracking */}
        {trackingError && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error de Tracking</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{trackingError}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Mostrar resultados de tracking - Versión simplificada */}
        {trackingResult && (
          <div className="space-y-6">
            {/* Header del tracking simplificado */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <div className="bg-blue-100 p-3 rounded-xl mr-4">
                    <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-1">
                      {trackingResult.tracking_info?.tracking_number || trackingResult.tracking_number || 'No disponible'}
                    </h3>
                    <div className="flex items-center space-x-2">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                        trackingResult.status?.includes('Delivered') ? 'bg-green-100 text-green-800' : 
                        trackingResult.status?.includes('Transit') ? 'bg-blue-100 text-blue-800' : 
                        'bg-orange-100 text-orange-800'
                      }`}>
                        {trackingResult.status?.includes('Delivered') && '✅'}
                        {trackingResult.status?.includes('Transit') && '🚛'}
                        {translateStatus(trackingResult.status || 'No disponible')}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Sección principal: Desglose de pesos y cotización */}
            {(trackingResult.weights_summary || trackingResult.weights_three_sums || trackingResult.weights_by_piece) && (
              <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                <h4 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                  <div className="bg-orange-100 p-2 rounded-lg mr-3">
                    <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16l3-3m-3 3l-3-3" />
                    </svg>
                  </div>
                  Análisis de Pesos para Cotización
                </h4>

                {/* Peso Total Final - destacado */}
        {(trackingResult.weights_summary?.highest_for_quote || trackingResult.weights_three_sums?.highest_for_quote) && (
                  <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-6 mb-6">
          <div className="flex items-center justify-between gap-4 flex-wrap">
                      <div className="flex items-center space-x-4">
                        <div className="bg-green-100 p-3 rounded-xl">
                          <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                          </svg>
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">PESO TOTAL PARA COTIZACIÓN</h3>
                          <div className="text-3xl font-bold text-green-800">
                            {(trackingResult.weights_three_sums?.highest_for_quote || trackingResult.weights_summary?.highest_for_quote || 0).toFixed(2)} KG
                          </div>
                          <div className="text-sm text-green-600 mt-1">
                            Este es el peso más alto entre declarado, actual y dimensional
                          </div>
                        </div>
                      </div>

                      {/* CTA: Cotizar con este peso (flujo de cuenta ocurre al presionar) */}
                      <div className="flex items-center space-x-3 ml-auto">
                        <button
                          onClick={onQuoteClick}
                          disabled={quoteBusy}
                          className={`px-4 py-3 rounded-xl font-semibold text-white shadow ${quoteBusy ? 'bg-gray-400' : 'bg-dhl-red hover:bg-red-700'} transition`}
                          title="Cotizar usando el peso más alto"
                        >
                          {quoteBusy ? 'Preparando…' : 'Cotizar con este peso'}
                        </button>
                      </div>
                    </div>

                    {/* Mensaje de estado pequeño */}
                    {quoteStatus && (
                      <p className="mt-2 text-xs text-gray-600">{quoteStatus}</p>
                    )}
                  </div>
                )}

                {/* Desglose de pesos por pieza */}
                {trackingResult.weights_by_piece && trackingResult.weights_by_piece.length > 0 && (
                  <div className="space-y-4">
                    <h5 className="text-lg font-semibold text-gray-800 mb-4">
                      📦 Pesos por Pieza ({trackingResult.weights_by_piece.length})
                    </h5>
                    <div className="space-y-3">
                      {trackingResult.weights_by_piece.map((piece, index) => (
                        <div key={index} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center space-x-2">
                              <div className="bg-blue-100 text-blue-700 rounded-lg px-3 py-1 font-semibold text-sm">
                                Pieza #{piece.index + 1}
                              </div>
                              {piece.piece_id && (
                                <div className="text-xs text-gray-500 bg-white px-2 py-1 rounded border">
                                  {piece.piece_id}
                                </div>
                              )}
                            </div>
                          </div>
                          
                          {/* Grid de 3 pesos por pieza */}
                          <div className="grid grid-cols-3 gap-3">
                            <div className="text-center bg-blue-50 rounded-lg p-3 border border-blue-200">
                              <div className="text-xs text-blue-600 font-medium mb-1">DECLARADO</div>
                              <div className="text-xl font-bold text-blue-800">
                                {piece.declared ? piece.declared.toFixed(2) : '0.00'}
                              </div>
                              <div className="text-xs text-blue-600">{piece.unit}</div>
                            </div>
                            
                            <div className="text-center bg-orange-50 rounded-lg p-3 border border-orange-200">
                              <div className="text-xs text-orange-600 font-medium mb-1">ACTUAL</div>
                              <div className="text-xl font-bold text-orange-800">
                                {piece.actual ? piece.actual.toFixed(2) : '0.00'}
                              </div>
                              <div className="text-xs text-orange-600">{piece.unit}</div>
                            </div>
                            
                            <div className="text-center bg-green-50 rounded-lg p-3 border border-green-200">
                              <div className="text-xs text-green-600 font-medium mb-1">DIMENSIONAL</div>
                              <div className="text-xl font-bold text-green-800">
                                {piece.dimensional ? piece.dimensional.toFixed(2) : '0.00'}
                              </div>
                              <div className="text-xs text-green-600">{piece.unit}</div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Resumen de totales */}
                {trackingResult.weights_three_sums && (
                  <div className="mt-6 bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <h5 className="font-semibold text-gray-800 mb-3">📊 Totales por Tipo de Peso</h5>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center">
                        <div className="text-sm text-gray-600 mb-1">Total Declarado</div>
                        <div className="text-lg font-bold text-blue-800">
                          {trackingResult.weights_three_sums.sum_declared.toFixed(2)} KG
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-sm text-gray-600 mb-1">Total Actual</div>
                        <div className="text-lg font-bold text-orange-800">
                          {trackingResult.weights_three_sums.sum_actual.toFixed(2)} KG
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-sm text-gray-600 mb-1">Total Dimensional</div>
                        <div className="text-lg font-bold text-green-800">
                          {trackingResult.weights_three_sums.sum_dimensional.toFixed(2)} KG
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Historial de eventos */}
            {trackingResult.events && trackingResult.events.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h4 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Historial de Eventos
                </h4>
                <div className="space-y-4">
                  {trackingResult.events.map((event, index) => (
                    <div key={index} className="flex items-start border-l-4 border-dhl-red pl-4 py-2">
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <h5 className="font-medium text-gray-900">{event.description}</h5>
                          <span className="text-sm text-gray-500">{event.date}</span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">
                          {event.location} {event.time && `- ${event.time}`}
                        </p>
                        {event.additional_info && (
                          <p className="text-xs text-gray-500 mt-1">{event.additional_info}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

TrackingTab.propTypes = {
  trackingNumber: PropTypes.string.isRequired,
  setTrackingNumber: PropTypes.func.isRequired,
  handleTracking: PropTypes.func.isRequired,
  trackingLoading: PropTypes.bool.isRequired,
  trackingError: PropTypes.string,
  trackingResult: PropTypes.object,
  translateStatus: PropTypes.func.isRequired,
  onNavigateToRate: PropTypes.func,
  updateRateData: PropTypes.func,
  updateAddress: PropTypes.func,
  setNotification: PropTypes.func,
  onQuoteClick: PropTypes.func,
  quoteBusy: PropTypes.bool,
  quoteStatus: PropTypes.string
};

TrackingTab.defaultProps = {
  trackingError: null,
  trackingResult: null,
  onNavigateToRate: null,
  updateRateData: null,
  updateAddress: null,
  setNotification: null,
  onQuoteClick: () => {},
  quoteBusy: false,
  quoteStatus: ''
};

export default TrackingTab;
