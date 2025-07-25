import React from 'react';
import './App.css';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import Navigation from './components/Navigation';
import GitHubPagesDemo from './components/GitHubPagesDemo';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import AddAccount from './components/AddAccount';
import config from './config';

function AppContent({ selectedAccount, setSelectedAccount }) {
  const { isAuthenticated } = useAuth();

  return (
    <div className="App">
      {isAuthenticated ? (
        <>
          <Navigation />
          <Dashboard selectedAccount={selectedAccount} setSelectedAccount={setSelectedAccount} />
        </>
      ) : (
        <Login />
      )}
    </div>
  );
}

function App() {
  const [selectedAccount, setSelectedAccount] = React.useState('706065602');
  const currentMode = config.getCurrentMode();

  // Si estamos en GitHub Pages (sin backend), mostrar la demo estática
  if (!currentMode.hasBackend) {
    return (
      <Router basename="/dhl-front-client">
        <GitHubPagesDemo />
      </Router>
    );
  }

  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/add-account" element={<AddAccount />} />
          <Route
            path="/"
            element={<AppContent selectedAccount={selectedAccount} setSelectedAccount={setSelectedAccount} />}
          />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;