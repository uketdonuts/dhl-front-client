import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import AccountDropdown from './AccountDropdown';
import RateResults from './RateResults';

const Dashboard = ({ selectedAccount, setSelectedAccount }) => {
  const { isAuthenticated, user } = useAuth();
  const [activeTab, setActiveTab] = useState('rate');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [comparisonResult, setComparisonResult] = useState(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [comparisonError, setComparisonError] = useState('');
  
  // Estados para crear envío
  const [shipmentLoading, setShipmentLoading] = useState(false);
  const [shipmentResult, setShipmentResult] = useState(null);
  const [shipmentError, setShipmentError] = useState('');
  
  // Estado para notificaciones
  const [notification, setNotification] = useState(null);
  
  // Estados para crear envío - Datos de prueba SOAP
  const [shipmentData, setShipmentData] = useState({
    shipper: {
      name: 'Test Shipper',
      company: 'Test Company',
      phone: '+507 123 4567',
      email: 'shipper@test.com',
      address: 'River House, 1 Eas Wall road',
      city: 'Panama',
      state: 'PA',
      postalCode: '0000',
      country: 'PA'
    },
    recipient: {
      name: 'Test Recipient',
      company: 'Recipient Company',
      phone: '+1 305 123 4567',
      email: 'recipient@test.com',
      address: '123 Main Street',
      city: 'BOG',
      state: 'BOG',
      postalCode: '110111',
      country: 'CO'
    },
    package: {
      weight: 45,
      length: 1,
      width: 1,
      height: 1,
      description: 'Test Package',
      value: 100,
      currency: 'USD'
    },
    service: 'P',
    payment: 'S',
  });

  // Estados para cotización de tarifas - Datos de prueba SOAP
  const [rateData, setRateData] = useState({
    origin: {
      postal_code: "0000",
      city: "Panama",
      country: "PA",  // Cambiar de country_code a country
      state: "PA"     // Cambiar de state_code a state
    },
    destination: {
      postal_code: "110111",
      city: "BOG", 
      country: "CO"   // Cambiar a CO para Colombia
    },
    weight: 45,
    dimensions: {
      length: 20,  // Dimensiones reales
      width: 15,
      height: 10
    },
    declared_weight: 45,
    service: 'P',
    account_number: '706014493', // Cuenta válida que funciona
  });

  // Configurar axios para incluir el token
  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  // Sincronizar rateData.account_number si cambia selectedAccount
  useEffect(() => {
    if (selectedAccount) {
      setRateData(prev => ({ ...prev, account_number: selectedAccount }));
    }
  }, [selectedAccount]);

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

  // Función para comparar tipos de contenido
  const compareContentTypes = async () => {
    setComparisonLoading(true);
    setComparisonError('');
    setComparisonResult(null);
    
    try {
      const requestData = {
        originAddress: {
          cityName: rateData.origin.city,
          countryCode: rateData.origin.country,
          postalCode: rateData.origin.postal_code
        },
        destinationAddress: {
          cityName: rateData.destination.city,
          countryCode: rateData.destination.country,
          postalCode: rateData.destination.postal_code
        },
        packages: [
          {
            weight: rateData.weight,
            dimensions: rateData.dimensions
          }
        ],
        plannedShippingDate: new Date().toISOString().split('T')[0]
      };
      
      const response = await axios.post('/api/dhl/rate/compare/', requestData, {
        headers: getAuthHeaders()
      });
      
      setComparisonResult(response.data);
    } catch (error) {
      console.error('Error comparando tipos de contenido:', error);
      setComparisonError(error.response?.data?.error || 'Error al comparar tipos de contenido');
    } finally {
      setComparisonLoading(false);
    }
  };

  // Función para crear envío
  const handleCreateShipment = async () => {
    setShipmentLoading(true);
    setShipmentError('');
    setShipmentResult(null);

    try {
      const response = await axios.post('/api/dhl/shipment/', shipmentData, {
        headers: getAuthHeaders()
      });
      
      setShipmentResult(response.data);
    } catch (err) {
      setShipmentError(err.response?.data?.message || 'Error al crear envío');
    } finally {
      setShipmentLoading(false);
    }
  };

  // Función para crear shipment desde cotización
  const handleCreateShipmentFromRate = (selectedRate, originalRateData) => {
    // Convertir datos de cotización a datos de shipment
    const newShipmentData = {
      shipper: {
        name: 'Remitente',
        company: 'Mi Empresa',
        phone: '+507 123 4567',
        email: 'remitente@empresa.com',
        address: 'Dirección del remitente',
        city: originalRateData.origin.city || 'Panama',
        state: originalRateData.origin.state || 'PA',
        postalCode: originalRateData.origin.postal_code || '0000',
        country: originalRateData.origin.country || 'PA'
      },
      recipient: {
        name: 'Destinatario',
        company: 'Empresa Destino',
        phone: '+1 305 123 4567',
        email: 'destinatario@empresa.com',
        address: 'Dirección del destinatario',
        city: originalRateData.destination.city || 'BOG',
        state: originalRateData.destination.state || 'BOG',
        postalCode: originalRateData.destination.postal_code || '110111',
        country: originalRateData.destination.country || 'CO'
      },
      package: {
        weight: originalRateData.weight || 45,
        length: originalRateData.dimensions?.length || 20,
        width: originalRateData.dimensions?.width || 15,
        height: originalRateData.dimensions?.height || 10,
        description: 'Paquete según cotización',
        value: 100,
        currency: 'USD'
      },
      service: selectedRate.service_code || originalRateData.service || 'P',
      payment: 'S'
    };

    // Actualizar datos de shipment
    setShipmentData(newShipmentData);
    
    // Cambiar a tab de shipment
    setActiveTab('shipment');
    
    // Mostrar notificación
    setNotification({
      type: 'success',
      message: `Datos de shipment pre-llenados con ${selectedRate.service_name}`,
      details: `Peso: ${originalRateData.weight} kg | Origen: ${originalRateData.origin.city}, ${originalRateData.origin.country} | Destino: ${originalRateData.destination.city}, ${originalRateData.destination.country}`
    });
    
    // Ocultar notificación después de 5 segundos
    setTimeout(() => setNotification(null), 5000);
  };

  // Función para actualizar datos del remitente
  const updateShipper = (field, value) => {
    setShipmentData(prev => ({
      ...prev,
      shipper: {
        ...prev.shipper,
        [field]: value
      }
    }));
  };

  // Función para actualizar datos del destinatario
  const updateRecipient = (field, value) => {
    setShipmentData(prev => ({
      ...prev,
      recipient: {
        ...prev.recipient,
        [field]: value
      }
    }));
  };

  // Función para actualizar datos del paquete
  const updatePackage = (field, value) => {
    setShipmentData(prev => ({
      ...prev,
      package: {
        ...prev.package,
        [field]: value
      }
    }));
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
      {/* Notificación */}
      {notification && (
        <div className={`mb-4 p-4 rounded-lg border ${
          notification.type === 'success' 
            ? 'bg-green-50 border-green-200 text-green-800'
            : 'bg-red-50 border-red-200 text-red-800'
        }`}>
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <p className="font-medium">{notification.message}</p>
              {notification.details && (
                <p className="mt-1 text-sm opacity-90">{notification.details}</p>
              )}
            </div>
            <button
              onClick={() => setNotification(null)}
              className="ml-3 flex-shrink-0 text-gray-400 hover:text-gray-600"
            >
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      )}
      
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

      {/* Dropdown de cuentas DHL */}
      <AccountDropdown selectedAccount={selectedAccount} setSelectedAccount={setSelectedAccount} />

      {/* Pestañas de navegación */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('rate')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'rate'
                ? 'border-dhl-red text-dhl-red'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Cotizar Tarifas
          </button>
          <button
            onClick={() => setActiveTab('compare')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'compare'
                ? 'border-dhl-red text-dhl-red'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Comparar Tipos
          </button>
          <button
            onClick={() => setActiveTab('shipment')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'shipment'
                ? 'border-dhl-red text-dhl-red'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Crear Envío
          </button>
        </nav>
      </div>

      {/* Contenido de la pestaña activa */}
      <div>
        {activeTab === 'rate' && (
          <div className="space-y-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Cotización de Tarifas DHL Express
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Origen */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Origen</h3>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Código Postal
                      </label>
                      <input
                        type="text"
                        value={rateData.origin.postal_code}
                        onChange={(e) => updateAddress('origin', 'postal_code', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Ciudad
                      </label>
                      <input
                        type="text"
                        value={rateData.origin.city}
                        onChange={(e) => updateAddress('origin', 'city', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        País
                      </label>
                      <input
                        type="text"
                        value={rateData.origin.country}
                        onChange={(e) => updateAddress('origin', 'country', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                      />
                    </div>
                  </div>
                </div>

                {/* Destino */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Destino</h3>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Código Postal
                      </label>
                      <input
                        type="text"
                        value={rateData.destination.postal_code}
                        onChange={(e) => updateAddress('destination', 'postal_code', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Ciudad
                      </label>
                      <input
                        type="text"
                        value={rateData.destination.city}
                        onChange={(e) => updateAddress('destination', 'city', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        País
                      </label>
                      <input
                        type="text"
                        value={rateData.destination.country}
                        onChange={(e) => updateAddress('destination', 'country', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Datos del paquete */}
              <div className="mt-6">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Datos del Paquete</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Peso (kg)
                    </label>
                    <input
                      type="number"
                      value={rateData.weight}
                      onChange={(e) => updateRateData('weight', parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo de Contenido
                    </label>
                    <select
                      value={rateData.service}
                      onChange={(e) => updateRateData('service', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                    >
                      <option value="P">Paquetes (NON_DOCUMENTS)</option>
                      <option value="D">Documentos (DOCUMENTS)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Número de Cuenta DHL
                    </label>
                    <input
                      type="text"
                      value={rateData.account_number}
                      onChange={(e) => updateRateData('account_number', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                      placeholder="Ej: 706014493"
                    />
                  </div>
                </div>

                {/* Dimensiones del paquete */}
                <div className="mt-4">
                  <h4 className="text-md font-medium text-gray-900 mb-3">Dimensiones (cm)</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Largo (cm)
                      </label>
                      <input
                        type="number"
                        value={rateData.dimensions.length}
                        onChange={(e) => updateDimensions('length', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                        placeholder="20"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Ancho (cm)
                      </label>
                      <input
                        type="number"
                        value={rateData.dimensions.width}
                        onChange={(e) => updateDimensions('width', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                        placeholder="15"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Alto (cm)
                      </label>
                      <input
                        type="number"
                        value={rateData.dimensions.height}
                        onChange={(e) => updateDimensions('height', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                        placeholder="10"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 space-y-2">
                <button
                  onClick={handleRateRequest}
                  disabled={loading}
                  className="w-full bg-dhl-red text-white py-2 px-4 rounded-md hover:bg-red-700 disabled:opacity-50"
                >
                  {loading ? 'Obteniendo tarifas...' : 'Obtener Tarifas'}
                </button>
              </div>
            </div>

            {/* Mostrar errores */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Error</h3>
                    <div className="mt-2 text-sm text-red-700">
                      <p>{error}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Mostrar resultados con el nuevo componente */}
            {result && result.success && (
              <RateResults 
                result={result}
                originalRateData={rateData}
                onCreateShipment={handleCreateShipmentFromRate}
                weightBreakdown={result.weight_breakdown}
                contentInfo={result.content_info}
              />
            )}
          </div>
        )}

        {activeTab === 'compare' && (
          <div className="space-y-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Comparación DOCUMENTS vs NON_DOCUMENTS
              </h2>
              
              <p className="text-gray-600 mb-6">
                Esta herramienta compara las tarifas y servicios disponibles entre envíos de documentos y paquetes regulares.
              </p>

              <div className="mb-6">
                <button
                  onClick={compareContentTypes}
                  disabled={comparisonLoading}
                  className="bg-blue-600 text-white py-2 px-6 rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {comparisonLoading ? 'Comparando...' : 'Comparar Tipos de Contenido'}
                </button>
              </div>

              {/* Mostrar errores de comparación */}
              {comparisonError && (
                <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-red-800">Error en Comparación</h3>
                      <div className="mt-2 text-sm text-red-700">
                        <p>{comparisonError}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Mostrar resultados de comparación */}
              {comparisonResult && (
                <div className="space-y-6">
                  {/* Recomendaciones */}
                  <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                    <h3 className="text-lg font-medium text-blue-800 mb-3">
                      Recomendaciones
                    </h3>
                    <ul className="space-y-2">
                      {comparisonResult.recommendations.map((rec, index) => (
                        <li key={index} className="text-blue-700 flex items-start">
                          <svg className="h-5 w-5 text-blue-500 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Diferencias importantes */}
                  <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                    <h3 className="text-lg font-medium text-yellow-800 mb-3">
                      Diferencias Importantes
                    </h3>
                    <ul className="space-y-2">
                      {comparisonResult.important_differences.map((diff, index) => (
                        <li key={index} className="text-yellow-700 flex items-start">
                          <svg className="h-5 w-5 text-yellow-500 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                          </svg>
                          {diff}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Comparación de tarifas */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* DOCUMENTS */}
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <h3 className="text-lg font-medium text-green-800 mb-3">
                        DOCUMENTS
                      </h3>
                      {comparisonResult.documents_response?.rates ? (
                        <div className="space-y-3">
                          {comparisonResult.documents_response.rates.map((rate, index) => (
                            <div key={index} className="bg-white p-3 rounded border">
                              <div className="font-medium text-gray-900">{rate.service_name}</div>
                              <div className="text-sm text-gray-600">
                                Precio: {rate.total_charge} {rate.currency}
                              </div>
                              <div className="text-sm text-gray-600">
                                Tiempo: {rate.delivery_time}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-600">No hay servicios disponibles para documentos</p>
                      )}
                    </div>

                    {/* NON_DOCUMENTS */}
                    <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                      <h3 className="text-lg font-medium text-orange-800 mb-3">
                        NON_DOCUMENTS (Paquetes)
                      </h3>
                      {comparisonResult.non_documents_response?.rates ? (
                        <div className="space-y-3">
                          {comparisonResult.non_documents_response.rates.map((rate, index) => (
                            <div key={index} className="bg-white p-3 rounded border">
                              <div className="font-medium text-gray-900">{rate.service_name}</div>
                              <div className="text-sm text-gray-600">
                                Precio: {rate.total_charge} {rate.currency}
                              </div>
                              <div className="text-sm text-gray-600">
                                Tiempo: {rate.delivery_time}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-600">No hay servicios disponibles para paquetes</p>
                      )}
                    </div>
                  </div>

                  {/* Análisis detallado */}
                  {comparisonResult.analysis && (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <h3 className="text-lg font-medium text-gray-800 mb-3">
                        Análisis Detallado
                      </h3>
                      <div className="space-y-2 text-sm text-gray-700">
                        <p><strong>Total de servicios para documentos:</strong> {comparisonResult.analysis.documents_services_count}</p>
                        <p><strong>Total de servicios para paquetes:</strong> {comparisonResult.analysis.non_documents_services_count}</p>
                        <p><strong>Servicios comunes:</strong> {comparisonResult.analysis.common_services}</p>
                        <p><strong>Servicios solo para documentos:</strong> {comparisonResult.analysis.documents_only_services}</p>
                        <p><strong>Servicios solo para paquetes:</strong> {comparisonResult.analysis.non_documents_only_services}</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'shipment' && (
          <div className="space-y-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Crear Nuevo Envío DHL Express
              </h2>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Datos del Remitente */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Datos del Remitente</h3>
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Nombre *
                        </label>
                        <input
                          type="text"
                          value={shipmentData.shipper.name}
                          onChange={(e) => updateShipper('name', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                          placeholder="Nombre del remitente"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Empresa
                        </label>
                        <input
                          type="text"
                          value={shipmentData.shipper.company}
                          onChange={(e) => updateShipper('company', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                          placeholder="Nombre de la empresa"
                        />
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Dirección *
                      </label>
                      <input
                        type="text"
                        value={shipmentData.shipper.address}
                        onChange={(e) => updateShipper('address', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                        placeholder="Dirección completa"
                      />
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Ciudad *
                        </label>
                        <input
                          type="text"
                          value={shipmentData.shipper.city}
                          onChange={(e) => updateShipper('city', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                          placeholder="Ciudad"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Estado/Provincia
                        </label>
                        <input
                          type="text"
                          value={shipmentData.shipper.state}
                          onChange={(e) => updateShipper('state', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                          placeholder="Estado"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Código Postal *
                        </label>
                        <input
                          type="text"
                          value={shipmentData.shipper.postalCode}
                          onChange={(e) => updateShipper('postalCode', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                          placeholder="00000"
                        />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          País *
                        </label>
                        <input
                          type="text"
                          value={shipmentData.shipper.country}
                          onChange={(e) => updateShipper('country', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                          placeholder="PA"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Teléfono *
                        </label>
                        <input
                          type="text"
                          value={shipmentData.shipper.phone}
                          onChange={(e) => updateShipper('phone', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                          placeholder="+507 123 4567"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Email
                        </label>
                        <input
                          type="email"
                          value={shipmentData.shipper.email}
                          onChange={(e) => updateShipper('email', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                          placeholder="remitente@email.com"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Datos del Destinatario */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Datos del Destinatario</h3>
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Nombre *
                        </label>
                        <input
                          type="text"
                          value={shipmentData.recipient.name}
                          onChange={(e) => updateRecipient('name', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                          placeholder="Nombre del destinatario"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Empresa
                        </label>
                        <input
                          type="text"
                          value={shipmentData.recipient.company}
                          onChange={(e) => updateRecipient('company', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                          placeholder="Nombre de la empresa"
                        />
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Dirección *
                      </label>
                      <input
                        type="text"
                        value={shipmentData.recipient.address}
                        onChange={(e) => updateRecipient('address', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                        placeholder="Dirección completa"
                      />
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Ciudad *
                        </label>
                        <input
                          type="text"
                          value={shipmentData.recipient.city}
                          onChange={(e) => updateRecipient('city', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                          placeholder="Ciudad"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Estado/Provincia
                        </label>
                        <input
                          type="text"
                          value={shipmentData.recipient.state}
                          onChange={(e) => updateRecipient('state', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                          placeholder="Estado"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Código Postal *
                        </label>
                        <input
                          type="text"
                          value={shipmentData.recipient.postalCode}
                          onChange={(e) => updateRecipient('postalCode', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                          placeholder="110111"
                        />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          País *
                        </label>
                        <input
                          type="text"
                          value={shipmentData.recipient.country}
                          onChange={(e) => updateRecipient('country', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                          placeholder="CO"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Teléfono *
                        </label>
                        <input
                          type="text"
                          value={shipmentData.recipient.phone}
                          onChange={(e) => updateRecipient('phone', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                          placeholder="+1 305 123 4567"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Email
                        </label>
                        <input
                          type="email"
                          value={shipmentData.recipient.email}
                          onChange={(e) => updateRecipient('email', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                          placeholder="destinatario@email.com"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Datos del Paquete */}
              <div className="mt-8">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Información del Paquete</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Peso (kg) *
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={shipmentData.package.weight}
                      onChange={(e) => updatePackage('weight', parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                      placeholder="45"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Largo (cm) *
                    </label>
                    <input
                      type="number"
                      value={shipmentData.package.length}
                      onChange={(e) => updatePackage('length', parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                      placeholder="20"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Ancho (cm) *
                    </label>
                    <input
                      type="number"
                      value={shipmentData.package.width}
                      onChange={(e) => updatePackage('width', parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                      placeholder="15"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Alto (cm) *
                    </label>
                    <input
                      type="number"
                      value={shipmentData.package.height}
                      onChange={(e) => updatePackage('height', parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                      placeholder="10"
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Descripción *
                    </label>
                    <input
                      type="text"
                      value={shipmentData.package.description}
                      onChange={(e) => updatePackage('description', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                      placeholder="Descripción del contenido"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Valor Declarado *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={shipmentData.package.value}
                      onChange={(e) => updatePackage('value', parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                      placeholder="100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Moneda
                    </label>
                    <select
                      value={shipmentData.package.currency}
                      onChange={(e) => updatePackage('currency', e.target.value)}
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
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo de Servicio
                    </label>
                    <select
                      value={shipmentData.service}
                      onChange={(e) => setShipmentData(prev => ({ ...prev, service: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                    >
                      <option value="P">Paquetes (NON_DOCUMENTS)</option>
                      <option value="D">Documentos (DOCUMENTS)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo de Pago
                    </label>
                    <select
                      value={shipmentData.payment}
                      onChange={(e) => setShipmentData(prev => ({ ...prev, payment: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                    >
                      <option value="S">Remitente (Shipper)</option>
                      <option value="R">Destinatario (Recipient)</option>
                      <option value="T">Tercero (Third Party)</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Botones de acción */}
              <div className="mt-8 space-y-2">
                <button
                  onClick={handleCreateShipment}
                  disabled={shipmentLoading}
                  className="w-full bg-dhl-red text-white py-3 px-4 rounded-md hover:bg-red-700 disabled:opacity-50 font-medium"
                >
                  {shipmentLoading ? 'Creando envío...' : 'Crear Envío DHL'}
                </button>
              </div>
            </div>

            {/* Mostrar errores de envío */}
            {shipmentError && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Error al crear envío</h3>
                    <div className="mt-2 text-sm text-red-700">
                      <p>{shipmentError}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Mostrar resultados de envío */}
            {shipmentResult && shipmentResult.success && (
              <div className="bg-green-50 border border-green-200 rounded-md p-6">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-lg font-medium text-green-800 mb-3">
                      ¡Envío creado exitosamente!
                    </h3>
                    <div className="space-y-2">
                      {shipmentResult.shipment_data?.tracking_number && (
                        <div className="bg-white p-3 rounded border">
                          <div className="font-medium text-gray-900">Número de Seguimiento</div>
                          <div className="text-lg font-mono text-green-700">
                            {shipmentResult.shipment_data.tracking_number}
                          </div>
                        </div>
                      )}
                      {shipmentResult.shipment_data?.shipment_id && (
                        <div className="bg-white p-3 rounded border">
                          <div className="font-medium text-gray-900">ID de Envío</div>
                          <div className="text-gray-700">
                            {shipmentResult.shipment_data.shipment_id}
                          </div>
                        </div>
                      )}
                      {shipmentResult.shipment_data?.total_cost && (
                        <div className="bg-white p-3 rounded border">
                          <div className="font-medium text-gray-900">Costo Total</div>
                          <div className="text-gray-700">
                            {shipmentResult.shipment_data.total_cost} {shipmentResult.shipment_data.currency}
                          </div>
                        </div>
                      )}
                      {shipmentResult.shipment_data?.estimated_delivery && (
                        <div className="bg-white p-3 rounded border">
                          <div className="font-medium text-gray-900">Entrega Estimada</div>
                          <div className="text-gray-700">
                            {shipmentResult.shipment_data.estimated_delivery}
                          </div>
                        </div>
                      )}
                      {shipmentResult.shipment_data?.label_url && (
                        <div className="bg-white p-3 rounded border">
                          <div className="font-medium text-gray-900">Etiqueta de Envío</div>
                          <a
                            href={shipmentResult.shipment_data.label_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-dhl-red hover:text-red-700"
                          >
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Descargar Etiqueta PDF
                          </a>
                        </div>
                      )}
                    </div>
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
