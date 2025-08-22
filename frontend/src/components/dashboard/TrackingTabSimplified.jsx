import React from 'react';
import PropTypes from 'prop-types';
import useFormValidation from '../../hooks/useFormValidation';

/**
 * Componente simplificado para Rastreo enfocado en pesos y cotización
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
  updateRateData
}) => {
  const validation = useFormValidation({ tracking_number: trackingNumber }, 'tracking');

  const handleSubmit = () => {
    if (validation.validate()) {
      handleTracking();
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          🔍 Rastreo de Envíos DHL Express
        </h2>
        
        <p className="text-gray-600 mb-6">
          Consulta el estado de tu envío y obtén los pesos exactos para cotizar.
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
                placeholder="Ej: 6869687790"
                onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
              />
              <button
                onClick={handleSubmit}
                disabled={trackingLoading || !validation.canSubmit}
                className={`py-2 px-6 rounded-md font-semibold transition-all duration-200 ${
                  validation.canSubmit && !trackingLoading
                    ? 'bg-dhl-red text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-dhl-red focus:ring-offset-2'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                {trackingLoading ? '🔄 Consultando...' : '🔍 Rastrear'}
              </button>
            </div>
            {validation.hasFieldError('tracking_number') && (
              <p className="mt-1 text-sm text-red-600">{validation.getFieldError('tracking_number')}</p>
            )}
          </div>
        </div>

        {/* Mostrar errores */}
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

        {/* Resultados simplificados - solo pesos y cotización */}
        {trackingResult && (
          <div className="space-y-6">
            
            {/* Header con tracking number y estado */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">
                    📦 {trackingResult.tracking_number}
                  </h3>
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                    trackingResult.status === 'Delivered' ? 'bg-green-100 text-green-800' : 
                    trackingResult.status === 'In Transit' ? 'bg-blue-100 text-blue-800' : 
                    'bg-orange-100 text-orange-800'
                  }`}>
                    {trackingResult.status === 'Delivered' && '✅'}
                    {trackingResult.status === 'In Transit' && '🚛'}
                    {trackingResult.status ? translateStatus(trackingResult.status) : 'Estado no disponible'}
                  </span>
                </div>

                {/* Botón principal de cotización */}
                {trackingResult.weights_summary?.highest_for_quote && (
                  <button
                    onClick={() => {
                      const totalWeight = trackingResult.weights_summary.highest_for_quote;
                      if (onNavigateToRate && updateRateData) {
                        onNavigateToRate();
                        updateRateData('weight', totalWeight);
                        updateRateData('declared_weight', totalWeight);
                      }
                    }}
                    className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white px-8 py-4 rounded-xl font-bold text-lg shadow-lg transition-all duration-200 flex items-center space-x-3"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                    </svg>
                    <div>
                      <div>💰 COTIZAR AHORA</div>
                      <div className="text-sm font-normal">con {trackingResult.weights_summary.highest_for_quote.toFixed(2)} kg</div>
                    </div>
                  </button>
                )}
              </div>
            </div>

            {/* Peso Total para Cotización - Destacado */}
            {trackingResult.weights_summary && (
              <div className="bg-gradient-to-r from-yellow-100 to-orange-100 border-2 border-yellow-400 rounded-xl p-6">
                <div className="text-center">
                  <div className="flex items-center justify-center mb-3">
                    <svg className="w-10 h-10 mr-3 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16l-3-9m3 9l3-9" />
                    </svg>
                    <h4 className="text-2xl font-bold text-gray-800">PESO TOTAL PARA COTIZAR</h4>
                  </div>
                  <div className="text-6xl font-bold text-orange-600 mb-3">
                    {trackingResult.weights_summary.highest_for_quote?.toFixed(2) || '0.00'}
                    <span className="text-3xl ml-2">{trackingResult.weights_summary.unit?.toUpperCase() || 'KG'}</span>
                  </div>
                  <p className="text-gray-600 text-lg">
                    🏆 <strong>Peso más alto</strong> entre: Envío Total, Suma de Piezas y Pieza Mayor
                  </p>
                </div>
              </div>
            )}

            {/* Tabla de pesos por pieza */}
            {trackingResult.weights_by_piece && trackingResult.weights_by_piece.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-xl p-6">
                <h4 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
                  <svg className="w-6 h-6 mr-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                  📋 Detalle de Pesos por Pieza ({trackingResult.weights_by_piece.length} piezas)
                </h4>
                
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="px-6 py-4 text-left text-sm font-bold text-gray-700 uppercase tracking-wider">
                          📦 Pieza
                        </th>
                        <th className="px-6 py-4 text-left text-sm font-bold text-gray-700 uppercase tracking-wider">
                          💼 Declarado<br/>
                          <span className="text-xs normal-case font-normal">(Weight)</span>
                        </th>
                        <th className="px-6 py-4 text-left text-sm font-bold text-gray-700 uppercase tracking-wider">
                          ⚖️ Repesaje<br/>
                          <span className="text-xs normal-case font-normal">(ActualWeight)</span>
                        </th>
                        <th className="px-6 py-4 text-left text-sm font-bold text-gray-700 uppercase tracking-wider">
                          📐 Dimensional<br/>
                          <span className="text-xs normal-case font-normal">(DimWeight)</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {trackingResult.weights_by_piece.map((piece, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-6 py-4 text-sm font-bold text-gray-900">
                            Pieza {piece.index + 1}
                            {piece.piece_id && (
                              <div className="text-xs text-gray-500 font-mono mt-1">
                                {piece.piece_id.length > 20 ? piece.piece_id.substring(0, 20) + '...' : piece.piece_id}
                              </div>
                            )}
                          </td>
                          <td className="px-6 py-4">
                            <div className="text-lg font-bold text-blue-600">
                              {piece.declared !== null ? `${piece.declared.toFixed(3)}` : 'N/A'}
                            </div>
                            <div className="text-xs text-gray-500">{piece.unit?.toUpperCase() || 'KG'}</div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="text-lg font-bold text-green-600">
                              {piece.actual !== null ? `${piece.actual.toFixed(3)}` : 'N/A'}
                            </div>
                            <div className="text-xs text-gray-500">{piece.unit?.toUpperCase() || 'KG'}</div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="text-lg font-bold text-purple-600">
                              {piece.dimensional !== null ? `${piece.dimensional.toFixed(3)}` : 'N/A'}
                            </div>
                            <div className="text-xs text-gray-500">{piece.unit?.toUpperCase() || 'KG'}</div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Resumen de totales */}
                {trackingResult.weights_three_sums && (
                  <div className="mt-8 bg-gradient-to-r from-gray-50 to-blue-50 rounded-xl p-6 border">
                    <h5 className="font-bold text-gray-800 mb-4 text-center text-lg">
                      📊 TOTALES POR TIPO DE PESO (Estilo SOAP)
                    </h5>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                      <div className="text-center bg-blue-100 rounded-lg p-4">
                        <div className="text-sm font-medium text-blue-700 mb-1">💼 Total Declarados</div>
                        <div className="text-2xl font-bold text-blue-600">
                          {trackingResult.weights_three_sums.sum_declared?.toFixed(3) || '0.000'}
                        </div>
                        <div className="text-xs text-blue-500">KG</div>
                      </div>
                      <div className="text-center bg-green-100 rounded-lg p-4">
                        <div className="text-sm font-medium text-green-700 mb-1">⚖️ Total Repesajes</div>
                        <div className="text-2xl font-bold text-green-600">
                          {trackingResult.weights_three_sums.sum_actual?.toFixed(3) || '0.000'}
                        </div>
                        <div className="text-xs text-green-500">KG</div>
                      </div>
                      <div className="text-center bg-purple-100 rounded-lg p-4">
                        <div className="text-sm font-medium text-purple-700 mb-1">📐 Total Dimensionales</div>
                        <div className="text-2xl font-bold text-purple-600">
                          {trackingResult.weights_three_sums.sum_dimensional?.toFixed(3) || '0.000'}
                        </div>
                        <div className="text-xs text-purple-500">KG</div>
                      </div>
                      <div className="text-center bg-orange-100 rounded-lg p-4 border-2 border-orange-400">
                        <div className="text-sm font-medium text-orange-700 mb-1">🏆 Mayor de los 3</div>
                        <div className="text-2xl font-bold text-orange-600">
                          {trackingResult.weights_three_sums.highest_for_quote?.toFixed(3) || '0.000'}
                        </div>
                        <div className="text-xs text-orange-500">KG</div>
                      </div>
                    </div>
                    
                    {/* Nota explicativa */}
                    <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                      <p className="text-sm text-yellow-800 text-center">
                        💡 <strong>Información:</strong> El sistema calculó estos totales sumando los pesos individuales de cada pieza (método SOAP). 
                        El <strong>peso mayor</strong> se usará automáticamente para la cotización.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Botón secundario para nueva consulta */}
            <div className="text-center pt-6">
              <button
                onClick={() => {
                  setTrackingNumber('');
                  // Limpiar resultados si hay función para ello
                }}
                className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-6 py-2 rounded-lg font-medium transition-all duration-200"
              >
                🔍 Nueva Consulta
              </button>
            </div>
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
  updateRateData: PropTypes.func
};

TrackingTab.defaultProps = {
  trackingError: null,
  trackingResult: null,
  onNavigateToRate: null,
  updateRateData: null
};

export default TrackingTab;
