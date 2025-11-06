
import { DashboardData } from '../types';

const API_BASE_URL = 'http://127.0.0.1:8081';

const handleResponse = async (response: Response) => {
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`);
    }
    return response;
};

// Fetch dashboard stats
export const fetchDashboardData = async (): Promise<DashboardData> => {
    const response = await fetch(`${API_BASE_URL}/data.json`);
    await handleResponse(response);
    return response.json();
};

// Fetch activity logs
export const fetchLogs = async (): Promise<string[]> => {
    const response = await fetch(`${API_BASE_URL}/api/logs`);
    await handleResponse(response);
    return response.json();
};

// Fetch configuration file
export const fetchConfig = async (): Promise<string> => {
    const response = await fetch(`${API_BASE_URL}/api/config`);
    await handleResponse(response);
    return response.text();
};

// Save configuration file
export const saveConfig = async (config: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/api/config`, {
        method: 'POST',
        headers: {
            'Content-Type': 'text/plain; charset=utf-8',
        },
        body: config,
    });
    await handleResponse(response);
    const result = await response.json();
    if (!result.success) {
        throw new Error(result.message || 'Échec de la sauvegarde de la configuration.');
    }
};

// Fetch domains lists (blocked and allowed with external data)
export const fetchDomains = async (): Promise<{
    blocked: Array<{ domain: string; source: string; removable: boolean }>;
    allowed: Array<{ domain: string; source: string; removable: boolean }>;
    counts: {
        total_blocked: number;
        manual_blocked: number;
        external_blocked: number;
        total_allowed: number;
        manual_allowed: number;
        external_allowed: number;
    };
    display_limited: boolean;
}> => {
    const response = await fetch(`${API_BASE_URL}/api/domains`);
    await handleResponse(response);
    return response.json();
};

// Toggle protection on/off
export const toggleProtection = async (): Promise<{ success: boolean; protection_enabled: boolean; message: string }> => {
    const response = await fetch(`${API_BASE_URL}/api/protection/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    });
    await handleResponse(response);
    return response.json();
};

// Get current protection status
export const getProtectionStatus = async (): Promise<{ protection_enabled: boolean }> => {
    const response = await fetch(`${API_BASE_URL}/data.json`);
    await handleResponse(response);
    const data = await response.json();
    return { protection_enabled: data.protection_enabled !== false }; // Default to true if not specified
};

// Get current settings
export const getSettings = async (): Promise<{
    protection_enabled: boolean;
    block_ip_direct: boolean;
    block_http_traffic: boolean;
    block_http_other_ports: boolean;
}> => {
    const response = await fetch(`${API_BASE_URL}/api/settings`);
    await handleResponse(response);
    return response.json();
};

// Update settings
export const updateSettings = async (settings: {
    block_ip_direct?: boolean;
    block_http_traffic?: boolean;
    block_http_other_ports?: boolean;
}): Promise<{ success: boolean }> => {
    const response = await fetch(`${API_BASE_URL}/api/settings`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
    });
    await handleResponse(response);
    return response.json();
};

// Get update status
export const getUpdateStatus = async (): Promise<{
    status: string;
    last_update: string | null;
    last_update_human: string;
    error: string | null;
    next_update: string | null;
    update_interval_hours: number;
}> => {
    const response = await fetch(`${API_BASE_URL}/api/update/status`);
    await handleResponse(response);
    return response.json();
};

// Trigger manual update
export const triggerUpdate = async (): Promise<{ success: boolean; message: string }> => {
    const response = await fetch(`${API_BASE_URL}/api/update/trigger`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    });
    await handleResponse(response);
    return response.json();
};
