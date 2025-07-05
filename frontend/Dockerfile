FROM node:18-alpine

# Establecer directorio de trabajo
WORKDIR /app

# Copiar package.json y package-lock.json
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el código de la aplicación
COPY . .

# Crear usuario no-root para seguridad
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Cambiar permisos
RUN chown -R nextjs:nodejs /app
USER nextjs

# Exponer puerto
EXPOSE 3000

# Variables de entorno por defecto
ENV NODE_ENV=development
ENV REACT_APP_API_URL=http://localhost:5000/api

# Comando para ejecutar la aplicación
CMD ["npm", "start"] 