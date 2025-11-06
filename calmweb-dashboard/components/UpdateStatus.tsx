import React, { useState, useEffect } from 'react';
import { ICONS } from '../constants';
import { getUpdateStatus, triggerUpdate } from '../services/api';

interface UpdateStatusData {
    status: string;
    last_update: string | null;
    last_update_human: string;
    error: string | null;
    next_update: string | null;
    update_interval_hours: number;
}

const UpdateStatus: React.FC = () => {
    const [updateStatus, setUpdateStatus] = useState<UpdateStatusData | null>(null);
    const [loading, setLoading] = useState(true);
    const [updating, setUpdating] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const loadUpdateStatus = async () => {
        try {
            const status = await getUpdateStatus();
            setUpdateStatus(status);
            setError(null);
        } catch (err) {
            setError('Échec du chargement du statut de mise à jour');
            console.error('Error loading update status:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadUpdateStatus();

        // Refresh status every 30 seconds
        const interval = setInterval(loadUpdateStatus, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleManualUpdate = async () => {
        if (updating) return;

        setUpdating(true);
        try {
            const result = await triggerUpdate();
            if (result.success) {
                // Reload status after successful update
                setTimeout(loadUpdateStatus, 2000);
            } else {
                setError(result.message || 'Échec de la mise à jour');
            }
        } catch (err) {
            setError('Échec du déclenchement de la mise à jour');
            console.error('Update error:', err);
        } finally {
            setUpdating(false);
        }
    };

    const getStatusIcon = () => {
        if (!updateStatus) return ICONS.CLOCK;

        switch (updateStatus.status) {
            case 'updating':
                return ICONS.REFRESH;
            case 'success':
                return ICONS.CHECK;
            case 'error':
                return ICONS.X;
            default:
                return ICONS.CLOCK;
        }
    };

    const getStatusColor = () => {
        if (!updateStatus) return 'text-calm-gray-400';

        switch (updateStatus.status) {
            case 'updating':
                return 'text-calm-blue-500';
            case 'success':
                return 'text-calm-green';
            case 'error':
                return 'text-calm-red';
            default:
                return 'text-calm-gray-400';
        }
    };

    const getStatusText = () => {
        if (!updateStatus) return 'Chargement...';

        switch (updateStatus.status) {
            case 'updating':
                return 'Mise à jour des listes...';
            case 'success':
                return 'Listes à jour';
            case 'error':
                return 'Échec de la mise à jour';
            case 'idle':
                return 'En attente de la prochaine mise à jour';
            default:
                return 'Statut inconnu';
        }
    };

    if (loading) {
        return (
            <div className="bg-calm-gray-800 p-4 rounded-lg">
                <div className="flex items-center space-x-2">
                    <div className="text-calm-gray-400">{ICONS.CLOCK}</div>
                    <span className="text-sm text-calm-gray-400">Chargement du statut de mise à jour...</span>
                </div>
            </div>
        );
    }

    if (error && !updateStatus) {
        return (
            <div className="bg-calm-gray-800 p-4 rounded-lg">
                <div className="flex items-center space-x-2">
                    <div className="text-calm-red">{ICONS.X}</div>
                    <span className="text-sm text-calm-red">{error}</span>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-calm-gray-800 p-4 rounded-lg">
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                    <div className={`${getStatusColor()} ${updateStatus?.status === 'updating' || updating ? 'animate-spin' : ''}`}>
                        {getStatusIcon()}
                    </div>
                    <div>
                        <div className="text-sm font-medium text-calm-gray-200">
                            {getStatusText()}
                        </div>
                        <div className="text-xs text-calm-gray-400">
                            {updateStatus?.last_update_human && (
                                <>Dernière mise à jour : {updateStatus.last_update_human}</>
                            )}
                            {updateStatus?.next_update && updateStatus.status !== 'updating' && (
                                <> • Suivante : {updateStatus.next_update}</>
                            )}
                        </div>
                        {updateStatus?.error && (
                            <div className="text-xs text-calm-red mt-1">
                                Erreur : {updateStatus.error}
                            </div>
                        )}
                    </div>
                </div>

                <button
                    onClick={handleManualUpdate}
                    disabled={updating || updateStatus?.status === 'updating'}
                    className={`px-3 py-1 text-xs rounded transition-colors ${
                        updating || updateStatus?.status === 'updating'
                            ? 'bg-calm-gray-600 text-calm-gray-400 cursor-not-allowed'
                            : 'bg-calm-blue-600 text-white hover:bg-calm-blue-500'
                    }`}
                    title="Mettre à jour manuellement les listes externes"
                >
                    {updating || updateStatus?.status === 'updating' ? (
                        <span className="flex items-center space-x-1">
                            <span className="animate-spin">{ICONS.REFRESH}</span>
                            <span>Mise à jour...</span>
                        </span>
                    ) : (
                        <span className="flex items-center space-x-1">
                            <span>{ICONS.REFRESH}</span>
                            <span>Mettre à jour</span>
                        </span>
                    )}
                </button>
            </div>

            {updateStatus && (
                <div className="mt-3 text-xs text-calm-gray-500">
                    Mise à jour automatique toutes les {updateStatus.update_interval_hours} heure{updateStatus.update_interval_hours !== 1 ? 's' : ''}
                </div>
            )}
        </div>
    );
};

export default UpdateStatus;