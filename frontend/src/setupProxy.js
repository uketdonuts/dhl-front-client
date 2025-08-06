const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Determinar la URL del backend según el entorno
  let backendUrl;
  
  if (process.env.REACT_APP_BACKEND_URL) {
    // Usar variable de entorno si está definida
    backendUrl = process.env.REACT_APP_BACKEND_URL;
  } else {
    // Detectar si estamos dentro de Docker o desarrollo local
    const isDocker = process.env.NODE_ENV === 'production' || process.env.REACT_APP_ENVIRONMENT === 'development';
    backendUrl = isDocker ? 'http://backend:8000' : 'http://localhost:10000';
  }
  
  console.log('🔧 Proxy configurado para:', backendUrl);
  console.log('🔧 Variables de entorno:', {
    REACT_APP_BACKEND_URL: process.env.REACT_APP_BACKEND_URL,
    REACT_APP_ENVIRONMENT: process.env.REACT_APP_ENVIRONMENT,
    NODE_ENV: process.env.NODE_ENV
  });
  
  // Ajustar proxy para API de Django
  app.use(
    '/api',
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
      secure: false,
      logLevel: 'debug',
      onError: (err, req, res) => {
        console.error('❌ Proxy Error:', err.message);
        console.error('❌ Target URL:', backendUrl);
        res.status(500).json({ 
          error: 'Backend connection failed', 
          target: backendUrl,
          message: err.message 
        });
      },
      onProxyReq: (proxyReq, req, res) => {
        console.log('📤 Proxy Request:', req.method, req.url, '→', backendUrl + req.url);
      }
    })
  );

  // Bloquear archivos de hot-reload (JSON y JS)
  app.use(/^\/.*\.hot-update\.(json|js)$/, (req, res) => {
    res.status(404).end();
  });
};