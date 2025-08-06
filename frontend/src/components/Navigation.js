import React from 'react';
import { useAuth } from '../contexts/AuthContext';

const Navigation = () => {
  const { user, logout } = useAuth();

  return (
    <nav className="bg-white border-b border-corporate-200 shadow-soft sticky top-0 z-50">
      <div className="container-main">
        <div className="flex justify-between items-center h-16">
          {/* Logo y marca */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <div className="h-10 w-10 bg-dhl-yellow rounded-lg flex items-center justify-center shadow-soft">
                <span className="text-sm font-bold text-corporate-900">DHL</span>
              </div>
              <div className="flex flex-col">
                <span className="text-lg font-semibold text-corporate-900">
                  Front Client
                </span>
                <span className="text-xs text-corporate-500 -mt-1">
                  Express Shipping Platform
                </span>
              </div>
            </div>
          </div>
          
          {/* Usuario y acciones */}
          <div className="flex items-center space-x-4">
            {/* Información del usuario */}
            <div className="hidden md:flex items-center space-x-3">
              <div className="flex flex-col text-right">
                <span className="text-sm font-medium text-corporate-700">
                  {user?.username}
                </span>
                <span className="text-xs text-corporate-500">
                  Usuario activo
                </span>
              </div>
              <div className="h-8 w-8 bg-corporate-100 rounded-full flex items-center justify-center">
                <span className="text-sm font-medium text-corporate-700">
                  {user?.username?.charAt(0).toUpperCase()}
                </span>
              </div>
            </div>
            
            {/* Divisor */}
            <div className="hidden md:block h-6 w-px bg-corporate-200"></div>
            
            {/* Botón de cerrar sesión */}
            <button
              onClick={logout}
              className="btn btn-outline text-sm flex items-center space-x-2 hover:border-error-300 hover:text-error-600 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span className="hidden sm:inline">Cerrar Sesión</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation; 