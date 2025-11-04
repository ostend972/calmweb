
import React from 'react';

interface StatCardProps {
    icon: React.ReactNode;
    value: string | number;
    label: string;
}

const StatCard: React.FC<StatCardProps> = ({ icon, value, label }) => {
    return (
        <div className="bg-calm-gray-800 p-6 rounded-lg shadow-lg flex items-center space-x-4 transition-transform hover:scale-105">
            <div>{icon}</div>
            <div>
                <h3 className="text-3xl font-bold text-calm-gray-100">{value}</h3>
                <p className="text-sm text-calm-gray-400">{label}</p>
            </div>
        </div>
    );
};

export default StatCard;
