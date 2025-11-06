
import React, { useState, useEffect } from 'react';
import { ICONS } from '../constants';
import { fetchConfig, saveConfig, fetchDomains, getSettings, updateSettings } from '../services/api';

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

    // Helper function to save domains to custom.cfg
    const saveDomainsToConfig = async (domainsToSave: string[]) => {
        const configLines = [
            '# CalmWeb Custom Configuration',
            '# Domaines manuels à bloquer (un par ligne)',
            '',
            '[BLOCK]'
        ];

        if (domainsToSave.length > 0) {
            domainsToSave.forEach(domain => {
                configLines.push(domain);
            });
        } else {
            configLines.push('# Aucun domaine manuel bloqué');
        }

        const configContent = configLines.join('\n');
        await saveConfig(configContent);
    };

    const handleAddDomain = async () => {
        if (inputValue) {
            // Check if domain already exists in any form (manual or external)
            const domainExists = domains.some(d => d.domain === inputValue) || manualDomains.includes(inputValue);

            if (!domainExists) {
                const newManualDomains = [...manualDomains, inputValue];

                // Add to manual domains list
                setManualDomains(newManualDomains);

                // Also add to the display list
                const newDomain = {
                    domain: inputValue,
                    source: 'manual',
                    removable: true
                };
                setDomains([...domains, newDomain]);

                // Auto-save to persist the change
                try {
                    await saveDomainsToConfig(newManualDomains);
                } catch (error) {
                    console.error('Failed to auto-save domain:', error);
                }
            }

            setInputValue('');
        }
    };

    const handleRemoveDomain = async (domainToRemove: string, isRemovable: boolean) => {
        if (isRemovable) {
            const newManualDomains = manualDomains.filter(domain => domain !== domainToRemove);

            // Remove from manual domains list
            setManualDomains(newManualDomains);

            // Also remove from the display list
            setDomains(domains.filter(domainObj => domainObj.domain !== domainToRemove));

            // Auto-save to persist the change
            try {
                await saveDomainsToConfig(newManualDomains);
            } catch (error) {
                console.error('Failed to auto-save after domain removal:', error);
            }
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

                // Charger les settings depuis la nouvelle API
                const settingsData = await getSettings();
                console.log('Settings from API:', settingsData); // Debug

                const configSettings = {
                    blockIpDirect: settingsData.block_ip_direct,
                    blockHttp: settingsData.block_http_traffic,
                    blockOtherPorts: settingsData.block_http_other_ports
                };

                console.log('Converted config settings:', configSettings); // Debug
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

        // Update only local state - no immediate save
        // Settings will be applied when user clicks "Sauvegarder"
        setSettings(prev => ({ ...prev, [id]: checked }));
        console.log(`Setting ${id} changed to ${checked} (will be saved on "Sauvegarder")`);
    };

    const handleSave = async () => {
        setSaveStatus('saving');
        try {
            // 1. Sauvegarder les paramètres de protection via l'API
            const parameterMap: { [key: string]: string } = {
                'blockIpDirect': 'block_ip_direct',
                'blockHttp': 'block_http_traffic',
                'blockOtherPorts': 'block_http_other_ports'
            };

            const settingsToSave: any = {};
            Object.entries(settings).forEach(([key, value]) => {
                const backendParam = parameterMap[key];
                if (backendParam) {
                    settingsToSave[backendParam] = value;
                }
            });

            await updateSettings(settingsToSave);
            console.log('Protection settings saved:', settingsToSave);

            // 2. Sauvegarder les domaines manuels bloqués dans custom.cfg
            const configLines = [
                '# CalmWeb Custom Configuration',
                '# Domaines manuels à bloquer (un par ligne)',
                '',
                '[BLOCK]'
            ];

            // Ajouter les domaines manuels bloqués (ou un commentaire si vide)
            if (manualBlockedDomains.length > 0) {
                manualBlockedDomains.forEach(domain => {
                    configLines.push(domain);
                });
            } else {
                configLines.push('# Aucun domaine manuel bloqué');
            }

            // Note: La whitelist reste en cache (non sauvegardée)
            const configContent = configLines.join('\n');
            await saveConfig(configContent);
            console.log('Domains and settings saved successfully');

            setSaveStatus('success');
            setTimeout(() => setSaveStatus('idle'), 3000);
        } catch (err) {
            setSaveStatus('error');
            console.error('Save error:', err);
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
