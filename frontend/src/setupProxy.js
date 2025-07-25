const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Ajustar proxy para API de Django
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://backend:8000',
      changeOrigin: true,
      secure: false,
      logLevel: 'debug'
    })
  );

  // Bloquear archivos de hot-reload (JSON y JS)
  app.use(/^\/.*\.hot-update\.(json|js)$/, (req, res) => {
    res.status(404).end();
  });
};