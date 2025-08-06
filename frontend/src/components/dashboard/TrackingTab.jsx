import React from 'react';
import PropTypes from 'prop-types';
import useFormValidation from '../../hooks/useFormValidation';
import FormValidationStatus from '../FormValidationStatus';

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
  updateRateData
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

          {/* Estado de validación */}
          {!validation.isValid && (
            <FormValidationStatus
              isValid={validation.isValid}
              className="mt-4"
            />
          )}
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

        {/* Mostrar resultados de tracking */}
        {trackingResult && (
          <div className="space-y-6">
            {/* Header del tracking con estado mejorado */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-start justify-between mb-6">
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
                        trackingResult.tracking_info?.status_description === 'Delivered' ? 'bg-green-100 text-green-800' : 
                        trackingResult.tracking_info?.status_description === 'In Transit' ? 'bg-blue-100 text-blue-800' : 
                        trackingResult.tracking_info?.status_description === 'Out for Delivery' ? 'bg-purple-100 text-purple-800' :
                        'bg-orange-100 text-orange-800'
                      }`}>
                        {trackingResult.tracking_info?.status_description === 'Delivered' && '✅'}
                        {trackingResult.tracking_info?.status_description === 'In Transit' && '🚛'}
                        {trackingResult.tracking_info?.status_description === 'Out for Delivery' && '🚚'}
                        {trackingResult.tracking_info?.status_description ? translateStatus(trackingResult.tracking_info.status_description) : 'No disponible'}
                      </span>
                    </div>
                  </div>
                </div>
                
                {/* Botón de cotizar con repesaje */}
                {trackingResult.piece_details && trackingResult.piece_details.length > 0 && 
                 trackingResult.piece_details[0].weight_info && 
                 trackingResult.piece_details[0].weight_info.actual_weight_reweigh && (
                  <button
                    onClick={() => {
                      const piece = trackingResult.piece_details[0];
                      const actualWeight = piece.weight_info.actual_weight_reweigh;
                      // Cambiar a la pestaña de cotización y prellenar peso
                      if (onNavigateToRate && updateRateData) {
                        onNavigateToRate();
                        updateRateData('weight', actualWeight);
                        updateRateData('declared_weight', actualWeight);
                      }
                    }}
                    className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white px-4 py-2 rounded-lg font-medium shadow-sm transition-all duration-200 flex items-center space-x-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                    </svg>
                    <span>Cotizar con {trackingResult.piece_details[0].weight_info.actual_weight_reweigh}kg</span>
                  </button>
                )}
              </div>
              
              {/* Grid de información básica */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {trackingResult.tracking_info && (
                  <>
                    <div className="bg-white/70 backdrop-blur rounded-lg p-3">
                      <div className="flex items-center mb-1">
                        <svg className="w-4 h-4 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        <span className="text-sm font-medium text-gray-700">Origen</span>
                      </div>
                      <div className="text-gray-900 font-medium">{trackingResult.tracking_info.origin || 'No disponible'}</div>
                    </div>
                    
                    <div className="bg-white/70 backdrop-blur rounded-lg p-3">
                      <div className="flex items-center mb-1">
                        <svg className="w-4 h-4 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        <span className="text-sm font-medium text-gray-700">Destino</span>
                      </div>
                      <div className="text-gray-900 font-medium">{trackingResult.tracking_info.destination || 'No disponible'}</div>
                    </div>
                    
                    <div className="bg-white/70 backdrop-blur rounded-lg p-3">
                      <div className="flex items-center mb-1">
                        <svg className="w-4 h-4 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                        <span className="text-sm font-medium text-gray-700">Servicio</span>
                      </div>
                      <div className="text-gray-900 font-medium">{trackingResult.tracking_info.service_type || 'No disponible'}</div>
                    </div>
                    
                    <div className="bg-white/70 backdrop-blur rounded-lg p-3">
                      <div className="flex items-center mb-1">
                        <svg className="w-4 h-4 mr-2 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 4V7a2 2 0 012-2h4a2 2 0 012 2v4.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="text-sm font-medium text-gray-700">Peso Total</span>
                      </div>
                      <div className="text-gray-900 font-medium">{trackingResult.tracking_info.total_weight || 0} {trackingResult.tracking_info.weight_unit || 'kg'}</div>
                    </div>
                  </>
                )}
              </div>
            </div>

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

            {/* Información adicional y detalles completos */}
            {trackingResult.tracking_info && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Detalles del servicio */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <h4 className="text-lg font-medium text-gray-800 mb-3 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a4 4 0 118 0v4m-4 8a3 3 0 100-6 3 3 0 000 6z" />
                    </svg>
                    Detalles del Servicio
                  </h4>
                  <div className="space-y-2 text-sm">
                    {trackingResult.tracking_info.service_name && (
                      <div className="flex justify-between">
                        <span className="font-medium text-gray-700">Servicio:</span>
                        <span className="text-gray-600">{trackingResult.tracking_info.service_name}</span>
                      </div>
                    )}
                    {trackingResult.tracking_info.description && (
                      <div className="flex justify-between">
                        <span className="font-medium text-gray-700">Descripción:</span>
                        <span className="text-gray-600">{trackingResult.tracking_info.description}</span>
                      </div>
                    )}
                    {trackingResult.tracking_info.shipment_timestamp && (
                      <div className="flex justify-between">
                        <span className="font-medium text-gray-700">Fecha Envío:</span>
                        <span className="text-gray-600">{trackingResult.tracking_info.shipment_timestamp}</span>
                      </div>
                    )}
                    {trackingResult.tracking_info.estimated_delivery && (
                      <div className="flex justify-between">
                        <span className="font-medium text-gray-700">Entrega Estimada:</span>
                        <span className="text-gray-600">{trackingResult.tracking_info.estimated_delivery}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Información de peso y piezas */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <h4 className="text-lg font-medium text-gray-800 mb-3 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                    </svg>
                    Información del Paquete
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-700">Número de Piezas:</span>
                      <span className="text-gray-600">{trackingResult.total_pieces || trackingResult.tracking_info.number_of_pieces || 'No especificado'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-700">Peso Total:</span>
                      <span className="text-gray-600">
                        {trackingResult.tracking_info.total_weight > 0 
                          ? `${trackingResult.tracking_info.total_weight} ${trackingResult.tracking_info.weight_unit}` 
                          : 'No especificado'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-700">Eventos de Tracking:</span>
                      <span className="text-gray-600">{trackingResult.total_events || 0} eventos</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Detalles de origen y destino expandidos */}
            {trackingResult.tracking_info && (trackingResult.tracking_info.origin_details || trackingResult.tracking_info.destination_details) && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Información detallada del origen */}
                {trackingResult.tracking_info.origin_details && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h4 className="text-lg font-medium text-green-800 mb-3 flex items-center">
                      <svg className="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      Origen Detallado
                    </h4>
                    <div className="space-y-2 text-sm">
                      <div><span className="font-medium">Ubicación:</span> {trackingResult.tracking_info.origin_details.description}</div>
                      {trackingResult.tracking_info.origin_details.code && (
                        <div><span className="font-medium">Código:</span> {trackingResult.tracking_info.origin_details.code}</div>
                      )}
                      {trackingResult.tracking_info.origin_details.full_address && (
                        <div><span className="font-medium">Dirección:</span> {trackingResult.tracking_info.origin_details.full_address}</div>
                      )}
                    </div>
                  </div>
                )}

                {/* Información detallada del destino */}
                {trackingResult.tracking_info.destination_details && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="text-lg font-medium text-blue-800 mb-3 flex items-center">
                      <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      Destino Detallado
                    </h4>
                    <div className="space-y-2 text-sm">
                      <div><span className="font-medium">Ubicación:</span> {trackingResult.tracking_info.destination_details.description}</div>
                      {trackingResult.tracking_info.destination_details.code && (
                        <div><span className="font-medium">Código:</span> {trackingResult.tracking_info.destination_details.code}</div>
                      )}
                      {trackingResult.tracking_info.destination_details.full_address && (
                        <div><span className="font-medium">Dirección:</span> {trackingResult.tracking_info.destination_details.full_address}</div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Detalles de piezas individuales - Layout compacto y mejorado */}
            {trackingResult.piece_details && trackingResult.piece_details.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                <h4 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                  <div className="bg-gray-100 p-2 rounded-lg mr-3">
                    <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  </div>
                  Información de Paquetes ({trackingResult.piece_details.length})
                </h4>
                
                <div className="space-y-4">
                  {trackingResult.piece_details.map((piece, index) => (
                    <div key={index} className="bg-gradient-to-br from-gray-50 to-blue-50 border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-all duration-300">
                      
                      {/* Header del paquete */}
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-3">
                          <div className="bg-blue-100 text-blue-700 rounded-lg px-3 py-2 font-semibold">
                            📦 Paquete #{index + 1}
                          </div>
                          {piece.piece_id && (
                            <div className="text-xs text-gray-500 bg-white px-3 py-1 rounded-full border">
                              {piece.piece_id}
                            </div>
                          )}
                        </div>
                        
                        {/* Indicador de repesaje prominente */}
                        {piece.weight_info && piece.weight_info.declared_weight !== piece.weight_info.actual_weight_reweigh && (
                          <div className="bg-gradient-to-r from-orange-500 to-orange-600 text-white px-4 py-2 rounded-full text-sm font-semibold flex items-center space-x-2 shadow-md">
                            <span>⚖️</span>
                            <span>Repesaje DHL</span>
                          </div>
                        )}
                      </div>

                      {/* Layout principal mejorado */}
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        
                        {/* Sección 1: Información de Peso (Principal) */}
                        {piece.weight_info ? (
                          <div className="lg:col-span-2 bg-white rounded-xl p-5 shadow-sm border">
                            <div className="flex items-center mb-4">
                              <div className="bg-blue-100 p-2 rounded-lg mr-3">
                                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16l3-3m-3 3l-3-3" />
                                </svg>
                              </div>
                              <h5 className="text-lg font-semibold text-gray-800">Desglose de Peso</h5>
                            </div>
                            
                            {/* Grid de pesos */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                              <div className="text-center bg-blue-50 rounded-lg p-3 border border-blue-200">
                                <div className="text-xs text-blue-600 font-medium mb-1">DECLARADO</div>
                                <div className="text-2xl font-bold text-blue-800">{piece.weight_info.declared_weight}</div>
                                <div className="text-xs text-blue-600">{piece.weight_info.unit}</div>
                              </div>
                              
                              <div className="text-center bg-orange-50 rounded-lg p-3 border border-orange-200">
                                <div className="text-xs text-orange-600 font-medium mb-1">REAL (DHL)</div>
                                <div className="text-2xl font-bold text-orange-800">{piece.weight_info.actual_weight_reweigh}</div>
                                <div className="text-xs text-orange-600">{piece.weight_info.unit}</div>
                              </div>
                              
                              <div className="text-center bg-green-50 rounded-lg p-3 border border-green-200">
                                <div className="text-xs text-green-600 font-medium mb-1">FACTURABLE</div>
                                <div className="text-2xl font-bold text-green-800">{piece.weight_info.chargeable_weight}</div>
                                <div className="text-xs text-green-600">{piece.weight_info.unit}</div>
                              </div>
                            </div>
                            
                            {/* Diferencia y botón de cotizar */}
                            {piece.weight_info.declared_weight !== piece.weight_info.actual_weight_reweigh && (
                              <div className="bg-gray-50 rounded-lg p-4 border-l-4 border-red-400">
                                <div className="flex items-center justify-between mb-3">
                                  <div className="flex items-center space-x-2">
                                    <span className="text-2xl">
                                      {piece.weight_info.declared_weight > piece.weight_info.actual_weight_reweigh ? '📉' : '📈'}
                                    </span>
                                    <div>
                                      <div className="font-semibold text-red-800">Diferencia de Peso</div>
                                      <div className="text-lg font-bold text-red-900">
                                        {Math.abs(piece.weight_info.declared_weight - piece.weight_info.actual_weight_reweigh).toFixed(2)} {piece.weight_info.unit}
                                      </div>
                                    </div>
                                  </div>
                                </div>
                                
                                {/* Botón de cotizar prominente */}
                                <button
                                  onClick={() => {
                                    if (onNavigateToRate && updateRateData) {
                                      onNavigateToRate();
                                      updateRateData('weight', piece.weight_info.actual_weight_reweigh);
                                      updateRateData('declared_weight', piece.weight_info.actual_weight_reweigh);
                                    }
                                  }}
                                  className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-4 py-3 rounded-lg font-semibold transition-all duration-200 flex items-center justify-center space-x-2 shadow-md hover:shadow-lg transform hover:scale-105"
                                >
                                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                                  </svg>
                                  <span>Cotizar con Peso Real ({piece.weight_info.actual_weight_reweigh} {piece.weight_info.unit})</span>
                                </button>
                              </div>
                            )}
                          </div>
                        ) : (
                          piece.weight > 0 && (
                            <div className="lg:col-span-2 bg-white rounded-xl p-5 shadow-sm border">
                              <h5 className="font-semibold text-gray-800 mb-2">Información de Peso</h5>
                              <div className="text-2xl font-bold text-gray-900">{piece.weight} {piece.weight_unit}</div>
                            </div>
                          )
                        )}

                        {/* Sección 2: Información Adicional (Lateral) */}
                        <div className="space-y-4">
                          {piece.dimensions && (piece.dimensions.length > 0 || piece.dimensions.width > 0 || piece.dimensions.height > 0) && (
                            <div className="bg-white rounded-lg p-4 shadow-sm border">
                              <div className="flex items-center mb-2">
                                <svg className="w-4 h-4 mr-2 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                                </svg>
                                <span className="text-sm font-semibold text-gray-700">Dimensiones</span>
                              </div>
                              <div className="text-center bg-indigo-50 rounded-lg p-3">
                                <div className="font-bold text-indigo-800 text-lg font-mono">
                                  {piece.dimensions.length} × {piece.dimensions.width} × {piece.dimensions.height}
                                </div>
                                <div className="text-xs text-indigo-600">cm</div>
                              </div>
                            </div>
                          )}
                          
                          {piece.type_code && (
                            <div className="bg-white rounded-lg p-4 shadow-sm border">
                              <div className="flex items-center mb-2">
                                <svg className="w-4 h-4 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                                </svg>
                                <span className="text-sm font-semibold text-gray-700">Tipo de Paquete</span>
                              </div>
                              <div className="text-center bg-purple-50 rounded-lg p-2">
                                <div className="font-semibold text-purple-800">{piece.type_code}</div>
                              </div>
                            </div>
                          )}
                          
                          {piece.description && (
                            <div className="bg-white rounded-lg p-4 shadow-sm border">
                              <div className="flex items-center mb-2">
                                <svg className="w-4 h-4 mr-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                <span className="text-sm font-semibold text-gray-700">Descripción</span>
                              </div>
                              <div className="text-sm text-gray-800 bg-gray-50 rounded p-2">{piece.description}</div>
                            </div>
                          )}
                        </div>
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
  updateRateData: PropTypes.func
};

TrackingTab.defaultProps = {
  trackingError: null,
  trackingResult: null,
  onNavigateToRate: null,
  updateRateData: null
};

export default TrackingTab;
