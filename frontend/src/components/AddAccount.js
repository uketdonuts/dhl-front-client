import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const LOCAL_KEY = 'dhl_accounts';

export default function AddAccount() {
  const [account, setAccount] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = account.trim();
    if (!/^\d{9,}$/.test(trimmed)) {
      setError('Debe ser un número de cuenta válido (mínimo 9 dígitos)');
      return;
    }
    const stored = JSON.parse(localStorage.getItem(LOCAL_KEY)) || [];
    if (stored.includes(trimmed)) {
      setError('La cuenta ya existe');
      return;
    }
    stored.push(trimmed);
    localStorage.setItem(LOCAL_KEY, JSON.stringify(stored));
    navigate(-1); // Volver atrás
  };

  return (
    <div style={{ maxWidth: 400, margin: '2rem auto' }}>
      <h2>Agregar nueva cuenta DHL</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={account}
          onChange={e => setAccount(e.target.value)}
          placeholder="Número de cuenta"
          style={{ width: '100%', padding: 8, marginBottom: 8 }}
        />
        {error && <div style={{ color: 'red', marginBottom: 8 }}>{error}</div>}
        <button type="submit">Agregar</button>
        <button type="button" onClick={() => navigate(-1)} style={{ marginLeft: 8 }}>
          Cancelar
        </button>
      </form>
    </div>
  );
}
