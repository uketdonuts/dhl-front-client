import React from 'react';
import { useAuth } from '../contexts/AuthContext';

const Navigation = () => {
  const { user, logout } = useAuth();

  return (
    <nav className="bg-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0 flex items-center">
              <div className="h-8 w-8 bg-dhl-yellow rounded flex items-center justify-center">
                <span className="text-sm font-bold text-gray-800">DHL</span>
              </div>
              <span className="ml-2 text-xl font-semibold text-gray-800">
                Front Client
              </span>
            </div>
          </div>
          
          <div className="flex items-center">
            <div className="ml-4 flex items-center md:ml-6">
              <div className="flex items-center space-x-4">
                <span className="text-gray-700">
                  Bienvenido, {user?.username}
                </span>
                <button
                  onClick={logout}
                  className="bg-dhl-red hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200"
                >
                  Cerrar Sesión
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation; 