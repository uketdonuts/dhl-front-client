import React, { useState } from 'react';
import SmartLocationDropdown from './SmartLocationDropdown';

/**
 * Componente de prueba específico para probar el flujo jerárquico de códigos postales de Canadá
 * País → Área de Servicio → Código Postal
 */
const CanadaPostalCodeTest = () => {
  const [originLocation, setOriginLocation] = useState({});
  const [destinationLocation, setDestinationLocation] = useState({});

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">
        🇨🇦 Prueba de Códigos Postales de Canadá - Flujo Jerárquico
      </h2>
      
      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="text-lg font-semibold text-blue-800 mb-2">Flujo esperado:</h3>
        <ol className="list-decimal list-inside text-blue-700 space-y-1">
          <li><strong>Seleccionar País:</strong> Canadá (CA)</li>
          <li><strong>Seleccionar Área de Servicio:</strong> YVR (Vancouver), YYC (Calgary), YUL (Montreal), etc.</li>
          <li><strong>Seleccionar Código Postal:</strong> Códigos específicos del área seleccionada</li>
        </ol>
        <div className="mt-3 text-sm text-blue-600">
          <strong>Nota:</strong> Para Canadá, el sistema requiere seleccionar un área de servicio antes de mostrar códigos postales específicos.
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Origen */}
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-gray-700 border-b pb-2">
            📍 Ubicación de Origen
          </h3>
          
          <SmartLocationDropdown
            value={originLocation}
            onChange={setOriginLocation}
            placeholder="Selecciona ubicación de origen..."
            required={true}
            className="space-y-3"
          />
          
          {/* Debug info */}
          <div className="mt-4 p-3 bg-gray-50 border rounded-lg">
            <h4 className="font-medium text-gray-700 mb-2">Valores seleccionados:</h4>
            <pre className="text-xs text-gray-600 bg-white p-2 rounded border overflow-auto">
              {JSON.stringify(originLocation, null, 2)}
            </pre>
          </div>
        </div>

        {/* Destino */}
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-gray-700 border-b pb-2">
            🎯 Ubicación de Destino
          </h3>
          
          <SmartLocationDropdown
            value={destinationLocation}
            onChange={setDestinationLocation}
            placeholder="Selecciona ubicación de destino..."
            required={true}
            className="space-y-3"
          />
          
          {/* Debug info */}
          <div className="mt-4 p-3 bg-gray-50 border rounded-lg">
            <h4 className="font-medium text-gray-700 mb-2">Valores seleccionados:</h4>
            <pre className="text-xs text-gray-600 bg-white p-2 rounded border overflow-auto">
              {JSON.stringify(destinationLocation, null, 2)}
            </pre>
          </div>
        </div>
      </div>

      {/* Resultado final */}
      {(originLocation.postalCode || destinationLocation.postalCode) && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="text-lg font-semibold text-green-800 mb-3">
            ✅ Códigos Postales Seleccionados
          </h3>
          
          <div className="grid md:grid-cols-2 gap-4">
            {originLocation.postalCode && (
              <div className="bg-white p-3 rounded border">
                <h4 className="font-medium text-gray-700">Origen:</h4>
                <p className="text-lg text-green-700">
                  {originLocation.postalCodeRange} ({originLocation.serviceAreaName || originLocation.serviceArea})
                </p>
                <p className="text-sm text-gray-600">
                  {originLocation.countryName}
                </p>
              </div>
            )}
            
            {destinationLocation.postalCode && (
              <div className="bg-white p-3 rounded border">
                <h4 className="font-medium text-gray-700">Destino:</h4>
                <p className="text-lg text-green-700">
                  {destinationLocation.postalCodeRange} ({destinationLocation.serviceAreaName || destinationLocation.serviceArea})
                </p>
                <p className="text-sm text-gray-600">
                  {destinationLocation.countryName}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Guía de áreas de servicio comunes */}
      <div className="mt-6 p-4 bg-gray-50 border rounded-lg">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">
          📋 Áreas de Servicio Comunes de Canadá
        </h3>
        
        <div className="grid md:grid-cols-3 gap-4 text-sm">
          <div>
            <strong className="text-gray-700">Principales:</strong>
            <ul className="mt-1 space-y-1 text-gray-600">
              <li>YVR - Vancouver</li>
              <li>YYC - Calgary</li>
              <li>YUL - Montreal</li>
              <li>YOW - Ottawa</li>
            </ul>
          </div>
          
          <div>
            <strong className="text-gray-700">Regionales:</strong>
            <ul className="mt-1 space-y-1 text-gray-600">
              <li>YEG - Edmonton</li>
              <li>YWG - Winnipeg</li>
              <li>YHZ - Halifax</li>
              <li>YQR - Regina</li>
            </ul>
          </div>
          
          <div>
            <strong className="text-gray-700">Otros:</strong>
            <ul className="mt-1 space-y-1 text-gray-600">
              <li>YXE - Saskatoon</li>
              <li>YYT - St. John's</li>
              <li>YQM - Moncton</li>
              <li>DEFAULT - General</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CanadaPostalCodeTest;