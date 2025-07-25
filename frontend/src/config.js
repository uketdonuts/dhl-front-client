// Configuración de la aplicación para diferentes entornos
const config = {
  // Detectar si estamos en GitHub Pages (sin backend)
  isGitHubPages: process.env.REACT_APP_ENVIRONMENT === 'production' && 
                 (!process.env.REACT_APP_API_URL || process.env.REACT_APP_API_URL === ''),
  
  // URLs de API
  apiUrl: process.env.REACT_APP_API_URL || '/api',
  backendUrl: process.env.REACT_APP_BACKEND_URL || '/api',
  
  // Configuración para diferentes modos
  modes: {
    development: {
      hasBackend: true,
      showAllFeatures: true,
      apiUrl: '/api'
    },
    production: {
      hasBackend: true,
      showAllFeatures: true,
      apiUrl: '/api'
    },
    'github-pages': {
      hasBackend: false,
      showAllFeatures: false,
      apiUrl: null
    }
  },
  
  // Obtener configuración actual
  getCurrentMode() {
    if (this.isGitHubPages) {
      return this.modes['github-pages'];
    }
    return this.modes[process.env.REACT_APP_ENVIRONMENT || 'development'];
  }
};

export default config;