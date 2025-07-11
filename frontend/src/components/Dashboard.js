import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import AccountDropdown from './AccountDropdown';

const Dashboard = ({ selectedAccount, setSelectedAccount }) => {
  const { isAuthenticated, user } = useAuth();
  const [activeTab, setActiveTab] = useState('rate');
  const [shipmentId, setShipmentId] = useState('2287013540');
  const [trackingNumber, setTrackingNumber] = useState('5339266472');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [pdfUrl, setPdfUrl] = useState(null);
  
  // Estados para crear envío
  const [shipmentData, setShipmentData] = useState({
    shipper: {
      name: 'Juan Perez',
      company: 'Mi Empresa SA',
      phone: '+1 234 567 8900',
      email: 'juan@empresa.com',
      address: 'Av. Principal 123, Edificio ABC',
      city: 'Madrid',
      state: 'Madrid',
      postalCode: '28001',
      country: 'US'
    },
    recipient: {
      name: 'Maria Garcia',
      company: 'Empresa Destino SL',
      phone: '+1 987 654 3210',
      email: 'maria@empresa.com',
      address: 'Calle Secundaria 456, Oficina 10',
      city: 'New York',
      state: 'NY',
      postalCode: '10001',
      country: 'US'
    },
    package: {
      weight: 2.5,
      length: 25,
      width: 20,
      height: 15,
      description: 'Electronics and Documents',
      value: 250,
      currency: 'USD'
    },
    service: 'P', // P = DHL Express Worldwide
    payment: 'S' // S = Shipper pays
  });

  // Estados para cotización de tarifas
  const [rateData, setRateData] = useState({
    origin: {
      postal_code: "85281",
      city: "Tempe",
      country_code: "US",
      state_code: "AZ"
    },
    destination: {
      postal_code: "10082",
      city: "Berlin", 
      country_code: "DE"
    },
    weight: 25,
    dimensions: {
      length: 1,
      width: 1,
      height: 1
    }
  });

  // Configurar axios para incluir el token en todas las requests
  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const handleGetePOD = async () => {
    setLoading(true);
    setError('');
    setResult(null);
    setPdfUrl(null);

    try {
      const response = await axios.post('/api/dhl/epod/', {
        shipment_id: shipmentId
      }, { headers: getAuthHeaders() });

      if (response.data.success) {
        setResult(response.data);
        // Si hay PDF data, crear un blob para previsualización
        if (response.data.pdf_data) {
          const byteCharacters = atob(response.data.pdf_data);
          const byteNumbers = new Array(byteCharacters.length);
          for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
          }
          const byteArray = new Uint8Array(byteNumbers);
          const blob = new Blob([byteArray], { type: 'application/pdf' });
          const url = window.URL.createObjectURL(blob);
          setPdfUrl(url);
        }
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Error al obtener ePOD');
    } finally {
      setLoading(false);
    }
  };

  const downloadPDF = () => {
    if (pdfUrl) {
      const link = document.createElement('a');
      link.href = pdfUrl;
      link.download = `ePOD_${shipmentId}.pdf`;
      link.click();
    }
  };

  // Limpiar URL del PDF cuando se cambie de pestaña
  const handleTabChange = (tabId) => {
    if (pdfUrl && tabId !== 'getePOD') {
      window.URL.revokeObjectURL(pdfUrl);
      setPdfUrl(null);
    }
    setActiveTab(tabId);
  };

  // Limpiar URL del PDF cuando el componente se desmonte
  useEffect(() => {
    return () => {
      if (pdfUrl) {
        window.URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [pdfUrl]);

  const handleRateRequest = async () => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await axios.post('/api/dhl/rate/', rateData, {
        headers: getAuthHeaders()
      });
      
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Error al obtener tarifas');
    } finally {
      setLoading(false);
    }
  };

  // Función para actualizar datos de cotización
  const updateRateData = (field, value) => {
    setRateData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Función para actualizar datos de origen/destino
  const updateAddress = (type, field, value) => {
    setRateData(prev => ({
      ...prev,
      [type]: {
        ...prev[type],
        [field]: value
      }
    }));
  };

  // Función para actualizar dimensiones
  const updateDimensions = (field, value) => {
    setRateData(prev => ({
      ...prev,
      dimensions: {
        ...prev.dimensions,
        [field]: parseFloat(value) || 0
      }
    }));
  };

  const handleTrackingRequest = async () => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await axios.post('/api/dhl/tracking/', {
        tracking_number: trackingNumber
      }, { headers: getAuthHeaders() });
      
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Error al obtener seguimiento');
    } finally {
      setLoading(false);
    }
  };

  const handleShipmentRequest = async () => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      // Incluir la cuenta seleccionada en los datos del envío
      const shipmentDataWithAccount = {
        ...shipmentData,
        account_number: selectedAccount
      };

      const response = await axios.post('/api/dhl/shipment/', shipmentDataWithAccount, {
        headers: getAuthHeaders()
      });
      
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Error al crear envío');
    } finally {
      setLoading(false);
    }
  };

  // Función para actualizar datos del envío
  const updateShipmentData = (section, field, value) => {
    setShipmentData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  // Función para generar datos aleatorios
  const generateSampleData = async () => {
    try {
      const response = await axios.get('/api/test-data/', {
        headers: getAuthHeaders()
      });
      
      if (response.data.success) {
        setShipmentData(response.data.data);
        setError('');
      } else {
        setError('Error al generar datos de prueba');
      }
    } catch (err) {
      setError('Error al conectar con el servidor para generar datos');
    }
  };



  const renderTabContent = () => {
    switch (activeTab) {
      case 'getePOD':
        return (
          <div className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-md">
              <h3 className="font-medium text-blue-900 mb-2">Comprobante de Entrega Electrónico (ePOD)</h3>
              <p className="text-blue-700 text-sm">
                Obtén el comprobante de entrega electrónico de DHL con la información de la entrega.
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ID de Envío
              </label>
              <input
                type="text"
                value={shipmentId}
                onChange={(e) => setShipmentId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                placeholder="Ingrese el ID del envío"
              />
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={handleGetePOD}
                disabled={loading}
                className="btn-primary"
              >
                {loading ? 'Obteniendo ePOD...' : 'Obtener ePOD'}
              </button>
              
              {pdfUrl && (
                <button
                  onClick={downloadPDF}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors duration-200 flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Descargar PDF
                </button>
              )}
            </div>

            {/* Previsualización del PDF */}
            {pdfUrl && (
              <div className="mt-6">
                <h4 className="text-lg font-medium text-gray-900 mb-3">Previsualización del ePOD</h4>
                <div className="border border-gray-300 rounded-lg overflow-hidden bg-gray-50">
                  <iframe
                    src={pdfUrl}
                    className="w-full h-96"
                    title="Previsualización ePOD"
                    style={{ minHeight: '600px' }}
                  />
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  💡 Utiliza el botón "Descargar PDF" para guardar el archivo en tu dispositivo
                </p>
              </div>
            )}
          </div>
        );

      case 'rate':
        return (
          <div className="space-y-6">
            <div className="bg-blue-50 p-4 rounded-md">
              <h3 className="font-medium text-blue-900 mb-2">Cotización de Tarifas</h3>
              <p className="text-blue-700 text-sm">
                Ingresa los datos del envío para obtener una cotización de DHL Express.
              </p>
            </div>

            {/* Origen */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900 border-b pb-2">Origen</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Código Postal
                    </label>
                    <input
                      type="text"
                      value={rateData.origin.postal_code}
                      onChange={(e) => updateAddress('origin', 'postal_code', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                      placeholder="85281"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      País
                    </label>
                    <input
                      type="text"
                      value={rateData.origin.country_code}
                      onChange={(e) => updateAddress('origin', 'country_code', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                      placeholder="US"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ciudad
                  </label>
                  <input
                    type="text"
                    value={rateData.origin.city}
                    onChange={(e) => updateAddress('origin', 'city', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="Tempe"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Estado/Provincia (opcional)
                  </label>
                  <input
                    type="text"
                    value={rateData.origin.state_code || ''}
                    onChange={(e) => updateAddress('origin', 'state_code', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="AZ"
                  />
                </div>
              </div>

              {/* Destino */}
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900 border-b pb-2">Destino</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Código Postal
                    </label>
                    <input
                      type="text"
                      value={rateData.destination.postal_code}
                      onChange={(e) => updateAddress('destination', 'postal_code', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                      placeholder="10082"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      País
                    </label>
                    <input
                      type="text"
                      value={rateData.destination.country_code}
                      onChange={(e) => updateAddress('destination', 'country_code', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                      placeholder="DE"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ciudad
                  </label>
                  <input
                    type="text"
                    value={rateData.destination.city}
                    onChange={(e) => updateAddress('destination', 'city', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="Berlin"
                  />
                </div>
              </div>
            </div>

            {/* Peso y Dimensiones */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900 border-b pb-2">Peso</h4>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Peso (kg)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={rateData.weight}
                    onChange={(e) => updateRateData('weight', parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="25"
                  />
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-medium text-gray-900 border-b pb-2">Dimensiones (cm)</h4>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Largo
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={rateData.dimensions.length}
                      onChange={(e) => updateDimensions('length', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                      placeholder="1"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Ancho
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={rateData.dimensions.width}
                      onChange={(e) => updateDimensions('width', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                      placeholder="1"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Alto
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={rateData.dimensions.height}
                      onChange={(e) => updateDimensions('height', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                      placeholder="1"
                    />
                  </div>
                </div>
              </div>
            </div>

            <button
              onClick={handleRateRequest}
              disabled={loading}
              className="btn-primary w-full"
            >
              {loading ? 'Obteniendo tarifas...' : 'Cotizar Tarifas'}
            </button>

            {/* Resultados de Cotización */}
            {result && result.success && result.rates && (
              <div className="mt-8">
                <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="mr-2">💰</span>
                  Resultados de Cotización
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {result.rates.map((rate, idx) => (
                    <div key={idx} className="bg-white rounded-lg shadow-md border p-5 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center mb-2">
                          <span className="text-2xl mr-2">🚚</span>
                          <span className="font-bold text-dhl-red text-lg">{rate.service_name}</span>
                          <span className="ml-2 text-xs bg-dhl-red text-white rounded px-2 py-0.5">{rate.service_code}</span>
                        </div>
                        <div className="text-3xl font-bold text-green-600 mb-2">
                          {rate.total_charge} {rate.currency}
                        </div>
                        <div className="text-gray-700 mb-2">
                          <span className="font-medium">Entrega:</span> {rate.delivery_time}
                        </div>
                        <div className="text-gray-700 mb-2">
                          <span className="font-medium">Peso:</span> {rate.weight} kg
                        </div>
                        <div className="text-gray-700 mb-2">
                          <span className="font-medium">Dimensiones:</span> {rate.dimensions.length}×{rate.dimensions.width}×{rate.dimensions.height} cm
                        </div>
                      </div>
                      <button
                        className="mt-4 w-full bg-dhl-red text-white font-semibold py-2 rounded hover:bg-red-700 transition-colors"
                        onClick={() => alert(`Seleccionaste el servicio ${rate.service_name}`)}
                      >
                        Seleccionar
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );

      case 'tracking':
        return (
          <div className="space-y-6">
            <div className="bg-blue-50 p-4 rounded-md">
              <h3 className="font-medium text-blue-900 mb-2">Seguimiento de Envíos</h3>
              <p className="text-blue-700 text-sm">
                Ingresa el número de seguimiento para obtener información detallada del envío.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Número de Seguimiento
                </label>
                <input
                  type="text"
                  value={trackingNumber}
                  onChange={(e) => setTrackingNumber(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                  placeholder="Ingrese el número de seguimiento"
                />
              </div>
              <button
                onClick={handleTrackingRequest}
                disabled={loading}
                className="btn-primary w-full"
              >
                {loading ? 'Obteniendo seguimiento...' : 'Obtener Seguimiento'}
              </button>
            </div>

            {/* Resultados de Tracking */}
            {result && result.success && result.tracking_info && (
              <div className="mt-8">
                <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="mr-2">📍</span>
                  Información de Seguimiento
                </h4>
                
                {/* Información del envío */}
                <div className="bg-white rounded-lg shadow-md border p-6 mb-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-dhl-red">{result.tracking_info.awb_number}</div>
                      <div className="text-sm text-gray-500">Número de Tracking</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-lg font-semibold ${result.tracking_info.status === 'Delivered' ? 'text-green-600' : 'text-blue-600'}`}>
                        {result.tracking_info.status}
                      </div>
                      <div className="text-sm text-gray-500">Estado</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-semibold text-gray-700">{result.tracking_info.service}</div>
                      <div className="text-sm text-gray-500">Servicio</div>
                    </div>
                  </div>
                  
                  <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm font-medium text-gray-500">Origen</div>
                      <div className="text-gray-900">{result.tracking_info.origin}</div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-500">Destino</div>
                      <div className="text-gray-900">{result.tracking_info.destination}</div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-500">Entrega Estimada</div>
                      <div className="text-gray-900">{result.tracking_info.estimated_delivery}</div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-500">Peso</div>
                      <div className="text-gray-900">{result.tracking_info.weight}</div>
                    </div>
                  </div>
                </div>

                {/* Timeline de eventos */}
                <div className="bg-white rounded-lg shadow-md border p-6">
                  <h5 className="font-semibold text-gray-900 mb-4">Historial de Eventos</h5>
                  <div className="space-y-4">
                    {result.events && result.events.map((event, index) => (
                      <div key={index} className="flex items-start space-x-4">
                        <div className={`flex-shrink-0 w-3 h-3 rounded-full mt-2 ${
                          event.code === 'DL' ? 'bg-green-500' : 
                          event.code === 'OFD' ? 'bg-blue-500' : 
                          'bg-gray-400'
                        }`}></div>
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="text-sm font-medium text-gray-900">{event.description}</p>
                              <p className="text-sm text-gray-500">{event.location}</p>
                            </div>
                            <div className="text-xs text-gray-400">
                              {new Date(event.timestamp).toLocaleString('es-ES', {
                                day: '2-digit',
                                month: '2-digit',
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        );

      case 'shipment':
        return (
          <div className="space-y-6">
            <div className="bg-blue-50 p-4 rounded-md">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-medium text-blue-900 mb-2">Crear Nuevo Envío DHL Express</h3>
                  <p className="text-blue-700 text-sm">
                    Complete la información del remitente, destinatario y paquete para crear un envío.
                  </p>
                </div>
                <button
                  onClick={generateSampleData}
                  className="ml-4 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-colors duration-200 flex items-center text-sm"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Datos de Prueba
                </button>
              </div>
            </div>

            {/* Selector de Cuenta DHL */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H9m0 0H7m2 0v-3a1 1 0 011-1h1a1 1 0 011 1v3M9 7h6m0 0v2m0-2h2m-2 2v2m0-2H9m8-2V5" />
                    </svg>
                    <label className="text-sm font-medium text-gray-700">
                      Cuenta de envío DHL:
                    </label>
                  </div>
                  <AccountDropdown
                    value={selectedAccount}
                    onChange={setSelectedAccount}
                  />
                </div>
                <div className="text-xs text-gray-500">
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    Cuenta actual: {selectedAccount}
                  </span>
                </div>
              </div>
            </div>

            {/* Información del Remitente */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-4 flex items-center">
                <span className="mr-2">📤</span>
                Información del Remitente
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nombre Completo *</label>
                  <input
                    type="text"
                    value={shipmentData.shipper.name}
                    onChange={(e) => updateShipmentData('shipper', 'name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="Juan Pérez"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Empresa</label>
                  <input
                    type="text"
                    value={shipmentData.shipper.company}
                    onChange={(e) => updateShipmentData('shipper', 'company', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="Mi Empresa S.A."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono *</label>
                  <input
                    type="tel"
                    value={shipmentData.shipper.phone}
                    onChange={(e) => updateShipmentData('shipper', 'phone', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="+1 234 567 8900"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                  <input
                    type="email"
                    value={shipmentData.shipper.email}
                    onChange={(e) => updateShipmentData('shipper', 'email', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="juan@empresa.com"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Dirección *</label>
                  <input
                    type="text"
                    value={shipmentData.shipper.address}
                    onChange={(e) => updateShipmentData('shipper', 'address', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="Av. Principal 123, Edificio ABC"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ciudad *</label>
                  <input
                    type="text"
                    value={shipmentData.shipper.city}
                    onChange={(e) => updateShipmentData('shipper', 'city', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="Madrid"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Estado/Provincia</label>
                  <input
                    type="text"
                    value={shipmentData.shipper.state}
                    onChange={(e) => updateShipmentData('shipper', 'state', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="Madrid"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Código Postal *</label>
                  <input
                    type="text"
                    value={shipmentData.shipper.postalCode}
                    onChange={(e) => updateShipmentData('shipper', 'postalCode', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="28001"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">País *</label>
                  <select
                    value={shipmentData.shipper.country}
                    onChange={(e) => updateShipmentData('shipper', 'country', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                  >
                    <option value="US">Estados Unidos</option>
                    <option value="ES">España</option>
                    <option value="MX">México</option>
                    <option value="CO">Colombia</option>
                    <option value="AR">Argentina</option>
                    <option value="BR">Brasil</option>
                    <option value="DE">Alemania</option>
                    <option value="FR">Francia</option>
                    <option value="GB">Reino Unido</option>
                    <option value="CA">Canadá</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Información del Destinatario */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-4 flex items-center">
                <span className="mr-2">📥</span>
                Información del Destinatario
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nombre Completo *</label>
                  <input
                    type="text"
                    value={shipmentData.recipient.name}
                    onChange={(e) => updateShipmentData('recipient', 'name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="María García"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Empresa</label>
                  <input
                    type="text"
                    value={shipmentData.recipient.company}
                    onChange={(e) => updateShipmentData('recipient', 'company', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="Empresa Destino S.L."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono *</label>
                  <input
                    type="tel"
                    value={shipmentData.recipient.phone}
                    onChange={(e) => updateShipmentData('recipient', 'phone', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="+34 123 456 789"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                  <input
                    type="email"
                    value={shipmentData.recipient.email}
                    onChange={(e) => updateShipmentData('recipient', 'email', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="maria@empresa.com"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Dirección *</label>
                  <input
                    type="text"
                    value={shipmentData.recipient.address}
                    onChange={(e) => updateShipmentData('recipient', 'address', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="Calle Secundaria 456, Oficina 10"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ciudad *</label>
                  <input
                    type="text"
                    value={shipmentData.recipient.city}
                    onChange={(e) => updateShipmentData('recipient', 'city', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="Barcelona"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Estado/Provincia</label>
                  <input
                    type="text"
                    value={shipmentData.recipient.state}
                    onChange={(e) => updateShipmentData('recipient', 'state', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="Cataluña"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Código Postal *</label>
                  <input
                    type="text"
                    value={shipmentData.recipient.postalCode}
                    onChange={(e) => updateShipmentData('recipient', 'postalCode', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="08001"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">País *</label>
                  <select
                    value={shipmentData.recipient.country}
                    onChange={(e) => updateShipmentData('recipient', 'country', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                  >
                    <option value="US">Estados Unidos</option>
                    <option value="ES">España</option>
                    <option value="MX">México</option>
                    <option value="CO">Colombia</option>
                    <option value="AR">Argentina</option>
                    <option value="BR">Brasil</option>
                    <option value="DE">Alemania</option>
                    <option value="FR">Francia</option>
                    <option value="GB">Reino Unido</option>
                    <option value="CA">Canadá</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Información del Paquete */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-4 flex items-center">
                <span className="mr-2">📦</span>
                Información del Paquete
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Peso (kg) *</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    value={shipmentData.package.weight}
                    onChange={(e) => updateShipmentData('package', 'weight', parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Largo (cm) *</label>
                  <input
                    type="number"
                    min="1"
                    value={shipmentData.package.length}
                    onChange={(e) => updateShipmentData('package', 'length', parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ancho (cm) *</label>
                  <input
                    type="number"
                    min="1"
                    value={shipmentData.package.width}
                    onChange={(e) => updateShipmentData('package', 'width', parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Alto (cm) *</label>
                  <input
                    type="number"
                    min="1"
                    value={shipmentData.package.height}
                    onChange={(e) => updateShipmentData('package', 'height', parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Descripción del Contenido *</label>
                  <input
                    type="text"
                    value={shipmentData.package.description}
                    onChange={(e) => updateShipmentData('package', 'description', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                    placeholder="Ropa, electrónicos, documentos, etc."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Valor Declarado *</label>
                  <input
                    type="number"
                    min="1"
                    value={shipmentData.package.value}
                    onChange={(e) => updateShipmentData('package', 'value', parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Moneda</label>
                  <select
                    value={shipmentData.package.currency}
                    onChange={(e) => updateShipmentData('package', 'currency', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                  >
                    <option value="USD">USD - Dólar Americano</option>
                    <option value="EUR">EUR - Euro</option>
                    <option value="MXN">MXN - Peso Mexicano</option>
                    <option value="COP">COP - Peso Colombiano</option>
                    <option value="ARS">ARS - Peso Argentino</option>
                    <option value="BRL">BRL - Real Brasileño</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Opciones de Servicio */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-4 flex items-center">
                <span className="mr-2">⚙️</span>
                Opciones de Servicio
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Servicio</label>
                  <select
                    value={shipmentData.service}
                    onChange={(e) => updateShipmentData('service', '', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                  >
                    <option value="P">DHL Express Worldwide</option>
                    <option value="K">DHL Express 9:00</option>
                    <option value="U">DHL Express 12:00</option>
                    <option value="Y">DHL Express Economy Select</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Forma de Pago</label>
                  <select
                    value={shipmentData.payment}
                    onChange={(e) => setShipmentData(prev => ({...prev, payment: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-transparent"
                  >
                    <option value="S">Remitente Paga</option>
                    <option value="R">Destinatario Paga</option>
                    <option value="T">Tercero Paga</option>
                  </select>
                </div>
              </div>
            </div>

            <button
              onClick={handleShipmentRequest}
              disabled={loading || !shipmentData.shipper.name || !shipmentData.recipient.name}
              className="btn-primary w-full py-3 text-lg"
            >
              {loading ? 'Creando envío...' : 'Crear Envío DHL Express'}
            </button>
          </div>
        );



      default:
        return null;
    }
  };

  // Si no está autenticado, mostrar mensaje
  if (!isAuthenticated) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                No autenticado
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>Debes iniciar sesión para acceder a los servicios de DHL.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Panel de Control DHL
        </h1>
        <p className="text-gray-600">
          Gestiona tus envíos y servicios de DHL Express
        </p>
        {user && (
          <p className="text-sm text-gray-500 mt-1">
            Conectado como: <span className="font-medium">{user.username}</span>
          </p>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'rate', name: 'Cotizar Tarifas', icon: '💰' },
            { id: 'getePOD', name: 'Obtener ePOD', icon: '📄' },
            { id: 'tracking', name: 'Seguimiento', icon: '📍' },
            { id: 'shipment', name: 'Crear Envío', icon: '📦' },
      
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-dhl-red text-dhl-red'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="bg-white rounded-lg shadow dhl-card p-6">
        {renderTabContent()}

        {/* Error Display */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Error
                </h3>
                <div className="mt-2 text-sm text-red-700">
                  {error}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Result Display */}
        {result && !(result.pdf_data && activeTab === 'getePOD') && (
          <div className="mt-6">
            {activeTab === 'shipment' && result.success && result.tracking_number && (
              // Vista especial para envíos creados exitosamente
              <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg shadow-lg overflow-hidden">
                {/* Header con tracking number */}
                <div className="bg-gradient-to-r from-green-600 to-blue-600 px-6 py-4 text-white">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <svg className="w-8 h-8 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                      </svg>
                      <div>
                        <h3 className="text-xl font-bold">¡Envío Creado Exitosamente!</h3>
                        <p className="text-green-100 text-sm">Número de Tracking Generado</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold tracking-wider">{result.tracking_number}</div>
                      <div className="text-green-100 text-xs">Copia este número</div>
                    </div>
                  </div>
                </div>

                {/* Información del envío */}
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {/* Información de entrega */}
                    <div className="bg-white rounded-lg p-4 shadow-sm border">
                      <div className="flex items-center mb-3">
                        <svg className="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <h4 className="font-semibold text-gray-900">Tiempo de Entrega</h4>
                      </div>
                      <p className="text-2xl font-bold text-green-600">{result.estimated_delivery}</p>
                      <p className="text-sm text-gray-500 mt-1">Estimado por DHL Express</p>
                    </div>

                    {/* Costo */}
                    <div className="bg-white rounded-lg p-4 shadow-sm border">
                      <div className="flex items-center mb-3">
                        <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                        </svg>
                        <h4 className="font-semibold text-gray-900">Costo del Envío</h4>
                      </div>
                      <p className="text-lg font-semibold text-gray-700">{result.cost}</p>
                      <p className="text-sm text-gray-500 mt-1">Basado en tarifas actuales</p>
                    </div>

                    {/* Estado */}
                    <div className="bg-white rounded-lg p-4 shadow-sm border">
                      <div className="flex items-center mb-3">
                        <svg className="w-5 h-5 text-purple-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <h4 className="font-semibold text-gray-900">Estado</h4>
                      </div>
                      <div className="flex items-center">
                        <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                        <span className="text-green-700 font-medium">Enviado</span>
                      </div>
                      <p className="text-sm text-gray-500 mt-1">Listo para recolección</p>
                    </div>
                  </div>

                  {/* Detalles del envío */}
                  <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Remitente */}
                    <div className="bg-white rounded-lg p-4 shadow-sm border">
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <svg className="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        Remitente
                      </h4>
                      <div className="space-y-1 text-sm">
                        <p className="font-medium">{result.shipment_data?.shipper?.name}</p>
                        <p className="text-gray-600">{result.shipment_data?.shipper?.company}</p>
                        <p className="text-gray-600">{result.shipment_data?.shipper?.address}</p>
                        <p className="text-gray-600">{result.shipment_data?.shipper?.city}, {result.shipment_data?.shipper?.state} {result.shipment_data?.shipper?.postalCode}</p>
                        <p className="text-gray-600">{result.shipment_data?.shipper?.phone}</p>
                      </div>
                    </div>

                    {/* Destinatario */}
                    <div className="bg-white rounded-lg p-4 shadow-sm border">
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        Destinatario
                      </h4>
                      <div className="space-y-1 text-sm">
                        <p className="font-medium">{result.shipment_data?.recipient?.name}</p>
                        <p className="text-gray-600">{result.shipment_data?.recipient?.company}</p>
                        <p className="text-gray-600">{result.shipment_data?.recipient?.address}</p>
                        <p className="text-gray-600">{result.shipment_data?.recipient?.city}, {result.shipment_data?.recipient?.state} {result.shipment_data?.recipient?.postalCode}</p>
                        <p className="text-gray-600">{result.shipment_data?.recipient?.phone}</p>
                      </div>
                    </div>
                  </div>

                  {/* Información del paquete */}
                  <div className="mt-6 bg-white rounded-lg p-4 shadow-sm border">
                    <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                      <svg className="w-5 h-5 text-purple-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                      </svg>
                      Detalles del Paquete
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500">Peso</p>
                        <p className="font-medium">{result.shipment_data?.package?.weight} kg</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Dimensiones</p>
                        <p className="font-medium">{result.shipment_data?.package?.length}×{result.shipment_data?.package?.width}×{result.shipment_data?.package?.height} cm</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Valor Declarado</p>
                        <p className="font-medium">{result.shipment_data?.package?.value} {result.shipment_data?.package?.currency}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Contenido</p>
                        <p className="font-medium">{result.shipment_data?.package?.description}</p>
                      </div>
                    </div>
                  </div>

                  {/* Acciones */}
                  <div className="mt-6 flex flex-wrap gap-3">
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(result.tracking_number);
                        alert('Número de tracking copiado al portapapeles');
                      }}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-200 flex items-center"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      Copiar Tracking
                    </button>
                    <button
                      onClick={() => {
                        setTrackingNumber(result.tracking_number);
                        setActiveTab('tracking');
                      }}
                      className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors duration-200 flex items-center"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      </svg>
                      Hacer Seguimiento
                    </button>
                    <button
                      onClick={() => {
                        setShipmentId(result.tracking_number);
                        setActiveTab('getePOD');
                      }}
                      className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-colors duration-200 flex items-center"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Obtener ePOD
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard; 