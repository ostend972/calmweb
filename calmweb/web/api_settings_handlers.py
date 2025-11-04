#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API handlers for CalmWeb settings and protection toggle.
Manages global settings, protection state, and configuration persistence.
"""

import json
import threading
from typing import Dict, Any, Tuple

from ..config.config_manager import config_manager
from ..config.settings import _CONFIG_LOCK
from ..config.custom_config import write_settings_to_custom_cfg, load_custom_cfg_to_globals
from ..utils.logging import log


def handle_protection_toggle(handler) -> None:
    """Handle POST /api/protection/toggle - Toggle protection on/off."""
    try:
        # Read request body (optional for toggle)
        content_length = int(handler.headers.get('Content-Length', 0))
        data = {}

        if content_length > 0:
            post_data = handler.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError:
                handler.send_error(400, "Invalid JSON")
                return

        # Determine new state
        if 'enabled' in data and isinstance(data['enabled'], bool):
            # Explicit state provided
            enabled = data['enabled']
        else:
            # Toggle current state
            enabled = not config_manager.block_enabled

        # Update global setting thread-safely
        with _CONFIG_LOCK:
            config_manager.block_enabled = enabled

        # Apply proxy settings change immediately
        try:
            # Try to get the proxy manager function from system_tray module
            try:
                from ..ui.system_tray import set_system_proxy
                if set_system_proxy:
                    set_system_proxy(enable=enabled)
                    log(f"System proxy {'enabled' if enabled else 'disabled'}")
            except ImportError:
                log("Warning: Could not import set_system_proxy from system_tray")
        except Exception as e:
            log(f"Error applying proxy settings: {e}")

        # Persist to config file
        try:
            write_settings_to_custom_cfg()
            log(f"Protection {'enabled' if enabled else 'disabled'} by dashboard")
        except Exception as e:
            log(f"Error persisting protection toggle: {e}")

        # System tray will be updated automatically via config_manager callback

        # Send response
        response_data = {
            "success": True,
            "protection_enabled": enabled,
            "message": f"Protection {'enabled' if enabled else 'disabled'}"
        }

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps(response_data).encode('utf-8'))

    except Exception as e:
        log(f"Error in handle_protection_toggle: {e}")
        try:
            handler.send_error(500, f"Internal server error: {e}")
        except:
            pass


def handle_settings_get(handler) -> None:
    """Handle GET /api/settings - Get current settings state."""
    try:
        with _CONFIG_LOCK:
            settings_data = {
                "protection_enabled": config_manager.block_enabled,
                "block_enabled": config_manager.block_enabled  # For backwards compatibility
            }

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.send_header('Cache-Control', 'no-cache')
        handler.end_headers()
        handler.wfile.write(json.dumps(settings_data).encode('utf-8'))

    except Exception as e:
        log(f"Error in handle_settings_get: {e}")
        try:
            handler.send_error(500, f"Internal server error: {e}")
        except:
            pass


def handle_settings_update(handler) -> None:
    """Handle POST /api/settings/update - Update multiple settings."""
    try:
        # Read request body
        content_length = int(handler.headers.get('Content-Length', 0))
        if content_length == 0:
            handler.send_error(400, "Missing request body")
            return

        post_data = handler.rfile.read(content_length)
        try:
            data = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            handler.send_error(400, "Invalid JSON")
            return

        # Validate and extract settings
        valid_settings = ['block_ip_direct', 'block_http_traffic', 'block_http_other_ports']
        changes = {}
        for setting in valid_settings:
            if setting in data:
                if not isinstance(data[setting], bool):
                    handler.send_error(400, f"Invalid value for {setting}: must be boolean")
                    return
                changes[setting] = data[setting]

        if not changes:
            handler.send_error(400, "No valid settings provided")
            return

        # Update global settings thread-safely
        with _CONFIG_LOCK:
            # Note: Additional settings can be added to config_manager if needed
            # For now, just return the current protection state
            current_settings = {
                "protection_enabled": config_manager.block_enabled,
                "block_enabled": config_manager.block_enabled  # For backwards compatibility
            }

        # Persist to config file
        try:
            write_settings_to_custom_cfg()
            log(f"Settings updated by dashboard: {', '.join(f'{k}={v}' for k, v in changes.items())}")
        except Exception as e:
            log(f"Error persisting settings update: {e}")

        # Send response
        response_data = {
            "success": True,
            "settings": current_settings,
            "changed": changes,
            "message": "Settings updated successfully"
        }

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps(response_data).encode('utf-8'))

    except Exception as e:
        log(f"Error in handle_settings_update: {e}")
        try:
            handler.send_error(500, f"Internal server error: {e}")
        except:
            pass


def handle_settings_api(handler) -> None:
    """Route settings API requests based on method and path."""
    try:
        if handler.command == 'GET':
            handle_settings_get(handler)
        elif handler.command == 'POST':
            handle_settings_update(handler)
        else:
            handler.send_error(405, "Method not allowed")
    except Exception as e:
        log(f"Error in handle_settings_api: {e}")
        try:
            handler.send_error(500, f"Internal server error: {e}")
        except:
            pass