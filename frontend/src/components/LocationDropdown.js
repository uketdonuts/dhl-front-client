import React, { useState, useEffect } from 'react';
import serviceZoneService from '../services/serviceZoneService';

/**
 * Componente de dropdown para seleccionar ubicaciones DHL
 * Maneja la jerarquía: País -> Estado -> Ciudad -> Área de Servicio
 */
const LocationDropdown = ({
  onLocationChange,
  initialLocation = {},
  required = false,
  disabled = false,
  className = '',
  showServiceArea = false
}) => {
  // Estados
  const [countries, setCountries] = useState([]);
  const [states, setStates] = useState([]);
  const [cities, setCities] = useState([]);
  const [serviceAreas, setServiceAreas] = useState([]);
  const [postalCodes, setPostalCodes] = useState([]);
  
  // Valores seleccionados
  const [selectedCountry, setSelectedCountry] = useState(initialLocation.countryCode || '');
  const [selectedState, setSelectedState] = useState(initialLocation.stateCode || '');
  const [selectedCity, setSelectedCity] = useState(initialLocation.cityName || '');
  const [selectedServiceArea, setSelectedServiceArea] = useState(initialLocation.serviceArea || '');
  const [selectedPostalCode, setSelectedPostalCode] = useState(initialLocation.postalCode || '');
  
  // Estados de carga
  const [loadingCountries, setLoadingCountries] = useState(false);
  const [loadingStates, setLoadingStates] = useState(false);
  const [loadingCities, setLoadingCities] = useState(false);
  const [loadingServiceAreas, setLoadingServiceAreas] = useState(false);
  const [loadingPostalCodes, setLoadingPostalCodes] = useState(false);
  
  // Errores
  const [error, setError] = useState('');

  // Cargar países al montar el componente
  useEffect(() => {
    loadCountries();
  }, []);

  // Cargar estados cuando cambie el país
  useEffect(() => {
    if (selectedCountry) {
      loadStates(selectedCountry);
      // Limpiar selecciones dependientes
      setSelectedState('');
      setSelectedCity('');
      setSelectedServiceArea('');
      setSelectedPostalCode('');
      setStates([]);
      setCities([]);
      setServiceAreas([]);
      setPostalCodes([]);
    }
  }, [selectedCountry]);

  // Cargar ciudades cuando cambie el estado
  useEffect(() => {
    if (selectedCountry) {
      loadCities(selectedCountry, selectedState);
      // Limpiar selecciones dependientes
      setSelectedCity('');
      setSelectedServiceArea('');
      setSelectedPostalCode('');
      setCities([]);
      setServiceAreas([]);
      setPostalCodes([]);
    }
  }, [selectedCountry, selectedState]);

  // Cargar áreas de servicio cuando cambie la ciudad
  useEffect(() => {
    if (selectedCountry && showServiceArea) {
      loadServiceAreas(selectedCountry, selectedState, selectedCity);
      setSelectedServiceArea('');
    }
  }, [selectedCountry, selectedState, selectedCity, showServiceArea]);

  // Cargar códigos postales cuando cambie la ubicación
  useEffect(() => {
    if (selectedCountry) {
      loadPostalCodes(selectedCountry, selectedState, selectedCity);
      setSelectedPostalCode('');
    }
  }, [selectedCountry, selectedState, selectedCity]);

  // Notificar cambios al componente padre
  useEffect(() => {
    const location = {
      countryCode: selectedCountry,
      stateCode: selectedState,
      cityName: selectedCity,
      serviceArea: selectedServiceArea,
      postalCode: selectedPostalCode
    };

    // Buscar nombres completos
    const countryName = countries.find(c => c.country_code === selectedCountry)?.country_name || '';
    const stateName = states.find(s => s.state_code === selectedState)?.state_name || '';

    onLocationChange({
      ...location,
      countryName,
      stateName
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCountry, selectedState, selectedCity, selectedServiceArea, selectedPostalCode, countries, states]);

  // Funciones de carga
  const loadCountries = async () => {
    setLoadingCountries(true);
    setError('');
    
    try {
      const result = await serviceZoneService.getCountries();
      if (result.success) {
        setCountries(result.data);
      } else {
        setError('Error al cargar países: ' + result.error);
      }
    } catch (err) {
      setError('Error al cargar países');
      console.error('Error cargando países:', err);
    } finally {
      setLoadingCountries(false);
    }
  };

  const loadStates = async (countryCode) => {
    setLoadingStates(true);
    
    try {
      const result = await serviceZoneService.getStatesByCountry(countryCode);
      if (result.success) {
        setStates(result.data);
      } else {
        console.warn('No se pudieron cargar estados:', result.error);
        setStates([]);
      }
    } catch (err) {
      console.error('Error cargando estados:', err);
      setStates([]);
    } finally {
      setLoadingStates(false);
    }
  };

  const loadCities = async (countryCode, stateCode = null) => {
    setLoadingCities(true);
    
    try {
      const result = await serviceZoneService.getCitiesByCountryState(countryCode, stateCode);
      if (result.success) {
        setCities(result.data);
      } else {
        console.warn('No se pudieron cargar ciudades:', result.error);
        setCities([]);
      }
    } catch (err) {
      console.error('Error cargando ciudades:', err);
      setCities([]);
    } finally {
      setLoadingCities(false);
    }
  };

  const loadServiceAreas = async (countryCode, stateCode = null, cityName = null) => {
    setLoadingServiceAreas(true);
    
    try {
      const result = await serviceZoneService.getServiceAreasByLocation(countryCode, {
        stateCode,
        cityName
      });
      if (result.success) {
        setServiceAreas(result.data);
      } else {
        console.warn('No se pudieron cargar áreas de servicio:', result.error);
        setServiceAreas([]);
      }
    } catch (err) {
      console.error('Error cargando áreas de servicio:', err);
      setServiceAreas([]);
    } finally {
      setLoadingServiceAreas(false);
    }
  };

  const loadPostalCodes = async (countryCode, stateCode = null, cityName = null) => {
    setLoadingPostalCodes(true);
    
    try {
      const result = await serviceZoneService.getPostalCodesByLocation(countryCode, {
        stateCode,
        cityName
      });
      if (result.success) {
        setPostalCodes(result.data);
      } else {
        console.warn('No se pudieron cargar códigos postales:', result.error);
        setPostalCodes([]);
      }
    } catch (err) {
      console.error('Error cargando códigos postales:', err);
      setPostalCodes([]);
    } finally {
      setLoadingPostalCodes(false);
    }
  };

  // Handlers de cambio
  const handleCountryChange = (e) => {
    setSelectedCountry(e.target.value);
  };

  const handleStateChange = (e) => {
    setSelectedState(e.target.value);
  };

  const handleCityChange = (e) => {
    setSelectedCity(e.target.value);
  };

  const handleServiceAreaChange = (e) => {
    setSelectedServiceArea(e.target.value);
  };

  const handlePostalCodeChange = (e) => {
    setSelectedPostalCode(e.target.value);
  };

  return (
    <div className={`location-dropdown ${className}`}>
      {error && (
        <div className="alert alert-danger mb-3">
          {error}
        </div>
      )}

      {/* Dropdown de Países */}
      <div className="mb-3">
        <label className="form-label">
          País {required && <span className="text-danger">*</span>}
        </label>
        <select
          className="form-select"
          value={selectedCountry}
          onChange={handleCountryChange}
          disabled={disabled || loadingCountries}
          required={required}
        >
          <option value="">
            {loadingCountries ? 'Cargando países...' : 'Seleccionar país'}
          </option>
          {countries.map((country) => (
            <option key={country.country_code} value={country.country_code}>
              {country.country_name}
            </option>
          ))}
        </select>
      </div>

      {/* Dropdown de Estados (solo si hay estados disponibles) */}
      {states.length > 0 && (
        <div className="mb-3">
          <label className="form-label">Estado/Provincia</label>
          <select
            className="form-select"
            value={selectedState}
            onChange={handleStateChange}
            disabled={disabled || loadingStates || !selectedCountry}
          >
            <option value="">
              {loadingStates ? 'Cargando estados...' : 'Seleccionar estado (opcional)'}
            </option>
            {states.map((state) => (
              <option key={state.state_code} value={state.state_code}>
                {state.state_name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Dropdown de Ciudades */}
      {selectedCountry && (
        <div className="mb-3">
          <label className="form-label">Ciudad</label>
          <select
            className="form-select"
            value={selectedCity}
            onChange={handleCityChange}
            disabled={disabled || loadingCities || !selectedCountry}
          >
            <option value="">
              {loadingCities ? 'Cargando ciudades...' : 'Seleccionar ciudad (opcional)'}
            </option>
            {cities.map((city, index) => (
              <option key={`${city.city_name}-${index}`} value={city.city_name}>
                {city.city_name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Dropdown de Áreas de Servicio (solo si se requiere) */}
      {showServiceArea && selectedCountry && (
        <div className="mb-3">
          <label className="form-label">Área de Servicio DHL</label>
          <select
            className="form-select"
            value={selectedServiceArea}
            onChange={handleServiceAreaChange}
            disabled={disabled || loadingServiceAreas || !selectedCountry}
          >
            <option value="">
              {loadingServiceAreas ? 'Cargando áreas...' : 'Seleccionar área de servicio'}
            </option>
            {serviceAreas.map((area, index) => (
              <option key={`${area.service_area}-${index}`} value={area.service_area}>
                {area.service_area}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Dropdown de Códigos Postales */}
      {selectedCountry && postalCodes.length > 0 && (
        <div className="mb-3">
          <label className="form-label">Código Postal</label>
          <select
            className="form-select"
            value={selectedPostalCode}
            onChange={handlePostalCodeChange}
            disabled={disabled || loadingPostalCodes || !selectedCountry}
          >
            <option value="">
              {loadingPostalCodes ? 'Cargando códigos postales...' : 'Seleccionar código postal (opcional)'}
            </option>
            {postalCodes.map((postal, index) => (
              <option key={`${postal.postal_code_from}-${postal.postal_code_to}-${index}`} value={`${postal.postal_code_from}-${postal.postal_code_to}`}>
                {postal.postal_code_from === postal.postal_code_to 
                  ? postal.postal_code_from 
                  : `${postal.postal_code_from} - ${postal.postal_code_to}`}
                {postal.service_area && ` (${postal.service_area})`}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Información de debug (solo en desarrollo) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="mt-2">
          <small className="text-muted">
            Debug: {selectedCountry}/{selectedState}/{selectedCity}/{selectedServiceArea}/{selectedPostalCode}
          </small>
        </div>
      )}
    </div>
  );
};

export default LocationDropdown;
