import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import AccountDropdown from './AccountDropdown';
import ActivityHistoryTab from './dashboard/ActivityHistoryTab';
import ContactModal from './ContactModal';
import RateTabImproved from './dashboard/RateTabImproved';
import LandedCostTab from './dashboard/LandedCostTab';
import ShipmentTab from './dashboard/ShipmentTab';
import TrackingTab from './dashboard/TrackingTab';
import EpodTab from './dashboard/EpodTab';

// Componente para mostrar errores específicos de DHL
const DhlErrorAlert = ({ error, onDismiss }) => {
  if (!error) return null;

  const getErrorIcon = (message) => {
    if (message.includes('410518') || message.includes('suspendido') || message.includes('suspended')) {
      return '🚫';
    } else if (message.includes('autenticación') || message.includes('401')) {
      return '🔒';
    } else if (message.includes('ubicación') || message.includes('404')) {
      return '📍';
    } else if (message.includes('límite') || message.includes('429')) {
      return '⏳';
    }
    return '⚠️';
  };

  const isWarning = error.includes('suspendido') || error.includes('suspended') || error.includes('410518');
  const alertClass = isWarning ? 'alert-dhl-warning' : 'alert-dhl-error';

  return (
    <div className={`${alertClass} mb-4 relative`}>
      <div className="title">
        <span className="mr-2">{getErrorIcon(error)}</span>
        Error DHL API
        {onDismiss && (
          <button 
            onClick={onDismiss}
            className="ml-auto text-current hover:opacity-75"
          >
            ✕
          </button>
        )}
      </div>
      <div className="details">
        {error}
      </div>
    </div>
  );
};

const Dashboard = ({ selectedAccount, setSelectedAccount }) => {
  const { isAuthenticated, user } = useAuth();
  const [activeTab, setActiveTab] = useState('rate');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  
  // Estados para crear envío - Completamente vacío
  const [shipmentData, setShipmentData] = useState({
    shipper: {
      name: '',
      company: '',
      phone: '',
      email: '',
      address: '',
      city: '',
      state: '',
      postalCode: '',
      country: ''
    },
    recipient: {
      name: '',
      company: '',
      phone: '',
      email: '',
      address: '',
      city: '',
      state: '',
      postalCode: '',
      country: ''
    },
    package: {
      weight: 0,
      length: 0,
      width: 0,
      height: 0,
      description: '',
      value: 0,
      currency: 'USD'
    },
    service: 'P',
    payment: 'S',
    account_number: ''
  });
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
  
  // Estados para modal de contactos
  const [contactModalOpen, setContactModalOpen] = useState(false);
  const [contactTargetType, setContactTargetType] = useState('shipper');
  
  // Función para traducir estados del tracking
  const translateStatus = (status) => {
    const statusTranslations = {
      'Delivered': 'Entregado',
      'Out for Delivery': 'En ruta de entrega',
      'In Transit': 'En tránsito',
      'Pickup': 'Recolectado',
      'Arrived at Facility': 'Llegó a instalación',
      'Departed Facility': 'Salió de instalación',
      'Customs Released': 'Liberado de aduanas',
      'Customs Clearance': 'Despacho aduanero',
      'Success': 'En tránsito'
    };
    return statusTranslations[status] || status;
  };
  
  // Estados para cotización de tarifas - Completamente vacío
  const [rateData, setRateData] = useState({
    origin: {
      postal_code: "",
      city: "",
      country: "",
      state: ""
    },
    destination: {
      postal_code: "",
      city: "", 
      country: ""
    },
    weight: 0,
    dimensions: {
      length: 0,
      width: 0,
      height: 0
    },
    declared_weight: 0,
    service: 'P',
    account_number: '',
  });

  // Configurar axios para incluir el token
  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  // Sincronizar account_number si cambia selectedAccount
  useEffect(() => {
    if (selectedAccount) {
      setRateData(prev => ({ ...prev, account_number: selectedAccount }));
      setShipmentData(prev => ({ ...prev, account_number: selectedAccount }));
      // ✅ Agregar sincronización para otras pestañas si es necesario
    } else {
      // Limpiar account_number si no hay cuenta seleccionada
      setRateData(prev => ({ ...prev, account_number: '' }));
      setShipmentData(prev => ({ ...prev, account_number: '' }));
    }
  }, [selectedAccount]);

  const handleRateRequest = async () => {
    // Validar datos requeridos
    if (!rateData.origin.country || !rateData.destination.country) {
      setError('Por favor selecciona al menos el país de origen y destino');
      return;
    }

    if (!rateData.origin.city || !rateData.destination.city) {
      setError('Por favor selecciona la ciudad de origen y destino');
      return;
    }

    if (!rateData.weight || rateData.weight <= 0) {
      setError('Por favor ingresa un peso válido mayor a 0');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    // Debug: log de datos antes de enviar la cotización
    console.log('📊 DATOS DE COTIZACIÓN ENVIADOS:', {
      origin: rateData.origin,
      destination: rateData.destination,
      originCountry: rateData.origin.country,
      destinationCountry: rateData.destination.country
    });

    try {
      const response = await axios.post('/api/dhl/rate/', rateData, {
        headers: getAuthHeaders()
      });
      
      setResult(response.data);
    } catch (err) {
      // Mejorar el manejo de errores específicos de DHL
      const errorResponse = err.response?.data;
      let errorMessage = 'Error al obtener tarifas';
      let errorDetails = '';

      if (errorResponse) {
        // Verificar si es un error específico de DHL API
        if (errorResponse.error_code && errorResponse.message) {
          // Analizar tipos específicos de errores DHL
          const dhlMessage = errorResponse.message;
          
          if (dhlMessage.includes('410518') || dhlMessage.includes('destination facility is suspended')) {
            errorMessage = '🚫 Destino no disponible temporalmente';
            errorDetails = 'DHL ha suspendido el servicio a este destino. La suspensión puede ser temporal debido a restricciones operativas, políticas o logísticas. Por favor intenta con otro destino o contacta a DHL para más información.';
          } else if (dhlMessage.includes('410') && dhlMessage.includes('suspended')) {
            errorMessage = '🚫 Servicio suspendido';
            errorDetails = 'El servicio DHL a este destino está temporalmente suspendido. Esto puede deberse a restricciones operativas o logísticas.';
          } else if (dhlMessage.includes('400') || errorResponse.error_code === '400') {
            errorMessage = '❌ Error de validación';
            errorDetails = dhlMessage.replace('Error DHL API: ', '');
          } else if (errorResponse.error_code === '401') {
            errorMessage = '🔒 Error de autenticación';
            errorDetails = 'Las credenciales de DHL no son válidas o han expirado.';
          } else if (errorResponse.error_code === '404') {
            errorMessage = '📍 Ubicación no encontrada';
            errorDetails = 'Una o ambas ubicaciones (origen/destino) no pudieron ser validadas por DHL.';
          } else if (errorResponse.error_code === '429') {
            errorMessage = '⏳ Límite de solicitudes excedido';
            errorDetails = 'Se han realizado demasiadas solicitudes. Por favor espera un momento antes de intentar nuevamente.';
          } else {
            errorMessage = '⚠️ Error de DHL API';
            errorDetails = dhlMessage.replace('Error DHL API: ', '');
          }
        } else {
          // Error genérico del backend
          errorMessage = errorResponse.message || errorMessage;
        }
      }

      // Configurar notificación de error mejorada
      setError(errorMessage);
      
      // Si hay detalles específicos, mostrar notificación expandida
      if (errorDetails) {
        setNotification({
          type: 'error',
          message: errorMessage,
          details: errorDetails
        });
        
        setTimeout(() => setNotification(null), 10000); // Más tiempo para errores importantes
      }

      console.error('Error detallado al obtener tarifas:', {
        errorResponse,
        originalError: err,
        timestamp: new Date().toISOString()
      });
    } finally {
      setLoading(false);
    }
  };

  // Función para actualizar datos de cotización
  const updateRateData = (field, value) => {
    setRateData(prev => {
      const newData = {
        ...prev,
        [field]: value
      };
      
      // Sincronizar declared_weight con weight cuando se actualiza el peso
      if (field === 'weight') {
        newData.declared_weight = value;
      }
      
      return newData;
    });
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

  // Función para navegar a la pestaña de cotización
  const navigateToRate = () => {
    setActiveTab('rate');
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
      
      // Si el envío fue exitoso, guardar contactos automáticamente
      if (response.data.success) {
        await saveContactsFromShipment(shipmentData);
      }
    } catch (err) {
      setShipmentError(err.response?.data?.message || 'Error al crear envío');
    } finally {
      setShipmentLoading(false);
    }
  };

  // Función para descargar documentos PDF desde base64
  const downloadDocument = (base64Content, filename) => {
    try {
      if (!base64Content) {
        throw new Error('No hay contenido PDF disponible');
      }

      // Eliminar prefijo data:application/pdf;base64, si existe
      const cleanBase64 = base64Content.replace(/^data:application\/pdf;base64,/, '');
      
      // Validar que el contenido base64 sea válido
      if (!cleanBase64 || cleanBase64.length === 0) {
        throw new Error('Contenido PDF vacío o inválido');
      }

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
      alert(`Error al descargar el documento: ${error.message}`);
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
      
      if (selectedAccount) {
        requestData.account_number = selectedAccount;
      }

      const response = await axios.post('/api/dhl/epod/', 
        requestData, 
        { headers: getAuthHeaders() }
      );
      
      setEpodResult(response.data);
    } catch (err) {
      let errorMessage = err.response?.data?.message || 'Error al obtener el comprobante de entrega';
      
      if (err.response?.data?.error_data) {
        const errorData = err.response.data.error_data;
        
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

  // Función para resetear el estado de ePOD
  const resetEpodState = () => {
    setEpodTrackingNumber('');
    setEpodResult(null);
    setEpodError('');
  };

  // Helper function para preservar datos de cotización de forma inteligente
  const preserveQuoteDataForShipment = (originalRateData, selectedRate) => {
    console.log('🧪 PRESERVE FUNCTION INPUT:', {
      'originalRateData.origin': originalRateData.origin,
      'originalRateData.destination': originalRateData.destination,
      'selectedRate': selectedRate
    });

    const result = {
      // Datos básicos preservados
      weight: originalRateData.weight || originalRateData.declared_weight || 1,
      dimensions: {
        length: originalRateData.dimensions?.length || 1,
        width: originalRateData.dimensions?.width || 1,
        height: originalRateData.dimensions?.height || 1
      },
      service: selectedRate.service_code || originalRateData.service || 'P',
      account_number: originalRateData.account_number || '',
      
      // Origen completo
      origin: {
        city: originalRateData.origin?.city || '',
        state: originalRateData.origin?.state || '',
        postal_code: originalRateData.origin?.postal_code || '',
        country: originalRateData.origin?.country || '',
        country_name: originalRateData.origin_country_name || originalRateData.origin?.country_name || ''
      },
      
      // Destino completo
      destination: {
        city: originalRateData.destination?.city || '',
        state: originalRateData.destination?.state || '',
        postal_code: originalRateData.destination?.postal_code || '',
        country: originalRateData.destination?.country || '',
        country_name: originalRateData.destination_country_name || originalRateData.destination?.country_name || ''
      },
      
      // Información de la tarifa seleccionada
      selectedRate: {
        service_name: selectedRate.service_name,
        service_code: selectedRate.service_code,
        total_charge: selectedRate.total_charge,
        currency: selectedRate.currency,
        delivery_date: selectedRate.delivery_date
      }
    };

    console.log('🧪 PRESERVE FUNCTION OUTPUT:', result);
    return result;
  };

  // Función para crear shipment desde cotización
  const handleCreateShipmentFromRate = (selectedRate, originalRateData) => {
    // Validar que originalRateData existe y tiene la estructura esperada
    if (!originalRateData || !originalRateData.origin || !originalRateData.destination) {
      console.error('Error: originalRateData no válido', originalRateData);
      alert('Error: No se pudieron obtener los datos de origen y destino para crear el shipment');
      return;
    }

    // DEBUG: Mostrar todos los datos recibidos
    console.log('🔍 DEBUG COMPLETO DE DATOS RECIBIDOS:', {
      'originalRateData completo': originalRateData,
      'selectedRate completo': selectedRate,
      'originalRateData.origin': originalRateData.origin,
      'originalRateData.destination': originalRateData.destination
    });

    // ✅ VALIDACIÓN CORREGIDA: Los países están llegando correctamente
    console.log('✅ PAÍSES DETECTADOS:', {
      'origen': originalRateData.origin.country,
      'destino': originalRateData.destination.country
    });

    // Usar la función helper para preservar todos los datos
    const preservedData = preserveQuoteDataForShipment(originalRateData, selectedRate);

    // Debug específico para country fields
    console.log('🔍 DEBUG COUNTRY DATA:', {
      'originalRateData.origin.country': originalRateData.origin?.country,
      'originalRateData.destination.country': originalRateData.destination?.country,
      'preservedData.origin.country': preservedData.origin?.country,
      'preservedData.destination.country': preservedData.destination?.country
    });

    // Capturar TODOS los datos de la cotización para pre-llenar el shipment
    console.log('📦 Creando shipment desde cotización:', {
      selectedRate,
      originalRateData,
      preservedData,
      timestamp: new Date().toISOString()
    });

    const newShipmentData = {
      shipper: {
        name: '',
        company: '',
        phone: '',
        email: '',
        address: '',
        city: preservedData.origin.city,
        state: preservedData.origin.state,
        postalCode: preservedData.origin.postal_code,
        country: preservedData.origin.country,
        countryName: preservedData.origin.country_name
      },
      recipient: {
        name: '',
        company: '',
        phone: '',
        email: '',
        address: '',
        city: preservedData.destination.city,
        state: preservedData.destination.state,
        postalCode: preservedData.destination.postal_code,
        country: preservedData.destination.country,
        countryName: preservedData.destination.country_name
      },
      package: {
        weight: preservedData.weight,
        length: preservedData.dimensions.length,
        width: preservedData.dimensions.width,
        height: preservedData.dimensions.height,
        description: '',
        value: 0,
        currency: 'USD'
      },
      service: preservedData.service,
      payment: 'S',
      account_number: preservedData.account_number,
      
      // Información adicional preservada para referencia
      _quotedData: preservedData,
      _originalQuoteData: {
        ...originalRateData,
        preservedAt: new Date().toISOString(),
        selectedRateServiceName: selectedRate.service_name
      }
    };

    setShipmentData(newShipmentData);
    setActiveTab('shipment');
    
    // Mensaje más detallado con toda la información preservada
    const originInfo = `${preservedData.origin.city}, ${preservedData.origin.country}`;
    const destinationInfo = `${preservedData.destination.city}, ${preservedData.destination.country}`;
    const dimensionsInfo = `${preservedData.dimensions.length}x${preservedData.dimensions.width}x${preservedData.dimensions.height} cm`;
    
    setNotification({
      type: 'success',
      message: `✅ Formulario de envío prellenado con datos de cotización: ${preservedData.selectedRate.service_name}`,
      details: `� Direcciones y dimensiones completadas automáticamente. Por favor, complete los datos personales del remitente y destinatario (nombres, teléfonos, emails) antes de crear el envío. 💰 Tarifa: ${preservedData.selectedRate.currency} ${preservedData.selectedRate.total_charge}`
    });
    
    console.log('✅ Shipment creado con datos preservados:', newShipmentData);
    setTimeout(() => setNotification(null), 8000);
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

  // Funciones para el modal de contactos
  const openContactModal = (targetType) => {
    setContactTargetType(targetType);
    setContactModalOpen(true);
  };

  const handleContactSelect = (contactData) => {
    if (contactTargetType === 'shipper') {
      setShipmentData(prev => ({
        ...prev,
        shipper: contactData
      }));
    } else if (contactTargetType === 'recipient') {
      setShipmentData(prev => ({
        ...prev,
        recipient: contactData
      }));
    }
    setContactModalOpen(false);
  };

  // Función para intercambiar datos entre remitente y destinatario
  const switchShipperRecipient = () => {
    setShipmentData(prev => ({
      ...prev,
      shipper: prev.recipient,
      recipient: prev.shipper
    }));
    
    setNotification({
      type: 'success',
      message: '📋 Datos intercambiados correctamente',
      details: 'Los datos del remitente y destinatario han sido intercambiados'
    });
    
    setTimeout(() => setNotification(null), 3000);
  };

  // Función para guardar contactos automáticamente después de crear envío
  const saveContactsFromShipment = async (shipmentData) => {
    try {
      const contactsToSave = {
        shipper: {
          name: shipmentData.shipper.name,
          company: shipmentData.shipper.company,
          phone: shipmentData.shipper.phone,
          email: shipmentData.shipper.email,
          address: shipmentData.shipper.address,
          city: shipmentData.shipper.city,
          state: shipmentData.shipper.state,
          postal_code: shipmentData.shipper.postalCode,
          country: shipmentData.shipper.country
        },
        recipient: {
          name: shipmentData.recipient.name,
          company: shipmentData.recipient.company,
          phone: shipmentData.recipient.phone,
          email: shipmentData.recipient.email,
          address: shipmentData.recipient.address,
          city: shipmentData.recipient.city,
          state: shipmentData.recipient.state,
          postal_code: shipmentData.recipient.postalCode,
          country: shipmentData.recipient.country
        }
      };

      await axios.post('/api/contacts/from-shipment/', contactsToSave, {
        headers: getAuthHeaders()
      });

      // Contactos guardados automáticamente - proceso silencioso
    } catch (error) {
      // Error guardando contactos automáticamente - proceso silencioso
      // No mostrar error al usuario ya que es un proceso silencioso
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
    <div className="container-main py-4 md:py-8 px-2 md:px-4">{/* Responsive padding */}
      {/* Notificación mejorada */}
      {notification && (
        <div className={`mb-6 alert ${
          notification.type === 'success' 
            ? 'alert-success'
            : 'alert-error'
        }`}>
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              {notification.type === 'success' ? (
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              )}
            </div>
            <div className="flex-1">
              <p className="font-medium">{notification.message}</p>
              {notification.details && (
                <p className="mt-1 text-sm opacity-90">{notification.details}</p>
              )}
            </div>
            <button
              onClick={() => setNotification(null)}
              className="flex-shrink-0 text-current opacity-60 hover:opacity-100 transition-opacity"
            >
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Header de la aplicación responsive */}
      <div className="section-header">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div className="flex-1">
            <h1 className="section-title text-xl md:text-2xl">Panel de Control DHL Express</h1>
            <p className="section-subtitle text-sm md:text-base">
              Gestiona tus envíos, cotizaciones y seguimiento de paquetes
            </p>
            {user && (
              <div className="flex flex-wrap items-center mt-2 space-x-2 gap-1">
                <div className="badge badge-info text-xs">
                  <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                  </svg>
                  {user.username}
                </div>
                <div className="badge badge-success text-xs">
                  <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Conectado
                </div>
              </div>
            )}
          </div>
          
          {/* Selector de cuenta DHL mejorado para móviles */}
          <div className="w-full lg:w-auto">
            <div className="card">
              <div className="card-body p-3 md:p-4">
                <AccountDropdown selectedAccount={selectedAccount} setSelectedAccount={setSelectedAccount} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navegación por pestañas mejorada con responsive design */}
      <div className="card mb-8">
        <div className="card-header">
          {/* Navegación Desktop */}
          <nav className="hidden md:flex flex-wrap space-x-1">
            {/* Pestañas principales */}
            <button 
              onClick={() => setActiveTab('rate')} 
              className={`nav-tab ${activeTab === 'rate' ? 'nav-tab-active' : 'nav-tab-inactive'}`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
              <span>Cotizar Tarifas</span>
            </button>
            
            <button 
              onClick={() => setActiveTab('landed-cost')} 
              className={`nav-tab ${activeTab === 'landed-cost' ? 'nav-tab-active' : 'nav-tab-inactive'}`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              <span>Costo de Importación</span>
            </button>
            
            <button 
              onClick={() => setActiveTab('shipment')} 
              className={`nav-tab ${activeTab === 'shipment' ? 'nav-tab-active' : 'nav-tab-inactive'}`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
              <span>Crear Envío</span>
            </button>
            
            <button 
              onClick={() => setActiveTab('tracking')} 
              className={`nav-tab ${activeTab === 'tracking' ? 'nav-tab-active' : 'nav-tab-inactive'}`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>Rastreo</span>
            </button>
            
            <button 
              onClick={() => setActiveTab('epod')} 
              className={`nav-tab ${activeTab === 'epod' ? 'nav-tab-active' : 'nav-tab-inactive'}`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>Comprobante ePOD</span>
            </button>
            
            {/* Separador */}
            <div className="border-l border-corporate-300 h-6 self-center mx-2"></div>
            
            {/* Pestaña especial */}
            <button 
              onClick={() => setActiveTab('activity-history')} 
              className={`nav-tab ${activeTab === 'activity-history' ? 'nav-tab-active bg-info-500 text-white' : 'nav-tab-inactive'}`}
              title="Historial de actividades del sistema"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span>Historial</span>
            </button>
          </nav>

          {/* Navegación Mobile */}
          <nav className="md:hidden">
            {/* Grid de 3x2 para móvil */}
            <div className="grid grid-cols-3 gap-2 mb-3">
              {/* Fila 1 */}
              <button 
                onClick={() => setActiveTab('rate')} 
                className={`mobile-nav-tab ${activeTab === 'rate' ? 'mobile-nav-tab-active' : 'mobile-nav-tab-inactive'}`}
              >
                <svg className="w-5 h-5 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
                <span className="text-xs leading-tight">Cotizar</span>
              </button>
              
              <button 
                onClick={() => setActiveTab('landed-cost')} 
                className={`mobile-nav-tab ${activeTab === 'landed-cost' ? 'mobile-nav-tab-active' : 'mobile-nav-tab-inactive'}`}
              >
                <svg className="w-5 h-5 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                <span className="text-xs leading-tight">Aranceles</span>
              </button>
              
              <button 
                onClick={() => setActiveTab('shipment')} 
                className={`mobile-nav-tab ${activeTab === 'shipment' ? 'mobile-nav-tab-active' : 'mobile-nav-tab-inactive'}`}
              >
                <svg className="w-5 h-5 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
                <span className="text-xs leading-tight">Envío</span>
              </button>

              {/* Fila 2 */}
              <button 
                onClick={() => setActiveTab('tracking')} 
                className={`mobile-nav-tab ${activeTab === 'tracking' ? 'mobile-nav-tab-active' : 'mobile-nav-tab-inactive'}`}
              >
                <svg className="w-5 h-5 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span className="text-xs leading-tight">Rastreo</span>
              </button>
              
              <button 
                onClick={() => setActiveTab('epod')} 
                className={`mobile-nav-tab ${activeTab === 'epod' ? 'mobile-nav-tab-active' : 'mobile-nav-tab-inactive'}`}
              >
                <svg className="w-5 h-5 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span className="text-xs leading-tight">ePOD</span>
              </button>
              
              <button 
                onClick={() => setActiveTab('activity-history')} 
                className={`mobile-nav-tab ${activeTab === 'activity-history' ? 'mobile-nav-tab-active' : 'mobile-nav-tab-inactive'}`}
              >
                <svg className="w-5 h-5 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <span className="text-xs leading-tight">Historial</span>
              </button>
            </div>
          </nav>
        </div>
      </div>

      {/* Contenido de la pestaña activa */}
      <div>
        {activeTab === 'rate' && (
          <div>
            {/* Componente mejorado para errores específicos de DHL */}
            <DhlErrorAlert 
              error={error} 
              onDismiss={() => setError('')}
            />
            
            <RateTabImproved
              rateData={rateData}
              updateAddress={updateAddress}
              updateRateData={updateRateData}
              updateDimensions={updateDimensions}
              handleRateRequest={handleRateRequest}
              loading={loading}
              error={error}
              result={result}
              handleCreateShipmentFromRate={handleCreateShipmentFromRate}
              selectedAccount={selectedAccount}
            />
          </div>
        )}

        {/* Sección Costo Total de Importación */}
        {activeTab === 'landed-cost' && (
          <LandedCostTab
            handleCreateShipmentFromRate={handleCreateShipmentFromRate}
            setActiveTab={setActiveTab}
            selectedAccount={selectedAccount}
          />
        )}

        {activeTab === 'shipment' && (
          <ShipmentTab
            shipmentData={shipmentData}
            updateShipper={updateShipper}
            updateRecipient={updateRecipient}
            updatePackage={updatePackage}
            openContactModal={openContactModal}
            handleCreateShipment={handleCreateShipment}
            shipmentLoading={shipmentLoading}
            shipmentError={shipmentError}
            shipmentResult={shipmentResult}
            switchShipperRecipient={switchShipperRecipient}
          />
        )}

        {activeTab === 'tracking' && (
          <TrackingTab
            trackingNumber={trackingNumber}
            setTrackingNumber={setTrackingNumber}
            handleTracking={handleTracking}
            trackingLoading={trackingLoading}
            trackingError={trackingError}
            trackingResult={trackingResult}
            translateStatus={translateStatus}
            onNavigateToRate={navigateToRate}
            updateRateData={updateRateData}
          />
         )}

        {activeTab === 'epod' && (
          <EpodTab
            epodTrackingNumber={epodTrackingNumber}
            setEpodTrackingNumber={setEpodTrackingNumber}
            handleEpod={handleEpod}
            epodLoading={epodLoading}
            epodError={epodError}
            epodResult={epodResult}
            selectedAccount={selectedAccount}
            downloadDocument={downloadDocument}
            resetEpodState={resetEpodState}
          />
         )}

        {activeTab === 'activity-history' && (
          <ActivityHistoryTab />
         )}
      </div>
      
      {/* Modal de Agenda de Contactos */}
      <ContactModal
        isOpen={contactModalOpen}
        onClose={() => setContactModalOpen(false)}
        onSelectContact={handleContactSelect}
      />
    </div>
  );
};

// PropTypes para validación de tipos
Dashboard.propTypes = {
  selectedAccount: PropTypes.string,
  setSelectedAccount: PropTypes.func.isRequired,
};

Dashboard.defaultProps = {
  selectedAccount: null,
};

export default Dashboard;
