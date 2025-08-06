import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import serviceZoneService from '../services/serviceZoneService';

/**
 * Dropdown inteligente de ubicaciones con buscadores avanzados y cache optimizado
 * Maneja diferentes estructuras de países automáticamente
 */
const SmartLocationDropdown = ({ 
  value = {}, 
  onChange, 
  className = "",
  placeholder = "Selecciona ubicación...",
  required = false
}) => {
  // Estados locales
  const [countries, setCountries] = useState([]);
  const [states, setStates] = useState([]);
  const [cities, setCities] = useState([]);
  const [postalCodes, setPostalCodes] = useState([]);
  
  // Estados de cache y optimización
  const [loadingStates, setLoadingStates] = useState({
    countries: false,
    states: false,
    cities: false,
    postalCodes: false,
    countryAnalysis: false
  });
  
  // Referencias para evitar llamadas duplicadas
  const loadingRef = useRef({
    countries: false,
    states: false,
    cities: false,
    postalCodes: false,
    countryAnalysis: false
  });
  
  // Estados de búsqueda
  const [countrySearch, setCountrySearch] = useState('');
  const [stateSearch, setStateSearch] = useState('');
  const [citySearch, setCitySearch] = useState('');
  const [postalSearch, setPostalSearch] = useState('');
  
  // Estados de dropdowns abiertos
  const [openDropdown, setOpenDropdown] = useState(null);
  
  // Información del país seleccionado (con cache local)
  const [countryInfo, setCountryInfo] = useState({
    hasStates: false,
    hasCities: false,
    hasPostalCodes: false,
    pattern: null,
    dataStructure: {
      city_name_available: true,
      service_area_available: false,
      recommended_city_field: 'city_name'
    }
  });

  /**
   * Cargar países con optimización de cache
   */
  const loadCountries = useCallback(async () => {
    // Evitar cargas duplicadas
    if (loadingRef.current.countries) return;
    
    try {
      setLoadingStates(prev => ({ ...prev, countries: true }));
      loadingRef.current.countries = true;
      
      const result = await serviceZoneService.getCountries();
      if (result.success) {
        setCountries(result.data);
      }
    } catch (error) {
      console.error('Error cargando países:', error);
    } finally {
      setLoadingStates(prev => ({ ...prev, countries: false }));
      loadingRef.current.countries = false;
    }
  }, []);

  /**
   * Analizar estructura del país para determinar campos disponibles (con cache optimizado)
   */
  const analyzeCountryStructure = useCallback(async (countryCode) => {
    // Evitar análisis duplicados
    if (loadingRef.current.countryAnalysis) return;
    
    try {
      setLoadingStates(prev => ({ ...prev, countryAnalysis: true }));
      loadingRef.current.countryAnalysis = true;
      
      const analysis = await serviceZoneService.analyzeCountryStructure(countryCode);
      setCountryInfo({
        hasStates: analysis.hasStates,
        hasCities: analysis.hasCities,
        hasPostalCodes: analysis.hasPostalCodes,
        pattern: analysis.pattern,
        dataStructure: analysis.dataStructure || {
          city_name_available: true,
          service_area_available: false,
          recommended_city_field: 'city_name'
        }
      });
    } catch (error) {
      console.error('Error analizando estructura del país:', error);
      // Valores por defecto si falla
      setCountryInfo({
        hasStates: false,
        hasCities: true,
        hasPostalCodes: true,
        pattern: 'MIXED',
        dataStructure: {
          city_name_available: true,
          service_area_available: false,
          recommended_city_field: 'city_name'
        }
      });
    } finally {
      setLoadingStates(prev => ({ ...prev, countryAnalysis: false }));
      loadingRef.current.countryAnalysis = false;
    }
  }, []);

  /**
   * Cargar estados del país con cache optimizado
   */
  const loadStates = useCallback(async (countryCode) => {
    // Evitar cargas duplicadas
    if (loadingRef.current.states) return;
    
    try {
      setLoadingStates(prev => ({ ...prev, states: true }));
      loadingRef.current.states = true;
      
      const result = await serviceZoneService.getStates(countryCode);
      if (result.success) {
        setStates(result.data);
      }
    } catch (error) {
      console.error('Error cargando estados:', error);
    } finally {
      setLoadingStates(prev => ({ ...prev, states: false }));
      loadingRef.current.states = false;
    }
  }, []);

  /**
   * Cargar ciudades con detección automática de campo optimizado
   */
  const loadCities = useCallback(async (filters) => {
    // Evitar cargas duplicadas
    if (loadingRef.current.cities) return;
    
    try {
      setLoadingStates(prev => ({ ...prev, cities: true }));
      loadingRef.current.cities = true;
      
      // Usar el nuevo método smart que detecta automáticamente el campo correcto
      const result = await serviceZoneService.getCities(filters);
      
      if (result.success && result.data) {
        // El endpoint ahora retorna data con formato consistente
        setCities(result.data);
        
        // Log para debugging
        if (result.data_type) {
          console.log(`🎯 Campo usado para ${filters.country}: ${result.data_type}`);
        }
      } else {
        setCities([]);
      }
      
    } catch (error) {
      console.error('Error cargando ciudades:', error);
      setCities([]);
    } finally {
      setLoadingStates(prev => ({ ...prev, cities: false }));
      loadingRef.current.cities = false;
    }
  }, []);

  /**
   * Cargar códigos postales con filtros optimizado y manejo de países grandes
   */
  const loadPostalCodes = useCallback(async (filters) => {
    // Evitar cargas duplicadas
    if (loadingRef.current.postalCodes) return;
    
    try {
      setLoadingStates(prev => ({ ...prev, postalCodes: true }));
      loadingRef.current.postalCodes = true;
      
      const data = await serviceZoneService.getPostalCodes(filters);
      
      // Manejar respuesta con filtros requeridos
      if (!data.success && data.errorType === 'FILTERS_REQUIRED') {
        setPostalCodes({
          ...data,
          requiresFilters: true,
          message: data.error,
          suggestion: data.suggestion,
          availableStates: data.availableFilters?.states || [],
          availableCities: data.availableFilters?.cities || [],
          availableServiceAreas: data.availableFilters?.service_areas || [],
          recommendations: data.recommendations || {}
        });
        
        // También actualizar el estado de información del país
        setCountryInfo(prev => ({
          ...prev,
          hasPostalCodes: true,
          requiresFiltersForPostalCodes: true,
          postalCodeFiltersMessage: data.error,
          availableStatesForPostalCodes: data.availableFilters?.states || [],
          availableCitiesForPostalCodes: data.availableFilters?.cities || [],
          availableServiceAreasForPostalCodes: data.availableFilters?.service_areas || []
        }));
        
        return;
      }
      
      setPostalCodes(data);
    } catch (error) {
      console.error('Error cargando códigos postales:', error);
      setPostalCodes({
        success: false,
        error: 'Error al cargar códigos postales',
        data: []
      });
    } finally {
      setLoadingStates(prev => ({ ...prev, postalCodes: false }));
      loadingRef.current.postalCodes = false;
    }
  }, []);

  // Cargar países al montar (con cache y precarga)
  useEffect(() => {
    const initializeCache = async () => {
      try {
        // Cargar países inmediatamente
        await loadCountries();
        
        // Precargar cache para países comunes en background
        serviceZoneService.preloadCommonCountries().catch(error => {
          console.warn('Precarga de cache falló:', error);
        });
      } catch (error) {
        console.error('Error inicializando cache:', error);
      }
    };
    
    initializeCache();
  }, [loadCountries]);

  // Analizar estructura del país cuando cambia (con cache)
  useEffect(() => {
    if (value.country) {
      analyzeCountryStructure(value.country);
    }
  }, [value.country, analyzeCountryStructure]);

  // Cargar estados cuando cambia país (con cache optimizado)
  useEffect(() => {
    if (value.country && countryInfo.hasStates) {
      loadStates(value.country);
    } else {
      setStates([]);
    }
  }, [value.country, countryInfo.hasStates, loadStates]);

  // Cargar ciudades cuando cambia país/estado (con cache optimizado)
  useEffect(() => {
    if (value.country && countryInfo.hasCities) {
      const filters = { country: value.country };
      // Solo enviar state si el país realmente tiene estados Y hay un state seleccionado
      if (countryInfo.hasStates && value.state && value.state.trim() !== '') {
        filters.state = value.state;
      }
      loadCities(filters);
    } else {
      setCities([]);
    }
  }, [value.country, value.state, countryInfo.hasCities, countryInfo.hasStates, loadCities]);

  // Cargar códigos postales cuando cambia país/estado/ciudad (con manejo inteligente de países grandes)
  useEffect(() => {
    if (value.country && countryInfo.hasPostalCodes) {
      const filters = { country: value.country };
      
      // Para países grandes, requerir al menos estado o ciudad
      const LARGE_COUNTRIES = ['CA', 'US', 'GB', 'DE', 'FR', 'AU', 'IN'];
      const isLargeCountry = LARGE_COUNTRIES.includes(value.country?.toUpperCase());
      
      // Si es un país grande y no tiene filtros específicos, no cargar automáticamente
      if (isLargeCountry && !value.state && !value.city && !countryInfo.requiresFiltersForPostalCodes) {
        // Simular una carga para mostrar el mensaje de filtros requeridos
        loadPostalCodes(filters);
        return;
      }
      
      // Si tiene filtros específicos o no es país grande, cargar normalmente
      if (value.state) filters.state = value.state;
      if (value.city) filters.city = value.city;
      
      // Solo cargar si tenemos filtros suficientes o no es país grande
      if (!isLargeCountry || value.state || value.city) {
        loadPostalCodes(filters);
      } else {
        // Para países grandes sin filtros, limpiar códigos postales
        setPostalCodes({
          success: false,
          requiresFilters: true,
          message: `Para ${value.country?.toUpperCase()}, seleccione provincia/estado o ciudad para ver códigos postales`,
          data: []
        });
      }
    } else {
      setPostalCodes([]);
    }
  }, [value.country, value.state, value.city, countryInfo.hasPostalCodes, countryInfo.requiresFiltersForPostalCodes, loadPostalCodes]);

  /**
   * Filtrar opciones por búsqueda
   */
  const filterOptions = (options, searchTerm, labelKey = 'name') => {
    if (!searchTerm) return options;
    return options.filter(option => 
      option[labelKey]?.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  // Opciones filtradas
  const filteredCountries = useMemo(() => 
    filterOptions(countries, countrySearch, 'country_name'), 
    [countries, countrySearch]
  );
  const filteredStates = useMemo(() => 
    filterOptions(states, stateSearch, 'state_name'), 
    [states, stateSearch]
  );
  const filteredCities = useMemo(() => 
    filterOptions(cities, citySearch, 'display_name'), 
    [cities, citySearch]
  );
  const filteredPostalCodes = useMemo(() => 
    filterOptions(postalCodes, postalSearch, 'display_range'), 
    [postalCodes, postalSearch]
  );

  /**
   * Manejar selección de país
   */
  const handleCountrySelect = (country) => {
    const newValue = {
      country: country.country_code,
      countryName: country.country_name,
      state: '',
      stateName: '',
      city: '',
      cityName: '',
      postalCode: '',
      postalCodeRange: ''
    };
    onChange(newValue);
    setOpenDropdown(null);
    setCountrySearch('');
  };

  /**
   * Manejar selección de estado
   */
  const handleStateSelect = (state) => {
    const newValue = {
      ...value,
      state: state.state_code,
      stateName: state.state_name,
      city: '',
      cityName: '',
      postalCode: '',
      postalCodeRange: ''
    };
    onChange(newValue);
    setOpenDropdown(null);
    setStateSearch('');
  };

  /**
   * Manejar selección de ciudad
   */
  const handleCitySelect = (city) => {
    const newValue = {
      ...value,
      city: city.code || city.name,
      cityName: city.display_name || city.name,
      postalCode: '',
      postalCodeRange: ''
    };
    onChange(newValue);
    setOpenDropdown(null);
    setCitySearch('');
  };

  /**
   * Manejar selección de código postal
   */
  const handlePostalCodeSelect = (postalCode) => {
    const newValue = {
      ...value,
      postalCode: postalCode.postal_code_from,
      postalCodeRange: postalCode.display_range
    };
    onChange(newValue);
    setOpenDropdown(null);
    setPostalSearch('');
  };

  /**
   * Renderizar dropdown con búsqueda y estados de carga optimizados
   */
  const renderSearchDropdown = (
    isOpen, 
    toggleOpen, 
    placeholder, 
    searchValue, 
    setSearchValue, 
    options, 
    onSelect, 
    displayKey = 'name',
    loadingType = null
  ) => {
    const isLoading = loadingType ? loadingStates[loadingType] : false;
    
    return (
      <div className="relative">
        <button
          type="button"
          onClick={toggleOpen}
          disabled={isLoading}
          className={`w-full p-3 border border-gray-300 rounded-lg text-left bg-white hover:border-blue-500 focus:border-blue-500 focus:outline-none ${
            isLoading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {isLoading ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Cargando...
            </span>
          ) : (
            placeholder
          )}
        </button>
        
        {isOpen && !isLoading && (
          <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-hidden">
            <div className="p-2 border-b">
              <input
                type="text"
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                placeholder="Buscar..."
                className="w-full p-2 border border-gray-200 rounded focus:outline-none focus:border-blue-500"
                autoFocus
              />
            </div>
            <div className="max-h-48 overflow-y-auto">
              {options.length > 0 ? (
                options.map((option, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => onSelect(option)}
                    className="w-full p-2 text-left hover:bg-blue-50 focus:bg-blue-100 focus:outline-none"
                  >
                    {option[displayKey]}
                  </button>
                ))
              ) : (
                <div className="p-2 text-gray-500 text-center">
                  {searchValue ? 'No se encontraron resultados' : 'Sin datos disponibles'}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Función para cerrar dropdowns al hacer click fuera
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!event.target.closest('.dropdown-container')) {
        setOpenDropdown(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* País */}
      <div className="dropdown-container">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          País {required && <span className="text-red-500">*</span>}
        </label>
        {renderSearchDropdown(
          openDropdown === 'country',
          () => setOpenDropdown(openDropdown === 'country' ? null : 'country'),
          value.countryName || 'Selecciona un país...',
          countrySearch,
          setCountrySearch,
          filteredCountries,
          handleCountrySelect,
          'country_name',
          'countries'
        )}
      </div>

      {/* Estado (solo si el país tiene estados) */}
      {countryInfo.hasStates && value.country && (
        <div className="dropdown-container">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Estado/Provincia
          </label>
          {renderSearchDropdown(
            openDropdown === 'state',
            () => setOpenDropdown(openDropdown === 'state' ? null : 'state'),
            value.stateName || 'Selecciona un estado...',
            stateSearch,
            setStateSearch,
            filteredStates,
            handleStateSelect,
            'state_name',
            'states'
          )}
        </div>
      )}

      {/* Ciudad (solo si el país tiene ciudades) */}
      {countryInfo.hasCities && value.country && (
        <div className="dropdown-container">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Ciudad
          </label>
          {renderSearchDropdown(
            openDropdown === 'city',
            () => setOpenDropdown(openDropdown === 'city' ? null : 'city'),
            value.cityName || 'Selecciona una ciudad...',
            citySearch,
            setCitySearch,
            filteredCities,
            handleCitySelect,
            'display_name',
            'cities'
          )}
        </div>
      )}

      {/* Código Postal (solo si el país tiene códigos postales) */}
      {countryInfo.hasPostalCodes && value.country && (
        <div className="dropdown-container">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Código Postal
          </label>
          
          {/* Mostrar mensaje informativo para países grandes que requieren filtros */}
          {postalCodes.requiresFilters && !value.state && !value.city ? (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start space-x-2">
                <svg className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                <div className="flex-1">
                  <p className="text-sm text-blue-800 font-medium">
                    Filtros requeridos para códigos postales
                  </p>
                  <p className="text-sm text-blue-600 mt-1">
                    {postalCodes.message || `Para ${value.country?.toUpperCase()}, seleccione provincia/estado o ciudad para ver códigos postales disponibles.`}
                  </p>
                  
                  {/* Mostrar estados disponibles */}
                  {postalCodes.availableStates && postalCodes.availableStates.length > 0 && (
                    <p className="text-xs text-blue-500 mt-2">
                      <strong>Provincias disponibles:</strong> {postalCodes.availableStates.slice(0, 8).join(', ')}{postalCodes.availableStates.length > 8 ? '...' : ''}
                    </p>
                  )}
                  
                  {/* Mostrar ciudades disponibles si no hay estados */}
                  {postalCodes.availableCities && postalCodes.availableCities.length > 0 && (
                    <p className="text-xs text-blue-500 mt-2">
                      <strong>Ciudades disponibles:</strong> {postalCodes.availableCities.slice(0, 6).join(', ')}{postalCodes.availableCities.length > 6 ? '...' : ''}
                    </p>
                  )}
                  
                  {/* Mostrar áreas de servicio disponibles si no hay estados ni ciudades */}
                  {postalCodes.availableServiceAreas && postalCodes.availableServiceAreas.length > 0 && (
                    <p className="text-xs text-blue-500 mt-2">
                      <strong>Áreas de servicio disponibles:</strong> {postalCodes.availableServiceAreas.slice(0, 8).join(', ')}{postalCodes.availableServiceAreas.length > 8 ? '...' : ''}
                    </p>
                  )}
                  
                  {/* Mostrar recomendación especial */}
                  {postalCodes.recommendations?.use_service_area_filter && (
                    <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-xs">
                      <p className="text-green-800">
                        🏢 <strong>Sugerencia:</strong> {postalCodes.recommendations.message}
                      </p>
                      <p className="text-green-700 mt-1">
                        Ejemplo: <code className="bg-green-100 px-1 rounded">?service_area=YVR</code> para Vancouver
                      </p>
                    </div>
                  )}
                  
                  {/* Mostrar recomendación especial para ciudades */}
                  {postalCodes.recommendations?.use_city_filter && (
                    <div className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded text-xs">
                      <p className="text-amber-800">
                        💡 <strong>Recomendación:</strong> {postalCodes.recommendations.message}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            // Dropdown normal para códigos postales
            renderSearchDropdown(
              openDropdown === 'postal',
              () => setOpenDropdown(openDropdown === 'postal' ? null : 'postal'),
              value.postalCodeRange || 'Selecciona código postal...',
              postalSearch,
              setPostalSearch,
              filteredPostalCodes,
              handlePostalCodeSelect,
              'display_range',
              'postalCodes'
            )
          )}
        </div>
      )}
    </div>
  );
};

export default SmartLocationDropdown;
