#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API handlers for the CalmWeb dashboard.
Handles REST API endpoints for configuration and logs.
"""

import os
import json

from ..config.settings import INSTALL_DIR
from ..config.custom_config import get_custom_cfg_path
from ..utils.logging import log, log_buffer, _LOG_LOCK


def handle_config_api(handler):
    """Handle /api/config endpoint - read or write custom.cfg file."""
    try:
        cfg_path = get_custom_cfg_path(INSTALL_DIR)
        
        # GET request - read config
        if handler.command == 'GET':
            if os.path.exists(cfg_path):
                with open(cfg_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            else:
                content = "# custom.cfg file not found\n# Create a new configuration file here"

            handler.send_response(200)
            handler.send_header('Content-type', 'text/plain; charset=utf-8')
            handler.send_header('Access-Control-Allow-Origin', 'http://127.0.0.1:8081')
            handler.end_headers()
            handler.wfile.write(content.encode('utf-8'))
        
        # POST request - save config
        elif handler.command == 'POST':
            content_length = int(handler.headers.get('Content-Length', 0))
            new_config = handler.rfile.read(content_length).decode('utf-8')
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
            
            # Write new config
            with open(cfg_path, 'w', encoding='utf-8') as f:
                f.write(new_config)
            
            log(f"Configuration saved successfully to {cfg_path}")
            
            handler.send_response(200)
            handler.send_header('Content-type', 'application/json')
            handler.send_header('Access-Control-Allow-Origin', 'http://127.0.0.1:8081')
            handler.end_headers()
            response = json.dumps({"success": True, "message": "Configuration saved successfully."})
            handler.wfile.write(response.encode('utf-8'))

    except Exception as e:
        log(f"Error handling config API: {e}")
        handler.send_error(500, f"Error handling configuration: {str(e)}")


def handle_logs_api(handler):
    """Handle /api/logs endpoint - return logs from buffer."""
    try:
        with _LOG_LOCK:
            logs = list(log_buffer)

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps(logs, ensure_ascii=False).encode('utf-8'))

    except Exception as e:
        log(f"Error retrieving logs: {e}")
        handler.send_error(500, "Error retrieving logs")


def handle_data_api(handler, dashboard_stats, dashboard_lock):
    """Handle /data.json endpoint - return dashboard statistics."""
    try:
        # Importer les stats à vie
        try:
            from ..utils.lifetime_stats import get_lifetime_stats, sync_lifetime_stats_with_dashboard

            # Synchroniser une seule fois si les stats sont vides
            try:
                lifetime_stats = get_lifetime_stats()
                if lifetime_stats.get('total_requests_lifetime', 0) == 0 and dashboard_stats['total_requests'] > 0:
                    sync_lifetime_stats_with_dashboard(dashboard_stats)
                    lifetime_stats = get_lifetime_stats()
                    log(f"✅ Lifetime stats synchronized with dashboard data")
                else:
                    log(f"✅ Lifetime stats loaded: {len(lifetime_stats)} keys")
            except Exception as sync_e:
                log(f"⚠️ Sync error: {sync_e}")
                lifetime_stats = get_lifetime_stats()
        except Exception as e:
            log(f"❌ Error loading lifetime stats: {e}")
            lifetime_stats = {}

        # Importer le statut de protection
        try:
            from ..config.config_manager import config_manager
            protection_enabled = config_manager.block_enabled
        except Exception:
            protection_enabled = True  # Default fallback

        with dashboard_lock:
            # Create a copy of dashboard data for thread safety
            data = {
                'blocked_today': dashboard_stats['blocked_today'],
                'allowed_today': dashboard_stats['allowed_today'],
                'total_requests': dashboard_stats['total_requests'],
                'recent_activity': list(dashboard_stats['recent_activity']),
                'blocked_domains_count': dict(dashboard_stats['blocked_domains_count']),
                'activity_by_hour': list(dashboard_stats['activity_by_hour']),
                # Ajouter les statistiques à vie
                'lifetime_stats': lifetime_stats,
                # Ajouter le statut de protection
                'protection_enabled': protection_enabled
            }

        if not isinstance(data, dict):
            raise ValueError("Invalid data format")

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        handler.end_headers()
        handler.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    except ValueError as e:
        log(f"Invalid dashboard data: {e}")
        handler.send_error(400, "Invalid data format")
    except json.JSONEncodeError as e:
        log(f"JSON encoding error: {e}")
        handler.send_error(500, "JSON encoding error")
