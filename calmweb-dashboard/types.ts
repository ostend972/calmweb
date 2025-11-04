
export enum Tab {
    Dashboard = 'dashboard',
    Configuration = 'config',
    Logs = 'logs',
    Stats = 'stats',
}

export enum LogType {
    Allowed = 'allowed',
    Blocked = 'blocked',
    Error = 'error',
}

export interface LogEntry {
    id: number;
    timestamp: string;
    type: LogType;
    message: string;
}

export interface ActivityEntry {
    id: number;
    timestamp: string;
    action: 'Allowed' | 'Blocked';
    domain: string;
    ip: string;
}

export interface ChartData {
    name: string;
    allowed: number;
    blocked: number;
}

export interface DashboardData {
  blocked_today: number;
  allowed_today: number;
  total_requests: number;
  recent_activity: ActivityEntry[];
  blocked_domains_count: { [domain: string]: number };
  activity_by_hour: ChartData[];
}
