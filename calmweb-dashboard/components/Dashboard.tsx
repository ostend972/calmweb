
import React, { useState, useEffect, useMemo } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend, BarChart, Bar, Cell } from 'recharts';
import StatCard from './StatCard';
import UpdateStatus from './UpdateStatus';
import { ICONS } from '../constants';
import { ActivityEntry, DashboardData } from '../types';
import { fetchDashboardData } from '../services/api';

const COLORS = ['#ef4444', '#f87171', '#fb923c', '#fca5a5', '#fdba74'];

const Dashboard: React.FC = () => {
    const [data, setData] = useState<DashboardData | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState<boolean>(true);

    const fetchData = async () => {
        try {
            const result = await fetchDashboardData();
            setData(result);
            setError(null);
        } catch (err) {
            setError('Échec du chargement des données du tableau de bord. Le serveur backend est-il en fonctionnement ?');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 3000); // 3 seconds pour plus de fluidité
        return () => clearInterval(interval);
    }, []);
    
    const transformedBlockedDomains = useMemo(() => {
        if (!data?.blocked_domains_count) return [];
        return Object.entries(data.blocked_domains_count)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 5);
    }, [data]);

    if (loading) {
        return <div className="text-center p-10">Chargement des données...</div>;
    }

    if (error) {
        return <div className="text-center p-10 text-calm-red">{error}</div>;
    }

    if (!data) {
        return <div className="text-center p-10">Aucune donnée à afficher.</div>;
    }

    return (
        <div className="space-y-6 transition-all duration-300">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard icon={ICONS.BLOCKED} value={data.blocked_today.toLocaleString('fr-FR')} label="Sites bloqués aujourd'hui" />
                <StatCard icon={ICONS.ALLOWED} value={data.allowed_today.toLocaleString('fr-FR')} label="Sites autorisés aujourd'hui" />
                <StatCard icon={ICONS.REQUESTS} value={data.total_requests.toLocaleString('fr-FR')} label="Requêtes totales" />
                <StatCard icon={ICONS.SECURITY} value="Élevé" label="Niveau de sécurité" />
            </div>

            <UpdateStatus />

            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                    <div className="lg:col-span-3 bg-calm-gray-800 p-6 rounded-lg shadow-lg">
                        <h3 className="text-lg font-semibold mb-4">Graphique horaire</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={data.activity_by_hour}>
                            <XAxis dataKey="name" stroke="#8f97a8" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis stroke="#8f97a8" fontSize={12} tickLine={false} axisLine={false} />
                            <Tooltip contentStyle={{ backgroundColor: '#1a2233', border: 'none', borderRadius: '0.5rem' }} />
                            <Legend />
                            <Line type="monotone" dataKey="allowed" name="Autorisés" stroke="#10b981" strokeWidth={2} dot={false} />
                            <Line type="monotone" dataKey="blocked" name="Bloqués" stroke="#ef4444" strokeWidth={2} dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
                <div className="lg:col-span-2 bg-calm-gray-800 p-6 rounded-lg shadow-lg">
                    <h3 className="text-lg font-semibold mb-4">Top des domaines bloqués</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart layout="vertical" data={transformedBlockedDomains} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                            <XAxis type="number" hide />
                            <YAxis type="category" dataKey="name" width={120} stroke="#d1d5db" tickLine={false} axisLine={false} style={{ fontSize: '12px' }}/>
                            <Tooltip cursor={{fill: 'rgba(255, 255, 255, 0.1)'}} contentStyle={{ backgroundColor: '#1a2233', border: 'none', borderRadius: '0.5rem' }} />
                            <Bar dataKey="value" name="Blocages" barSize={20} radius={[0, 10, 10, 0]}>
                                {transformedBlockedDomains.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="bg-calm-gray-800 p-6 rounded-lg shadow-lg">
                <h3 className="text-lg font-semibold mb-4">Activité Récente</h3>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left text-calm-gray-400">
                        <thead className="text-xs text-calm-gray-200 uppercase bg-calm-gray-700">
                            <tr>
                                <th scope="col" className="px-6 py-3">Heure</th>
                                <th scope="col" className="px-6 py-3">Action</th>
                                <th scope="col" className="px-6 py-3">Domaine</th>
                                <th scope="col" className="px-6 py-3">Adresse IP</th>
                            </tr>
                        </thead>
                        <tbody className="transition-all duration-300">
                            {data.recent_activity.map((activity) => (
                                <tr key={activity.id} className="border-b border-calm-gray-700 hover:bg-calm-gray-700/50 transition-all duration-200">
                                    <td className="px-6 py-4">{activity.timestamp}</td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded-full text-xs font-semibold transition-all duration-200 ${activity.action === 'Blocked' ? 'bg-red-900 text-red-300' : 'bg-green-900 text-green-300'}`}>
                                            {activity.action}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 font-mono">{activity.domain}</td>
                                    <td className="px-6 py-4 font-mono">{activity.ip}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
