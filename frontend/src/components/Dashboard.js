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
  
  // Estados para crear envío
  const [shipmentLoading, setShipmentLoading] = useState(false);
  const [shipmentResult, setShipmentResult] = useState(null);
  const [shipmentError, setShipmentError] = useState('');
  
  // Estados para tracking
  const [trackingNumber, setTrackingNumber] = useState('');
  const [trackingResult, setTrackingResult] = useState(null);
  const [trackingLoading, setTrackingLoading] = useState(false);
  const [trackingError, setTrackingError] = useState('');
  
  // Estados para ePOD (Proof of Delivery)
  const [epodTrackingNumber, setEpodTrackingNumber] = useState('');
  const [epodResult, setEpodResult] = useState(null);
  const [epodLoading, setEpodLoading] = useState(false);
  const [epodError, setEpodError] = useState('');
  
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
    account_number: '706091269', // Cuenta DHL sincronizada con dropdown (actualizada)
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
    account_number: '706091269', // Cuenta válida que funciona (actualizada)
  });

  // Configurar axios para incluir el token
  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  // Sincronizar account_number si cambia selectedAccount para todas las operaciones
  useEffect(() => {
    if (selectedAccount) {
      setRateData(prev => ({ ...prev, account_number: selectedAccount }));
      setShipmentData(prev => ({ ...prev, account_number: selectedAccount }));
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

  // Función para descargar documentos PDF desde base64
  const downloadDocument = (base64Content, filename) => {
    try {
      // Eliminar prefijo data:application/pdf;base64, si existe
      const cleanBase64 = base64Content.replace(/^data:application\/pdf;base64,/, '');
      
      // Convertir base64 a blob
      const byteCharacters = atob(cleanBase64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'application/pdf' });

      // Crear URL temporal y descargar
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error al descargar documento:', error);
      alert('Error al descargar el documento. Por favor, inténtalo de nuevo.');
    }
  };

  // Función para hacer tracking de envío
  const handleTracking = async () => {
    if (!trackingNumber.trim()) {
      setTrackingError('Por favor, ingresa un número de tracking válido');
      return;
    }

    setTrackingLoading(true);
    setTrackingError('');
    setTrackingResult(null);

    try {
      const requestData = { 
        tracking_number: trackingNumber.trim()
      };
      
      // Incluir account_number si está disponible
      if (selectedAccount) {
        requestData.account_number = selectedAccount;
      }

      const response = await axios.post('/api/dhl/tracking/', 
        requestData, 
        { headers: getAuthHeaders() }
      );
      
      setTrackingResult(response.data);
    } catch (err) {
      setTrackingError(err.response?.data?.message || 'Error al rastrear el envío');
    } finally {
      setTrackingLoading(false);
    }
  };

  // Función para obtener ePOD (Proof of Delivery)
  const handleEpod = async () => {
    if (!epodTrackingNumber.trim()) {
      setEpodError('Por favor, ingresa un número de tracking válido');
      return;
    }

    setEpodLoading(true);
    setEpodError('');
    setEpodResult(null);

    try {
      const requestData = { 
        shipment_id: epodTrackingNumber.trim()
      };
      
      // Incluir account_number si está disponible
      if (selectedAccount) {
        requestData.account_number = selectedAccount;
      }

      const response = await axios.post('/api/dhl/epod/', 
        requestData, 
        { headers: getAuthHeaders() }
      );
      
      setEpodResult(response.data);
    } catch (err) {
      // Crear un mensaje de error más informativo
      let errorMessage = err.response?.data?.message || 'Error al obtener el comprobante de entrega';
      
      // Si hay información adicional del error, agregarla
      if (err.response?.data?.error_data) {
        const errorData = err.response.data.error_data;
        
        // Extraer account_number de la URL si está disponible
        if (errorData.instance && typeof errorData.instance === 'string') {
          const accountMatch = errorData.instance.match(/shipperAccountNumber=(\d+)/);
          if (accountMatch) {
            const usedAccount = accountMatch[1];
            errorMessage += `\n\nCuenta utilizada: ${usedAccount}`;
            
            if (selectedAccount && selectedAccount !== usedAccount) {
              errorMessage += `\nCuenta seleccionada: ${selectedAccount}`;
            } else if (!selectedAccount) {
              errorMessage += `\n(Cuenta por defecto - no se seleccionó ninguna cuenta)`;
            }
          }
        }
        
        // Agregar detalles adicionales del error si están disponibles
        if (errorData.title) {
          errorMessage += `\n\nDetalle: ${errorData.title}`;
        }
        
        if (errorData.status) {
          errorMessage += `\nCódigo de estado: ${errorData.status}`;
        }
      }
      
      setEpodError(errorMessage);
    } finally {
      setEpodLoading(false);
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
      payment: 'S',
      account_number: selectedAccount || originalRateData.account_number || '706091269' // Usar cuenta seleccionada (actualizada)
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
            onClick={() => setActiveTab('tracking')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'tracking'
                ? 'border-dhl-red text-dhl-red'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Tracking
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
          <button
            onClick={() => setActiveTab('epod')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'epod'
                ? 'border-dhl-red text-dhl-red'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            ePOD
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

        {activeTab === 'tracking' && (
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
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                      placeholder="Ej: 1234567890"
                      onKeyPress={(e) => e.key === 'Enter' && handleTracking()}
                    />
                    <button
                      onClick={handleTracking}
                      disabled={trackingLoading || !trackingNumber.trim()}
                      className="bg-dhl-red text-white py-2 px-6 rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {trackingLoading ? 'Rastreando...' : 'Rastrear'}
                    </button>
                  </div>
                </div>
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
                  {/* Información principal del envío */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                    <div className="flex items-center mb-4">
                      <svg className="w-8 h-8 mr-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                      </svg>
                      <div>
                        <h3 className="text-xl font-semibold text-blue-900">
                          Tracking: {trackingResult.tracking_number || trackingNumber}
                        </h3>
                        <p className="text-blue-700">
                          Estado: <span className="font-medium">{trackingResult.status || 'En tránsito'}</span>
                        </p>
                      </div>
                    </div>
                    
                    {/* Información del envío */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      {trackingResult.shipment_info && (
                        <>
                          <div>
                            <span className="font-medium text-gray-700">Origen:</span>
                            <div className="text-gray-600">{trackingResult.shipment_info.origin}</div>
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">Destino:</span>
                            <div className="text-gray-600">{trackingResult.shipment_info.destination}</div>
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">Servicio:</span>
                            <div className="text-gray-600">{trackingResult.shipment_info.service_type}</div>
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">Fecha Estimada:</span>
                            <div className="text-gray-600">{trackingResult.shipment_info.estimated_delivery}</div>
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

                  {/* Detalles de piezas individuales */}
                  {trackingResult.piece_details && trackingResult.piece_details.length > 0 && (
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <h4 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                        <svg className="w-5 h-5 mr-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                        Detalles de Piezas ({trackingResult.piece_details.length})
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {trackingResult.piece_details.map((piece, index) => (
                          <div key={index} className="bg-gray-50 border border-gray-200 rounded p-3">
                            <h5 className="font-medium text-gray-800 mb-2">Pieza #{index + 1}</h5>
                            <div className="space-y-1 text-sm text-gray-600">
                              {piece.piece_id && <div><span className="font-medium">ID:</span> {piece.piece_id}</div>}
                              {piece.weight > 0 && <div><span className="font-medium">Peso:</span> {piece.weight} {piece.weight_unit}</div>}
                              {piece.dimensions && (piece.dimensions.length > 0 || piece.dimensions.width > 0 || piece.dimensions.height > 0) && (
                                <div><span className="font-medium">Dimensiones:</span> {piece.dimensions.length}x{piece.dimensions.width}x{piece.dimensions.height} {piece.dimensions.unit}</div>
                              )}
                              {piece.package_type && <div><span className="font-medium">Tipo:</span> {piece.package_type}</div>}
                              {piece.description && <div><span className="font-medium">Descripción:</span> {piece.description}</div>}
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

                      {/* URL de Tracking */}
                      {shipmentResult.shipment_data?.trackingUrl && (
                        <div className="bg-white p-4 rounded-lg border shadow-sm">
                          <div className="font-semibold text-gray-900 mb-2">Seguimiento en Línea</div>
                          <div className="flex space-x-2">
                            <button
                              onClick={() => {
                                setTrackingNumber(shipmentResult.tracking_number);
                                setActiveTab('tracking');
                              }}
                              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                            >
                              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                              </svg>
                              Ver Tracking Aquí
                            </button>
                          </div>
                        </div>
                      )}

                      {/* Información de Paquetes */}
                      {shipmentResult.shipment_data?.packages && shipmentResult.shipment_data.packages.length > 0 && (
                        <div className="bg-white p-4 rounded-lg border shadow-sm">
                          <div className="font-semibold text-gray-900 mb-3 flex items-center">
                            <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                            </svg>
                            Información de Paquetes ({shipmentResult.shipment_data.packages.length})
                          </div>
                          <div className="space-y-3">
                            {shipmentResult.shipment_data.packages.map((pkg, index) => (
                              <div key={index} className="bg-gray-50 p-3 rounded border">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                                  <div>
                                    <span className="font-medium text-gray-700">Paquete #{pkg.referenceNumber}:</span>
                                  </div>
                                  <div>
                                    <span className="font-medium text-gray-700">Tracking:</span>
                                    <div className="font-mono text-blue-700 bg-blue-50 px-2 py-1 rounded mt-1">
                                      {pkg.trackingNumber}
                                    </div>
                                  </div>

                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Documentos y Etiquetas */}
                      {shipmentResult.shipment_data?.documents && shipmentResult.shipment_data.documents.length > 0 && (
                        <div className="bg-white p-4 rounded-lg border shadow-sm">
                          <div className="font-semibold text-gray-900 mb-3 flex items-center">
                            <svg className="w-5 h-5 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Documentos Disponibles ({shipmentResult.shipment_data.documents.length})
                          </div>
                          <div className="space-y-2">
                            {shipmentResult.shipment_data.documents.map((doc, index) => (
                              <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded border">
                                <div className="flex items-center">
                                  <svg className="w-6 h-6 mr-3 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                  </svg>
                                  <div>
                                    <div className="font-medium text-gray-900">
                                      {doc.typeCode === 'label' ? 'Etiqueta de Envío' : `Documento ${doc.typeCode}`}
                                    </div>
                                    <div className="text-sm text-gray-600">
                                      Formato: {doc.imageFormat || 'PDF'}
                                    </div>
                                  </div>
                                </div>
                                <button
                                  onClick={() => downloadDocument(doc.content, `${doc.typeCode === 'label' ? 'etiqueta' : 'documento'}_${shipmentResult.tracking_number}.pdf`)}
                                  className="inline-flex items-center px-3 py-2 bg-dhl-red text-white text-sm rounded-md hover:bg-red-700 transition-colors"
                                >
                                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                  </svg>
                                  Descargar PDF
                                </button>
                              </div>
                            ))}
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
                          {shipmentResult.requested_by && (
                            <div>
                              <span className="font-medium text-gray-700">Creado por:</span>
                              <div className="text-gray-600">{shipmentResult.requested_by}</div>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Botón para crear otro envío */}
                      <div className="bg-white p-4 rounded-lg border shadow-sm">
                        <button
                          onClick={() => {
                            setShipmentResult(null);
                            setShipmentError('');
                          }}
                          className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                        >
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                          </svg>
                          Crear Otro Envío
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'epod' && (
          <div className="space-y-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                ePOD - Comprobante Electrónico de Entrega
              </h2>
              
              <p className="text-gray-600 mb-6">
                Descarga el comprobante electrónico de entrega (ePOD) en formato PDF para envíos ya entregados.
              </p>

              {/* Formulario de ePOD */}
              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Número de Tracking (Envío Entregado)
                  </label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={epodTrackingNumber}
                      onChange={(e) => setEpodTrackingNumber(e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                      placeholder="Ej: 1234567890"
                      onKeyPress={(e) => e.key === 'Enter' && handleEpod()}
                    />
                    <button
                      onClick={handleEpod}
                      disabled={epodLoading || !epodTrackingNumber.trim()}
                      className="bg-dhl-red text-white py-2 px-6 rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {epodLoading ? 'Obteniendo...' : 'Obtener ePOD'}
                    </button>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    ⚠️ El ePOD solo está disponible para envíos que ya han sido entregados.
                  </p>
                  
                  {/* Información de cuenta utilizada */}
                  <div className="mt-2 p-3 bg-blue-50 rounded border border-blue-200">
                    <div className="flex items-center text-sm">
                      <svg className="w-4 h-4 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-blue-700">
                        <strong>Cuenta DHL a utilizar:</strong>
                        <span className="font-mono ml-2">
                          {selectedAccount || '706014493 (cuenta por defecto)'}
                        </span>
                      </span>
                    </div>
                    {!selectedAccount && (
                      <div className="text-xs text-blue-600 mt-1 ml-6">
                        💡 Selecciona una cuenta específica en el dropdown superior si necesitas usar una cuenta diferente.
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Mostrar errores de ePOD */}
              {epodError && (
                <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3 flex-1">
                      <h3 className="text-sm font-medium text-red-800">Error obteniendo ePOD</h3>
                      <div className="mt-2 text-sm text-red-700">
                        <div className="whitespace-pre-line">{epodError}</div>
                        
                        {/* Mostrar información de la cuenta seleccionada */}
                        <div className="mt-3 p-3 bg-red-100 rounded border border-red-300">
                          <div className="text-xs text-red-600 space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-medium">Cuenta seleccionada:</span>
                              <span className="font-mono">
                                {selectedAccount || 'Ninguna (usando cuenta por defecto)'}
                              </span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="font-medium">Tracking number:</span>
                              <span className="font-mono">{epodTrackingNumber}</span>
                            </div>
                          </div>
                          
                          {!selectedAccount && (
                            <div className="mt-2 text-xs text-red-600">
                              <strong>💡 Sugerencia:</strong> Selecciona una cuenta DHL específica en el dropdown superior para usar esa cuenta en lugar de la cuenta por defecto.
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Mostrar resultados de ePOD */}
              {epodResult && epodResult.success && (
                <div className="space-y-6">
                  {/* Información del documento */}
                  <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                    <div className="flex items-center mb-4">
                      <svg className="w-8 h-8 mr-3 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div>
                        <h3 className="text-xl font-semibold text-green-900">
                          ePOD Disponible: {epodTrackingNumber}
                        </h3>
                        <p className="text-green-700">
                          Comprobante de entrega encontrado exitosamente
                        </p>
                      </div>
                    </div>
                    
                    {/* Información del documento */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-gray-700">Tipo:</span>
                        <div className="text-gray-600">{epodResult.type_code || 'POD'}</div>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Formato:</span>
                        <div className="text-gray-600">{epodResult.format || 'PDF'}</div>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Tamaño:</span>
                        <div className="text-gray-600">
                          {epodResult.size ? `${(epodResult.size / 1024).toFixed(1)} KB` : 'N/A'}
                        </div>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Cuenta DHL:</span>
                        <div className="text-gray-600 font-mono">
                          {selectedAccount || '706014493*'}
                        </div>
                        {!selectedAccount && (
                          <div className="text-xs text-gray-500 mt-1">*Cuenta por defecto</div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Botón de descarga principal */}
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <div className="text-center">
                      <div className="mb-4">
                        <svg className="w-16 h-16 mx-auto text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                      </div>
                      <h4 className="text-lg font-medium text-gray-900 mb-2">
                        Comprobante de Entrega
                      </h4>
                      <p className="text-gray-600 mb-4">
                        Documento oficial que confirma la entrega del envío {epodTrackingNumber}
                      </p>
                      <button
                        onClick={() => downloadDocument(epodResult.pdf_data, `ePOD_${epodTrackingNumber}${selectedAccount ? `_${selectedAccount}` : ''}.pdf`)}
                        className="inline-flex items-center px-6 py-3 bg-dhl-red text-white text-lg rounded-md hover:bg-red-700 transition-colors"
                      >
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Descargar Comprobante PDF
                      </button>
                    </div>
                  </div>

                  {/* Documentos adicionales */}
                  {epodResult.all_documents && epodResult.all_documents.length > 1 && (
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <h4 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
                        <svg className="w-5 h-5 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                        Documentos Adicionales ({epodResult.all_documents.length})
                      </h4>
                      <div className="space-y-2">
                        {epodResult.all_documents.map((doc, index) => (
                          <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded border">
                            <div className="flex items-center">
                              <svg className="w-6 h-6 mr-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                              <div>
                                <div className="font-medium text-gray-900">
                                  Documento {index + 1} - {doc.type_code}
                                </div>
                                <div className="text-sm text-gray-600">
                                  {doc.encoding_format} ({doc.size ? `${(doc.size / 1024).toFixed(1)} KB` : 'N/A'})
                                </div>
                              </div>
                            </div>
                            <button
                              onClick={() => downloadDocument(doc.content, `ePOD_${epodTrackingNumber}${selectedAccount ? `_${selectedAccount}` : ''}_doc${index + 1}.pdf`)}
                              className="inline-flex items-center px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
                            >
                              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                              Descargar
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Información adicional */}
                  {epodResult.raw_data && (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <h4 className="text-lg font-medium text-gray-800 mb-3">
                        Información Técnica
                      </h4>
                      <div className="text-sm text-gray-700 space-y-1">
                        <div className="flex">
                          <span className="font-medium w-32">Total documentos:</span>
                          <span>{epodResult.total_documents || 1}</span>
                        </div>
                        <div className="flex">
                          <span className="font-medium w-32">Formato base64:</span>
                          <span>{epodResult.is_base64 ? 'Sí' : 'No'}</span>
                        </div>
                        <div className="flex">
                          <span className="font-medium w-32">Estado:</span>
                          <span className="text-green-600 font-medium">Disponible para descarga</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Botón para nueva consulta */}
                  <div className="text-center">
                    <button
                      onClick={() => {
                        setEpodTrackingNumber('');
                        setEpodResult(null);
                        setEpodError('');
                      }}
                      className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Nueva Consulta ePOD
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
