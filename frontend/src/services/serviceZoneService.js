import api from '../config/api';

/**
 * Servicio para manejar las zonas de servicio DHL (dropdowns) con cache inteligente
 */
class ServiceZoneService {
  
  constructor() {
    // Cache con tiempo de vida (TTL) en milisegundos
    this.cache = {
      countries: { data: null, timestamp: 0, ttl: 10 * 60 * 1000 }, // 10 minutos
      countryAnalysis: {}, // Cache por país
      states: {}, // Cache por país
      cities: {}, // Cache por país + filtros
      serviceAreas: {}, // Cache por país  
      postalCodes: {} // Cache por filtros
    };
    
    // TTL por defecto para diferentes tipos de datos
    this.defaultTTL = {
      countries: 10 * 60 * 1000, // 10 minutos - datos estáticos
      countryAnalysis: 30 * 60 * 1000, // 30 minutos - estructura no cambia
      states: 15 * 60 * 1000, // 15 minutos - semi-estáticos
      cities: 5 * 60 * 1000, // 5 minutos - pueden cambiar más seguido
      serviceAreas: 15 * 60 * 1000, // 15 minutos - semi-estáticos
      postalCodes: 5 * 60 * 1000 // 5 minutos - pueden cambiar
    };
  }

  /**
   * Verifica si un item del cache sigue siendo válido
   */
  _isCacheValid(cacheItem) {
    if (!cacheItem || !cacheItem.data || !cacheItem.timestamp) {
      return false;
    }
    return Date.now() - cacheItem.timestamp < cacheItem.ttl;
  }

  /**
   * Guarda datos en cache con TTL
   */
  _setCache(type, key, data, customTTL = null) {
    const ttl = customTTL || this.defaultTTL[type] || 5 * 60 * 1000;
    
    if (type === 'countries') {
      this.cache.countries = {
        data: data,
        timestamp: Date.now(),
        ttl: ttl
      };
    } else {
      if (!this.cache[type]) {
        this.cache[type] = {};
      }
      this.cache[type][key] = {
        data: data,
        timestamp: Date.now(),
        ttl: ttl
      };
    }
    
    // Debug info
    console.log(`🔄 Cache actualizado: ${type}${key ? `:${key}` : ''} (TTL: ${ttl/1000}s)`);
  }

  /**
   * Obtiene datos del cache
   */
  _getCache(type, key = null) {
    let cacheItem;
    
    if (type === 'countries') {
      cacheItem = this.cache.countries;
    } else {
      cacheItem = this.cache[type]?.[key];
    }
    
    if (this._isCacheValid(cacheItem)) {
      console.log(`✅ Cache hit: ${type}${key ? `:${key}` : ''}`);
      return cacheItem.data;
    }
    
    console.log(`❌ Cache miss: ${type}${key ? `:${key}` : ''}`);
    return null;
  }

  /**
   * Limpia cache específico o todo el cache
   */
  clearCache(type = null, key = null) {
    if (!type) {
      // Limpiar todo el cache
      this.cache = {
        countries: { data: null, timestamp: 0, ttl: this.defaultTTL.countries },
        countryAnalysis: {},
        states: {},
        cities: {},
        serviceAreas: {},
        postalCodes: {}
      };
      console.log('🧹 Cache completamente limpiado');
    } else if (key) {
      // Limpiar cache específico
      if (this.cache[type]) {
        delete this.cache[type][key];
        console.log(`🧹 Cache limpiado: ${type}:${key}`);
      }
    } else {
      // Limpiar tipo de cache
      if (type === 'countries') {
        this.cache.countries = { data: null, timestamp: 0, ttl: this.defaultTTL.countries };
      } else {
        this.cache[type] = {};
      }
      console.log(`🧹 Cache limpiado: ${type}`);
    }
  }
  
  /**
   * Analiza la estructura de datos disponible para un país específico (con cache)
   */
  async analyzeCountryStructure(countryCode) {
  // Intentar obtener del cache primero (versionado para bustear caché vieja)
  const cacheKey = `${countryCode}:v2`;
  const cached = this._getCache('countryAnalysis', cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const response = await api.get(`/service-zones/analyze-country/${countryCode}/`);
      const result = {
        success: true,
        hasStates: response.data.hasStates,
        hasCities: response.data.hasCities,
        hasPostalCodes: response.data.hasPostalCodes,
        pattern: response.data.pattern,
        statistics: response.data.statistics,
        recommendations: response.data.recommendations,
        // Nueva información sobre estructura de datos
        dataStructure: response.data.data_structure || {
          city_name_available: true,
          service_area_available: false,
          recommended_city_field: 'city_name'
        }
      };
      
      // Guardar en cache (TTL largo porque la estructura del país no cambia)
  this._setCache('countryAnalysis', cacheKey, result);
      
      return result;
    } catch (error) {
      console.error('Error analizando estructura del país:', error);
      const fallbackResult = {
        success: false,
        error: error.response?.data?.message || error.message,
        hasStates: false,
        hasCities: true,
        hasPostalCodes: true,
        pattern: 'MIXED',
        dataStructure: {
          city_name_available: true,
          service_area_available: false,
          recommended_city_field: 'city_name'
        }
      };
      
      // Guardar fallback en cache por menos tiempo
  this._setCache('countryAnalysis', cacheKey, fallbackResult, 2 * 60 * 1000); // 2 minutos
      
      return fallbackResult;
    }
  }
  
  /**
   * Obtiene lista de países disponibles (con cache)
   */
  async getCountries() {
    // Intentar obtener del cache primero
    const cached = this._getCache('countries');
    if (cached) {
      return cached;
    }

    try {
      const response = await api.get('/service-zones/countries/');
      const result = {
        success: true,
        data: response.data.data || [],
        count: response.data.count || 0
      };
      
      // Guardar en cache (TTL largo porque países no cambian frecuentemente)
      this._setCache('countries', null, result);
      
      return result;
    } catch (error) {
      console.error('Error obteniendo países:', error);
      const fallbackResult = {
        success: false,
        error: error.response?.data?.message || 'Error al obtener países',
        data: []
      };
      
      // No cachear errores por mucho tiempo
      this._setCache('countries', null, fallbackResult, 1 * 60 * 1000); // 1 minuto
      
      return fallbackResult;
    }
  }

  /**
   * Obtiene estados/provincias por país (con cache)
   * @param {string} countryCode - Código de país ISO (2 letras)
   */
  async getStatesByCountry(countryCode) {
    if (!countryCode) {
      throw new Error('Código de país requerido');
    }

    const cacheKey = countryCode.toUpperCase();
    
    // Intentar obtener del cache primero
    const cached = this._getCache('states', cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const response = await api.get(`/service-zones/states/${countryCode.toUpperCase()}/`);
      const result = {
        success: true,
        data: response.data.data || [],
        count: response.data.count || 0,
        countryCode: response.data.country_code
      };
      
      // Guardar en cache
      this._setCache('states', cacheKey, result);
      
      return result;
    } catch (error) {
      console.error('Error obteniendo estados:', error);
      const fallbackResult = {
        success: false,
        error: error.response?.data?.message || 'Error al obtener estados',
        data: []
      };
      
      // Cachear error por menos tiempo
      this._setCache('states', cacheKey, fallbackResult, 2 * 60 * 1000); // 2 minutos
      
      return fallbackResult;
    }
  }

  /**
   * Obtiene ciudades por país y opcionalmente por estado (con cache)
   * @param {string} countryCode - Código de país ISO (2 letras)
   * @param {string} stateCode - Código de estado/provincia (opcional)
   */
  async getCitiesByCountryState(countryCode, stateCode = null, options = {}) {
    if (!countryCode) {
      throw new Error('Código de país requerido');
    }

  // Para Canadá, SIEMPRE usar endpoint por país (sin estado)
  const cc = countryCode.toUpperCase();
  const effectiveState = cc === 'CA' ? null : stateCode;

  // Incluir una pista en la clave de caché para diferenciar el origen preferido
  const baseKey = `${cc}${effectiveState ? `_${effectiveState.toUpperCase()}` : ''}_prefmap_v3`;
  const cacheKey = options.q ? `${baseKey}_q:${String(options.q).toLowerCase()}` : baseKey;
    
    // Intentar obtener del cache primero
  const cached = this._getCache('cities', cacheKey);
  if (cached && !options.bypassCache) {
      return cached;
    }

    try {
      let endpoint = `/service-zones/cities/${cc}/`;
      if (effectiveState) {
        endpoint += `${effectiveState.toUpperCase()}/`;
      }
      // Armar query con prefer=map y cache-busting siempre
      const params = new URLSearchParams();
      params.append('prefer', 'map');
      if (options.q) {
        params.append('q', options.q);
      }
      params.append('_ts', String(Date.now()));
      const url = `${endpoint}?${params.toString()}`;

      const response = await api.get(url);
      const result = {
        success: true,
        data: response.data.data || [],
        count: response.data.count || 0,
        countryCode: response.data.country_code,
        stateCode: response.data.state_code,
        data_type: response.data.data_type,
        preferences: response.data.preferences
      };
      
  // Guardar en cache
  this._setCache('cities', cacheKey, result);
      
      return result;
    } catch (error) {
      console.error('Error obteniendo ciudades:', error);
      const fallbackResult = {
        success: false,
        error: error.response?.data?.message || 'Error al obtener ciudades',
        data: []
      };
      
      // Cachear error por menos tiempo
      this._setCache('cities', cacheKey, fallbackResult, 2 * 60 * 1000); // 2 minutos
      
      return fallbackResult;
    }
  }

  /**
   * Obtiene áreas de servicio por ubicación (con cache)
   * @param {string} countryCode - Código de país ISO (2 letras)
   * @param {Object} options - Opciones adicionales
   * @param {string} options.stateCode - Código de estado/provincia
   * @param {string} options.cityName - Nombre de ciudad
   */
  async getServiceAreasByLocation(countryCode, options = {}) {
    if (!countryCode) {
      throw new Error('Código de país requerido');
    }

    // Crear clave de cache única basada en filtros
    const cacheKey = `${countryCode.toUpperCase()}_${options.stateCode || ''}_${options.cityName || ''}`;
    
    // Intentar obtener del cache primero
    const cached = this._getCache('serviceAreas', cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const params = new URLSearchParams();
      if (options.stateCode) {
        params.append('state_code', options.stateCode);
      }
      if (options.cityName) {
        params.append('city_name', options.cityName);
      }

      const endpoint = `/service-zones/areas/${countryCode.toUpperCase()}/`;
      const url = params.toString() ? `${endpoint}?${params.toString()}` : endpoint;

      const response = await api.get(url);
      const result = {
        success: true,
        data: response.data.data || [],
        count: response.data.count || 0,
        filters: response.data.filters
      };
      
      // Guardar en cache
      this._setCache('serviceAreas', cacheKey, result);
      
      return result;
    } catch (error) {
      console.error('Error obteniendo áreas de servicio:', error);
      const fallbackResult = {
        success: false,
        error: error.response?.data?.message || 'Error al obtener áreas de servicio',
        data: []
      };
      
      // Cachear error por menos tiempo
      this._setCache('serviceAreas', cacheKey, fallbackResult, 2 * 60 * 1000); // 2 minutos
      
      return fallbackResult;
    }
  }

  /**
   * Obtiene códigos postales por ubicación (con cache y manejo inteligente de países grandes)
   * @param {string} countryCode - Código de país ISO (2 letras)
   * @param {Object} options - Opciones adicionales
   * @param {string} options.stateCode - Código de estado/provincia (opcional)
   * @param {string} options.cityName - Nombre de ciudad (opcional)
   * @param {number} options.page - Número de página (opcional)
   * @param {number} options.pageSize - Tamaño de página (opcional)
   * @param {boolean} options.forceLoad - Forzar carga aunque sea país grande (opcional)
   */
  async getPostalCodesByLocation(countryCode, options = {}) {
    if (!countryCode) {
      throw new Error('Código de país requerido');
    }

    // Países con muchos códigos postales
    const LARGE_COUNTRIES = ['CA', 'US', 'GB', 'DE', 'FR', 'AU', 'IN'];
    const isLargeCountry = LARGE_COUNTRIES.includes(countryCode.toUpperCase());

    // Crear clave de cache única basada en filtros
    const cacheKey = `${countryCode.toUpperCase()}_${options.stateCode || ''}_${options.cityName || ''}_${options.serviceArea || ''}_${options.page || 1}`;
    
    // Intentar obtener del cache primero
    const cached = this._getCache('postalCodes', cacheKey);
    if (cached) {
      return cached;
    }

    try {
      // Evitar llamadas innecesarias: para países grandes sin filtros, devolver aviso local
      if (isLargeCountry && !options.stateCode && !options.cityName && !options.serviceArea && !options.forceLoad) {
        return {
          success: false,
          error: 'Para países grandes, seleccione provincia/estado, ciudad o área de servicio para ver códigos postales',
          errorType: 'FILTERS_REQUIRED',
          totalCount: 0,
          availableFilters: {
            states: [],
            cities: [],
            service_areas: []
          },
          suggestion: 'Añada al menos un filtro para cargar códigos postales',
          isLargeCountry: true,
          requiresFilters: true
        };
      }
      const params = new URLSearchParams();
      if (options.stateCode) {
        params.append('state_code', options.stateCode);
      }
      if (options.cityName) {
        params.append('city_name', options.cityName);
      }
      if (options.serviceArea) {
        params.append('service_area', options.serviceArea);
      }
      if (options.page) {
        params.append('page', options.page);
      }
      if (options.pageSize) {
        params.append('page_size', options.pageSize);
      }
      if (options.forceLoad) {
        params.append('force_all', 'true');
      }
      // Aumentar el límite cuando hay filtros específicos (ciudad/área) para traer "todos" los códigos
      // Backend soporta parámetro 'limit' (default 5000). Lo elevamos si hay filtros.
      const hasSpecificFilters = !!(options.cityName || options.serviceArea || options.stateCode);
      if (hasSpecificFilters) {
        // Valores conservadores pero altos; ajustables si se requiere
        const limit = options.limit || 20000;
        params.append('limit', String(limit));
      }

      const endpoint = `/service-zones/postal-codes/${countryCode.toUpperCase()}/`;
      const url = params.toString() ? `${endpoint}?${params.toString()}` : endpoint;

      const response = await api.get(url);
      
      // Manejar respuesta exitosa
      if (response.data.success) {
        // Normalizar paginación desde claves del backend
        const count = Number(response.data.count || 0);
        const page = Number(response.data.page || 1);
        const pageSize = Number(response.data.page_size || options.pageSize || 1000);
        const totalPages = Number(response.data.total_pages || (pageSize ? Math.ceil(count / pageSize) : 1));
        const hasNext = page < totalPages;

        const result = {
          success: true,
          data: response.data.data || [],
          pagination: {
            count,
            page,
            page_size: pageSize,
            total_pages: totalPages,
            has_next: hasNext
          },
          filters: response.data.filters,
          performance: response.data.performance,
          isLargeCountry: isLargeCountry
        };
        
        // Guardar en cache (menos tiempo para países grandes sin filtros)
        const cacheTime = isLargeCountry && !options.stateCode && !options.cityName && !options.serviceArea 
          ? 2 * 60 * 1000  // 2 minutos para países grandes sin filtros
          : this.defaultTTL.postalCodes; // Tiempo normal para otros casos
          
        this._setCache('postalCodes', cacheKey, result, cacheTime);
        
        return result;
      }
      
      // Manejar error de filtros requeridos
      if (response.data.error === 'FILTERS_REQUIRED') {
        const result = {
          success: false,
          error: response.data.message,
          errorType: 'FILTERS_REQUIRED',
          totalCount: response.data.total_count,
          availableFilters: response.data.available_filters,
          suggestion: response.data.suggestion,
          isLargeCountry: true,
          requiresFilters: true
        };
        
        // Cachear por más tiempo ya que es información estructural
        this._setCache('postalCodes', cacheKey, result, 30 * 60 * 1000); // 30 minutos
        
        return result;
      }
      
      throw new Error(response.data.message || 'Error desconocido');
      
    } catch (error) {
      console.error('Error obteniendo códigos postales:', error);
      
      // Manejar diferentes tipos de errores
      let errorResult;
      
      if (error.response?.status === 400 && error.response?.data?.error === 'FILTERS_REQUIRED') {
        errorResult = {
          success: false,
          error: error.response.data.message,
          errorType: 'FILTERS_REQUIRED',
          totalCount: error.response.data.total_count,
          availableFilters: error.response.data.available_filters,
          suggestion: error.response.data.suggestion,
          recommendations: error.response.data.recommendations,
          isLargeCountry: true,
          requiresFilters: true
        };
      } else {
        errorResult = {
          success: false,
          error: error.response?.data?.message || 'Error al obtener códigos postales',
          errorType: 'NETWORK_ERROR',
          data: [],
          isLargeCountry: isLargeCountry
        };
      }
      
      // Cachear error por menos tiempo
      this._setCache('postalCodes', cacheKey, errorResult, 2 * 60 * 1000); // 2 minutos
      
      return errorResult;
    }
  }

  /**
   * Búsqueda avanzada de zonas de servicio
   * @param {Object} searchParams - Parámetros de búsqueda
   * @param {string} searchParams.query - Término de búsqueda
   * @param {string} searchParams.countryCode - Código de país para filtrar
   * @param {number} searchParams.page - Número de página
   * @param {number} searchParams.pageSize - Tamaño de página
   */
  async searchServiceZones(searchParams = {}) {
    try {
      const params = new URLSearchParams();
      
      if (searchParams.query) {
        params.append('q', searchParams.query);
      }
      if (searchParams.countryCode) {
        params.append('country_code', searchParams.countryCode);
      }
      if (searchParams.page) {
        params.append('page', searchParams.page);
      }
      if (searchParams.pageSize) {
        params.append('page_size', searchParams.pageSize);
      }

      const url = `/service-zones/search/?${params.toString()}`;
      const response = await api.get(url);

      return {
        success: true,
        data: response.data.data || [],
        pagination: response.data.pagination,
        filters: response.data.filters
      };
    } catch (error) {
      console.error('Error en búsqueda de zonas:', error);
      return {
        success: false,
        error: error.response?.data?.message || 'Error al buscar zonas de servicio',
        data: []
      };
    }
  }

  /**
   * Obtiene una ubicación completa con jerarquía de dropdown
   * @param {string} countryCode - Código de país
   * @param {string} stateCode - Código de estado (opcional)
   * @param {string} cityName - Nombre de ciudad (opcional)
   */
  async getLocationHierarchy(countryCode, stateCode = null, cityName = null) {
    try {
      const results = {};

      // 1. Obtener países
      const countriesResult = await this.getCountries();
      results.countries = countriesResult.data;

      // 2. Si hay país, obtener estados
      if (countryCode) {
        const statesResult = await this.getStatesByCountry(countryCode);
        results.states = statesResult.data;

        // 3. Si hay estado o solo país, obtener ciudades
        const citiesResult = await this.getCitiesByCountryState(countryCode, stateCode);
        results.cities = citiesResult.data;

        // 4. Obtener áreas de servicio
        const areasResult = await this.getServiceAreasByLocation(countryCode, {
          stateCode,
          cityName
        });
        results.serviceAreas = areasResult.data;
      }

      return {
        success: true,
        data: results
      };
    } catch (error) {
      console.error('Error obteniendo jerarquía de ubicación:', error);
      return {
        success: false,
        error: error.message || 'Error al obtener datos de ubicación',
        data: {}
      };
    }
  }

  /**
   * Valida si una ubicación tiene servicio DHL
   * @param {Object} location - Datos de ubicación
   * @param {string} location.countryCode - Código de país
   * @param {string} location.stateCode - Código de estado (opcional)
   * @param {string} location.cityName - Nombre de ciudad (opcional)
   */
  async validateLocation(location) {
    try {
      const { countryCode, stateCode, cityName } = location;
      
      if (!countryCode) {
        return {
          success: false,
          error: 'Código de país requerido'
        };
      }

      const result = await this.getServiceAreasByLocation(countryCode, {
        stateCode,
        cityName
      });

      return {
        success: result.success,
        hasService: result.data.length > 0,
        serviceAreas: result.data,
        error: result.error
      };
    } catch (error) {
      console.error('Error validando ubicación:', error);
      return {
        success: false,
        hasService: false,
        error: error.message || 'Error al validar ubicación'
      };
    }
  }

  /**
   * Obtiene estados con interfaz simplificada para SmartLocationDropdown
   */
  async getStates(countryCode) {
    try {
      const result = await this.getStatesByCountry(countryCode);
      return result.data || [];
    } catch (error) {
      console.error('Error obteniendo estados simplificado:', error);
      return [];
    }
  }

  /**
   * Obtiene ciudades con filtros para SmartLocationDropdown
   */
  async getCities(filters = {}) {
    try {
      const country = (filters.country || '').toUpperCase();
      // Para Canadá, ignorar el filtro de estado para obtener la lista completa del país
    if (country === 'CA') {
  const result = await this.getCitiesByCountryState(filters.country, null, { q: filters.q || filters.search, bypassCache: filters.bypassCache });
        return result;
      }

      // Para otros países, solo enviar state si realmente es necesario
    if (filters.state && filters.state.trim() !== '') {
  const result = await this.getCitiesByCountryState(filters.country, filters.state, { q: filters.q || filters.search, bypassCache: filters.bypassCache });
        return result;
      } else {
  const result = await this.getCitiesByCountryState(filters.country, null, { q: filters.q || filters.search, bypassCache: filters.bypassCache });
        return result;
      }
    } catch (error) {
      console.error('Error obteniendo ciudades simplificado:', error);
      return {
        success: false,
        data: [],
        error: error.message
      };
    }
  }

  /**
   * Obtiene códigos postales con filtros para SmartLocationDropdown
   */
  async getPostalCodes(filters = {}) {
    try {
      // Solicitar con page_size alto para reducir paginación
      const baseOptions = {
        stateCode: filters.state,
        cityName: filters.city,
        serviceArea: filters.serviceArea,
        pageSize: 1000,
        page: 1
      };

      let result = await this.getPostalCodesByLocation(filters.country, baseOptions);
      
      // Si el dataset es pequeño (<= ~5000) y hay más páginas, traerlas todas y consolidar
      if (result.success && result.pagination?.has_next && result.pagination?.total_pages && result.pagination.total_pages <= 5) {
        const allData = [...(result.data || [])];
        const totalPages = result.pagination.total_pages;
        for (let p = 2; p <= totalPages; p++) {
          const pageRes = await this.getPostalCodesByLocation(filters.country, { ...baseOptions, page: p });
          if (pageRes.success && Array.isArray(pageRes.data)) {
            allData.push(...pageRes.data);
          }
        }
        // Reemplazar datos y ajustar paginación para reflejar consolidado
        result = {
          ...result,
          data: allData,
          pagination: {
            ...result.pagination,
            count: allData.length,
            page: 1,
            has_next: false
          }
        };
      }
      
      // Si hay error de filtros requeridos, devolver el error completo
      if (!result.success && result.errorType === 'FILTERS_REQUIRED') {
        return result;
      }
      
      // Formatear datos para mostrar rangos
      const formattedData = (result.data || []).map(item => ({
        ...item,
        display_range: item.postal_code_from === item.postal_code_to 
          ? item.postal_code_from 
          : `${item.postal_code_from} - ${item.postal_code_to}`
      }));
      
      return {
        ...result,
        data: formattedData
      };
    } catch (error) {
      console.error('Error obteniendo códigos postales simplificado:', error);
      return {
        success: false,
        error: error.message,
        data: []
      };
    }
  }

  /**
   * Obtiene áreas de servicio (códigos de ciudad/aeropuerto) por país
   * @param {string} countryCode - Código de país ISO (2 letras)
   */
  async getServiceAreas(countryCode) {
    try {
      if (!countryCode) {
        throw new Error('Código de país requerido');
      }

      const response = await api.get(`/service-zones/areas/${countryCode.toUpperCase()}/`);
      const baseAreas = response.data.data || [];

      // Resolver nombres amigables por área de servicio usando el endpoint dedicado
      const resolved = await Promise.all(
        baseAreas.map(async (item) => {
          const code = item.service_area || item.code || item.name;
          if (!code) {
            return { service_area: '', display_name: '' };
          }
          try {
            const res = await api.get('/service-zones/resolve-display/', {
              params: {
                country_code: countryCode.toUpperCase(),
                service_area: String(code).toUpperCase()
              }
            });
            const dn = res.data?.data?.display_name || String(code).toUpperCase();
            return { service_area: String(code).toUpperCase(), display_name: dn };
          } catch (e) {
            return { service_area: String(code).toUpperCase(), display_name: String(code).toUpperCase() };
          }
        })
      );

      // Evitar nombres duplicados: si se repite display_name, concatenar el código
      const counts = resolved.reduce((acc, a) => {
        const key = a.display_name || '';
        acc[key] = (acc[key] || 0) + 1;
        return acc;
      }, {});
      const uniqueList = resolved.map(a => ({
        service_area: a.service_area,
        display_name: counts[a.display_name] > 1 ? `${a.display_name} - ${a.service_area}` : a.display_name
      }));

      return {
        success: true,
        data: uniqueList,
        count: uniqueList.length
      };
    } catch (error) {
      console.error('Error obteniendo áreas de servicio:', error);
      return {
        success: false,
        data: [],
        count: 0,
        error: error.response?.data?.message || error.message
      };
    }
  }

  /**
   * Métodos públicos para gestión de cache
   */
  
  /**
   * Limpia todo el cache
   */
  clearAllCache() {
    this.clearCache();
  }

  /**
   * Limpia cache de un tipo específico
   */
  clearCacheType(type) {
    this.clearCache(type);
  }

  /**
   * Obtiene estadísticas del cache
   */
  getCacheStats() {
    const stats = {
      countries: this._isCacheValid(this.cache.countries) ? 'válido' : 'expirado',
      countryAnalysis: Object.keys(this.cache.countryAnalysis).length,
      states: Object.keys(this.cache.states).length,
      cities: Object.keys(this.cache.cities).length,
      serviceAreas: Object.keys(this.cache.serviceAreas).length,
      postalCodes: Object.keys(this.cache.postalCodes).length,
      totalCacheItems: Object.keys(this.cache.countryAnalysis).length + 
                       Object.keys(this.cache.states).length + 
                       Object.keys(this.cache.cities).length + 
                       Object.keys(this.cache.serviceAreas).length + 
                       Object.keys(this.cache.postalCodes).length
    };
    
    console.log('📊 Estadísticas del Cache:', stats);
    return stats;
  }

  /**
   * Precarga cache para países más comunes
   */
  async preloadCommonCountries() {
    const commonCountries = ['PA', 'CO', 'US', 'MX', 'CR', 'GT'];
    console.log('🚀 Precargando cache para países comunes...');
    
    try {
      // Precargar países
      await this.getCountries();
      
      // Precargar análisis de países comunes
      const promises = commonCountries.map(country => 
        this.analyzeCountryStructure(country)
      );
      
      await Promise.all(promises);
      console.log('✅ Cache precargado exitosamente');
    } catch (error) {
      console.error('❌ Error precargando cache:', error);
    }
  }
}

// Crear instancia única del servicio
const serviceZoneService = new ServiceZoneService();

export default serviceZoneService;
