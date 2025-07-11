const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy solo para requests de API
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://backend:8000',
      changeOrigin: true,
      secure: false,
      logLevel: 'silent',
      pathRewrite: {
        '^/api': '/api',
      },
    })
  );

  // Bloquear requests de hot-reload
  app.use('*.hot-update.json', (req, res) => {
    res.status(404).end();
  });
  
  app.use('*.hot-update.js', (req, res) => {
    res.status(404).end();
  });
}; 