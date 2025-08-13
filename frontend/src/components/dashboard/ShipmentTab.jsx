import React, { useState, useCallback, useEffect } from 'react';
import PropTypes from 'prop-types';
import SmartLocationDropdown from '../SmartLocationDropdown';
import useFormValidation from '../../hooks/useFormValidation';
import FormValidationStatus from '../FormValidationStatus';
import NumericInput from '../NumericInput';

/**
 * Componente para la pestaña "Crear Envío"
 */
const ShipmentTab = ({
  shipmentData,
  updateShipper,
  updateShipperBulk,
  updateRecipient,
  updateRecipientBulk,
  updatePackage,
  openContactModal,
  handleCreateShipment,
  shipmentLoading,
  shipmentError = null,
  shipmentResult = null,
  switchShipperRecipient
}) => {
  // Estados para las ubicaciones seleccionadas (formato SmartLocationDropdown)
  const [shipperLocation, setShipperLocation] = useState({
    country: shipmentData.shipper.country || '',
    countryName: '',
    state: shipmentData.shipper.state || '',
    stateName: '',
    city: shipmentData.shipper.city || '',
    cityName: shipmentData.shipper.city || '',
    postalCode: shipmentData.shipper.postalCode || '',
    postalCodeRange: '',
  serviceArea: shipmentData.shipper.serviceArea || ''
  });

  const [recipientLocation, setRecipientLocation] = useState({
    country: shipmentData.recipient.country || '',
    countryName: '',
    state: shipmentData.recipient.state || '',
    stateName: '',
    city: shipmentData.recipient.city || '',
    cityName: shipmentData.recipient.city || '',
    postalCode: shipmentData.recipient.postalCode || '',
    postalCodeRange: '',
  serviceArea: shipmentData.recipient.serviceArea || ''
  });

  // Sincronizar estados locales cuando cambia shipmentData (desde cotización) - Optimizado
  useEffect(() => {
    console.log('🔄 SINCRONIZANDO SHIPPER LOCATION:', shipmentData.shipper);
    console.log('🔍 Datos de ubicación preservados:', shipmentData._locationData);
    
    const preservedOrigin = shipmentData._locationData?.origin;
    setShipperLocation(prev => {
      // Construir nuevo valor preservando campos locales si props vienen vacías
      const nextLoc = {
        country: preservedOrigin?.country || shipmentData.shipper.country || prev.country || '',
        countryName: preservedOrigin?.countryName || shipmentData.shipper.countryName || prev.countryName || '',
        state: preservedOrigin?.state || shipmentData.shipper.state || prev.state || '',
        stateName: preservedOrigin?.stateName || shipmentData.shipper.stateName || prev.stateName || '',
        city: preservedOrigin?.cityName || preservedOrigin?.city || shipmentData.shipper.city || prev.city || '',
        cityName: preservedOrigin?.cityName || preservedOrigin?.city || shipmentData.shipper.city || prev.cityName || '',
        postalCode: preservedOrigin?.postalCode || shipmentData.shipper.postalCode || prev.postalCode || '',
        postalCodeRange: preservedOrigin?.postalCodeRange || shipmentData.shipper.postalCodeRange || prev.postalCodeRange || '',
        serviceArea: preservedOrigin?.serviceArea || shipmentData.shipper.serviceArea || prev.serviceArea || ''
      };
      const hasChanges = (
        prev.country !== nextLoc.country ||
        prev.state !== nextLoc.state ||
        prev.city !== nextLoc.city ||
        prev.postalCode !== nextLoc.postalCode ||
        prev.countryName !== nextLoc.countryName ||
        prev.stateName !== nextLoc.stateName ||
        prev.serviceArea !== nextLoc.serviceArea
      );
      if (hasChanges) {
        console.log('✅ Actualizando shipper location:', nextLoc);
      }
      return hasChanges ? nextLoc : prev;
    });
  }, [
    shipmentData.shipper.country,
    shipmentData.shipper.state, 
    shipmentData.shipper.city,
    shipmentData.shipper.postalCode,
    shipmentData.shipper.countryName,
    shipmentData.shipper.stateName,
  shipmentData.shipper.serviceArea,
    shipmentData._locationData?.origin
  ]);

  useEffect(() => {
    console.log('🔄 SINCRONIZANDO RECIPIENT LOCATION:', shipmentData.recipient);
    console.log('🔍 Datos de ubicación preservados (destino):', shipmentData._locationData);
    
    const preservedDestination = shipmentData._locationData?.destination;
    setRecipientLocation(prev => {
      const nextLoc = {
        country: preservedDestination?.country || shipmentData.recipient.country || prev.country || '',
        countryName: preservedDestination?.countryName || shipmentData.recipient.countryName || prev.countryName || '',
        state: preservedDestination?.state || shipmentData.recipient.state || prev.state || '',
        stateName: preservedDestination?.stateName || shipmentData.recipient.stateName || prev.stateName || '',
        city: preservedDestination?.cityName || preservedDestination?.city || shipmentData.recipient.city || prev.city || '',
        cityName: preservedDestination?.cityName || preservedDestination?.city || shipmentData.recipient.city || prev.cityName || '',
        postalCode: preservedDestination?.postalCode || shipmentData.recipient.postalCode || prev.postalCode || '',
        postalCodeRange: preservedDestination?.postalCodeRange || shipmentData.recipient.postalCodeRange || prev.postalCodeRange || '',
        serviceArea: preservedDestination?.serviceArea || shipmentData.recipient.serviceArea || prev.serviceArea || ''
      };
      const hasChanges = (
        prev.country !== nextLoc.country ||
        prev.state !== nextLoc.state ||
        prev.city !== nextLoc.city ||
        prev.postalCode !== nextLoc.postalCode ||
        prev.countryName !== nextLoc.countryName ||
        prev.stateName !== nextLoc.stateName ||
        prev.serviceArea !== nextLoc.serviceArea
      );
      if (hasChanges) {
        console.log('✅ Actualizando recipient location:', nextLoc);
      }
      return hasChanges ? nextLoc : prev;
    });
  }, [
    shipmentData.recipient.country,
    shipmentData.recipient.state,
    shipmentData.recipient.city,
    shipmentData.recipient.postalCode,
    shipmentData.recipient.countryName,
    shipmentData.recipient.stateName,
  shipmentData.recipient.serviceArea,
    shipmentData._locationData?.destination
  ]);

  // Manejar cambios en ubicación del remitente
  const handleShipperLocationChange = useCallback((location) => {
    console.log('📍 ACTUALIZANDO SHIPPER LOCATION:', location);
    
    // Actualizar estado local inmediatamente para UI responsiva
    setShipperLocation(location);
    
    // Usar función bulk para una sola actualización del estado global
    updateShipperBulk({
      country: location.country || '',
      state: location.state || '',
      city: location.cityName || location.city || '',
      postalCode: location.postalCode || ''
    });
  }, [updateShipperBulk]);

  // Manejar cambios en ubicación del destinatario
  const handleRecipientLocationChange = useCallback((location) => {
    console.log('📍 ACTUALIZANDO RECIPIENT LOCATION:', location);
    
    // Actualizar estado local inmediatamente para UI responsiva
    setRecipientLocation(location);
    
    // Usar función bulk para una sola actualización del estado global
    updateRecipientBulk({
      country: location.country || '',
      state: location.state || '',
      city: location.cityName || location.city || '',
      postalCode: location.postalCode || ''
    });
  }, [updateRecipientBulk]);

  // ✅ Hook de validación para shipment
  const validation = useFormValidation(shipmentData, 'shipment');

  // ✅ Manejar envío con validación
  const handleSubmit = () => {
    if (validation.validate()) {
      handleCreateShipment();
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Crear Nuevo Envío DHL Express
        </h2>
        
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Datos del Remitente */}
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Datos del Remitente</h3>
                <div className="flex gap-2">
                  {/* Botón de intercambio para móviles */}
                  <button
                    type="button"
                    onClick={switchShipperRecipient}
                    className="lg:hidden inline-flex items-center px-3 py-2 border border-dhl-red rounded-md text-sm font-medium text-dhl-red bg-white hover:bg-dhl-red hover:text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-dhl-red transition-colors duration-200"
                    title="Intercambiar datos"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    onClick={() => openContactModal('shipper')}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-dhl-red"
                    title="Seleccionar de agenda de contactos"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 4v12l-4-2-4 2V4M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    Agenda
                  </button>
                </div>
              </div>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
                    <input
                      type="text"
                      value={shipmentData.shipper.name}
                      onChange={e => updateShipper('name', e.target.value)}
                      className={validation.getFieldClass('shipper.name', 'w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
                      placeholder="Nombre del remitente"
                    />
                    {validation.hasFieldError('shipper.name') && (
                      <p className="mt-1 text-sm text-red-600">{validation.getFieldError('shipper.name')}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Empresa</label>
                    <input
                      type="text"
                      value={shipmentData.shipper.company}
                      onChange={e => updateShipper('company', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                      placeholder="Nombre de la empresa"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Dirección *</label>
                  <input
                    type="text"
                    value={shipmentData.shipper.address}
                    onChange={e => updateShipper('address', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                    placeholder="Dirección completa"
                  />
                </div>
                
                {/* Ubicación del Remitente con SmartLocationDropdown */}
                <div className="bg-blue-50 rounded-lg p-4 mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <span className="flex items-center">
                      <span className="w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-xs font-semibold mr-2">
                        📍
                      </span>
                      Ubicación del Remitente *
                    </span>
                  </label>
                  <SmartLocationDropdown
                    onChange={handleShipperLocationChange}
                    value={shipperLocation}
                    required={true}
                    className="mb-4"
                    placeholder="Selecciona ubicación del remitente..."
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono *</label>
                    <input
                      type="text"
                      value={shipmentData.shipper.phone}
                      onChange={e => updateShipper('phone', e.target.value)}
                      className={validation.getFieldClass('shipper.phone', 'w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
                      placeholder="+507 123 4567"
                    />
                    {validation.hasFieldError('shipper.phone') && (
                      <p className="mt-1 text-sm text-red-600">{validation.getFieldError('shipper.phone')}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <input
                      type="email"
                      value={shipmentData.shipper.email}
                      onChange={e => updateShipper('email', e.target.value)}
                      className={validation.getFieldClass('shipper.email', 'w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
                      placeholder="remitente@email.com"
                    />
                    {validation.hasFieldError('shipper.email') && (
                      <p className="mt-1 text-sm text-red-600">{validation.getFieldError('shipper.email')}</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Datos del Destinatario */}
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Datos del Destinatario</h3>
                <div className="flex gap-2">
                  {/* Botón de intercambio para móviles */}
                  <button
                    type="button"
                    onClick={switchShipperRecipient}
                    className="lg:hidden inline-flex items-center px-3 py-2 border border-dhl-red rounded-md text-sm font-medium text-dhl-red bg-white hover:bg-dhl-red hover:text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-dhl-red transition-colors duration-200"
                    title="Intercambiar datos"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    onClick={() => openContactModal('recipient')}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-dhl-red"
                    title="Seleccionar de agenda de contactos"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 4v12l-4-2-4 2V4M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    Agenda
                  </button>
                </div>
              </div>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
                    <input
                      type="text"
                      value={shipmentData.recipient.name}
                      onChange={e => updateRecipient('name', e.target.value)}
                      className={validation.getFieldClass('recipient.name', 'w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
                      placeholder="Nombre del destinatario"
                    />
                    {validation.hasFieldError('recipient.name') && (
                      <p className="mt-1 text-sm text-red-600">{validation.getFieldError('recipient.name')}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Empresa</label>
                    <input
                      type="text"
                      value={shipmentData.recipient.company}
                      onChange={e => updateRecipient('company', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                      placeholder="Nombre de la empresa"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Dirección *</label>
                  <input
                    type="text"
                    value={shipmentData.recipient.address}
                    onChange={e => updateRecipient('address', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                    placeholder="Dirección completa"
                  />
                </div>
                
                {/* Ubicación del Destinatario con SmartLocationDropdown */}
                <div className="bg-green-50 rounded-lg p-4 mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <span className="flex items-center">
                      <span className="w-6 h-6 bg-green-100 text-green-800 rounded-full flex items-center justify-center text-xs font-semibold mr-2">
                        📍
                      </span>
                      Ubicación del Destinatario *
                    </span>
                  </label>
                  <SmartLocationDropdown
                    onChange={handleRecipientLocationChange}
                    value={recipientLocation}
                    required={true}
                    className="mb-4"
                    placeholder="Selecciona ubicación del destinatario..."
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono *</label>
                    <input
                      type="text"
                      value={shipmentData.recipient.phone}
                      onChange={e => updateRecipient('phone', e.target.value)}
                      className={validation.getFieldClass('recipient.phone', 'w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
                      placeholder="+1 305 123 4567"
                    />
                    {validation.hasFieldError('recipient.phone') && (
                      <p className="mt-1 text-sm text-red-600">{validation.getFieldError('recipient.phone')}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <input
                      type="email"
                      value={shipmentData.recipient.email}
                      onChange={e => updateRecipient('email', e.target.value)}
                      className={validation.getFieldClass('recipient.email', 'w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
                      placeholder="destinatario@email.com"
                    />
                    {validation.hasFieldError('recipient.email') && (
                      <p className="mt-1 text-sm text-red-600">{validation.getFieldError('recipient.email')}</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Botón de Intercambio - Entre las secciones */}
          <div className="flex justify-center my-6">
            <button
              type="button"
              onClick={switchShipperRecipient}
              className="hidden lg:flex items-center gap-2 px-6 py-3 border-2 border-dhl-red text-dhl-red bg-white hover:bg-dhl-red hover:text-white rounded-lg shadow-md transition-all duration-200 font-medium"
              title="Intercambiar datos entre remitente y destinatario"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
            </button>
          </div>

          {/* Datos del Paquete */}
          <div className="mt-8">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Información del Paquete</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Peso (kg) *</label>
                <NumericInput
                  step={0.1}
                  value={shipmentData.package.weight}
                  onChange={(e, value) => updatePackage('weight', parseFloat(value) || 0)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                  placeholder="45"
                  min={0.01}
                  allowDecimals={true}
                  decimals={2}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Largo (cm) *</label>
                <NumericInput
                  value={shipmentData.package.length}
                  onChange={(e, value) => updatePackage('length', parseFloat(value) || 0)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                  placeholder="20"
                  min={1}
                  allowDecimals={true}
                  decimals={1}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ancho (cm) *</label>
                <NumericInput
                  value={shipmentData.package.width}
                  onChange={(e, value) => updatePackage('width', parseFloat(value) || 0)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                  placeholder="15"
                  min={1}
                  allowDecimals={true}
                  decimals={1}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Alto (cm) *</label>
                <NumericInput
                  value={shipmentData.package.height}
                  onChange={(e, value) => updatePackage('height', parseFloat(value) || 0)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                  placeholder="10"
                  min={1}
                  allowDecimals={true}
                  decimals={1}
                />
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descripción *</label>
                <input
                  type="text"
                  value={shipmentData.package.description}
                  onChange={e => updatePackage('description', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                  placeholder="Descripción del contenido"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Valor Declarado *</label>
                <NumericInput
                  step={0.01}
                  value={shipmentData.package.value}
                  onChange={(e, value) => updatePackage('value', parseFloat(value) || 0)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                  placeholder="100"
                  min={0.01}
                  allowDecimals={true}
                  decimals={2}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Moneda</label>
                <select
                  value={shipmentData.package.currency}
                  onChange={e => updatePackage('currency', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                >
                  <option value="USD">USD - Dólar Americano</option>
                  <option value="EUR">EUR - Euro</option>
                  <option value="GBP">GBP - Libra Esterlina</option>
                </select>
              </div>
            </div>
          </div>

          {/* Opciones de Servicio */}
          <div className="mt-8">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Opciones de Servicio</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Servicio</label>
                <select
                  value={shipmentData.service || 'P'}
                  onChange={e => updatePackage('service', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                >
                  <option value="P">Paquetes (NON_DOCUMENTS)</option>
                  <option value="D">Documentos (DOCUMENTS)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Pago</label>
                <select
                  value={shipmentData.payment || 'S'}
                  onChange={e => updatePackage('payment', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                >
                  <option value="S">Remitente (Shipper)</option>
                  <option value="R">Destinatario (Recipient)</option>
                  <option value="T">Tercero (Third Party)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Estado de validación */}
          <div className="mt-6">
            <FormValidationStatus
              isValid={validation.isValid}
            />
          </div>

          {/* Botones de acción */}
          <div className="mt-8 space-y-2">
            <button
              onClick={handleSubmit}
              disabled={shipmentLoading || !validation.canSubmit}
              className={`w-full py-3 px-4 rounded-md font-semibold transition-all duration-200 ${
                validation.canSubmit && !shipmentLoading
                  ? 'bg-dhl-red text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-dhl-red focus:ring-offset-2'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
              title={!validation.canSubmit ? `Complete todos los campos requeridos (${validation.missingCount} faltantes)` : ''}
            >
              {shipmentLoading ? (
                <span className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Creando envío...
                </span>
              ) : !validation.canSubmit ? (
                `⚠️ Complete ${validation.missingCount} campo(s) para continuar`
              ) : (
                '📦 Crear Envío DHL'
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mostrar errores de envío mejorados */}
      {shipmentError && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3 w-full">
              <h3 className="text-sm font-medium text-red-800">Error al crear envío</h3>
              <div className="mt-2 text-sm text-red-700">
                {/* Mostrar mensaje genérico para todos los errores */}
                <div className="whitespace-pre-wrap">Ha ocurrido un error</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mostrar resultados de envío mejorados */}
      {shipmentResult && shipmentResult.success && (
        <div className="bg-green-50 border border-green-200 rounded-md p-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-6 w-6 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3 w-full">
              <h3 className="text-lg font-medium text-green-800 mb-3">
                ¡Envío creado exitosamente!
              </h3>
              <div className="space-y-4">
                {/* Tracking Number Principal */}
                {shipmentResult.tracking_number && (
                  <div className="bg-white p-4 rounded-lg border shadow-sm">
                    <div className="font-semibold text-gray-900 mb-2 flex items-center">
                      <svg className="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Número de Seguimiento Principal
                    </div>
                    <div className="text-xl font-mono text-green-700 bg-green-50 p-2 rounded">
                      {shipmentResult.tracking_number}
                    </div>
                  </div>
                )}
                
                {/* Información Adicional */}
                <div className="bg-white p-4 rounded-lg border shadow-sm">
                  <div className="font-semibold text-gray-900 mb-3 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Información Adicional
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    {shipmentResult.shipment_id && (
                      <div>
                        <span className="font-medium text-gray-700">ID del Envío:</span>
                        <div className="text-gray-600">#{shipmentResult.shipment_id}</div>
                      </div>
                    )}
                    {shipmentResult.shipment_status && (
                      <div>
                        <span className="font-medium text-gray-700">Estado:</span>
                        <div className="text-gray-600 capitalize">{shipmentResult.shipment_status}</div>
                      </div>
                    )}
                    {shipmentResult.content_info && (
                      <div>
                        <span className="font-medium text-gray-700">Tipo de Contenido:</span>
                        <div className="text-gray-600">{shipmentResult.content_info.description}</div>
                      </div>
                    )}
                    {shipmentResult.request_timestamp && (
                      <div>
                        <span className="font-medium text-gray-700">Fecha de Creación:</span>
                        <div className="text-gray-600">
                          {new Date(shipmentResult.request_timestamp).toLocaleString('es-ES')}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Fallback para resultados sin success flag */}
      {shipmentResult && !shipmentResult.success && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <h3 className="text-sm font-medium text-green-800">Envío Creado con Éxito</h3>
          <pre className="mt-2 text-sm text-gray-700 whitespace-pre-wrap break-all">
            {JSON.stringify(shipmentResult, null, 2)}
          </pre>
        </div>
      )}

      {/* Información de ayuda */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Información sobre las Ubicaciones</h3>
            <div className="mt-1 text-sm text-blue-700">
              Los dropdowns muestran solo países y ciudades donde DHL Express tiene servicio disponible. 
              Si no encuentras tu ubicación, verifica que DHL Express tenga cobertura en esa área.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

ShipmentTab.propTypes = {
  shipmentData: PropTypes.object.isRequired,
  updateShipper: PropTypes.func.isRequired,
  updateShipperBulk: PropTypes.func.isRequired,
  updateRecipient: PropTypes.func.isRequired,
  updateRecipientBulk: PropTypes.func.isRequired,
  updatePackage: PropTypes.func.isRequired,
  openContactModal: PropTypes.func.isRequired,
  handleCreateShipment: PropTypes.func.isRequired,
  shipmentLoading: PropTypes.bool.isRequired,
  shipmentError: PropTypes.string,
  shipmentResult: PropTypes.object,
  switchShipperRecipient: PropTypes.func.isRequired
};

export default ShipmentTab;
