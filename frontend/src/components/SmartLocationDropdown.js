import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import serviceZoneService from '../services/serviceZoneService';
import { normalizeCityName } from '../utils/dhlValidations';
import { mapCountryNameToCode, mapCodeToCountryName } from '../utils/countryMappingService';

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
  const [serviceAreas, setServiceAreas] = useState([]);
  const [postalCodes, setPostalCodes] = useState([]);
  // Estado local para reflejar selección inmediata de código postal (evita parpadeos)
  const [localPostalSelection, setLocalPostalSelection] = useState({ postalCodeRange: '' });
  
  // Estados de cache y optimización
  const [loadingStates, setLoadingStates] = useState({
    countries: false,
    states: false,
    cities: false,
    serviceAreas: false,
    postalCodes: false,
    countryAnalysis: false
  });
  
  // Referencias para evitar llamadas duplicadas
  const loadingRef = useRef({
    countries: false,
    states: false,
    cities: false,
    serviceAreas: false,
    postalCodes: false,
    countryAnalysis: false
  });
  
  // Estados de búsqueda
  const [countrySearch, setCountrySearch] = useState('');
  const [stateSearch, setStateSearch] = useState('');
  const [citySearch, setCitySearch] = useState('');
  const [serviceAreaSearch, setServiceAreaSearch] = useState('');
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
  const analyzeCountryStructure = useCallback(async (countryInput) => {
    // Evitar análisis duplicados
    if (loadingRef.current.countryAnalysis) return;
    
    try {
      setLoadingStates(prev => ({ ...prev, countryAnalysis: true }));
      loadingRef.current.countryAnalysis = true;
      
      // Convertir nombre de país a código si es necesario
      const countryCode = mapCountryNameToCode(countryInput) || countryInput;
      console.log(`🔍 Analizando país: "${countryInput}" -> código: "${countryCode}"`);
      
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
      // getStates devuelve directamente un array en éxito
      if (Array.isArray(result)) {
        setStates(result);
      } else if (result?.success && Array.isArray(result.data)) {
        setStates(result.data);
      } else {
        setStates([]);
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
  const result = await serviceZoneService.getCities({ ...filters, bypassCache: true });
      
      if (result.success && result.data) {
        // El endpoint ahora retorna data con formato consistente
        setCities(result.data);
        
        // Log para debugging
        console.log(`🏙️ Ciudades recibidas para ${filters.country}${filters.state ? ' - ' + filters.state : ''}:`, result.data.length);
        if (result.data_type) console.log(`🎯 Campo usado para ${filters.country}: ${result.data_type}`);
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
   * Cargar áreas de servicio del país con cache optimizado
   */
  const loadServiceAreas = useCallback(async (countryCode) => {
    // Evitar cargas duplicadas
    if (loadingRef.current.serviceAreas) return;
    
    try {
      setLoadingStates(prev => ({ ...prev, serviceAreas: true }));
      loadingRef.current.serviceAreas = true;
      
      const result = await serviceZoneService.getServiceAreas(countryCode);
      if (result.success) {
        // Transformar usando los nombres amigables y únicos provistos por el servicio
        const transformedAreas = result.data.map(area => ({
          code: area.service_area,
          name: area.service_area,
          display_name: area.display_name || area.service_area
        }));
        setServiceAreas(transformedAreas);
      }
    } catch (error) {
      console.error('Error cargando áreas de servicio:', error);
      setServiceAreas([]);
    } finally {
      setLoadingStates(prev => ({ ...prev, serviceAreas: false }));
      loadingRef.current.serviceAreas = false;
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
      // Convertir nombre de país a código si es necesario
      const countryCode = mapCountryNameToCode(value.country) || value.country;
      loadStates(countryCode);
    } else {
      setStates([]);
    }
  }, [value.country, countryInfo.hasStates, loadStates]);

  // Cargar ciudades cuando cambia país/estado (con cache optimizado)
  useEffect(() => {
    if (value.country && countryInfo.hasCities) {
      // Convertir nombre de país a código si es necesario
      const countryCode = mapCountryNameToCode(value.country) || value.country;
      const filters = { country: countryCode };
      // Solo enviar state si el país realmente tiene estados Y hay un state seleccionado
      if (countryInfo.hasStates && value.state && value.state.trim() !== '') {
        filters.state = value.state;
      }
      // Limpiar búsqueda y prevenir resultados viejos al cambiar de país
      setCitySearch('');
      // Limpiar cache local de ciudades cuando cambia el país para evitar listas parciales
      try {
        if (value.country) {
          // Acceder a la instancia para limpiar ciudades de este país
          const keyPrefix = countryCode.toUpperCase();
          Object.keys(serviceZoneService.cache.cities || {}).forEach(k => {
            if (k.startsWith(keyPrefix)) {
              delete serviceZoneService.cache.cities[k];
            }
          });
        }
      } catch (e) {
        // noop
      }
      loadCities(filters);
    } else {
      setCities([]);
    }
  }, [value.country, value.state, countryInfo.hasCities, countryInfo.hasStates, loadCities]);

  // Cargar ciudades o áreas de servicio según la estructura del país
  useEffect(() => {
    // Si no hay país, limpiar y salir
    if (!value.country) {
      setServiceAreas([]);
      return;
    }

    // Solo gestionar áreas de servicio aquí.
    // La carga de ciudades ya la maneja el efecto anterior que depende de country/state.
    const useServiceAreas =
      countryInfo.dataStructure?.service_area_available === true &&
      countryInfo.dataStructure?.recommended_city_field === 'service_area';

    if (useServiceAreas) {
      // Convertir nombre de país a código si es necesario
      const countryCode = mapCountryNameToCode(value.country) || value.country;
      loadServiceAreas(countryCode);
    }
  }, [
    value.country,
    countryInfo.dataStructure?.service_area_available,
    countryInfo.dataStructure?.recommended_city_field,
    loadServiceAreas
  ]);

  // Cargar códigos postales cuando cambia país/estado/ciudad/área de servicio (con manejo inteligente de países grandes)
  useEffect(() => {
    if (value.country && countryInfo.hasPostalCodes) {
      // Convertir nombre de país a código si es necesario
      const countryCode = mapCountryNameToCode(value.country) || value.country;
      const filters = { country: countryCode };
      
      // Para países grandes, requerir al menos estado, ciudad o área de servicio
      const LARGE_COUNTRIES = ['CA', 'US', 'GB', 'DE', 'FR', 'AU', 'IN'];
      const isLargeCountry = LARGE_COUNTRIES.includes(countryCode?.toUpperCase());
      
      // Si es un país grande y no tiene filtros específicos, no cargar automáticamente
      if (isLargeCountry && !value.state && !value.city && !value.serviceArea && !countryInfo.requiresFiltersForPostalCodes) {
        // Simular una carga para mostrar el mensaje de filtros requeridos
        loadPostalCodes(filters);
        return;
      }
      
      // Si tiene filtros específicos o no es país grande, cargar normalmente
      if (value.state) filters.state = value.state;
      if (value.city) filters.city = value.city;
      if (value.serviceArea) filters.serviceArea = value.serviceArea;
      
      // Solo cargar si tenemos filtros suficientes o no es país grande
      if (!isLargeCountry || value.state || value.city || value.serviceArea) {
        loadPostalCodes(filters);
      } else {
        // Para países grandes sin filtros, limpiar códigos postales
        setPostalCodes({
          success: false,
          requiresFilters: true,
          message: `Para ${countryCode?.toUpperCase()}, seleccione provincia/estado, ciudad o área de servicio para ver códigos postales`,
          data: []
        });
      }
    } else {
      setPostalCodes([]);
    }
  }, [value.country, value.state, value.city, value.serviceArea, countryInfo.hasPostalCodes, countryInfo.requiresFiltersForPostalCodes, loadPostalCodes]);

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
  // Simplificado para debug - bypass useMemo temporalmente
  const filteredServiceAreas = (serviceAreas && serviceAreas.length > 0) 
    ? serviceAreas 
    : (postalCodes.availableServiceAreas || []).map(area => ({ code: area, name: area, display_name: area }));
  const filteredPostalCodes = useMemo(() => 
    filterOptions(postalCodes.data || [], postalSearch, 'display_range'), 
    [postalCodes.data, postalSearch]
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
      serviceArea: '',
      serviceAreaName: '',
      postalCode: '0', // Valor por defecto para países sin códigos postales
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
      serviceArea: '',
      serviceAreaName: '',
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
    // Usar nombre amigable sin sufijos de código (" - CODE")
  const rawCityName = city.display_name || city.name || '';
  const friendlyCity = normalizeCityName(rawCityName);
    const newValue = {
      ...value,
      city: friendlyCity,
      cityName: friendlyCity,
      serviceArea: '',
      serviceAreaName: '',
      postalCode: value.postalCode || '0', // Mantener código postal existente o usar '0'
      postalCodeRange: ''
    };
    onChange(newValue);
    setOpenDropdown(null);
    setCitySearch('');
  };

  /**
   * Manejar selección de código postal con fallback inteligente
   */
  const handlePostalCodeSelect = (postalCode) => {
    console.log('📮 handlePostalCodeSelect called with:', postalCode);
    console.log('🎯 Current value before update:', value);
    
    const newValue = {
      ...value,
      postalCode: postalCode.postal_code_from,
      postalCodeRange: postalCode.display_range
    };

    // Si hay service area y no hay ciudad ya seleccionada, usar service area como ciudad
        if (postalCode.service_area && !value.city) {
      const saCode = String(postalCode.service_area).toUpperCase();
      // Intentar resolver nombre amigable desde serviceAreas cargadas
          const match = (serviceAreas || []).find(sa => (sa.code || sa.service_area) === saCode);
          // Quitar sufijo " - CODE" si existe
          const rawFriendly = match?.display_name || saCode;
          const friendly = normalizeCityName(rawFriendly);
      newValue.city = friendly;
      newValue.cityName = friendly;
      newValue.serviceArea = saCode;
      newValue.serviceAreaName = saCode;
    }

    // Reflejar selección localmente para evitar reset visual mientras padre actualiza
    setLocalPostalSelection({ postalCodeRange: postalCode.display_range });
    console.log('🔄 About to call onChange with:', newValue);
    onChange(newValue);
    console.log('✅ Called onChange, closing dropdown');
    setOpenDropdown(null);
    setPostalSearch('');
  };

  // Mantener estado local sincronizado con el valor controlado del padre
  useEffect(() => {
    if (value && typeof value.postalCodeRange !== 'undefined') {
      setLocalPostalSelection((prev) =>
        prev.postalCodeRange !== value.postalCodeRange
          ? { postalCodeRange: value.postalCodeRange || '' }
          : prev
      );
    }
  }, [value?.postalCodeRange]);

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
    loadingType = null,
    onSearchChange = null,
    totalCount = null,
    displayFormatter = null
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
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={searchValue}
                  onChange={(e) => (onSearchChange ? onSearchChange(e.target.value) : setSearchValue(e.target.value))}
                  placeholder="Buscar..."
                  className="flex-1 p-2 border border-gray-200 rounded focus:outline-none focus:border-blue-500"
                  autoFocus
                />
                {typeof totalCount === 'number' && (
                  <span className="text-xs text-gray-500 whitespace-nowrap">{totalCount} resultados</span>
                )}
              </div>
            </div>
            <div className="max-h-48 overflow-y-auto">
      {options.length > 0 ? (
                options.map((option, index) => (
                  <button
                    key={index}
                    type="button"
                    onMouseDown={(e) => { e.preventDefault(); e.stopPropagation(); onSelect(option); }}
                    className="w-full p-2 text-left hover:bg-blue-50 focus:bg-blue-100 focus:outline-none"
                  >
        {displayFormatter ? displayFormatter(option) : (option[displayKey] || `[${displayKey} missing]`)}
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

  {/* Ciudad (usa áreas de servicio internamente cuando aplica, pero la UI muestra 'Ciudad') */}
      {value.country && (
        <div className="dropdown-container">
          <label className="block text-sm font-medium text-gray-700 mb-1">
    Ciudad
            <span className="text-xs text-gray-500 ml-2">(Requerido para códigos postales)</span>
          </label>
          {(() => {
            // Determinar qué datos usar según la estructura del país
            // Preferir SIEMPRE ciudades si están disponibles; para CA forzar ciudades
            const isCA = String(value.country || '').toUpperCase() === 'CA';
            const analysisRecommendsSA = countryInfo.dataStructure?.recommended_city_field === 'service_area';
            const hasCityOptions = Array.isArray(filteredCities) && filteredCities.length > 0;
            const useServiceAreas = !isCA && analysisRecommendsSA && !hasCityOptions;
            const options = useServiceAreas ? filteredServiceAreas : filteredCities;
            const searchValue = useServiceAreas ? serviceAreaSearch : citySearch;
            const setSearchValue = useServiceAreas ? setServiceAreaSearch : setCitySearch;
    const placeholder = (useServiceAreas ? loadingStates.serviceAreas : loadingStates.cities)
      ? 'Cargando ciudades...'
      : (value.cityName || value.city || 'Selecciona una ciudad...');
            
            const handleSelect = useServiceAreas 
              ? (item) => {
                  // Quitar sufijo " - CODE" si existe para usar solo el nombre
                  const rawFriendly = item.display_name || item.name || item.code;
                  const friendly = normalizeCityName(rawFriendly);
                  const newValue = {
                    ...value,
                    serviceArea: item.code,
                    serviceAreaName: item.name,
                    city: friendly, // Mostrar ciudad amigable en la UI
                    cityName: friendly,
                    postalCode: '',
                    postalCodeRange: ''
                  };
                  onChange(newValue);
                  setOpenDropdown(null);
                  // Cargar códigos postales
                  if (value.country) {
                    loadPostalCodes({
                      country: value.country,
                      serviceArea: item.code
                    });
                  }
                }
              : (item) => {
                  const newValue = {
                    ...value,
                    city: item.code || item.name,
                    cityName: item.display_name || item.name,
                    serviceArea: '',
                    serviceAreaName: '',
                    postalCode: '',
                    postalCodeRange: ''
                  };
                  onChange(newValue);
                  setOpenDropdown(null);
                  setCitySearch('');
                };

            // Mostrar el conteo real de opciones visibles (ciudades o áreas)
            const totalCount = (options && options.length) || 0;
            const onSearchChange = useServiceAreas
              ? (val) => setSearchValue(val)
        : (val) => {
                  setSearchValue(val);
                  // Búsqueda server-side para ciudades
          const isCA = String(value.country || '').toUpperCase() === 'CA';
          loadCities({ country: value.country, state: isCA ? undefined : value.state, q: val, bypassCache: true });
                };

            const displayFormatter = (opt) => normalizeCityName(opt.display_name || opt.name || '');
            return renderSearchDropdown(
              openDropdown === 'city',
              () => setOpenDropdown(openDropdown === 'city' ? null : 'city'),
              placeholder,
              searchValue,
              setSearchValue,
              options,
              handleSelect,
              'display_name',
              useServiceAreas ? 'serviceAreas' : 'cities',
              onSearchChange,
              totalCount,
              useServiceAreas ? null : displayFormatter
            );
          })()}
        </div>
      )}

      {/* Código Postal */}
      {countryInfo.hasPostalCodes && value.country && (value.serviceArea || value.city) && (
        <div className="dropdown-container">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Código Postal
          </label>
          
          {(() => {
            console.log('📮 Rendering postal code dropdown with:', {
              hasPostalCodes: countryInfo.hasPostalCodes,
              country: value.country,
              serviceArea: value.serviceArea,
              city: value.city,
              filteredPostalCodes: filteredPostalCodes?.length || 0,
              postalCodesData: postalCodes.data?.length || 0,
              postalSearch: postalSearch,
              currentValue: value.postalCodeRange
            });
            
            // Placeholder usa selección local primero para evitar parpadeo
            const postalPlaceholder = (localPostalSelection.postalCodeRange && String(localPostalSelection.postalCodeRange).trim())
              || (value.postalCodeRange && String(value.postalCodeRange).trim())
              || 'Selecciona código postal...';
            return renderSearchDropdown(
              openDropdown === 'postal',
              () => setOpenDropdown(openDropdown === 'postal' ? null : 'postal'),
              postalPlaceholder,
              postalSearch,
              setPostalSearch,
              filteredPostalCodes,
              handlePostalCodeSelect,
              'display_range',
              'postalCodes'
            );
          })()}
        </div>
      )}
    </div>
  );
};

export default SmartLocationDropdown;
