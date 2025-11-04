#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTML templates for the CalmWeb dashboard.
Provides the embedded HTML dashboard interface.
"""

def get_dashboard_html():
    """Return the complete HTML dashboard interface."""
    return """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CalmWeb - Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .stat-label {
            color: #666;
            font-size: 1.1em;
        }

        .blocked { color: #e74c3c; }
        .allowed { color: #27ae60; }
        .total { color: #3498db; }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .panel {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }

        .panel h3 {
            margin-bottom: 20px;
            color: #2c3e50;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
        }

        .activity-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #ecf0f1;
        }

        .activity-item:last-child {
            border-bottom: none;
        }

        .status-blocked {
            background: #e74c3c;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
        }

        .status-allowed {
            background: #27ae60;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
        }

        .chart-container {
            margin-top: 20px;
            height: 200px;
            background: #f8f9fa;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
        }

        .refresh-info {
            text-align: center;
            color: white;
            margin-top: 20px;
            opacity: 0.8;
        }

        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🛡️ CalmWeb Dashboard</h1>
            <p>Web Filtering Protection Status</p>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number blocked" id="blocked-count">-</div>
                <div class="stat-label">Requests Blocked Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-number allowed" id="allowed-count">-</div>
                <div class="stat-label">Requests Allowed Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-number total" id="total-count">-</div>
                <div class="stat-label">Total Requests</div>
            </div>
        </div>

        <div class="main-content">
            <div class="panel">
                <h3>📊 Recent Activity</h3>
                <div id="recent-activity">
                    <div style="text-align: center; color: #666; margin: 20px 0;">
                        Loading activity data...
                    </div>
                </div>
            </div>

            <div class="panel">
                <h3>🏆 Top Blocked Domains</h3>
                <div id="top-blocked">
                    <div style="text-align: center; color: #666; margin: 20px 0;">
                        Loading blocked domains...
                    </div>
                </div>
            </div>
        </div>

        <div class="refresh-info">
            ⟳ Dashboard updates automatically every 5 seconds
        </div>
    </div>

    <script>
        function updateDashboard() {
            fetch('/data.json')
                .then(response => response.json())
                .then(data => {
                    // Update statistics
                    document.getElementById('blocked-count').textContent = data.blocked_today || 0;
                    document.getElementById('allowed-count').textContent = data.allowed_today || 0;
                    document.getElementById('total-count').textContent = data.total_requests || 0;

                    // Update recent activity
                    const activityContainer = document.getElementById('recent-activity');
                    if (data.recent_activity && data.recent_activity.length > 0) {
                        activityContainer.innerHTML = data.recent_activity.slice(0, 10).map(item => `
                            <div class="activity-item">
                                <div>
                                    <strong>${item.domain}</strong><br>
                                    <small>${item.timestamp}</small>
                                </div>
                                <span class="status-${item.action.toLowerCase()}">${item.action}</span>
                            </div>
                        `).join('');
                    } else {
                        activityContainer.innerHTML = '<div style="text-align: center; color: #666;">No recent activity</div>';
                    }

                    // Update top blocked domains
                    const blockedContainer = document.getElementById('top-blocked');
                    if (data.blocked_domains_count && Object.keys(data.blocked_domains_count).length > 0) {
                        const sortedDomains = Object.entries(data.blocked_domains_count)
                            .sort(([,a], [,b]) => b - a)
                            .slice(0, 10);

                        blockedContainer.innerHTML = sortedDomains.map(([domain, count]) => `
                            <div class="activity-item">
                                <div><strong>${domain}</strong></div>
                                <span style="color: #e74c3c; font-weight: bold;">${count}x</span>
                            </div>
                        `).join('');
                    } else {
                        blockedContainer.innerHTML = '<div style="text-align: center; color: #666;">No blocked domains yet</div>';
                    }
                })
                .catch(error => {
                    console.error('Error updating dashboard:', error);
                });
        }

        // Initial load
        updateDashboard();

        // Auto-refresh every 5 seconds
        setInterval(updateDashboard, 5000);
    </script>
</body>
</html>"""