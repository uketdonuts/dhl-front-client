import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import axios from 'axios';
import SmartLocationDropdown from '../SmartLocationDropdown';

const PickupTab = ({ selectedAccount }) => {
  const [pickupData, setPickupData] = useState({
    pickup_date: '',
    pickup_time: '',
    ready_time: '',
    close_time: '',
    special_instructions: '',
    requester: {
      name: '',
      company: '',
      phone: '',
      email: '',
      address: '',
      city: '',
      cityName: '',
      state: '',
      stateName: '',
      postal_code: '',
      country: '',
      countryName: ''
    },
    package_info: {
      package_count: 1,
      total_weight: 0,
      currency: 'USD',
      declared_value: 0
    }
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [toast, setToast] = useState(null); // { type: 'success' | 'error', message: string }

  // Función para mostrar toast
  const showToast = (type, message) => {
    setToast({ type, message });
  };

  // Auto-ocultar toast después de 5 segundos
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => {
        setToast(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  // Función para validar horarios de recogida DHL
  const validatePickupTiming = (pickupDate, pickupTime, closeTime) => {
    const errors = [];
    
    // Crear objetos Date para comparar
    const now = new Date();
    const pickupDateTime = new Date(`${pickupDate}T${pickupTime}:00`);
    const closeDateTime = closeTime ? new Date(`${pickupDate}T${closeTime}:00`) : null;
    
    // 1. Validar que la fecha no sea en el pasado
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const pickupDateOnly = new Date(pickupDate);
    pickupDateOnly.setHours(0, 0, 0, 0);
    
    if (pickupDateOnly < today) {
      errors.push('La fecha de recogida no puede ser en el pasado');
    }
    
    // 2. Validar horario de operación DHL (09:00 - 19:00)
    const pickupHour = parseInt(pickupTime.split(':')[0]);
    const pickupMinute = parseInt(pickupTime.split(':')[1]);
    
    if (pickupHour < 9 || pickupHour >= 19 || (pickupHour === 19 && pickupMinute > 0)) {
      errors.push('El horario de recogida debe ser entre 09:00 y 19:00');
    }
    
    // 3. Validar hora de cierre si se proporciona
    if (closeTime) {
      const closeHour = parseInt(closeTime.split(':')[0]);
      const closeMinute = parseInt(closeTime.split(':')[1]);
      
      if (closeHour > 19 || (closeHour === 19 && closeMinute > 0)) {
        errors.push('La hora de cierre debe ser máximo 19:00');
      }
      
      // 4. Validar ventana mínima de 90 minutos
      const timeDiffMs = closeDateTime - pickupDateTime;
      const timeDiffMinutes = timeDiffMs / (1000 * 60);
      
      if (timeDiffMinutes < 90) {
        errors.push('Debe haber mínimo 90 minutos entre la hora de recogida y cierre');
      }
    }
    
    // 5. Para recogidas del mismo día, debe solicitarse antes de las 19:00
    if (pickupDateOnly.getTime() === today.getTime()) {
      const currentHour = now.getHours();
      if (currentHour >= 19) {
        errors.push('Las recogidas del mismo día deben solicitarse antes de las 19:00');
      }
    }
    
    // 6. Validar anticipación mínima (al menos 24 horas recomendado)
    const hoursUntilPickup = (pickupDateTime - now) / (1000 * 60 * 60);
    if (hoursUntilPickup < 1) {
      errors.push('La recogida debe programarse con al menos 1 hora de anticipación');
    }
    
    return errors;
  };

  // Debug: Trackear cambios en selectedAccount
  useEffect(() => {
    console.log('🏢 Selected account changed:', {
      selectedAccount: selectedAccount,
      hasAccount: !!selectedAccount,
      isString: typeof selectedAccount === 'string',
      isObject: typeof selectedAccount === 'object',
      accountNumber: typeof selectedAccount === 'string' ? selectedAccount : selectedAccount?.account_number,
      accountName: typeof selectedAccount === 'object' ? selectedAccount?.name : 'N/A'
    });
  }, [selectedAccount]);

  // Manejar cambios en los datos del solicitante
  const updateRequester = (field, value) => {
    setPickupData(prev => ({
      ...prev,
      requester: {
        ...prev.requester,
        [field]: value
      }
    }));
  };

  // Actualizar múltiples campos del solicitante de una vez (optimizado para SmartLocationDropdown)
  const updateRequesterLocation = useCallback((locationData) => {
    console.log('🔄 updateRequesterLocation called with:', locationData);
    
    setPickupData(prev => {
      const newState = {
        ...prev,
        requester: {
          ...prev.requester,
          country: locationData.country || '',
          countryName: locationData.countryName || '',
          state: locationData.state || '',
          stateName: locationData.stateName || '',
          city: locationData.cityName || locationData.city || '',
          cityName: locationData.cityName || locationData.city || '',
          // Persistir código postal y rango seleccionados desde el dropdown
          postal_code: locationData.postalCode || '',
          postal_code_range: locationData.postalCodeRange || '',
          // Mantener también service area si viene desde el selector
          service_area: locationData.serviceArea || prev.requester?.service_area || '',
          service_area_name: locationData.serviceAreaName || prev.requester?.service_area_name || ''
        }
      };
      console.log('📦 New pickup state after update:', newState.requester);
      return newState;
    });
  }, []);

  // Manejar cambios en la información del paquete
  const updatePackageInfo = (field, value) => {
    setPickupData(prev => ({
      ...prev,
      package_info: {
        ...prev.package_info,
        [field]: value
      }
    }));
  };

  // Manejar cambios en campos principales
  const updatePickupData = (field, value) => {
    setPickupData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Función para solicitar recogida
  const handlePickupRequest = async () => {
    console.log('🔍 Debugging pickup request:', {
      selectedAccount: selectedAccount,
      isString: typeof selectedAccount === 'string',
      isObject: typeof selectedAccount === 'object',
      hasAccountNumber: selectedAccount?.account_number,
      pickupDataCountry: pickupData.requester.country,
      pickupDataCity: pickupData.requester.city
    });

    if (!selectedAccount) {
      setError('Selecciona una cuenta DHL para continuar');
      showToast('error', 'Selecciona una cuenta DHL para continuar');
      return;
    }

    // Validar horarios DHL antes de enviar
    const timingErrors = validatePickupTiming(
      pickupData.pickup_date, 
      pickupData.pickup_time, 
      pickupData.close_time
    );
    
    if (timingErrors.length > 0) {
      const errorMessage = timingErrors.join('. ');
      setError(errorMessage);
      showToast('error', errorMessage);
      return;
    }

    // Obtener el account_number dependiendo si es string u objeto
    const accountNumber = typeof selectedAccount === 'string' 
      ? selectedAccount 
      : selectedAccount?.account_number;

    if (!accountNumber) {
      setError('La cuenta seleccionada no tiene número de cuenta válido');
      return;
    }

    // Validaciones básicas
    if (!pickupData.pickup_date || !pickupData.pickup_time) {
      setError('Fecha y hora de recogida son obligatorias');
      return;
    }

    if (!pickupData.requester.name || !pickupData.requester.phone) {
      setError('Nombre y teléfono del solicitante son obligatorios');
      return;
    }

    if (!pickupData.requester.address || !pickupData.requester.city || !pickupData.requester.country) {
      setError('Dirección completa del solicitante es obligatoria');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const token = localStorage.getItem('accessToken');
      
      console.log('📝 Creating payload with:', {
        selectedAccount: selectedAccount,
        accountNumber: selectedAccount?.account_number,
        pickupDate: pickupData.pickup_date,
        pickupTime: pickupData.pickup_time,
        requesterData: pickupData.requester
      });
      
      // Transformar datos al formato esperado por la API DHL
      const payload = {
        // Fecha y hora planificada en formato ISO
        plannedPickupDateAndTime: `${pickupData.pickup_date}T${pickupData.pickup_time}:00`,
        
        // Número de cuenta DHL
        account_number: accountNumber,
        
        // Hora de cierre (opcional)
        ...(pickupData.close_time && { closeTime: pickupData.close_time }),
        
        // Instrucciones especiales
        ...(pickupData.special_instructions && {
          specialInstructions: [{ 
            value: pickupData.special_instructions, 
            typeCode: 'TBD' 
          }]
        }),
        
        // Información del remitente (mismo que solicitante para pickup)
        shipper: {
          postalCode: pickupData.requester.postal_code || '',
          cityName: pickupData.requester.city,
          countryCode: pickupData.requester.country,
          provinceCode: pickupData.requester.state || '',
          addressLine1: pickupData.requester.address,
          ...(pickupData.requester.company && { addressLine2: pickupData.requester.company }),
          contactInformation: {
            fullName: pickupData.requester.name,
            ...(pickupData.requester.company && { companyName: pickupData.requester.company }),
            phone: pickupData.requester.phone,
            ...(pickupData.requester.email && { email: pickupData.requester.email })
          }
        },
        
        // Información del receptor (para pickup, por defecto es el mismo que remitente)
        receiver: {
          postalCode: pickupData.requester.postal_code || '',
          cityName: pickupData.requester.city,
          countryCode: pickupData.requester.country,
          provinceCode: pickupData.requester.state || '',
          addressLine1: pickupData.requester.address,
          ...(pickupData.requester.company && { addressLine2: pickupData.requester.company }),
          contactInformation: {
            fullName: pickupData.requester.name,
            ...(pickupData.requester.company && { companyName: pickupData.requester.company }),
            phone: pickupData.requester.phone,
            ...(pickupData.requester.email && { email: pickupData.requester.email })
          }
        },
        
        // Solicitante de la recogida
        bookingRequestor: {
          postalCode: pickupData.requester.postal_code || '',
          cityName: pickupData.requester.city,
          countryCode: pickupData.requester.country,
          provinceCode: pickupData.requester.state || '',
          addressLine1: pickupData.requester.address,
          ...(pickupData.requester.company && { addressLine2: pickupData.requester.company }),
          contactInformation: {
            fullName: pickupData.requester.name,
            ...(pickupData.requester.company && { companyName: pickupData.requester.company }),
            phone: pickupData.requester.phone,
            ...(pickupData.requester.email && { email: pickupData.requester.email })
          }
        },
        
        // Detalles de la recogida (mismo lugar que el solicitante)
        pickupDetails: {
          postalCode: pickupData.requester.postal_code || '',
          cityName: pickupData.requester.city,
          countryCode: pickupData.requester.country,
          provinceCode: pickupData.requester.state || '',
          addressLine1: pickupData.requester.address,
          ...(pickupData.requester.company && { addressLine2: pickupData.requester.company }),
          contactInformation: {
            fullName: pickupData.requester.name,
            ...(pickupData.requester.company && { companyName: pickupData.requester.company }),
            phone: pickupData.requester.phone,
            ...(pickupData.requester.email && { email: pickupData.requester.email })
          }
        }
      };

      console.log('📦 Final payload:', payload);
      console.log('🔑 Account number in payload:', payload.account_number);
      console.log('✅ Payload validation:', {
        hasAccountNumber: !!payload.account_number,
        hasPlannedDateTime: !!payload.plannedPickupDateAndTime,
        hasShipper: !!payload.shipper,
        hasReceiver: !!payload.receiver,
        hasBookingRequestor: !!payload.bookingRequestor,
        hasPickupDetails: !!payload.pickupDetails
      });

      console.log('Enviando solicitud de recogida:', payload);

      const response = await axios.post('/api/dhl/pickup/', payload, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.data.success) {
        setResult(response.data.data);
        setError('');
        
        // Extraer número de confirmación correctamente
        const confirmationNumber = response.data.data?.confirmation_number || 
                                 response.data.data?.dispatch_confirmation_number ||
                                 response.data.data?.raw_response?.dispatchConfirmationNumbers?.[0] ||
                                 'N/A';
        
        console.log('Recogida programada exitosamente:', response.data);
        console.log('Número de confirmación extraído:', confirmationNumber);
        
        // Mostrar toast de éxito
        showToast('success', `¡Recogida programada exitosamente! Número de confirmación: ${confirmationNumber}`);
        
        // Scroll hacia arriba para mostrar el resultado
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else {
        const errorMessage = response.data.error || 'Error al programar recogida';
        setError(errorMessage);
        setResult(null);
        showToast('error', errorMessage);
      }
    } catch (err) {
      console.error('Error en pickup request:', err);
      const errorMessage = err.response?.data?.error || 
                          err.response?.data?.message || 
                          err.response?.data?.details ||
                          'Error de conexión con el servidor';
      setError(errorMessage);
      setResult(null);
      showToast('error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Limpiar formulario
  const resetForm = () => {
    setPickupData({
      pickup_date: '',
      pickup_time: '',
      ready_time: '',
      close_time: '',
      special_instructions: '',
      requester: {
        name: '',
        company: '',
        phone: '',
        email: '',
        address: '',
        city: '',
        cityName: '',
        state: '',
        stateName: '',
        postal_code: '',
        country: '',
        countryName: ''
      },
      package_info: {
        package_count: 1,
        total_weight: 0,
        currency: 'USD',
        declared_value: 0
      }
    });
    setResult(null);
    setError('');
  };

  // Obtener fecha mínima (mañana)
  const getTomorrowDate = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Programar Recogida DHL Express
        </h2>
        
        {/* Indicador de cuenta seleccionada */}
        {!selectedAccount && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">Cuenta DHL Requerida</h3>
                <div className="mt-2 text-sm text-yellow-700">
                  Para programar una recogida necesitas seleccionar una cuenta DHL desde el menú principal.
                </div>
              </div>
            </div>
          </div>
        )}
        
        <p className="text-gray-600 mb-6">
          Programa una recogida de paquetes con DHL Express. Las recogidas deben programarse con al menos 24 horas de anticipación.
        </p>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error de Recogida</h3>
                <div className="mt-2 text-sm text-red-700">
                  {error}
                </div>
              </div>
            </div>
          </div>
        )}

        {result && (
          <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">Recogida Programada Exitosamente</h3>
                <div className="mt-2 text-sm text-green-700">
                  <p><strong>Número de confirmación:</strong> {
                    result.confirmation_number || 
                    result.dispatch_confirmation_number ||
                    result.raw_response?.dispatchConfirmationNumbers?.[0] ||
                    'N/A'
                  }</p>
                  <p><strong>Fecha de recogida:</strong> {pickupData.pickup_date}</p>
                  <p><strong>Hora:</strong> {pickupData.pickup_time}</p>
                  {result.pickup_charge && (
                    <p><strong>Costo de recogida:</strong> {result.pickup_charge.currency} {result.pickup_charge.amount}</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Formulario de recogida */}
        <div className="space-y-6">
          {/* Información de Recogida */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Información de Recogida</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Fecha de Recogida *
                </label>
                <input
                  type="date"
                  value={pickupData.pickup_date}
                  onChange={(e) => updatePickupData('pickup_date', e.target.value)}
                  min={getTomorrowDate()}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-dhl-red"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Hora de Recogida * <span className="text-xs text-gray-500">(09:00 - 19:00)</span>
                </label>
                <input
                  type="time"
                  value={pickupData.pickup_time}
                  onChange={(e) => updatePickupData('pickup_time', e.target.value)}
                  min="09:00"
                  max="19:00"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-dhl-red"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Hora de Apertura
                </label>
                <input
                  type="time"
                  value={pickupData.ready_time}
                  onChange={(e) => updatePickupData('ready_time', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-dhl-red"
                  placeholder="Hora disponible desde"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Hora de Cierre <span className="text-xs text-gray-500">(máx. 19:00, +90min desde recogida)</span>
                </label>
                <input
                  type="time"
                  value={pickupData.close_time}
                  onChange={(e) => updatePickupData('close_time', e.target.value)}
                  min="09:00"
                  max="19:00"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-dhl-red"
                  placeholder="Hora disponible hasta"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Instrucciones Especiales
              </label>
              <textarea
                value={pickupData.special_instructions}
                onChange={(e) => updatePickupData('special_instructions', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-dhl-red"
                rows={3}
                placeholder="Instrucciones adicionales para el conductor..."
              />
            </div>
          </div>

          {/* Información del Solicitante */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Información del Solicitante</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nombre Completo *
                </label>
                <input
                  type="text"
                  value={pickupData.requester.name}
                  onChange={(e) => updateRequester('name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-dhl-red"
                  placeholder="Nombre del solicitante"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Empresa
                </label>
                <input
                  type="text"
                  value={pickupData.requester.company}
                  onChange={(e) => updateRequester('company', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-dhl-red"
                  placeholder="Nombre de la empresa"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Teléfono *
                </label>
                <input
                  type="tel"
                  value={pickupData.requester.phone}
                  onChange={(e) => updateRequester('phone', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-dhl-red"
                  placeholder="+1234567890"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={pickupData.requester.email}
                  onChange={(e) => updateRequester('email', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-dhl-red"
                  placeholder="email@ejemplo.com"
                />
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Dirección *
              </label>
              <input
                type="text"
                value={pickupData.requester.address}
                onChange={(e) => updateRequester('address', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-dhl-red"
                placeholder="Dirección completa"
                required
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ubicación *
              </label>
              <SmartLocationDropdown
                key={`location-${selectedAccount?.account_number || 'default'}`}
                value={{
                  country: pickupData.requester.country,
                  countryName: pickupData.requester.countryName,
                  state: pickupData.requester.state,
                  stateName: pickupData.requester.stateName,
                  city: pickupData.requester.city,
                  cityName: pickupData.requester.cityName,
                  postalCode: pickupData.requester.postal_code,
                  postalCode: pickupData.requester.postal_code || '', // Ensure postal code is included
                  serviceArea: pickupData.requester.service_area,
                  serviceAreaName: pickupData.requester.service_area_name
                }}
                onChange={(location) => {
                  console.log('🌍 Location changed:', location);
                  updateRequesterLocation(location);
                  console.log('📍 Updated requester:', {
                    country: location.country,
                    countryName: location.countryName,
                    state: location.state,
                    stateName: location.stateName,
                    city: location.cityName || location.city,
                    postal_code: location.postalCode
                  });
                }}
                placeholder="Selecciona ubicación de recogida..."
                className="w-full"
                required
              />
            </div>
          </div>

          {/* Información de Paquetes */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Información de Paquetes</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cantidad de Paquetes
                </label>
                <input
                  type="number"
                  value={pickupData.package_info.package_count}
                  onChange={(e) => updatePackageInfo('package_count', parseInt(e.target.value) || 1)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-dhl-red"
                  min="1"
                  max="99"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Peso Total (kg)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={pickupData.package_info.total_weight}
                  onChange={(e) => updatePackageInfo('total_weight', parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-dhl-red"
                  min="0.1"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Valor Declarado
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={pickupData.package_info.declared_value}
                  onChange={(e) => updatePackageInfo('declared_value', parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-dhl-red"
                  min="0"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Moneda
                </label>
                <select
                  value={pickupData.package_info.currency}
                  onChange={(e) => updatePackageInfo('currency', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red focus:border-dhl-red"
                >
                  <option value="USD">USD - Dólar Americano</option>
                  <option value="EUR">EUR - Euro</option>
                  <option value="CAD">CAD - Dólar Canadiense</option>
                  <option value="GBP">GBP - Libra Esterlina</option>
                  <option value="CRC">CRC - Colón Costarricense</option>
                </select>
              </div>
            </div>
          </div>

          {/* Botones de Acción */}
          <div className="flex flex-col sm:flex-row sm:justify-end space-y-3 sm:space-y-0 sm:space-x-3">
            <button
              type="button"
              onClick={resetForm}
              disabled={loading}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-dhl-red disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Limpiar Formulario
            </button>
            
            <button
              type="button"
              onClick={handlePickupRequest}
              disabled={loading || !selectedAccount}
              className={`px-6 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                !selectedAccount
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : loading
                  ? 'bg-dhl-red opacity-75 text-white cursor-not-allowed'
                  : 'bg-dhl-red text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-dhl-red'
              }`}
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white inline" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Programando...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a1 1 0 011-1h6a1 1 0 011 1v4h3a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9a2 2 0 012-2h3z" />
                  </svg>
                  Programar Recogida
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Toast Notifications */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 max-w-sm w-full bg-white border rounded-md shadow-lg ${
          toast.type === 'success' ? 'border-green-400' : 'border-red-400'
        }`}>
          <div className="p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                {toast.type === 'success' ? (
                  <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
              <div className="ml-3">
                <p className={`text-sm ${toast.type === 'success' ? 'text-green-800' : 'text-red-800'}`}>
                  {toast.message}
                </p>
              </div>
              <div className="ml-auto pl-3">
                <div className="-mx-1.5 -my-1.5">
                  <button
                    type="button"
                    onClick={() => setToast(null)}
                    className={`inline-flex bg-white rounded-md p-1.5 ${
                      toast.type === 'success' ? 'text-green-400 hover:bg-green-100' : 'text-red-400 hover:bg-red-100'
                    } focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                      toast.type === 'success' ? 'focus:ring-green-500' : 'focus:ring-red-500'
                    }`}
                  >
                    <span className="sr-only">Cerrar</span>
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Panel de información */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">
              Horarios y Restricciones de Recogida DHL
            </h3>
            <div className="mt-2 text-sm text-blue-700">
              <ul className="list-disc list-inside space-y-1">
                <li><strong>Horario de operación:</strong> Los couriers están disponibles de 09:00 a 19:00</li>
                <li><strong>Ventana mínima:</strong> Debe haber al menos 90 minutos entre hora de recogida y cierre</li>
                <li><strong>Recogidas mismo día:</strong> Deben solicitarse antes de las 19:00</li>
                <li><strong>Anticipación:</strong> Se recomienda programar con al menos 24 horas de anticipación</li>
                <li>Asegúrese de que alguien esté disponible durante el horario especificado</li>
                <li>Los paquetes deben estar listos y etiquetados para la recogida</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

PickupTab.propTypes = {
  selectedAccount: PropTypes.object
};

export default PickupTab;
