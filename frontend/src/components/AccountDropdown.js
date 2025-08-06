import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const LOCAL_KEY = 'dhl_accounts';
const DEFAULT_ACCOUNTS = [
  '706065602',
  '706091269',
  '959390223',
  '963594404',
];

export default function AccountDropdown({ 
  value, 
  onChange, 
  selectedAccount, 
  setSelectedAccount 
}) {
  const [accounts, setAccounts] = useState([]);
  const navigate = useNavigate();

  // Determinar qué props usar (compatibilidad con ambas formas)
  const currentValue = value || selectedAccount || '';
  const currentOnChange = onChange || setSelectedAccount || (() => {});

  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem(LOCAL_KEY));
    if (stored && Array.isArray(stored) && stored.length > 0) {
      setAccounts(stored);
    } else {
      setAccounts(DEFAULT_ACCOUNTS);
      localStorage.setItem(LOCAL_KEY, JSON.stringify(DEFAULT_ACCOUNTS));
    }
  }, []);

  const handleChange = (e) => {
    const newValue = e.target.value;
    // Validar que la función onChange/setSelectedAccount sea una función antes de llamarla
    if (typeof currentOnChange === 'function') {
      currentOnChange(newValue);
    } else {
      console.error('AccountDropdown: onChange/setSelectedAccount prop is not a function');
    }
  };

  const handleAddAccount = () => {
    navigate('/add-account');
  };

  return (
    <div className="flex items-center space-x-3">
      {/* Label y cuenta activa */}
      <div className="flex items-center space-x-2">
        <svg className="w-5 h-5 text-corporate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <div className="flex flex-col">
          <span className="text-sm font-medium text-corporate-700">Cuenta DHL</span>
          <span className="text-xs text-corporate-500">Cuenta activa</span>
        </div>
      </div>

      {/* Selector de cuenta */}
      <div className="flex items-center space-x-2">
        <select 
          value={currentValue} 
          onChange={handleChange} 
          required
          className="form-input text-sm min-w-32 pr-8"
        >
          {accounts.map(acc => (
            <option key={acc} value={acc}>
              {acc}
            </option>
          ))}
        </select>

        {/* Botón para añadir cuenta */}
        <button 
          type="button" 
          onClick={handleAddAccount}
          className="btn btn-secondary text-sm flex items-center space-x-1"
          title="Agregar nueva cuenta DHL"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          <span className="hidden sm:inline">Nueva</span>
        </button>
      </div>
    </div>
  );
}
