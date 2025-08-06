import axios from 'axios';

// Configuración del API según el entorno
const getApiBaseURL = () => {
  // Si hay variable de entorno específica, usarla
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // Si estamos en producción o usando puerto 10000
  if (window.location.hostname === 'localhost' && window.location.port === '10000') {
    return 'http://localhost:10000/api';
  }
  
  // Para desarrollo local (puerto 3000) usar proxy
  return '';
};

// Crear instancia de axios configurada
const api = axios.create({
  baseURL: getApiBaseURL(),  // Usar la función para determinar baseURL
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Debug: Mostrar configuración en consola
console.log('🔧 API Configuration:', {
  baseURL: getApiBaseURL(),
  hostname: window.location.hostname,
  port: window.location.port,
  REACT_APP_API_URL: process.env.REACT_APP_API_URL
});

// Interceptor para agregar token automáticamente
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores de respuesta
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token expirado o inválido
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      // Redirigir al login si es necesario
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export { api };
export default api;
