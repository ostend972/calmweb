
import React from 'react';
import { Tab } from '../types';
import { ICONS } from '../constants';

interface NavTabsProps {
    activeTab: Tab;
    setActiveTab: (tab: Tab) => void;
}

const NavTabs: React.FC<NavTabsProps> = ({ activeTab, setActiveTab }) => {
    const tabs = [
        { id: Tab.Dashboard, label: 'Tableau de Bord', icon: ICONS.DASHBOARD },
        { id: Tab.Configuration, label: 'Configuration', icon: ICONS.CONFIG },
        { id: Tab.Logs, label: 'Journaux', icon: ICONS.LOGS },
        { id: Tab.Stats, label: 'Statistiques', icon: ICONS.STATS },
    ];

    return (
        <nav className="mt-6">
            <div className="border-b border-calm-gray-700">
                <div className="-mb-px flex space-x-4" aria-label="Tabs">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
                                ${activeTab === tab.id
                                    ? 'border-calm-blue-500 text-calm-blue-500'
                                    : 'border-transparent text-calm-gray-400 hover:text-calm-gray-200 hover:border-calm-gray-600'
                                }
                            `}
                        >
                            {tab.icon}
                            {tab.label}
                        </button>
                    ))}
                </div>
            </div>
        </nav>
    );
};

export default NavTabs;
