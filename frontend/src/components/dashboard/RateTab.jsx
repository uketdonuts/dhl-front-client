import React from 'react';
import PropTypes from 'prop-types';
import RateResults from '../RateResults';
import FieldTooltip from '../FieldTooltip';
import useFormValidation from '../../hooks/useFormValidation';
import FormValidationStatus from '../FormValidationStatus';
import NumericInput from '../NumericInput';

/**
 * Componente para la pestaña de Cotizar Tarifas
 */
const RateTab = ({
  rateData,
  updateAddress,
  updateRateData,
  updateDimensions,
  handleRateRequest,
  loading,
  error,
  result,
  handleCreateShipmentFromRate,
}) => {
  // ✅ Usar hook de validación
  const validation = useFormValidation(rateData, 'rate');

  // ✅ Manejar envío con validación
  const handleSubmit = () => {
    if (validation.validate()) {
      handleRateRequest();
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Cotización de Tarifas DHL Express
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Origen */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Origen</h3>
            <div className="space-y-3">
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                  Código Postal
                  <FieldTooltip fieldPath="rate.origin.postal_code" />
                </label>
                <input
                  type="text"
                  value={rateData.origin.postal_code}
                  onChange={e => updateAddress('origin', 'postal_code', e.target.value)}
                  className={validation.getFieldClass('origin.postal_code', 'w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
                  placeholder="0000"
                />
                {validation.hasFieldError('origin.postal_code') && (
                  <p className="mt-1 text-sm text-red-600">{validation.getFieldError('origin.postal_code')}</p>
                )}
              </div>
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                  Ciudad
                  <FieldTooltip fieldPath="rate.origin.city" />
                </label>
                <input
                  type="text"
                  value={rateData.origin.city}
                  onChange={e => updateAddress('origin', 'city', e.target.value)}
                  className={validation.getFieldClass('origin.city', 'w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
                  placeholder="Ciudad de Panamá"
                />
                {validation.hasFieldError('origin.city') && (
                  <p className="mt-1 text-sm text-red-600">{validation.getFieldError('origin.city')}</p>
                )}
              </div>
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                  Estado
                  <FieldTooltip fieldPath="rate.origin.state" />
                </label>
                <input
                  type="text"
                  value={rateData.origin.state}
                  onChange={e => updateAddress('origin', 'state', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                  placeholder="Opcional"
                />
              </div>
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                  País
                  <FieldTooltip fieldPath="rate.origin.country" />
                </label>
                <input
                  type="text"
                  value={rateData.origin.country}
                  onChange={e => updateAddress('origin', 'country', e.target.value)}
                  className={validation.getFieldClass('origin.country', 'w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
                  placeholder="PA"
                  maxLength="2"
                />
                {validation.hasFieldError('origin.country') && (
                  <p className="mt-1 text-sm text-red-600">{validation.getFieldError('origin.country')}</p>
                )}
              </div>
            </div>
          </div>

          {/* Destino */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Destino</h3>
            <div className="space-y-3">
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                  Código Postal
                  <FieldTooltip fieldPath="rate.destination.postal_code" />
                </label>
                <input
                  type="text"
                  value={rateData.destination.postal_code}
                  onChange={e => updateAddress('destination', 'postal_code', e.target.value)}
                  className={validation.getFieldClass('destination.postal_code', 'w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
                  placeholder="110111"
                />
                {validation.hasFieldError('destination.postal_code') && (
                  <p className="mt-1 text-sm text-red-600">{validation.getFieldError('destination.postal_code')}</p>
                )}
              </div>
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                  Ciudad
                  <FieldTooltip fieldPath="rate.destination.city" />
                </label>
                <input
                  type="text"
                  value={rateData.destination.city}
                  onChange={e => updateAddress('destination', 'city', e.target.value)}
                  className={validation.getFieldClass('destination.city', 'w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
                  placeholder="Bogotá"
                />
                {validation.hasFieldError('destination.city') && (
                  <p className="mt-1 text-sm text-red-600">{validation.getFieldError('destination.city')}</p>
                )}
              </div>
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                  Estado
                  <FieldTooltip fieldPath="rate.destination.state" />
                </label>
                <input
                  type="text"
                  value={rateData.destination.state}
                  onChange={e => updateAddress('destination', 'state', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                  placeholder="Opcional"
                />
              </div>
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                  País
                  <FieldTooltip fieldPath="rate.destination.country" />
                </label>
                <input
                  type="text"
                  value={rateData.destination.country}
                  onChange={e => updateAddress('destination', 'country', e.target.value)}
                  className={validation.getFieldClass('destination.country', 'w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
                  placeholder="CO"
                  maxLength="2"
                />
                {validation.hasFieldError('destination.country') && (
                  <p className="mt-1 text-sm text-red-600">{validation.getFieldError('destination.country')}</p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Datos del Paquete */}
        <div className="mt-6">
          <h3 className="text-lg font-medium text-gray-900 mb-3">Datos del Paquete</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                Peso (kg)
                <FieldTooltip fieldPath="rate.weight" />
              </label>
              <NumericInput
                step={0.1}
                min={0.01}
                value={rateData.weight}
                onChange={(e, value) => updateRateData('weight', parseFloat(value) || 0)}
                className={validation.getFieldClass('weight', 'w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
                placeholder="45"
                allowDecimals={true}
                decimals={2}
              />
              {validation.hasFieldError('weight') && (
                <p className="mt-1 text-sm text-red-600">{validation.getFieldError('weight')}</p>
              )}
            </div>
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                Tipo de Contenido
                <FieldTooltip fieldPath="rate.service" />
              </label>
              <select
                value={rateData.service}
                onChange={e => updateRateData('service', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
              >
                <option value="P">Paquetes (NON_DOCUMENTS)</option>
                <option value="D">Documentos (DOCUMENTS)</option>
              </select>
            </div>
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                Número de Cuenta DHL
                <FieldTooltip fieldPath="rate.account_number" />
              </label>
              <input
                type="text"
                value={rateData.account_number}
                onChange={e => updateRateData('account_number', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
                placeholder="706014493"
              />
            </div>
          </div>

          {/* Dimensiones */}
          <div className="mt-4">
            <h4 className="text-md font-medium text-gray-900 mb-3">Dimensiones (cm)</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                  Largo (cm)
                  <FieldTooltip fieldPath="rate.dimensions.length" />
                </label>
                <NumericInput
                  step={0.1}
                  min={1}
                  value={rateData.dimensions.length}
                  onChange={(e, value) => updateDimensions('length', value)}
                  className={validation.getFieldClass('dimensions.length', 'w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
                  placeholder="20"
                  allowDecimals={true}
                  decimals={1}
                />
                {validation.hasFieldError('dimensions.length') && (
                  <p className="mt-1 text-sm text-red-600">{validation.getFieldError('dimensions.length')}</p>
                )}
              </div>
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                  Ancho (cm)
                  <FieldTooltip fieldPath="rate.dimensions.width" />
                </label>
                <NumericInput
                  step={0.1}
                  min={1}
                  value={rateData.dimensions.width}
                  onChange={(e, value) => updateDimensions('width', value)}
                  className={validation.getFieldClass('dimensions.width', 'w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
                  placeholder="15"
                  allowDecimals={true}
                  decimals={1}
                />
                {validation.hasFieldError('dimensions.width') && (
                  <p className="mt-1 text-sm text-red-600">{validation.getFieldError('dimensions.width')}</p>
                )}
              </div>
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                  Alto (cm)
                  <FieldTooltip fieldPath="rate.dimensions.height" />
                </label>
                <NumericInput
                  step={0.1}
                  min={1}
                  value={rateData.dimensions.height}
                  onChange={(e, value) => updateDimensions('height', value)}
                  className={validation.getFieldClass('dimensions.height', 'w-full px-3 py-2 rounded-md focus:outline-none focus:ring-2')}
                  placeholder="10"
                  allowDecimals={true}
                  decimals={1}
                />
                {validation.hasFieldError('dimensions.height') && (
                  <p className="mt-1 text-sm text-red-600">{validation.getFieldError('dimensions.height')}</p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Estado de validación */}
        <div className="mt-6">
          <FormValidationStatus
            isValid={validation.isValid}
          />
        </div>

        {/* Botón para solicitar tarifas */}
        <div className="mt-6 space-y-2">
          <button
            onClick={handleSubmit}
            disabled={loading || !validation.canSubmit}
            className={`w-full py-3 px-4 rounded-md font-semibold transition-all duration-200 ${
              validation.canSubmit && !loading
                ? 'bg-dhl-red text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-dhl-red focus:ring-offset-2'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
            title={!validation.canSubmit ? `Complete todos los campos requeridos (${validation.missingCount} faltantes)` : ''}
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Obteniendo tarifas...
              </span>
            ) : !validation.canSubmit ? (
              `⚠️ Complete ${validation.missingCount} campo(s) para continuar`
            ) : (
              '🚀 Obtener Tarifas'
            )}
          </button>
        </div>
      </div>

      {/* Muestra errores */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Resultados de tarifas */}
      {result && result.success && (
        <RateResults
          result={result}
          originalRateData={rateData}
          onCreateShipment={handleCreateShipmentFromRate}
          weightBreakdown={result.weight_breakdown}
          contentInfo={result.content_info}
        />
      )}
    </div>
  );
};

RateTab.propTypes = {
  rateData: PropTypes.object.isRequired,
  updateAddress: PropTypes.func.isRequired,
  updateRateData: PropTypes.func.isRequired,
  updateDimensions: PropTypes.func.isRequired,
  handleRateRequest: PropTypes.func.isRequired,
  loading: PropTypes.bool.isRequired,
  error: PropTypes.string,
  result: PropTypes.object,
  handleCreateShipmentFromRate: PropTypes.func.isRequired,
};

RateTab.defaultProps = {
  error: null,
  result: null,
};

export default RateTab;
