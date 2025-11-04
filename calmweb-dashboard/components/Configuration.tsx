
import React, { useState, useEffect } from 'react';
import { ICONS } from '../constants';
import { fetchConfig, saveConfig, fetchDomains } from '../services/api';

const ToggleSwitch: React.FC<{ id: string; checked: boolean; onChange: (e: React.ChangeEvent<HTMLInputElement>) => void; }> = ({ id, checked, onChange }) => (
    <label htmlFor={id} className="relative inline-flex items-center cursor-pointer">
        <input type="checkbox" id={id} className="sr-only peer" checked={checked} onChange={onChange} />
        <div className="w-11 h-6 bg-calm-gray-600 rounded-full peer peer-focus:ring-4 peer-focus:ring-calm-blue-600/50 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-calm-blue-600"></div>
    </label>
);

const DomainList: React.FC<{
    title: string;
    domains: Array<{ domain: string; source: string; removable: boolean }>;
    setDomains: React.Dispatch<React.SetStateAction<Array<{ domain: string; source: string; removable: boolean }>>>;
    placeholder: string;
    listType: 'blocked' | 'allowed';
    manualDomains: string[];
    setManualDomains: React.Dispatch<React.SetStateAction<string[]>>;
}> = ({ title, domains, setDomains, placeholder, listType, manualDomains, setManualDomains }) => {
    const [inputValue, setInputValue] = useState('');

    const handleAddDomain = () => {
        if (inputValue && !manualDomains.includes(inputValue)) {
            setManualDomains([...manualDomains, inputValue]);
            setInputValue('');
        }
    };

    const handleRemoveDomain = (domainToRemove: string, isRemovable: boolean) => {
        if (isRemovable) {
            setManualDomains(manualDomains.filter(domain => domain !== domainToRemove));
        }
    };

    return (
        <div className="bg-calm-gray-800 p-6 rounded-lg">
            <h4 className={`text-lg font-semibold mb-4 ${listType === 'blocked' ? 'text-calm-red' : 'text-calm-green'}`}>{title}</h4>
            <div className="flex space-x-2 mb-4">
                <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddDomain()}
                    placeholder={placeholder}
                    className="w-full bg-calm-gray-700 text-calm-gray-200 border border-calm-gray-600 rounded-md px-3 py-2 focus:ring-2 focus:ring-calm-blue-500 focus:outline-none"
                />
                <button
                    onClick={handleAddDomain}
                    className="bg-calm-blue-600 text-white px-4 py-2 rounded-md hover:bg-calm-blue-500 transition-colors font-semibold"
                >
                    Ajouter
                </button>
            </div>
            <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
                {domains.map((domainObj, index) => (
                    <div key={`${domainObj.domain}-${index}`} className="flex justify-between items-center bg-calm-gray-700 p-2 rounded-md">
                        <div className="flex items-center space-x-2">
                            <span className="font-mono">{domainObj.domain}</span>
                            <span className={`text-xs px-2 py-1 rounded ${
                                domainObj.source === 'external'
                                    ? 'bg-calm-blue-600 text-calm-blue-100'
                                    : 'bg-calm-gray-600 text-calm-gray-200'
                            }`}>
                                {domainObj.source === 'external' ? 'Externe' : 'Manuel'}
                            </span>
                        </div>
                        {domainObj.removable && (
                            <button
                                onClick={() => handleRemoveDomain(domainObj.domain, domainObj.removable)}
                                className="text-calm-gray-400 hover:text-calm-red transition-colors"
                            >
                                {ICONS.TRASH}
                            </button>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

const Configuration: React.FC = () => {
    const [settings, setSettings] = useState({
        blockIpDirect: true,
        blockHttp: true,
        blockOtherPorts: false,
    });
    const [blockedDomains, setBlockedDomains] = useState<Array<{ domain: string; source: string; removable: boolean }>>([]);
    const [allowedDomains, setAllowedDomains] = useState<Array<{ domain: string; source: string; removable: boolean }>>([]);
    const [manualBlockedDomains, setManualBlockedDomains] = useState<string[]>([]);
    const [manualAllowedDomains, setManualAllowedDomains] = useState<string[]>([]);
    const [domainStats, setDomainStats] = useState({
        total_blocked: 0,
        manual_blocked: 0,
        external_blocked: 0,
        total_allowed: 0,
        manual_allowed: 0,
        external_allowed: 0
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');

    useEffect(() => {
        const loadConfig = async () => {
            try {
                setLoading(true);

                // Charger la configuration depuis custom.cfg
                const configText = await fetchConfig();

                // Parser les settings depuis [OPTIONS] dans custom.cfg
                const lines = configText.split('\n');
                let inOptionsSection = false;
                const configSettings = {
                    blockIpDirect: true,
                    blockHttp: true,
                    blockOtherPorts: false
                }; // Valeurs par défaut

                for (const line of lines) {
                    const trimmedLine = line.trim();
                    if (trimmedLine === '[OPTIONS]') {
                        inOptionsSection = true;
                        continue;
                    }
                    if (trimmedLine.startsWith('[') && trimmedLine !== '[OPTIONS]') {
                        inOptionsSection = false;
                        continue;
                    }

                    if (inOptionsSection && trimmedLine.includes('=')) {
                        const [key, value] = trimmedLine.split('=').map(s => s.trim());
                        console.log(`Parsing config: ${key} = ${value}`); // Debug
                        switch (key) {
                            case 'block_ip_direct':
                                configSettings.blockIpDirect = value === '1';
                                console.log(`blockIpDirect set to: ${configSettings.blockIpDirect}`); // Debug
                                break;
                            case 'block_http_traffic':
                                configSettings.blockHttp = value === '1';
                                console.log(`blockHttp set to: ${configSettings.blockHttp}`); // Debug
                                break;
                            case 'block_http_other_ports':
                                configSettings.blockOtherPorts = value === '1';
                                console.log(`blockOtherPorts set to: ${configSettings.blockOtherPorts}`); // Debug
                                break;
                        }
                    }
                }

                console.log('Final config settings:', configSettings); // Debug
                setSettings(configSettings);

                // Charger les domaines via la nouvelle API
                const domainsData = await fetchDomains();
                setBlockedDomains(domainsData.blocked);
                setAllowedDomains(domainsData.allowed);
                setDomainStats(domainsData.counts);

                // Extraire les domaines manuels pour les inputs
                const manualBlocked = domainsData.blocked
                    .filter(d => d.source === 'manual')
                    .map(d => d.domain);
                const manualAllowed = domainsData.allowed
                    .filter(d => d.source === 'manual')
                    .map(d => d.domain);

                setManualBlockedDomains(manualBlocked);
                setManualAllowedDomains(manualAllowed);

                setError(null);
            } catch (err) {
                setError('Failed to load configuration.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        loadConfig();
    }, []);

    const handleToggle = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { id, checked } = e.target;
        setSettings(prev => ({ ...prev, [id]: checked }));
    };

    const handleSave = async () => {
        setSaveStatus('saving');
        try {
            // Construire le contenu de custom.cfg avec les sections appropriées
            const configLines = ['# CalmWeb Configuration', '# Domaines à bloquer (un par ligne)', '', '[BLOCK]'];

            // Ajouter les domaines manuels bloqués
            manualBlockedDomains.forEach(domain => {
                configLines.push(domain);
            });

            configLines.push('[WHITELIST]');

            // Ajouter les domaines manuels autorisés
            manualAllowedDomains.forEach(domain => {
                configLines.push(domain);
            });

            configLines.push('[OPTIONS]');
            configLines.push(`block_ip_direct = ${settings.blockIpDirect ? 1 : 0}`);
            configLines.push(`block_http_traffic = ${settings.blockHttp ? 1 : 0}`);
            configLines.push(`block_http_other_ports = ${settings.blockOtherPorts ? 1 : 0}`);

            const configContent = configLines.join('\n');
            await saveConfig(configContent);
            setSaveStatus('success');
            setTimeout(() => setSaveStatus('idle'), 3000);
        } catch (err) {
            setSaveStatus('error');
            console.error(err);
            setTimeout(() => setSaveStatus('idle'), 3000);
        }
    };
    
    if (loading) return <div className="text-center p-10">Chargement de la configuration...</div>;
    if (error) return <div className="text-center p-10 text-calm-red">{error}</div>;

    return (
        <div className="space-y-8">
            <div className="bg-calm-gray-800 p-6 rounded-lg shadow-lg">
                <h3 className="text-xl font-bold mb-6">🛡️ Paramètres de Protection</h3>
                <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h4 className="font-semibold">Bloquer l'accès direct par IP</h4>
                            <p className="text-sm text-calm-gray-400">Empêche l'accès aux sites via leur adresse IP.</p>
                        </div>
                        <ToggleSwitch id="blockIpDirect" checked={settings.blockIpDirect} onChange={handleToggle} />
                    </div>
                    <div className="flex items-center justify-between">
                        <div>
                            <h4 className="font-semibold">Bloquer le trafic HTTP non sécurisé</h4>
                            <p className="text-sm text-calm-gray-400">Force l'utilisation de HTTPS pour toutes les connexions.</p>
                        </div>
                        <ToggleSwitch id="blockHttp" checked={settings.blockHttp} onChange={handleToggle} />
                    </div>
                    <div className="flex items-center justify-between">
                        <div>
                            <h4 className="font-semibold">Bloquer les ports non standard</h4>
                            <p className="text-sm text-calm-gray-400">Limite les connexions aux ports web standards (80, 443).</p>
                        </div>
                        <ToggleSwitch id="blockOtherPorts" checked={settings.blockOtherPorts} onChange={handleToggle} />
                    </div>
                </div>
            </div>

            <div>
                <h3 className="text-xl font-bold mb-6">📝 Gestion des Listes</h3>

                {/* Statistiques des domaines */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-calm-gray-800 p-4 rounded-lg">
                        <div className="text-2xl font-bold text-calm-red">{domainStats.total_blocked.toLocaleString()}</div>
                        <div className="text-sm text-calm-gray-400">Domaines bloqués</div>
                        <div className="text-xs text-calm-gray-500">
                            {domainStats.external_blocked.toLocaleString()} externes + {domainStats.manual_blocked} manuels
                        </div>
                    </div>
                    <div className="bg-calm-gray-800 p-4 rounded-lg">
                        <div className="text-2xl font-bold text-calm-green">{domainStats.total_allowed.toLocaleString()}</div>
                        <div className="text-sm text-calm-gray-400">Domaines autorisés</div>
                        <div className="text-xs text-calm-gray-500">
                            {domainStats.external_allowed.toLocaleString()} externes + {domainStats.manual_allowed} manuels
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <DomainList
                        title="🚫 Liste de Blocage"
                        domains={blockedDomains}
                        setDomains={setBlockedDomains}
                        placeholder="exemple-malveillant.com"
                        listType="blocked"
                        manualDomains={manualBlockedDomains}
                        setManualDomains={setManualBlockedDomains}
                    />
                    <DomainList
                        title="✅ Liste Blanche"
                        domains={allowedDomains}
                        setDomains={setAllowedDomains}
                        placeholder="exemple-autorise.com"
                        listType="allowed"
                        manualDomains={manualAllowedDomains}
                        setManualDomains={setManualAllowedDomains}
                    />
                </div>
            </div>
            
            <div className="flex justify-end items-center mt-6">
                {saveStatus === 'success' && <span className="text-calm-green mr-4">Configuration sauvegardée !</span>}
                {saveStatus === 'error' && <span className="text-calm-red mr-4">Erreur lors de la sauvegarde.</span>}
                <button
                    onClick={handleSave}
                    disabled={saveStatus === 'saving'}
                    className="bg-calm-blue-600 text-white px-6 py-2 rounded-md hover:bg-calm-blue-500 transition-colors font-semibold disabled:bg-calm-gray-600 disabled:cursor-not-allowed"
                >
                    {saveStatus === 'saving' ? 'Sauvegarde...' : 'Sauvegarder'}
                </button>
            </div>
        </div>
    );
};

export default Configuration;
