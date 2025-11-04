
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { fetchDashboardData } from '../services/api';
import { ICONS } from '../constants';

const StatCard: React.FC<{ icon: string; value: string; label: string; color?: string }> = ({ icon, value, label, color = "text-calm-gray-100" }) => (
    <div className="bg-calm-gray-800 p-6 rounded-lg shadow-lg flex items-center space-x-4 transition-all duration-300 hover:scale-105">
        <div className="text-4xl">{icon}</div>
        <div>
            <h3 className={`text-3xl font-bold transition-all duration-500 ${color}`}>{value}</h3>
            <p className="text-sm text-calm-gray-400">{label}</p>
        </div>
    </div>
);

const Stats: React.FC = () => {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const loadData = useCallback(async () => {
        try {
            if (loading) setLoading(true);
            const dashboardData = await fetchDashboardData();

            // Ne mettre à jour que si les données ont changé
            if (JSON.stringify(data?.lifetime_stats) !== JSON.stringify(dashboardData?.lifetime_stats)) {
                setData(dashboardData);
            }
            setError(null);
        } catch (err) {
            setError("Impossible de charger les statistiques.");
            console.error(err);
        } finally {
            if (loading) setLoading(false);
        }
    }, [data, loading]);

    useEffect(() => {
        loadData();

        // Actualiser toutes les 10 secondes pour plus de fluidité
        const interval = setInterval(loadData, 10000);
        return () => clearInterval(interval);
    }, [loadData]);

    if (loading) {
        return <div className="text-center p-10">Chargement des statistiques...</div>;
    }

    if (error) {
        return <div className="text-center p-10 text-calm-red">{error}</div>;
    }

    if (!data || !data.lifetime_stats || Object.keys(data.lifetime_stats).length === 0) {
        return <div className="text-center p-10">Statistiques à vie non disponibles. Redémarrez CalmWeb pour les initialiser.</div>;
    }

    const lifetimeStats = data.lifetime_stats;

    return (
        <div className="space-y-8 transition-all duration-300">
            {/* Titre */}
            <div className="transition-all duration-300">
                <h1 className="text-3xl font-bold text-calm-gray-100 mb-2">📈 Statistiques Depuis l'Installation</h1>
                <p className="text-calm-gray-400">Vue d'ensemble de l'activité de CalmWeb depuis sa première utilisation</p>
            </div>

            {/* Statistiques principales */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    icon={ICONS.BLOCKED}
                    value={lifetimeStats.total_blocked_lifetime?.toLocaleString('fr-FR') || '0'}
                    label="Sites bloqués au total"
                    color="text-calm-red"
                />
                <StatCard
                    icon={ICONS.ALLOWED}
                    value={lifetimeStats.total_allowed_lifetime?.toLocaleString('fr-FR') || '0'}
                    label="Sites autorisés au total"
                    color="text-calm-green"
                />
                <StatCard
                    icon={ICONS.REQUESTS}
                    value={lifetimeStats.total_requests_lifetime?.toLocaleString('fr-FR') || '0'}
                    label="Requêtes traitées au total"
                    color="text-calm-blue-500"
                />
                <StatCard
                    icon="📅"
                    value={lifetimeStats.days_since_installation?.toString() || '1'}
                    label="Jours depuis installation"
                />
            </div>

            {/* Moyennes et efficacité */}
            <div>
                <h2 className="text-2xl font-bold text-calm-gray-100 mb-4">⚡ Performance & Moyennes</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    <StatCard
                        icon="📊"
                        value={lifetimeStats.avg_requests_per_day?.toLocaleString('fr-FR') || '0'}
                        label="Requêtes/jour en moyenne"
                        color="text-yellow-400"
                    />
                    <StatCard
                        icon="🛡️"
                        value={`${lifetimeStats.blocked_percentage || 0}%`}
                        label="Taux de blocage global"
                        color="text-orange-500"
                    />
                    <StatCard
                        icon="🔢"
                        value={lifetimeStats.total_sessions?.toString() || '1'}
                        label="Sessions CalmWeb"
                    />
                    <StatCard
                        icon="⏰"
                        value={`${lifetimeStats.current_session_duration_hours || 0}h`}
                        label="Session actuelle"
                        color="text-purple-400"
                    />
                </div>
            </div>

            {/* Comparaison 24h vs Lifetime */}
            <div>
                <h2 className="text-2xl font-bold text-calm-gray-100 mb-4">📊 Comparaison Aujourd'hui vs Total</h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-calm-gray-800 p-6 rounded-lg shadow-lg">
                        <h3 className="text-lg font-semibold mb-4 text-calm-blue-400">Aujourd'hui (24h)</h3>
                        <div className="space-y-3">
                            <div className="flex justify-between">
                                <span>Sites bloqués:</span>
                                <span className="font-bold text-calm-red">{data.blocked_today?.toLocaleString('fr-FR') || '0'}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>Sites autorisés:</span>
                                <span className="font-bold text-calm-green">{data.allowed_today?.toLocaleString('fr-FR') || '0'}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>Total requêtes:</span>
                                <span className="font-bold">{data.total_requests?.toLocaleString('fr-FR') || '0'}</span>
                            </div>
                        </div>
                    </div>
                    <div className="bg-calm-gray-800 p-6 rounded-lg shadow-lg">
                        <h3 className="text-lg font-semibold mb-4 text-calm-purple-400">Depuis Installation</h3>
                        <div className="space-y-3">
                            <div className="flex justify-between">
                                <span>Sites bloqués:</span>
                                <span className="font-bold text-calm-red">{lifetimeStats.total_blocked_lifetime?.toLocaleString('fr-FR') || '0'}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>Sites autorisés:</span>
                                <span className="font-bold text-calm-green">{lifetimeStats.total_allowed_lifetime?.toLocaleString('fr-FR') || '0'}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>Total requêtes:</span>
                                <span className="font-bold">{lifetimeStats.total_requests_lifetime?.toLocaleString('fr-FR') || '0'}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Top domaines bloqués */}
            {lifetimeStats.top_blocked_domains_list && lifetimeStats.top_blocked_domains_list.length > 0 && (
                <div>
                    <h2 className="text-2xl font-bold text-calm-gray-100 mb-4">🏆 Top 10 des Domaines les Plus Bloqués</h2>
                    <div className="bg-calm-gray-800 p-6 rounded-lg shadow-lg">
                        <div className="space-y-3">
                            {lifetimeStats.top_blocked_domains_list.slice(0, 10).map((item: any, index: number) => (
                                <div key={index} className="flex justify-between items-center bg-calm-gray-700 p-4 rounded-md hover:bg-calm-gray-600 transition-colors">
                                    <div className="flex items-center space-x-3">
                                        <span className="bg-calm-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">
                                            {index + 1}
                                        </span>
                                        <span className="font-mono text-calm-gray-200">{item.domain}</span>
                                    </div>
                                    <span className="bg-calm-red text-calm-red-100 px-3 py-1 rounded-full text-sm font-semibold">
                                        {item.count.toLocaleString('fr-FR')} blocages
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Informations de session */}
            <div>
                <h2 className="text-2xl font-bold text-calm-gray-100 mb-4">ℹ️ Informations Système</h2>
                <div className="bg-calm-gray-800 p-6 rounded-lg shadow-lg">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                            <span className="text-calm-gray-400">Date d'installation:</span>
                            <span className="ml-2 font-mono">
                                {lifetimeStats.installation_date ?
                                    new Date(lifetimeStats.installation_date).toLocaleDateString('fr-FR') :
                                    'Inconnue'
                                }
                            </span>
                        </div>
                        <div>
                            <span className="text-calm-gray-400">Dernière mise à jour:</span>
                            <span className="ml-2 font-mono">
                                {lifetimeStats.last_updated ?
                                    new Date(lifetimeStats.last_updated).toLocaleString('fr-FR') :
                                    'Jamais'
                                }
                            </span>
                        </div>
                        <div>
                            <span className="text-calm-gray-400">Jours actifs:</span>
                            <span className="ml-2 font-bold">{lifetimeStats.days_active || 0} jours</span>
                        </div>
                        <div>
                            <span className="text-calm-gray-400">Session actuelle depuis:</span>
                            <span className="ml-2 font-mono">
                                {lifetimeStats.current_session_start ?
                                    new Date(lifetimeStats.current_session_start).toLocaleString('fr-FR') :
                                    'Inconnue'
                                }
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Stats;
