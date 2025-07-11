import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const LOCAL_KEY = 'dhl_accounts';
const DEFAULT_ACCOUNTS = [
  '706065602',
  '706091269',
  '959390223',
  '963594404',
];

export default function AccountDropdown({ value, onChange }) {
  const [accounts, setAccounts] = useState([]);
  const navigate = useNavigate();

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
    onChange(e.target.value);
  };

  const handleAddAccount = () => {
    navigate('/add-account');
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <select value={value} onChange={handleChange} required>
        {accounts.map(acc => (
          <option key={acc} value={acc}>{acc}</option>
        ))}
      </select>
      <button type="button" onClick={handleAddAccount} style={{ padding: '0 8px' }}>
        + Nueva cuenta
      </button>
    </div>
  );
}
