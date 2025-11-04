
import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import NavTabs from './components/NavTabs';
import Dashboard from './components/Dashboard';
import Configuration from './components/Configuration';
import Logs from './components/Logs';
import Stats from './components/Stats';
import { Tab } from './types';
import { toggleProtection, getProtectionStatus } from './services/api';

const App: React.FC = () => {
    const [isProtectionActive, setIsProtectionActive] = useState(true);
    const [activeTab, setActiveTab] = useState<Tab>(Tab.Dashboard);

    // Charger le statut de protection au démarrage et gérer les paramètres URL
    useEffect(() => {
        const loadProtectionStatus = async () => {
            try {
                const status = await getProtectionStatus();
                setIsProtectionActive(status.protection_enabled);
            } catch (error) {
                console.error('Erreur lors du chargement du statut de protection:', error);
                // Garder la valeur par défaut (true) en cas d'erreur
            }
        };

        // Vérifier les paramètres URL pour l'onglet initial
        const urlParams = new URLSearchParams(window.location.search);
        const tabParam = urlParams.get('tab');

        if (tabParam) {
            switch (tabParam) {
                case 'logs':
                    setActiveTab(Tab.Logs);
                    break;
                case 'config':
                    setActiveTab(Tab.Configuration);
                    break;
                case 'stats':
                    setActiveTab(Tab.Stats);
                    break;
                case 'dashboard':
                default:
                    setActiveTab(Tab.Dashboard);
                    break;
            }
        }

        loadProtectionStatus();
    }, []);

    // Fonction pour basculer la protection
    const handleToggleProtection = async () => {
        try {
            const result = await toggleProtection();
            if (result.success) {
                setIsProtectionActive(result.protection_enabled);
                console.log(result.message);
            } else {
                console.error('Erreur lors du basculement de la protection');
            }
        } catch (error) {
            console.error('Erreur lors du basculement de la protection:', error);
        }
    };

    const renderTabContent = () => {
        switch (activeTab) {
            case Tab.Dashboard:
                return <Dashboard />;
            case Tab.Configuration:
                return <Configuration />;
            case Tab.Logs:
                return <Logs />;
            case Tab.Stats:
                return <Stats />;
            default:
                return <Dashboard />;
        }
    };

    return (
        <div className="min-h-screen bg-calm-gray-900 text-calm-gray-200 font-sans">
            <div className="container mx-auto p-4 md:p-8">
                <Header
                    isProtectionActive={isProtectionActive}
                    onToggleProtection={handleToggleProtection}
                />
                <NavTabs activeTab={activeTab} setActiveTab={setActiveTab} />
                <main className="mt-6">
                    {renderTabContent()}
                </main>
            </div>
        </div>
    );
};

export default App;
