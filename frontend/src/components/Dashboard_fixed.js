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
    service: 'P',
    payment: 'S',
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
    },
    declared_weight: null,
    service: 'P',
    account_number: selectedAccount || '',
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
                        value={rateData.origin.country_code}
                        onChange={(e) => updateAddress('origin', 'country_code', e.target.value)}
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
                        value={rateData.destination.country_code}
                        onChange={(e) => updateAddress('destination', 'country_code', e.target.value)}
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
              </div>

              <button
                onClick={handleRateRequest}
                disabled={loading}
                className="mt-6 w-full bg-dhl-red text-white py-2 px-4 rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                {loading ? 'Obteniendo tarifas...' : 'Obtener Tarifas'}
              </button>
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

            {/* Mostrar resultados */}
            {result && result.success && (
              <div className="bg-green-50 border border-green-200 rounded-md p-4">
                <h3 className="text-lg font-medium text-green-800 mb-2">
                  Tarifas Obtenidas
                </h3>
                {result.rates && result.rates.length > 0 ? (
                  <div className="space-y-2">
                    {result.rates.map((rate, index) => (
                      <div key={index} className="bg-white p-3 rounded border">
                        <div className="font-medium">{rate.service_name}</div>
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
                  <p className="text-green-700">Cotización procesada exitosamente</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
