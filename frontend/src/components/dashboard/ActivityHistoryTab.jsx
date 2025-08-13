import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';

/**
 * Componente para la pestaña Historial de Actividades del sistema
 */
const ActivityHistoryTab = () => {
    const { user } = useAuth();
    const [activities, setActivities] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [filters, setFilters] = useState({
        username: '',
        action: '',
        status: '',
        date_from: '',
        date_to: '',
        page: 1,
        page_size: 20
    });
    const [pagination, setPagination] = useState(null);
    const [filterOptions, setFilterOptions] = useState({ actions: [], statuses: [] });
    const [activeTab, setActiveTab] = useState('activities'); // 'activities' o 'stats'

    const fetchActivities = useCallback(async () => {
        setLoading(true);
        setError('');
        
        try {
            const token = localStorage.getItem('token');
            const queryParams = new URLSearchParams();
            
            // Agregar filtros no vacíos
            Object.entries(filters).forEach(([key, value]) => {
                if (value && value !== '') {
                    queryParams.append(key, value);
                }
            });
            
            const response = await fetch(`/api/user-activities/?${queryParams}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                setActivities(data.data.activities);
                setPagination(data.data.pagination);
                setFilterOptions(data.data.filters);
            } else {
                setError('Ha ocurrido un error');
            }
        } catch (err) {
            setError('Ha ocurrido un error');
            console.error('Error:', err);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    useEffect(() => {
        if (user) {
            fetchActivities();
            fetchStats();
        }
    }, [user, filters.page, fetchActivities]);

    const fetchStats = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/user-activities/stats/', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                setStats(data.data);
            }
        } catch (err) {
            console.error('Error fetching stats:', err);
        }
    };

    const handleFilterChange = (key, value) => {
        setFilters(prev => ({
            ...prev,
            [key]: value,
            page: 1 // Reset a la primera página al cambiar filtros
        }));
    };

    const handleSearch = () => {
        fetchActivities();
    };

    const handleClearFilters = () => {
        setFilters({
            username: '',
            action: '',
            status: '',
            date_from: '',
            date_to: '',
            page: 1,
            page_size: 20
        });
    };

    const handlePageChange = (newPage) => {
        setFilters(prev => ({ ...prev, page: newPage }));
    };

    const getStatusColor = (status) => {
        const colors = {
            success: 'text-green-600 bg-green-100',
            error: 'text-red-600 bg-red-100',
            warning: 'text-yellow-600 bg-yellow-100',
            info: 'text-blue-600 bg-blue-100'
        };
        return colors[status] || 'text-gray-600 bg-gray-100';
    };

    const getActionIcon = (action) => {
        const icons = {
            login: '🔑',
            logout: '🚪',
            create_shipment: '📦',
            view_shipment: '👁️',
            edit_shipment: '✏️',
            delete_shipment: '🗑️',
            track_shipment: '📍',
            get_rate: '💰',
            compare_rates: '⚖️',
            create_account: '➕',
            edit_account: '✏️',
            delete_account: '❌',
            landed_cost_quote: '💰',
            epod_request: '📄',
            api_error: '⚠️',
            system_action: '⚙️'
        };
        return icons[action] || '📋';
    };

    // Helper: pretty print JSON safely, truncated
    const JsonPreview = ({ data, maxLength = 1200 }) => {
        // Hooks must be called before any early return
        const [expanded, setExpanded] = useState(false);
        if (!data) return null;

        let json = '';
        try {
            json = JSON.stringify(data, null, 2);
        } catch (_) {
            json = String(data);
        }
        const isLong = json.length > maxLength;
        const shown = expanded || !isLong ? json : json.slice(0, maxLength) + '...';
        return (
            <div className="mt-2 bg-gray-50 rounded border border-gray-200 text-xs font-mono whitespace-pre-wrap break-all p-3">
                {shown}
                {isLong && (
                    <button onClick={() => setExpanded(!expanded)} className="ml-2 text-blue-600 hover:underline">
                        {expanded ? 'Ver menos' : 'Ver más'}
                    </button>
                )}
            </div>
        );
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-gray-900">
                    Historial de Actividades
                </h2>
                <p className="mt-1 text-gray-600">
                    {user?.is_superuser 
                        ? 'Monitorea las actividades de todos los usuarios del sistema'
                        : 'Revisa tu historial de actividades en el sistema'
                    }
                </p>
            </div>

            {/* Tabs */}
            <div>
                <nav className="flex space-x-8">
                    <button
                        onClick={() => setActiveTab('activities')}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                            activeTab === 'activities'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        Actividades
                    </button>
                    <button
                        onClick={() => setActiveTab('stats')}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                            activeTab === 'stats'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        Estadísticas
                    </button>
                </nav>
            </div>

            {activeTab === 'activities' && (
                <>
                    {/* Filtros */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-lg font-medium text-gray-900 mb-4">Filtros</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            {user?.is_superuser && (
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Usuario
                                    </label>
                                    <input
                                        type="text"
                                        value={filters.username}
                                        onChange={(e) => handleFilterChange('username', e.target.value)}
                                        placeholder="Nombre de usuario"
                                        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                    />
                                </div>
                            )}
                            
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Acción
                                </label>
                                <select
                                    value={filters.action}
                                    onChange={(e) => handleFilterChange('action', e.target.value)}
                                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                >
                                    <option value="">Todas las acciones</option>
                                    {filterOptions.actions.map(action => (
                                        <option key={action.value} value={action.value}>
                                            {action.label}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Estado
                                </label>
                                <select
                                    value={filters.status}
                                    onChange={(e) => handleFilterChange('status', e.target.value)}
                                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                >
                                    <option value="">Todos los estados</option>
                                    {filterOptions.statuses.map(status => (
                                        <option key={status.value} value={status.value}>
                                            {status.label}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Fecha desde
                                </label>
                                <input
                                    type="datetime-local"
                                    value={filters.date_from}
                                    onChange={(e) => handleFilterChange('date_from', e.target.value)}
                                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                />
                            </div>
                            
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Fecha hasta
                                </label>
                                <input
                                    type="datetime-local"
                                    value={filters.date_to}
                                    onChange={(e) => handleFilterChange('date_to', e.target.value)}
                                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                />
                            </div>
                        </div>
                        
                        <div className="mt-4 flex space-x-3">
                            <button
                                onClick={handleSearch}
                                disabled={loading}
                                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
                            >
                                {loading ? 'Buscando...' : 'Buscar'}
                            </button>
                            <button
                                onClick={handleClearFilters}
                                className="bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300"
                            >
                                Limpiar filtros
                            </button>
                        </div>
                    </div>

                    {/* Error message */}
                    {error && (
                        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                            {error}
                        </div>
                    )}

                    {/* Lista de actividades */}
                    <div className="bg-white rounded-lg shadow overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-200">
                            <h3 className="text-lg font-medium text-gray-900">Actividades</h3>
                            {pagination && (
                                <p className="text-sm text-gray-600">
                                    {pagination.total_items} actividades encontradas
                                </p>
                            )}
                        </div>
                        
                        {loading ? (
                            <div className="flex justify-center py-8">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                            </div>
                        ) : activities.length === 0 ? (
                            <div className="text-center py-8 text-gray-500">
                                No se encontraron actividades
                            </div>
                        ) : (
                            <div className="divide-y divide-gray-200">
                                {activities.map((activity) => (
                                    <div key={activity.id} className="p-6 hover:bg-gray-50">
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-start space-x-3">
                                                <div className="text-2xl">
                                                    {getActionIcon(activity.action)}
                                                </div>
                                                <div className="flex-1">
                                                    <div className="flex items-center space-x-2">
                                                        <span className="font-medium text-gray-900">
                                                            {activity.action_display}
                                                        </span>
                                                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(activity.status)}`}>
                                                            {activity.status_display}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm text-gray-600 mt-1">
                                                        {activity.description}
                                                    </p>
                                                    <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                                                        {user?.is_superuser && (
                                                            <span>Usuario: {activity.user.username}</span>
                                                        )}
                                                        <span>{activity.created_at_formatted}</span>
                                                        {activity.ip_address && (
                                                            <span>IP: {activity.ip_address}</span>
                                                        )}
                                                        {activity.resource_type && (
                                                            <span>Recurso: {activity.resource_type}</span>
                                                        )}
                                                    </div>

                                                    {/* Payloads */}
                                                    {activity.metadata && (activity.metadata.request_payload || activity.metadata.response_payload) && (
                                                        <div className="mt-3 space-y-2">
                                                            {activity.metadata.request_payload && (
                                                                <div>
                                                                    <div className="text-xs font-semibold text-gray-700">Request</div>
                                                                    <JsonPreview data={activity.metadata.request_payload} />
                                                                </div>
                                                            )}
                                                            {activity.metadata.response_payload && (
                                                                <div>
                                                                    <div className="text-xs font-semibold text-gray-700">Response</div>
                                                                    <JsonPreview data={activity.metadata.response_payload} />
                                                                </div>
                                                            )}
                                                            {activity.metadata.raw_response_preview && (
                                                                <div>
                                                                    <div className="text-xs font-semibold text-gray-700">Respuesta cruda (preview)</div>
                                                                    <JsonPreview data={activity.metadata.raw_response_preview} />
                                                                </div>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                        
                        {/* Paginación */}
                        {pagination && pagination.total_pages > 1 && (
                            <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
                                <div className="flex-1 flex justify-between sm:hidden">
                                    <button
                                        onClick={() => handlePageChange(pagination.current_page - 1)}
                                        disabled={!pagination.has_previous}
                                        className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                                    >
                                        Anterior
                                    </button>
                                    <button
                                        onClick={() => handlePageChange(pagination.current_page + 1)}
                                        disabled={!pagination.has_next}
                                        className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                                    >
                                        Siguiente
                                    </button>
                                </div>
                                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                                    <div>
                                        <p className="text-sm text-gray-700">
                                            Mostrando página <span className="font-medium">{pagination.current_page}</span> de{' '}
                                            <span className="font-medium">{pagination.total_pages}</span>
                                        </p>
                                    </div>
                                    <div>
                                        <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                                            <button
                                                onClick={() => handlePageChange(pagination.current_page - 1)}
                                                disabled={!pagination.has_previous}
                                                className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                                            >
                                                Anterior
                                            </button>
                                            {/* Aquí podrías agregar números de página específicos */}
                                            <button
                                                onClick={() => handlePageChange(pagination.current_page + 1)}
                                                disabled={!pagination.has_next}
                                                className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                                            >
                                                Siguiente
                                            </button>
                                        </nav>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </>
            )}

            {activeTab === 'stats' && stats && (
                <div className="space-y-6">
                    {/* Resumen de estadísticas */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <div className="bg-white p-6 rounded-lg shadow">
                            <div className="text-2xl font-bold text-blue-600">{stats.summary.total_activities}</div>
                            <div className="text-sm text-gray-600">Actividades totales</div>
                        </div>
                        <div className="bg-white p-6 rounded-lg shadow">
                            <div className="text-2xl font-bold text-green-600">{stats.summary.success_rate}%</div>
                            <div className="text-sm text-gray-600">Tasa de éxito</div>
                        </div>
                        {user?.is_superuser && (
                            <div className="bg-white p-6 rounded-lg shadow">
                                <div className="text-2xl font-bold text-purple-600">{stats.summary.unique_users}</div>
                                <div className="text-sm text-gray-600">Usuarios únicos</div>
                            </div>
                        )}
                        <div className="bg-white p-6 rounded-lg shadow">
                            <div className="text-2xl font-bold text-orange-600">{stats.summary.period_days}</div>
                            <div className="text-sm text-gray-600">Días analizados</div>
                        </div>
                    </div>

                    {/* Gráficos y estadísticas adicionales */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Por acción */}
                        <div className="bg-white p-6 rounded-lg shadow">
                            <h3 className="text-lg font-medium text-gray-900 mb-4">Por Acción</h3>
                            <div className="space-y-2">
                                {Object.entries(stats.by_action).map(([action, count]) => (
                                    <div key={action} className="flex justify-between items-center">
                                        <span className="text-sm text-gray-600">
                                            {filterOptions.actions.find(a => a.value === action)?.label || action}
                                        </span>
                                        <span className="font-medium">{count}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Por estado */}
                        <div className="bg-white p-6 rounded-lg shadow">
                            <h3 className="text-lg font-medium text-gray-900 mb-4">Por Estado</h3>
                            <div className="space-y-2">
                                {Object.entries(stats.by_status).map(([statusKey, count]) => (
                                    <div key={statusKey} className="flex justify-between items-center">
                                        <span className={`text-sm px-2 py-1 rounded ${getStatusColor(statusKey)}`}>
                                            {filterOptions.statuses.find(s => s.value === statusKey)?.label || statusKey}
                                        </span>
                                        <span className="font-medium">{count}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Top usuarios (solo para superuser) */}
                    {user?.is_superuser && stats.top_users && stats.top_users.length > 0 && (
                        <div className="bg-white p-6 rounded-lg shadow">
                            <h3 className="text-lg font-medium text-gray-900 mb-4">Usuarios más activos</h3>
                            <div className="space-y-2">
                                {stats.top_users.map((topUser, index) => (
                                    <div key={topUser.username} className="flex justify-between items-center">
                                        <span className="text-sm text-gray-600">
                                            #{index + 1} {topUser.username}
                                        </span>
                                        <span className="font-medium">{topUser.activity_count} actividades</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default ActivityHistoryTab;
