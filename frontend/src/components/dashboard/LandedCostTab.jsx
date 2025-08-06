import React, { useState, useCallback, useEffect } from 'react';
import PropTypes from 'prop-types';
import { api } from '../../config/api';
import FieldTooltip from '../FieldTooltip';
import SmartLocationDropdown from '../SmartLocationDropdown';
import { DHL_CATEGORIES } from '../../constants/dhlCategories';
import useFormValidation from '../../hooks/useFormValidation';
import FormValidationStatus from '../FormValidationStatus';
import NumericInput from '../NumericInput';

/**
 * Componente para la pestaña "Costo Total de Importación"
 * Incluye toda la funcionalidad del calculador integrada directamente
 */
const LandedCostTab = ({ handleCreateShipmentFromRate, setActiveTab, selectedAccount }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  
  // Estado del formulario - Completamente vacío
  const [formData, setFormData] = useState({
    origin: {
      postal_code: '',
      city: '',
      country: ''
    },
    destination: {
      postal_code: '',
      city: '',
      country: ''
    },
    weight: 0,
    dimensions: {
      length: 0,
      width: 0,
      height: 0
    },
    currency_code: 'USD',
    service: 'P',  // Tipo de contenido: P (NON_DOCUMENTS) o D (DOCUMENTS)
    is_customs_declarable: true,
    is_dtp_requested: false,
    is_insurance_requested: false,
    get_cost_breakdown: true,
    shipment_purpose: 'personal',
    transportation_mode: 'air',
    merchant_selected_carrier_name: 'DHL',
    account_number: '',
    items: [{
      name: '',
      description: '',
      manufacturer_country: '',
      part_number: '',
      quantity: 1,
      quantity_type: 'pcs',
      unit_price: 0,
      unit_price_currency_code: 'USD',
      customs_value: 0,
      customs_value_currency_code: 'USD',
      commodity_code: '',
      weight: 0,
      weight_unit_of_measurement: 'metric',
      category: '',
      brand: ''
    }]
  });

  // ✅ Hook de validación para landed cost
  const validation = useFormValidation(formData, 'landedCost');

  // Estados para las ubicaciones seleccionadas (formato SmartLocationDropdown)
  const [originLocation, setOriginLocation] = useState({
    country: formData.origin.country || '',
    countryName: '',
    state: '',
    stateName: '',
    city: formData.origin.city || '',
    cityName: formData.origin.city || '',
    postalCode: formData.origin.postal_code || '',
    postalCodeRange: ''
  });

  const [destinationLocation, setDestinationLocation] = useState({
    country: formData.destination.country || '',
    countryName: '',
    state: '',
    stateName: '',
    city: formData.destination.city || '',
    cityName: formData.destination.city || '',
    postalCode: formData.destination.postal_code || '',
    postalCodeRange: ''
  });

  // ✅ SINCRONIZAR ACCOUNT_NUMBER CON DROPDOWN SUPERIOR
  useEffect(() => {
    if (selectedAccount) {
      setFormData(prev => ({
        ...prev,
        account_number: selectedAccount
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        account_number: ''
      }));
    }
  }, [selectedAccount]);

  // Manejar cambios en origen
  const handleOriginLocationChange = useCallback((location) => {
    setOriginLocation(location);
    
    // Actualizar datos del formulario
    setFormData(prev => ({
      ...prev,
      origin: {
        ...prev.origin,
        country: location.country || '',
        city: location.city || '',
        postal_code: location.postalCode || ''
      }
    }));
  }, []);

  // Función para crear envío desde landed cost
  const handleCreateShipmentFromLandedCost = useCallback(() => {
    if (!result || !result.success || !result.landed_cost) {
      alert('No hay resultados de landed cost para crear un envío');
      return;
    }

    // Crear estructura similar a rate data para usar la función existente
    const simulatedRateData = {
      origin: {
        country: formData.origin.country,
        city: formData.origin.city,
        postal_code: formData.origin.postal_code,
        country_name: originLocation.countryName || formData.origin.country
      },
      destination: {
        country: formData.destination.country,
        city: formData.destination.city,
        postal_code: formData.destination.postal_code,
        country_name: destinationLocation.countryName || formData.destination.country
      },
      weight: formData.weight,
      dimensions: formData.dimensions,
      service: formData.service,
      account_number: formData.account_number
    };

    // Crear estructura de rate simulada desde landed cost
    const simulatedRate = {
      service_name: 'DHL Express (desde Landed Cost)',
      service_code: formData.service,
      total_charge: result.landed_cost.total_cost || 0,
      currency: result.landed_cost.currency || 'USD',
      delivery_date: null,
      charges: result.landed_cost.breakdown || []
    };

    console.log('📦 Creando envío desde Landed Cost:', {
      simulatedRateData,
      simulatedRate,
      originalFormData: formData
    });

    // Mostrar notificación
    alert(`✅ Datos prellenados desde Landed Cost:\n• Origen: ${formData.origin.city}, ${formData.origin.country}\n• Destino: ${formData.destination.city}, ${formData.destination.country}\n• Peso: ${formData.weight}kg\n• Costo estimado: ${result.landed_cost.currency} ${result.landed_cost.total_cost?.toLocaleString()}\n\nNavegando a la pestaña "Crear Envío"...`);

    // Usar la función existente del Dashboard
    handleCreateShipmentFromRate(simulatedRate, simulatedRateData);
    
    // Cambiar a la pestaña de shipment
    setActiveTab('shipment');
  }, [result, formData, originLocation, destinationLocation, handleCreateShipmentFromRate, setActiveTab]);

  // Manejar cambios en destino
  const handleDestinationLocationChange = useCallback((location) => {
    setDestinationLocation(location);
    
    // Actualizar datos del formulario
    setFormData(prev => ({
      ...prev,
      destination: {
        ...prev.destination,
        country: location.country || '',
        city: location.city || '',
        postal_code: location.postalCode || ''
      }
    }));
  }, []);

  // Manejo de cambios en inputs
  const handleInputChange = (section, field, value) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  const handleDirectChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Manejo de items
  const handleItemChange = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = value;
    setFormData(prev => ({
      ...prev,
      items: newItems
    }));
  };

  const addItem = () => {
    setFormData(prev => ({
      ...prev,
      items: [...prev.items, {
        name: '',
        description: '',
        manufacturer_country: '',
        part_number: '',
        quantity: 1,
        quantity_type: 'pcs',
        unit_price: '',
        unit_price_currency_code: 'USD',
        customs_value: '',
        customs_value_currency_code: 'USD',
        commodity_code: '',
        weight: '',
        weight_unit_of_measurement: 'metric',
        category: '',
        brand: ''
      }]
    }));
  };

  const removeItem = (index) => {
    if (formData.items.length > 1) {
      setFormData(prev => ({
        ...prev,
        items: prev.items.filter((_, i) => i !== index)
      }));
    }
  };

  // Función para limpiar formulario
  const clearForm = () => {
    setFormData({
      origin: {
        postal_code: '',
        city: '',
        country: ''
      },
      destination: {
        postal_code: '',
        city: '',
        country: ''
      },
      weight: '',
      dimensions: {
        length: '',
        width: '',
        height: ''
      },
      currency_code: 'USD',
      service: 'P',
      is_customs_declarable: true,
      is_dtp_requested: false,
      is_insurance_requested: false,
      get_cost_breakdown: true,
      shipment_purpose: 'personal',
      transportation_mode: 'air',
      merchant_selected_carrier_name: 'DHL',
      account_number: '',
      items: [{
        name: '',
        description: '',
        manufacturer_country: '',
        part_number: '',
        quantity: 1,
        quantity_type: 'pcs',
        unit_price: '',
        unit_price_currency_code: 'USD',
        customs_value: '',
        customs_value_currency_code: 'USD',
        commodity_code: '',
        weight: '',
        weight_unit_of_measurement: 'metric',
        category: '',
        brand: ''
      }]
    });
    setResult(null);
    setError(null);
  };

  // Envío del formulario
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // ✅ Validar antes de enviar
    if (!validation.validate()) {
      return;
    }
    
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await api.post('/dhl/landed-cost/', formData);
      setResult(response.data);
    } catch (err) {
      console.error('Error calculando costo total:', err);
      setError(err.response?.data?.message || 'Error al calcular costo total de importación');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="max-w-6xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">
            Calculadora de Costo Total de Importación
          </h2>
          <p className="text-gray-600 mb-8 text-center">
            Calcula el costo total de importación incluyendo shipping, aranceles, impuestos y fees
          </p>

          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Origen y Destino */}
            <div className="grid md:grid-cols-2 gap-8">
              {/* Origen */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <span className="w-8 h-8 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-sm font-semibold mr-2">
                    1
                  </span>
                  📤 Dirección de Origen
                </h3>
                
                <SmartLocationDropdown
                  onChange={handleOriginLocationChange}
                  value={originLocation}
                  required={true}
                  className="mb-4"
                  placeholder="Selecciona origen..."
                />
              </div>

              {/* Destino */}
              <div className="bg-green-50 rounded-lg p-4">
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <span className="w-8 h-8 bg-green-100 text-green-800 rounded-full flex items-center justify-center text-sm font-semibold mr-2">
                    2
                  </span>
                  📥 Dirección de Destino
                </h3>
                
                <SmartLocationDropdown
                  onChange={handleDestinationLocationChange}
                  value={destinationLocation}
                  required={true}
                  className="mb-4"
                  placeholder="Selecciona destino..."
                />
              </div>
            </div>

            {/* Dimensiones del Paquete */}
            <div className="bg-yellow-50 rounded-lg p-4">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <span className="w-8 h-8 bg-yellow-100 text-yellow-800 rounded-full flex items-center justify-center text-sm font-semibold mr-2">
                  3
                </span>
                📦 Información del Paquete
              </h3>
              <div className="grid md:grid-cols-4 gap-4">
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                    Peso (kg)
                    <FieldTooltip fieldPath="weight" />
                  </label>
                  <NumericInput
                    value={formData.weight}
                    onChange={(e, value) => handleDirectChange('weight', parseFloat(value) || '')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="45"
                    step={0.1}
                    min={0.01}
                    allowDecimals={true}
                    decimals={2}
                  />
                </div>
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                    Largo (cm)
                    <FieldTooltip fieldPath="dimensions.length" />
                  </label>
                  <NumericInput
                    value={formData.dimensions.length}
                    onChange={(e, value) => handleInputChange('dimensions', 'length', parseFloat(value) || '')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="20"
                    step={0.1}
                    min={1}
                    allowDecimals={true}
                    decimals={1}
                  />
                </div>
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                    Ancho (cm)
                    <FieldTooltip fieldPath="dimensions.width" />
                  </label>
                  <NumericInput
                    value={formData.dimensions.width}
                    onChange={(e, value) => handleInputChange('dimensions', 'width', parseFloat(value) || '')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="15"
                    step={0.1}
                    min={1}
                    allowDecimals={true}
                    decimals={1}
                  />
                </div>
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                    Alto (cm)
                    <FieldTooltip fieldPath="dimensions.height" />
                  </label>
                  <NumericInput
                    value={formData.dimensions.height}
                    onChange={(e, value) => handleInputChange('dimensions', 'height', parseFloat(value) || '')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="10"
                    step={0.1}
                    min={1}
                    allowDecimals={true}
                    decimals={1}
                  />
                </div>
              </div>
            </div>

            {/* Configuración */}
            <div className="space-y-4">
              <h3 className="text-xl font-semibold text-gray-900 border-b pb-2">⚙️ Configuración</h3>
              <div className="grid md:grid-cols-4 gap-4">
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                    Moneda
                    <FieldTooltip fieldPath="currency_code" />
                  </label>
                  <select
                    value={formData.currency_code}
                    onChange={(e) => handleDirectChange('currency_code', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="USD">USD - Dólar</option>
                    <option value="EUR">EUR - Euro</option>
                    <option value="COP">COP - Peso Colombiano</option>
                    <option value="MXN">MXN - Peso Mexicano</option>
                  </select>
                </div>
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                    Tipo de Contenido
                    <FieldTooltip fieldPath="service" />
                  </label>
                  <select
                    value={formData.service}
                    onChange={(e) => handleDirectChange('service', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="P">Paquetes (NON_DOCUMENTS)</option>
                    <option value="D">Documentos (DOCUMENTS)</option>
                  </select>
                </div>
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                    Propósito
                    <FieldTooltip fieldPath="shipment_purpose" />
                  </label>
                  <select
                    value={formData.shipment_purpose}
                    onChange={(e) => handleDirectChange('shipment_purpose', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="personal">Personal</option>
                    <option value="commercial">Comercial</option>
                  </select>
                </div>
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                    Transporte
                    <FieldTooltip fieldPath="transport_mode" />
                  </label>
                  <select
                    value={formData.transportation_mode}
                    onChange={(e) => handleDirectChange('transportation_mode', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="air">Aéreo</option>
                    <option value="ocean">Marítimo</option>
                    <option value="ground">Terrestre</option>
                  </select>
                </div>
              </div>

              {/* Campo para número de cuenta DHL */}
              <div className="mt-4">
                <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                  Número de Cuenta DHL
                  <FieldTooltip fieldPath="account_number" />
                  {selectedAccount && (
                    <span className="ml-2 text-xs text-green-600 bg-green-100 px-2 py-1 rounded">
                      🔄 Sincronizado desde dropdown
                    </span>
                  )}
                </label>
                <input
                  type="text"
                  value={formData.account_number}
                  onChange={(e) => handleDirectChange('account_number', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
                    selectedAccount 
                      ? 'border-green-300 bg-green-50 focus:ring-green-500' 
                      : 'border-gray-300 focus:ring-orange-500'
                  }`}
                  placeholder="Ej: 706091269"
                />
                {selectedAccount && (
                  <p className="text-xs text-green-600 mt-1">
                    ✅ Cuenta sincronizada automáticamente desde el dropdown superior
                  </p>
                )}
              </div>
            </div>

            {/* Checkboxes */}
            <div className="mt-4 grid md:grid-cols-3 gap-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_dtp_requested}
                  onChange={(e) => handleDirectChange('is_dtp_requested', e.target.checked)}
                  className="mr-2 w-4 h-4 text-orange-600 bg-gray-100 border-gray-300 rounded focus:ring-orange-500"
                />
                <span className="text-sm text-gray-700 flex items-center">
                  DTP (Duties & Taxes Paid)
                  <FieldTooltip fieldPath="is_dtp_requested" />
                </span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_insurance_requested}
                  onChange={(e) => handleDirectChange('is_insurance_requested', e.target.checked)}
                  className="mr-2 w-4 h-4 text-orange-600 bg-gray-100 border-gray-300 rounded focus:ring-orange-500"
                />
                <span className="text-sm text-gray-700 flex items-center">
                  Solicitar Seguro
                  <FieldTooltip fieldPath="is_insurance_requested" />
                </span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.get_cost_breakdown}
                  onChange={(e) => handleDirectChange('get_cost_breakdown', e.target.checked)}
                  className="mr-2 w-4 h-4 text-orange-600 bg-gray-100 border-gray-300 rounded focus:ring-orange-500"
                />
                <span className="text-sm text-gray-700 flex items-center">
                  Desglose de Costos
                  <FieldTooltip fieldPath="get_cost_breakdown" />
                </span>
              </label>
            </div>

            {/* Productos/Items */}
            <div className="space-y-6">
              <h3 className="text-xl font-semibold text-gray-900 border-b pb-2">🛍️ Productos</h3>
              {formData.items.map((item, index) => (
                <div key={index} className="border rounded-lg p-6 bg-gray-50">
                  <div className="flex justify-between items-center mb-4">
                    <h4 className="text-lg font-medium text-gray-900">Producto {index + 1}</h4>
                    {formData.items.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeItem(index)}
                        className="text-red-600 hover:text-red-800 font-medium"
                      >
                        ❌ Eliminar
                      </button>
                    )}
                  </div>
                  
                  <div className="grid md:grid-cols-3 gap-4">
                    <div>
                      <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                        Nombre *
                        <FieldTooltip fieldPath="items.name" />
                      </label>
                      <input
                        type="text"
                        value={item.name}
                        onChange={(e) => handleItemChange(index, 'name', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                        placeholder="Ej: KNITWEAR COTTON"
                        required
                      />
                    </div>
                    <div>
                      <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                        Descripción *
                        <FieldTooltip fieldPath="items.description" />
                      </label>
                      <input
                        type="text"
                        value={item.description}
                        onChange={(e) => handleItemChange(index, 'description', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                        placeholder="Descripción detallada"
                        required
                      />
                    </div>
                    <div>
                      <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                        País Manufactura *
                        <FieldTooltip fieldPath="items.manufacturer_country" />
                      </label>
                      <input
                        type="text"
                        value={item.manufacturer_country}
                        onChange={(e) => handleItemChange(index, 'manufacturer_country', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                        placeholder="Ej: US"
                        maxLength="2"
                        required
                      />
                    </div>
                    <div>
                      <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                        Cantidad *
                        <FieldTooltip fieldPath="items.quantity" />
                      </label>
                      <NumericInput
                        value={item.quantity}
                        onChange={(e, value) => handleItemChange(index, 'quantity', parseInt(value) || 1)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                        min={1}
                        allowDecimals={false}
                        required
                      />
                    </div>
                    <div>
                      <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                        Precio Unitario *
                        <FieldTooltip fieldPath="items.unit_price" />
                      </label>
                      <NumericInput
                        value={item.unit_price}
                        onChange={(e, value) => handleItemChange(index, 'unit_price', parseFloat(value) || '')}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                        placeholder="2500"
                        step={0.01}
                        min={0.01}
                        allowDecimals={true}
                        decimals={2}
                        required
                      />
                    </div>
                    <div>
                      <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                        Valor Aduanero *
                        <FieldTooltip fieldPath="items.customs_value" />
                      </label>
                      <NumericInput
                        value={item.customs_value}
                        onChange={(e, value) => handleItemChange(index, 'customs_value', parseFloat(value) || '')}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                        placeholder="5000"
                        step={0.01}
                        min={0.01}
                        allowDecimals={true}
                        decimals={2}
                        required
                      />
                    </div>
                    <div>
                      <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                        Código Commodity (HS) *
                        <FieldTooltip fieldPath="items.commodity_code" />
                      </label>
                      <input
                        type="text"
                        value={item.commodity_code}
                        onChange={(e) => handleItemChange(index, 'commodity_code', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                        placeholder="640391"
                        required
                      />
                    </div>
                    <div>
                      <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                        Peso Item (kg) *
                        <FieldTooltip fieldPath="weight" />
                      </label>
                      <NumericInput
                        value={item.weight}
                        onChange={(e, value) => handleItemChange(index, 'weight', parseFloat(value) || '')}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                        placeholder="22.5"
                        step={0.1}
                        min={0.01}
                        allowDecimals={true}
                        decimals={2}
                        required
                      />
                    </div>
                    <div>
                      <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                        Marca
                        <FieldTooltip fieldPath="items.brand" />
                      </label>
                      <input
                        type="text"
                        value={item.brand}
                        onChange={(e) => handleItemChange(index, 'brand', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                        placeholder="COTTON BRAND"
                      />
                    </div>
                    <div>
                      <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                        Número de Parte
                        <FieldTooltip fieldPath="items.part_number" />
                      </label>
                      <input
                        type="text"
                        value={item.part_number}
                        onChange={(e) => handleItemChange(index, 'part_number', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                        placeholder="SKU-12345"
                      />
                    </div>
                    <div>
                      <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                        Categoría
                        <FieldTooltip fieldPath="items.category" />
                      </label>
                      <select
                        value={item.category}
                        onChange={(e) => handleItemChange(index, 'category', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                      >
                        <option value="">Seleccionar categoría</option>
                        {DHL_CATEGORIES.map(category => (
                          <option key={category.code} value={category.code}>
                            {category.code} - {category.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              ))}
              
              <div className="flex justify-center">
                <button
                  type="button"
                  onClick={addItem}
                  className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  ➕ Agregar Producto
                </button>
              </div>
            </div>

            {/* Estado de validación */}
            <div className="mt-8">
              <FormValidationStatus
                isValid={validation.isValid}
              />
            </div>

            {/* Botones */}
            <div className="flex gap-4 justify-end">
              <button
                type="button"
                onClick={clearForm}
                className="px-6 py-3 bg-gray-500 text-white font-semibold rounded-lg hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition duration-300"
              >
                🗑️ Limpiar Formulario
              </button>
              <button
                type="submit"
                disabled={loading || !validation.canSubmit}
                className={`px-8 py-3 font-semibold rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 transition duration-300 ${
                  validation.canSubmit && !loading
                    ? 'bg-gradient-to-r from-green-500 to-blue-500 text-white hover:from-green-600 hover:to-blue-600 focus:ring-green-500'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
                title={!validation.canSubmit ? `Complete todos los campos requeridos (${validation.missingCount} faltantes)` : ''}
              >
                {loading ? (
                  <span className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Calculando...
                  </span>
                ) : !validation.canSubmit ? (
                  `⚠️ Complete ${validation.missingCount} campo(s) para continuar`
                ) : (
                  '🧮 Calcular Costo Total'
                )}
              </button>
            </div>
          </form>

          {/* Resultados */}
          {error && (
            <div className="mt-8 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
              <h3 className="font-semibold mb-2">❌ Error</h3>
              <p>{error}</p>
            </div>
          )}

          {result && result.success && (
            <div className="mt-8 space-y-6">
              <div className="p-6 bg-green-100 border border-green-400 text-green-700 rounded-lg">
                <h3 className="text-xl font-semibold mb-4">✅ Costo Total Calculado</h3>
                
                {result.landed_cost && (
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold mb-2">💰 Resumen de Costos</h4>
                      <div className="space-y-2 text-lg">
                        <div className="flex justify-between">
                          <span>Costo Total:</span>
                          <span className="font-bold">
                            {result.landed_cost.currency} {result.landed_cost.total_cost?.toLocaleString() || '0'}
                          </span>
                        </div>
                        <div className="text-sm text-green-600 space-y-1">
                          <div className="flex justify-between">
                            <span>• Shipping:</span>
                            <span>{result.landed_cost.currency} {result.landed_cost.shipping_cost?.toLocaleString() || '0'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>• Aranceles:</span>
                            <span>{result.landed_cost.currency} {result.landed_cost.duties?.toLocaleString() || '0'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>• Impuestos:</span>
                            <span>{result.landed_cost.currency} {result.landed_cost.taxes?.toLocaleString() || '0'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>• Fees:</span>
                            <span>{result.landed_cost.currency} {result.landed_cost.fees?.toLocaleString() || '0'}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {result.landed_cost.breakdown && (
                      <div>
                        <h4 className="font-semibold mb-2">📊 Desglose Detallado</h4>
                        <div className="text-sm space-y-1 max-h-40 overflow-y-auto">
                          {result.landed_cost.breakdown.map((item, index) => (
                            <div key={index} className="flex justify-between">
                              <span>• {item.name || item.description}:</span>
                              <span>{item.priceCurrency} {item.price?.toLocaleString() || '0'}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Botón para crear envío */}
                <div className="mt-6 flex justify-center">
                  <button
                    onClick={handleCreateShipmentFromLandedCost}
                    className="px-8 py-3 bg-gradient-to-r from-blue-500 to-green-500 text-white font-semibold rounded-lg hover:from-blue-600 hover:to-green-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-300 shadow-lg"
                  >
                    📦 Crear Envío con estos Datos
                  </button>
                </div>
                
                {result.warnings && result.warnings.length > 0 && (
                  <div className="mt-4 p-3 bg-yellow-100 border border-yellow-400 rounded">
                    <h4 className="font-semibold text-yellow-800 mb-2">⚠️ Advertencias</h4>
                    <ul className="text-sm text-yellow-700">
                      {result.warnings.map((warning, index) => (
                        <li key={index}>• {warning}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

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
    </div>
  );
};

// PropTypes para validación de props
LandedCostTab.propTypes = {
  handleCreateShipmentFromRate: PropTypes.func.isRequired,
  setActiveTab: PropTypes.func.isRequired,
  selectedAccount: PropTypes.string, // ✅ Agregar selectedAccount
};

export default LandedCostTab;
