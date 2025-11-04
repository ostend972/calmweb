
import React, { useState, useMemo, useEffect } from 'react';
import { LogEntry, LogType } from '../types';
import { fetchLogs } from '../services/api';

const parseLogString = (logString: string, index: number): LogEntry => {
    // Format CalmWeb: [12:36:35] ✅ [Proxy ALLOW HTTPS] media.discordapp.net
    const match = logString.match(/^\[(.*?)\]\s*(.*?)$/);

    if (!match) {
        return { id: Date.now() + index, timestamp: "N/A", type: LogType.Error, message: logString };
    }

    const [, timestamp, fullMessage] = match;
    let type: LogType;

    // Détecter le type selon les icônes et mots-clés
    if (fullMessage.includes('🚫') || fullMessage.includes('BLOCK')) {
        type = LogType.Blocked;
    } else if (fullMessage.includes('✅') || fullMessage.includes('ALLOW') || fullMessage.includes('BYPASS')) {
        type = LogType.Allowed;
    } else if (fullMessage.includes('❌') || fullMessage.includes('Error') || fullMessage.includes('ERROR')) {
        type = LogType.Error;
    } else {
        type = LogType.Allowed; // Par défaut pour les messages informatifs
    }

    return {
        id: Date.now() + index,
        timestamp,
        type,
        message: fullMessage,
    };
};

const Logs: React.FC = () => {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [filter, setFilter] = useState<string>('all');
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [isCleared, setIsCleared] = useState<boolean>(false);

    useEffect(() => {
        const loadLogs = async () => {
            try {
                if (loading) setLoading(true);
                const rawLogs = await fetchLogs();
                const parsedLogs = rawLogs.map(parseLogString).reverse();
                setLogs(parsedLogs);
                setError(null);
            } catch (err) {
                setError('Failed to fetch logs.');
                console.error(err);
            } finally {
                if (loading) setLoading(false);
            }
        };

        loadLogs();
        // Auto-refresh logs every 5 seconds pour plus de fluidité
        const interval = setInterval(loadLogs, 5000);
        return () => clearInterval(interval);
    }, []);

    const filteredLogs = useMemo(() => {
        if (isCleared) return [];
        if (filter === 'all') return logs;
        return logs.filter(log => log.type === filter);
    }, [logs, filter, isCleared]);

    const getBadgeClass = (type: LogType) => {
        switch (type) {
            case LogType.Allowed: return 'bg-green-900 text-green-300';
            case LogType.Blocked: return 'bg-red-900 text-red-300';
            case LogType.Error: return 'bg-yellow-900 text-yellow-300';
        }
    };
    
    const exportLogs = () => {
        const csvContent = "data:text/csv;charset=utf-8," 
            + ["Timestamp", "Type", "Message"].join(",") + "\n"
            + filteredLogs.map(e => `"${e.timestamp}","${e.type}","${e.message}"`).join("\n");
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "calmweb_logs.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div className="bg-calm-gray-800 p-6 rounded-lg shadow-lg transition-all duration-300">
            <div className="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
                <h3 className="text-xl font-bold">📋 Journaux d'Activité</h3>
                <div className="flex items-center space-x-2">
                    <select
                        id="log-filter"
                        value={filter}
                        onChange={e => setFilter(e.target.value)}
                        className="bg-calm-gray-700 text-calm-gray-200 border border-calm-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-calm-blue-500 focus:outline-none"
                    >
                        <option value="all">Tous</option>
                        <option value="blocked">Bloqués</option>
                        <option value="allowed">Autorisés</option>
                        <option value="error">Erreurs</option>
                    </select>
                    <button
                        onClick={() => {
                            setLogs([]);
                            setIsCleared(true);
                        }}
                        className="bg-calm-red hover:bg-red-600 text-white font-semibold px-4 py-2 rounded-md transition-colors"
                    >
                        Effacer
                    </button>
                    <button
                        onClick={async () => {
                            setIsCleared(false);
                            setLoading(true);
                            try {
                                const rawLogs = await fetchLogs();
                                const parsedLogs = rawLogs.map(parseLogString).reverse();
                                setLogs(parsedLogs);
                                setError(null);
                            } catch (err) {
                                setError('Failed to refresh logs.');
                                console.error(err);
                            } finally {
                                setLoading(false);
                            }
                        }}
                        className="bg-calm-gray-600 hover:bg-calm-gray-500 text-white font-semibold px-4 py-2 rounded-md transition-colors"
                    >
                        Actualiser
                    </button>
                    <button onClick={exportLogs} className="bg-calm-blue-600 hover:bg-calm-blue-500 text-white font-semibold px-4 py-2 rounded-md transition-colors">Exporter</button>
                </div>
            </div>

            <div className="logs-container overflow-y-auto h-[60vh] pr-2">
                {loading && <div className="text-center">Chargement des journaux...</div>}
                {error && <div className="text-center text-calm-red">{error}</div>}
                {!loading && !error && (
                     <div className="font-mono text-sm space-y-2 transition-all duration-300">
                        {filteredLogs.length > 0 ? filteredLogs.map(log => (
                            <div key={log.id} className="flex items-start p-2 rounded-md hover:bg-calm-gray-700/50 transition-all duration-200 animate-in fade-in slide-in-from-top-1">
                                <span className="text-calm-gray-400 mr-4 whitespace-nowrap">{log.timestamp}</span>
                                <span className={`px-2 py-0.5 rounded-full text-xs font-semibold mr-4 uppercase transition-all duration-200 ${getBadgeClass(log.type)}`}>
                                    {log.type}
                                </span>
                                <span className="text-calm-gray-200 flex-1 break-all">{log.message}</span>
                            </div>
                        )) : <div className="text-center text-calm-gray-400">Aucun journal à afficher.</div>}
                     </div>
                )}
            </div>
        </div>
    );
};

export default Logs;
