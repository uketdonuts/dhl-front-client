import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const DHLAccountManager = ({ onAccountCreated }) => {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newAccount, setNewAccount] = useState({
    account_number: '',
    account_name: ''
  });
  const { user } = useAuth();

  // Configurar axios para incluir el token en todas las requests
  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  // Cargar cuentas existentes
  const loadAccounts = async () => {
    try {
      const response = await axios.get('/api/dhl/accounts/', {
        headers: getAuthHeaders()
      });
      setAccounts(response.data);
    } catch (err) {
      console.error('Error loading accounts:', err);
    }
  };

  // Crear nueva cuenta
  const createAccount = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/dhl/accounts/create/', newAccount, {
        headers: getAuthHeaders()
      });
      
      if (response.data.success) {
        setAccounts([...accounts, response.data.account]);
        setNewAccount({ account_number: '', account_name: '' });
        setShowCreateForm(false);
        
        if (onAccountCreated) {
          onAccountCreated(response.data.account);
        }
      } else {
        setError(response.data.message || 'Error al crear la cuenta');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Error al crear la cuenta');
    } finally {
      setLoading(false);
    }
  };

  // Crear cuenta por defecto automáticamente
  const createDefaultAccount = async () => {
    setLoading(true);
    setError('');

    try {
      const defaultAccountData = {
        account_number: '706065602',
        account_name: 'Cuenta DHL por defecto'
      };

      const response = await axios.post('/api/dhl/accounts/create/', defaultAccountData, {
        headers: getAuthHeaders()
      });
      
      if (response.data.success) {
        setAccounts([response.data.account]);
        
        if (onAccountCreated) {
          onAccountCreated(response.data.account);
        }
      } else {
        setError(response.data.message || 'Error al crear la cuenta por defecto');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Error al crear la cuenta por defecto');
    } finally {
      setLoading(false);
    }
  };

  // Eliminar cuenta
  const deleteAccount = async (accountId) => {
    if (!window.confirm('¿Estás seguro de que quieres eliminar esta cuenta?')) {
      return;
    }

    try {
      await axios.delete(`/api/dhl/accounts/${accountId}/delete/`, {
        headers: getAuthHeaders()
      });
      
      setAccounts(accounts.filter(acc => acc.id !== accountId));
    } catch (err) {
      setError(err.response?.data?.message || 'Error al eliminar la cuenta');
    }
  };

  // Establecer como predeterminada
  const setAsDefault = async (accountId) => {
    try {
      const response = await axios.post(`/api/dhl/accounts/${accountId}/set-default/`, {}, {
        headers: getAuthHeaders()
      });
      
      if (response.data.success) {
        // Actualizar el estado local
        setAccounts(accounts.map(acc => ({
          ...acc,
          is_default: acc.id === accountId
        })));
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Error al establecer como predeterminada');
    }
  };

  useEffect(() => {
    loadAccounts();
  }, []);

  return (
    <div className="bg-white rounded-lg shadow-md border p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Gestión de Cuentas DHL</h3>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          {showCreateForm ? 'Cancelar' : 'Agregar Cuenta'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* Formulario para crear nueva cuenta */}
      {showCreateForm && (
        <form onSubmit={createAccount} className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="text-md font-medium text-gray-900 mb-3">Nueva Cuenta DHL</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Número de Cuenta *
              </label>
              <input
                type="text"
                value={newAccount.account_number}
                onChange={(e) => setNewAccount({...newAccount, account_number: e.target.value})}
                placeholder="706065602"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nombre de la Cuenta *
              </label>
              <input
                type="text"
                value={newAccount.account_name}
                onChange={(e) => setNewAccount({...newAccount, account_name: e.target.value})}
                placeholder="Mi Cuenta DHL"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50"
            >
              {loading ? 'Creando...' : 'Crear Cuenta'}
            </button>
            <button
              type="button"
              onClick={() => setShowCreateForm(false)}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
            >
              Cancelar
            </button>
          </div>
        </form>
      )}

      {/* Lista de cuentas existentes */}
      <div className="space-y-3">
        {accounts.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-500 mb-4">
              <svg className="mx-auto h-12 w-12 text-gray-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H9m0 0H7m2 0v-3a1 1 0 011-1h1a1 1 0 011 1v3M9 7h6m0 0v2m0-2h2m-2 2v2m0-2H9m8-2V5" />
              </svg>
              <p className="text-lg font-medium">No tienes cuentas DHL configuradas</p>
              <p className="text-sm text-gray-400">Necesitas al menos una cuenta para usar el tracking</p>
            </div>
            <button
              onClick={createDefaultAccount}
              disabled={loading}
              className="px-6 py-3 bg-dhl-red text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50"
            >
              {loading ? 'Creando...' : 'Crear Cuenta por Defecto'}
            </button>
          </div>
        ) : (
          accounts.map((account) => (
            <div key={account.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  <svg className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H9m0 0H7m2 0v-3a1 1 0 011-1h1a1 1 0 011 1v3M9 7h6m0 0v2m0-2h2m-2 2v2m0-2H9m8-2V5" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{account.account_name}</p>
                  <p className="text-sm text-gray-500">{account.account_number}</p>
                  <div className="flex items-center space-x-2 mt-1">
                    {account.is_default && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Predeterminada
                      </span>
                    )}
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      account.validation_status === 'valid' ? 'bg-green-100 text-green-800' :
                      account.validation_status === 'invalid' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {account.validation_status === 'valid' ? 'Válida' :
                       account.validation_status === 'invalid' ? 'Inválida' :
                       'Pendiente'}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {!account.is_default && (
                  <button
                    onClick={() => setAsDefault(account.id)}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    Establecer como predeterminada
                  </button>
                )}
                <button
                  onClick={() => deleteAccount(account.id)}
                  className="text-red-600 hover:text-red-800 text-sm"
                >
                  Eliminar
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default DHLAccountManager;
