import React, { useState, useCallback, useEffect } from 'react';
import PropTypes from 'prop-types';
import SmartLocationDropdown from '../SmartLocationDropdown';
import RateResults from '../RateResults';
import FieldTooltip from '../FieldTooltip';
import NumericInput from '../NumericInput';

// Función para calcular N días laborales en el futuro
const calculateBusinessDays = (days) => {
  let current = new Date();
  let daysAhead = 1;
  let businessDaysFound = 0;

  while (businessDaysFound < days) {
    const nextDate = new Date(current);
    nextDate.setDate(current.getDate() + daysAhead);

    // 0=Domingo, 6=Sábado
    const dayOfWeek = nextDate.getDay();
    if (dayOfWeek !== 0 && dayOfWeek !== 6) {
      businessDaysFound++;
      if (businessDaysFound >= days) {
        return nextDate;
      }
    }
    daysAhead++;
  }
  return new Date();
};

// Función para verificar si una fecha es día laboral
const isBusinessDay = (date) => {
  const dayOfWeek = date.getDay();
  return dayOfWeek !== 0 && dayOfWeek !== 6; // No domingo ni sábado
};

/**
 * Componente mejorado para la pestaña de Cotizar Tarifas con dropdowns inteligentes
 */
const RateTabImproved = ({
  rateData,
  updateAddress,
  updateRateData,
  updateDimensions,
  handleRateRequest,
  loading,
  error,
  result,
  handleCreateShipmentFromRate,
  selectedAccount,
  onLocationDataChange, // Nueva prop para exponer datos de ubicación completos
}) => {
  // Estados para las ubicaciones seleccionadas (formato SmartLocationDropdown)
  const [originLocation, setOriginLocation] = useState({
    country: rateData.origin.country || '',
    countryName: rateData.origin_country_name || '',
    state: rateData.origin.state || '',
    stateName: '',
    city: rateData.origin.city || '',
    cityName: rateData.origin.city || '',
    postalCode: rateData.origin.postal_code || '',
    postalCodeRange: '',
    serviceArea: rateData.origin.service_area || '',
  // serviceAreaName intentionally not tracked for payload
  });

  const [destinationLocation, setDestinationLocation] = useState({
    country: rateData.destination.country || '',
    countryName: rateData.destination_country_name || '',
    state: rateData.destination.state || '',
    stateName: '',
    city: rateData.destination.city || '',
    cityName: rateData.destination.city || '',
    postalCode: rateData.destination.postal_code || '',
    postalCodeRange: '',
    serviceArea: rateData.destination.service_area || '',
  // serviceAreaName intentionally not tracked for payload
  });

  // Ref para forzar actualización de los dropdowns
  const [forceUpdateFlag, setForceUpdateFlag] = useState(0);

  // Estado para la fecha de envío (mínimo 5 días laborales)
  const [shippingDate, setShippingDate] = useState('');
  const [minDate, setMinDate] = useState('');

  // Calcular fecha mínima (5 días laborales) al montar el componente
  useEffect(() => {
    const minBusinessDate = calculateBusinessDays(5);
    const formatted = minBusinessDate.toISOString().split('T')[0];
    setMinDate(formatted);
    setShippingDate(formatted);
    // Actualizar el estado global de rateData con la fecha calculada
    if (updateRateData) {
      updateRateData('shippingDate', formatted);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Solo ejecutar al montar el componente

  // 🔄 Sincronizar dropdowns cuando rateData cambie (ej: desde tracking)
  useEffect(() => {
    console.log('🔄 RateData cambió, sincronizando dropdowns...', {
      origin: rateData.origin,
      destination: rateData.destination,
      originCountryName: rateData.origin_country_name,
      destinationCountryName: rateData.destination_country_name
    });
    
    // Crear un pequeño delay para permitir que todas las actualizaciones se procesen
    const timeoutId = setTimeout(() => {
      // Actualizar dropdown de origen con datos completos
      setOriginLocation(prev => {
        const newOriginLocation = {
          country: rateData.origin.country || '',
          countryName: rateData.origin_country_name || '',
          state: rateData.origin.state || '',
          stateName: prev.stateName || '',
          city: rateData.origin.city || '',
          cityName: rateData.origin.city || '',
          postalCode: rateData.origin.postal_code || '',
          postalCodeRange: prev.postalCodeRange || '',
          serviceArea: rateData.origin.service_area || '',
        };
        
        // Solo actualizar si hay cambios para evitar re-renders innecesarios
        const hasChanges = (
          prev.country !== newOriginLocation.country ||
          prev.city !== newOriginLocation.city ||
          prev.countryName !== newOriginLocation.countryName ||
          prev.postalCode !== newOriginLocation.postalCode
        );
        
        if (hasChanges) {
          console.log('✅ Actualizando dropdown origen:', {
            anterior: prev,
            nuevo: newOriginLocation
          });
          // Forzar actualización si es necesario
          setForceUpdateFlag(flag => flag + 1);
          return newOriginLocation;
        }
        return prev;
      });

      // Actualizar dropdown de destino con datos completos
      setDestinationLocation(prev => {
        const newDestinationLocation = {
          country: rateData.destination.country || '',
          countryName: rateData.destination_country_name || '',
          state: rateData.destination.state || '',
          stateName: prev.stateName || '',
          city: rateData.destination.city || '',
          cityName: rateData.destination.city || '',
          postalCode: rateData.destination.postal_code || '',
          postalCodeRange: prev.postalCodeRange || '',
          serviceArea: rateData.destination.service_area || '',
        };
        
        // Solo actualizar si hay cambios para evitar re-renders innecesarios
        const hasChanges = (
          prev.country !== newDestinationLocation.country ||
          prev.city !== newDestinationLocation.city ||
          prev.countryName !== newDestinationLocation.countryName ||
          prev.postalCode !== newDestinationLocation.postalCode
        );
        
        if (hasChanges) {
          console.log('✅ Actualizando dropdown destino:', {
            anterior: prev,
            nuevo: newDestinationLocation
          });
          // Forzar actualización si es necesario
          setForceUpdateFlag(flag => flag + 1);
          return newDestinationLocation;
        }
        return prev;
      });
    }, 200); // Delay más largo para asegurar que los datos se procesen

    return () => clearTimeout(timeoutId);
  }, [
    rateData.origin.country,
    rateData.origin.city,
    rateData.origin.postal_code,
    rateData.origin.state,
    rateData.origin.service_area,
    rateData.origin_country_name,
    rateData.destination.country,
    rateData.destination.city,
    rateData.destination.postal_code,
    rateData.destination.state,
    rateData.destination.service_area,
    rateData.destination_country_name
  ]);

  // Manejar cambios en origen
  const handleOriginLocationChange = useCallback((location) => {
    setOriginLocation(location);
    
    // Actualizar datos del rate
    updateAddress('origin', 'country', location.country || '');
    updateAddress('origin', 'state', location.state || '');
    updateAddress('origin', 'city', location.cityName || location.city || '');
    
    // Actualizar código postal si viene del dropdown
    if (location.postalCode) {
      updateAddress('origin', 'postal_code', location.postalCode);
    }

    // Actualizar serviceArea si viene del dropdown
    if (location.serviceArea) {
      updateAddress('origin', 'service_area', location.serviceArea);
      // No enviar service_area_name en el payload
    }
    
    // Si hay nombre de país completo, actualizar también
    if (location.countryName) {
      updateRateData('origin_country_name', location.countryName);
    }

    // Notificar cambios de ubicación al componente padre
    if (onLocationDataChange) {
      onLocationDataChange('origin', location);
    }
  }, [updateAddress, updateRateData, onLocationDataChange]);

  // Manejar cambios en destino
  const handleDestinationLocationChange = useCallback((location) => {
    setDestinationLocation(location);
    
    // Actualizar datos del rate
    updateAddress('destination', 'country', location.country || '');
    updateAddress('destination', 'state', location.state || '');
    updateAddress('destination', 'city', location.cityName || location.city || '');
    
    // Actualizar código postal si viene del dropdown
    if (location.postalCode) {
      updateAddress('destination', 'postal_code', location.postalCode);
    }

    // Actualizar serviceArea si viene del dropdown
    if (location.serviceArea) {
      updateAddress('destination', 'service_area', location.serviceArea);
      // No enviar service_area_name en el payload
    }
    
    // Si hay nombre de país completo, actualizar también
    if (location.countryName) {
      updateRateData('destination_country_name', location.countryName);
    }

    // Notificar cambios de ubicación al componente padre
    if (onLocationDataChange) {
      onLocationDataChange('destination', location);
    }
  }, [updateAddress, updateRateData, onLocationDataChange]);

  return (
    <div className="space-y-6">
      {/* Card principal */}
      <div className="card">
        <div className="card-header">
          <h2 className="section-title">Cotización de Tarifas DHL Express</h2>
          <p className="section-subtitle">
            Obtén tarifas precisas para envíos nacionales e internacionales
          </p>
        </div>

        <div className="card-body">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Origen */}
            <div className="card bg-info-50 border-info-200">
              <div className="card-header border-info-200">
                <div className="flex items-center space-x-3">
                  <div className="flex items-center justify-center w-8 h-8 bg-info-500 text-white rounded-full text-sm font-semibold">
                    1
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-corporate-900">Dirección de Origen</h3>
                    <p className="text-sm text-info-600">Desde dónde se realizará el envío</p>
                  </div>
                </div>
              </div>
              
              <div className="card-body">
                <SmartLocationDropdown
                  key={`origin-${originLocation.country}-${originLocation.city}-${forceUpdateFlag}`}
                  onChange={handleOriginLocationChange}
                  value={originLocation}
                  required={true}
                  className="mb-4"
                  placeholder="Selecciona ciudad de origen..."
                />
              </div>
            </div>

            {/* Destino */}
            <div className="card bg-success-50 border-success-200">
              <div className="card-header border-success-200">
                <div className="flex items-center space-x-3">
                  <div className="flex items-center justify-center w-8 h-8 bg-success-500 text-white rounded-full text-sm font-semibold">
                    2
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-corporate-900">Dirección de Destino</h3>
                    <p className="text-sm text-success-600">A dónde se entregará el envío</p>
                  </div>
                </div>
              </div>
              
              <div className="card-body">
                <SmartLocationDropdown
                  key={`destination-${destinationLocation.country}-${destinationLocation.city}-${forceUpdateFlag}`}
                  onChange={handleDestinationLocationChange}
                  value={destinationLocation}
                  required={true}
                  className="mb-4"
                  placeholder="Selecciona ciudad de destino..."
                />
              </div>
            </div>
          </div>

          {/* Datos del Paquete */}
          <div className="card bg-warning-50 border-warning-200 mt-8">
            <div className="card-header border-warning-200">
              <div className="flex items-center space-x-3">
                <div className="flex items-center justify-center w-8 h-8 bg-warning-500 text-white rounded-full text-sm font-semibold">
                  3
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-corporate-900">Datos del Paquete</h3>
                  <p className="text-sm text-warning-600">Especifica peso y dimensiones</p>
                </div>
              </div>
            </div>
            
            <div className="card-body">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <label className="form-label flex items-center">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16l-3-9m3 9l3-9" />
                    </svg>
                    Peso (kg)
                    <FieldTooltip fieldPath="rate.weight" />
                  </label>
                  <NumericInput
                    step={0.1}
                    min={0.01}
                    value={rateData.weight}
                    onChange={(e, value) => updateRateData('weight', parseFloat(value) || 0)}
                    className="form-input"
                    placeholder="2.5"
                    allowDecimals={true}
                    decimals={2}
                  />
                </div>
                <div>
                  <label className="form-label flex items-center">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 7a2 2 0 00-2 2v2m0 0V9a2 2 0 012-2m0 2a2 2 0 002 2h2a2 2 0 002-2m0 0a2 2 0 012-2V5a2 2 0 00-2-2H9a2 2 0 00-2 2v2a2 2 0 002 2zm4 0a1 1 0 000-2zm0 0a1 1 0 000 2z" />
                    </svg>
                    Tipo de Contenido
                    <FieldTooltip fieldPath="rate.service" />
                  </label>
                  <select
                    value={rateData.service}
                    onChange={e => updateRateData('service', e.target.value)}
                    className="form-input"
                  >
                    <option value="P">📦 Paquetes</option>
                    <option value="D">📄 Documentos</option>
                  </select>
                </div>
                <div>
                  <label className="form-label flex items-center">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                    Número de Cuenta DHL
                    <FieldTooltip fieldPath="rate.account_number" />
                    {selectedAccount && (
                      <span className="ml-2 text-xs text-green-600 bg-green-100 px-2 py-1 rounded">
                        🔄 Sincronizado
                      </span>
                    )}
                  </label>
                  <input
                    type="text"
                    value={rateData.account_number}
                    onChange={e => updateRateData('account_number', e.target.value)}
                    className={`form-input ${
                      selectedAccount 
                        ? 'border-green-300 bg-green-50 focus:ring-green-500' 
                        : ''
                    }`}
                    placeholder="706014493"
                  />
                  {selectedAccount && (
                    <p className="text-xs text-green-600 mt-1">
                      ✅ Cuenta sincronizada automáticamente desde el dropdown superior
                    </p>
                  )}
                </div>
              </div>

              {/* Dimensiones */}
              <div className="mt-6">
                <h4 className="text-lg font-medium text-corporate-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-warning-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4a1 1 0 011-1h4M4 8H2m2 0l4-4m0 0v3m0-3h3m8 0V4a1 1 0 00-1-1h-4m0 0v3m0-3h-3m0 8h3m-3 0v3m3-3v3m0-3a1 1 0 00-1 1h-4m4-1V8m0 0l-4-4" />
                  </svg>
                  Dimensiones (cm)
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="form-label flex items-center">
                      Largo
                      <FieldTooltip fieldPath="rate.dimensions.length" />
                    </label>
                    <NumericInput
                      step={0.1}
                      min={0.1}
                      value={rateData.dimensions.length}
                      onChange={(e, value) => updateDimensions('length', parseFloat(value) || 0)}
                      className="form-input"
                      placeholder="30"
                      allowDecimals={true}
                      decimals={1}
                    />
                  </div>
                  <div>
                    <label className="form-label flex items-center">
                      Ancho
                      <FieldTooltip fieldPath="rate.dimensions.width" />
                    </label>
                    <NumericInput
                      step={0.1}
                      min={0.1}
                      value={rateData.dimensions.width}
                      onChange={(e, value) => updateDimensions('width', parseFloat(value) || 0)}
                      className="form-input"
                      placeholder="20"
                      allowDecimals={true}
                      decimals={1}
                    />
                  </div>
                  <div>
                    <label className="form-label flex items-center">
                      Alto
                      <FieldTooltip fieldPath="rate.dimensions.height" />
                    </label>
                    <NumericInput
                      step={0.1}
                      min={0.1}
                      value={rateData.dimensions.height}
                      onChange={(e, value) => updateDimensions('height', parseFloat(value) || 0)}
                      className="form-input"
                      placeholder="10"
                      allowDecimals={true}
                      decimals={1}
                    />
                  </div>
                </div>
              </div>

              {/* Fecha de Envío */}
              <div className="mt-6">
                <h4 className="text-lg font-medium text-corporate-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-warning-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  Fecha de Envío
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="form-label flex items-center">
                      Fecha Programada de Envío
                      <FieldTooltip fieldPath="rate.shippingDate" />
                    </label>
                    <input
                      type="date"
                      value={shippingDate}
                      min={minDate}
                      onChange={(e) => {
                        const selectedDate = new Date(e.target.value);
                        if (isBusinessDay(selectedDate)) {
                          setShippingDate(e.target.value);
                          updateRateData('shippingDate', e.target.value);
                        } else {
                          alert('Por favor seleccione un día laboral (Lunes a Viernes)');
                        }
                      }}
                      className="form-input"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Mínimo 5 días laborales desde hoy. Solo días laborales (Lun-Vie)
                    </p>
                  </div>
                  <div className="flex items-center bg-info-50 border border-info-200 rounded-md p-3">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-info-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-info-700">
                        <strong>Nota:</strong> DHL requiere al menos 5 días laborales de anticipación para garantizar disponibilidad de servicio.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Botón de Cotizar */}
          <div className="card-footer">
            <div className="flex justify-center">
              <button
                onClick={handleRateRequest}
                disabled={loading || !rateData.origin.country || !rateData.destination.country}
                className={`btn ${
                  loading || !rateData.origin.country || !rateData.destination.country
                    ? 'bg-corporate-400 cursor-not-allowed text-white'
                    : 'btn-primary shadow-medium hover:shadow-strong transform hover:scale-105'
                } px-8 py-3 text-base font-semibold flex items-center space-x-3`}
              >
                {loading ? (
                  <>
                    <div className="loading-spinner w-5 h-5"></div>
                    <span>Cotizando tarifas...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                    <span>Cotizar Tarifas DHL</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Alertas de error */}
      {error && (
        <div className="alert alert-error">
          <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <div>
            <h3 className="font-medium">Error en la cotización</h3>
            <p className="mt-1 text-sm opacity-90">{error}</p>
          </div>
        </div>
      )}

      {/* Resultados exitosos */}
      {result && result.success && result.rates && result.rates.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3 className="text-xl font-semibold text-corporate-900 flex items-center">
              <svg className="w-6 h-6 mr-2 text-success-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Resultados de Cotización
            </h3>
          </div>
          <div className="card-body">
            <RateResults 
              result={result} 
              originalRateData={rateData}
              onCreateShipment={handleCreateShipmentFromRate}
            />
          </div>
        </div>
      )}

      {/* Sin tarifas disponibles */}
      {result && result.success && (!result.rates || result.rates.length === 0) && (
        <div className="alert alert-warning">
          <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <div>
            <h3 className="font-medium">Sin Tarifas Disponibles</h3>
            <p className="mt-1 text-sm opacity-90">
              {result.message || 'No se encontraron tarifas para esta ruta y peso.'}
            </p>
          </div>
        </div>
      )}

      {/* Mensaje de error de resultado */}
      {result && !result.success && (
        <div className="alert alert-error">
          <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <div>
            <h3 className="font-medium">Error en Cotización</h3>
            <p className="mt-1 text-sm opacity-90">
              Ha ocurrido un error
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

RateTabImproved.propTypes = {
  rateData: PropTypes.object.isRequired,
  updateAddress: PropTypes.func.isRequired,
  updateRateData: PropTypes.func.isRequired,
  updateDimensions: PropTypes.func.isRequired,
  handleRateRequest: PropTypes.func.isRequired,
  loading: PropTypes.bool,
  error: PropTypes.string,
  result: PropTypes.object,
  handleCreateShipmentFromRate: PropTypes.func,
  selectedAccount: PropTypes.string,
  onLocationDataChange: PropTypes.func
};

export default RateTabImproved;
