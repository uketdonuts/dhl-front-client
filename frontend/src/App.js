import React from 'react';
import './App.css';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import Navigation from './components/Navigation';
import { AuthProvider, useAuth } from './contexts/AuthContext';

function AppContent() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="App">
      {isAuthenticated ? (
        <>
          <Navigation />
          <Dashboard />
        </>
      ) : (
        <Login />
      )}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App; 