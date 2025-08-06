import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const ContactModal = ({ isOpen, onClose, onSelectContact }) => {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState({});

  // Configurar axios para incluir el token
  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const fetchContacts = useCallback(async (searchTerm = '', pageNum = 1, favoritesOnly = false) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: pageNum,
        page_size: 10,
        ...(searchTerm && { search: searchTerm }),
        ...(favoritesOnly && { favorites: 'true' })
      });

      const response = await axios.get(`/api/contacts/?${params}`, {
        headers: getAuthHeaders()
      });

      if (response.data.success) {
        setContacts(response.data.data.contacts);
        setPagination(response.data.data.pagination);
      }
    } catch (error) {
      console.error('Error fetching contacts:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchContacts(search, page, showFavoritesOnly);
    }
  }, [isOpen, search, page, showFavoritesOnly, fetchContacts]);

  const handleSearch = (e) => {
    const term = e.target.value;
    setSearch(term);
    setPage(1);
  };

  const toggleFavorite = async (contactId, currentStatus) => {
    try {
      await axios.post(`/api/contacts/${contactId}/favorite/`, {}, {
        headers: getAuthHeaders()
      });
      
      // Actualizar el estado local
      setContacts(prev => 
        prev.map(contact => 
          contact.id === contactId 
            ? { ...contact, is_favorite: !currentStatus }
            : contact
        )
      );
    } catch (error) {
      console.error('Error toggling favorite:', error);
    }
  };

  const handleSelectContact = async (contact) => {
    try {
      // Registrar el uso del contacto
      await axios.post(`/api/contacts/${contact.id}/use/`, {}, {
        headers: getAuthHeaders()
      });
      
      // Mapear los datos del contacto al formato esperado por el formulario
      const contactData = {
        name: contact.name,
        company: contact.company || '',
        phone: contact.phone,
        email: contact.email,
        address: contact.address,
        city: contact.city,
        state: contact.state || '',
        postalCode: contact.postal_code,
        country: contact.country
      };
      
      onSelectContact(contactData);
      onClose();
    } catch (error) {
      console.error('Error using contact:', error);
      // Aun así seleccionar el contacto
      const contactData = {
        name: contact.name,
        company: contact.company || '',
        phone: contact.phone,
        email: contact.email,
        address: contact.address,
        city: contact.city,
        state: contact.state || '',
        postalCode: contact.postal_code,
        country: contact.country
      };
      
      onSelectContact(contactData);
      onClose();
    }
  };

  const handlePrevPage = () => {
    if (pagination.has_previous) {
      setPage(prev => prev - 1);
    }
  };

  const handleNextPage = () => {
    if (pagination.has_next) {
      setPage(prev => prev + 1);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-hidden">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            📞 Agenda de Contactos
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Controles de búsqueda y filtros */}
        <div className="mb-4 space-y-3">
          <div className="flex gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Buscar por nombre, empresa, email, teléfono o ciudad..."
                value={search}
                onChange={handleSearch}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-dhl-red"
              />
            </div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={showFavoritesOnly}
                onChange={(e) => {
                  setShowFavoritesOnly(e.target.checked);
                  setPage(1);
                }}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">Solo favoritos ⭐</span>
            </label>
          </div>
        </div>

        {/* Lista de contactos */}
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-dhl-red"></div>
              <p className="mt-2 text-gray-600">Cargando contactos...</p>
            </div>
          ) : contacts.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              {search ? 'No se encontraron contactos con esa búsqueda' : 'No tienes contactos guardados'}
            </div>
          ) : (
            <div className="max-h-96 overflow-y-auto">
              {contacts.map((contact) => (
                <div
                  key={contact.id}
                  className="p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => handleSelectContact(contact)}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium text-gray-900">{contact.name}</h3>
                        {contact.company && (
                          <span className="text-sm text-gray-600">({contact.company})</span>
                        )}
                        <div className="flex items-center gap-1">
                          {contact.is_favorite && (
                            <span className="text-yellow-500" title="Favorito">⭐</span>
                          )}
                          {contact.usage_count > 0 && (
                            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                              Usado {contact.usage_count} veces
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="space-y-1 text-sm text-gray-600">
                        <div className="flex items-center gap-4">
                          <span>📧 {contact.email}</span>
                          <span>📱 {contact.phone}</span>
                        </div>
                        <div>📍 {contact.address}, {contact.city}, {contact.country}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleFavorite(contact.id, contact.is_favorite);
                        }}
                        className={`p-1 rounded hover:bg-gray-200 ${
                          contact.is_favorite ? 'text-yellow-500' : 'text-gray-400'
                        }`}
                        title={contact.is_favorite ? 'Quitar de favoritos' : 'Agregar a favoritos'}
                      >
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.719c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Paginación */}
        {pagination.total_pages > 1 && (
          <div className="mt-4 flex justify-between items-center">
            <div className="text-sm text-gray-600">
              Página {pagination.current_page} de {pagination.total_pages} 
              ({pagination.total_count} contactos total)
            </div>
            <div className="flex gap-2">
              <button
                onClick={handlePrevPage}
                disabled={!pagination.has_previous}
                className="px-3 py-1 bg-gray-200 text-gray-700 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300"
              >
                Anterior
              </button>
              <button
                onClick={handleNextPage}
                disabled={!pagination.has_next}
                className="px-3 py-1 bg-gray-200 text-gray-700 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300"
              >
                Siguiente
              </button>
            </div>
          </div>
        )}

        {/* Botones de acción */}
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
};

export default ContactModal;
