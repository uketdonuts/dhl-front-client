import React, { useState } from 'react';

const RateCard = ({ rate, index, expanded, onToggle, onCreateShipment }) => {
  const formatCurrency = (amount, currency = 'USD') => {
    return `${currency} ${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return 'No disponible';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('es-ES') + ' ' + date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4 shadow-sm">
      {/* Vista resumida */}
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg font-semibold text-gray-900">
              📦 {rate.service_name}
            </span>
            {rate.service_code && (
              <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {rate.service_code}
              </span>
            )}
          </div>
          
          <div className="text-xl font-bold text-green-600 mb-1">
            💰 {formatCurrency(rate.total_charge, rate.currency)}
          </div>
          
          {rate.delivery_date && (
            <div className="text-sm text-gray-600 mb-2">
              📅 Entrega: {formatDateTime(rate.delivery_date)}
            </div>
          )}
          
          {rate.charges && rate.charges.length > 0 && (
            <div className="text-sm text-blue-600">
              ℹ️ Desglose disponible: {rate.charges.length} conceptos
            </div>
          )}
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={() => onToggle(index)}
            className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 transition-colors"
          >
            {expanded ? '🔼 Ocultar detalles' : '🔍 Ver detalles'}
          </button>
          
          <button
            onClick={() => onCreateShipment(rate)}
            className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-green-600 rounded-md hover:bg-green-700 transition-colors"
          >
            📦 Crear Shipment
          </button>
        </div>
      </div>

      {/* Vista expandida */}
      {expanded && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Información de entrega */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                📅 Información de Entrega
              </h4>
              <div className="space-y-2 text-sm">
                {rate.delivery_date && (
                  <div>
                    <span className="font-medium">Fecha:</span> {formatDateTime(rate.delivery_date)}
                  </div>
                )}
                {rate.delivery_time && (
                  <div>
                    <span className="font-medium">Hora:</span> {rate.delivery_time}
                  </div>
                )}
                {rate.cutoff_time && (
                  <div>
                    <span className="font-medium">Hora límite:</span> {rate.cutoff_time}
                  </div>
                )}
                {rate.next_business_day && (
                  <div className="text-green-600 font-medium">
                    ✅ Entrega próximo día hábil
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Desglose de precios */}
          {rate.charges && rate.charges.length > 0 && (
            <div className="mt-6">
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                💰 Desglose de Precios
              </h4>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="space-y-2">
                  {rate.charges.map((charge, chargeIndex) => (
                    <div key={chargeIndex} className="flex justify-between items-center text-sm">
                      <span className="text-gray-700">
                        • {charge.description || charge.code || 'Concepto'}
                      </span>
                      <span className="font-medium">
                        {formatCurrency(charge.amount, rate.currency)}
                      </span>
                    </div>
                  ))}
                  <div className="border-t border-gray-300 pt-2 mt-3">
                    <div className="flex justify-between items-center font-semibold">
                      <span>Total:</span>
                      <span className="text-lg">
                        {formatCurrency(rate.total_charge, rate.currency)}
                      </span>
                    </div>
                  </div>
                  
                  {/* Verificación de cálculos */}
                  {(() => {
                    const subtotal = rate.charges.reduce((sum, charge) => sum + (charge.amount || 0), 0);
                    const difference = Math.abs(subtotal - rate.total_charge);
                    return difference > 0.01 && (
                      <div className="text-amber-600 text-xs mt-2 flex items-center">
                        ⚠️ Diferencia detectada: {formatCurrency(difference, rate.currency)}
                      </div>
                    );
                  })()}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const RateResults = ({ result, originalRateData, onCreateShipment }) => {
  const [expandedRates, setExpandedRates] = useState({});

  const toggleExpanded = (index) => {
    setExpandedRates(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const handleCreateShipment = (selectedRate) => {
    if (onCreateShipment) {
      onCreateShipment(selectedRate, originalRateData);
    }
  };



  if (!result || !result.success) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Resumen principal */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-green-800 mb-2 flex items-center">
          ✅ Cotización Exitosa
        </h3>
        <p className="text-green-700">
          Se encontraron {result.rates?.length || 0} servicios disponibles
        </p>
      </div>

      {/* Lista de tarifas */}
      {result.rates && result.rates.length > 0 && (
        <div>
          <h3 className="text-xl font-semibold text-gray-900 mb-4">
            📋 Servicios Disponibles
          </h3>
          <div className="space-y-4">
            {result.rates.map((rate, index) => (
              <RateCard
                key={index}
                rate={rate}
                index={index}
                expanded={expandedRates[index]}
                onToggle={toggleExpanded}
                onCreateShipment={handleCreateShipment}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RateResults;
