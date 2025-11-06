
import React from 'react';

interface HeaderProps {
    isProtectionActive: boolean;
    onToggleProtection: () => void;
}

const Header: React.FC<HeaderProps> = ({ isProtectionActive, onToggleProtection }) => {
    return (
        <header className="flex flex-col md:flex-row justify-between items-center pb-6 border-b border-calm-gray-700">
            <div className="flex items-center mb-4 md:mb-0">
                <img src="/calmweb-logo.png" alt="CalmWeb Logo" className="h-12 w-12 rounded-lg mr-4" />
                <h1 className="text-2xl md:text-3xl font-bold text-calm-gray-100">Tableau de Bord CalmWeb</h1>
            </div>
            <div className="flex items-center bg-calm-gray-800 p-2 rounded-lg">
                <div className="flex items-center mr-4">
                    <span className={`h-3 w-3 rounded-full mr-2 ${isProtectionActive ? 'bg-calm-green animate-pulse' : 'bg-calm-red'}`}></span>
                    <span className="text-sm font-medium">{isProtectionActive ? 'Protection Active' : 'Protection Inactive'}</span>
                </div>
                <button 
                    onClick={onToggleProtection}
                    className={`px-4 py-2 text-sm font-semibold rounded-md transition-colors ${isProtectionActive ? 'bg-calm-red hover:bg-red-600' : 'bg-calm-green hover:bg-green-600'} text-white`}
                >
                    {isProtectionActive ? 'Désactiver' : 'Activer'}
                </button>
            </div>
        </header>
    );
};

export default Header;
