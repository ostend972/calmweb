#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API handlers for auto-update functionality.
"""

import json
from ..utils.auto_updater import auto_updater
from ..utils.logging import log


def handle_update_status(handler) -> None:
    """Handle GET /api/update/status - Get current update status."""
    try:
        status = auto_updater.get_status()

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.send_header('Cache-Control', 'no-cache')
        handler.end_headers()
        handler.wfile.write(json.dumps(status).encode('utf-8'))

    except Exception as e:
        log(f"Error in handle_update_status: {e}")
        try:
            handler.send_error(500, f"Internal server error: {e}")
        except:
            pass


def handle_update_trigger(handler) -> None:
    """Handle POST /api/update/trigger - Manually trigger update."""
    try:
        log("Manual update triggered from dashboard")
        success = auto_updater.update_external_lists()

        response_data = {
            "success": success,
            "message": "Update completed successfully" if success else "Update failed"
        }

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps(response_data).encode('utf-8'))

    except Exception as e:
        log(f"Error in handle_update_trigger: {e}")
        try:
            handler.send_error(500, f"Internal server error: {e}")
        except:
            pass


def handle_update_api(handler) -> None:
    """Route update API requests based on method and path."""
    try:
        if handler.command == 'GET':
            if handler.path == '/api/update/status':
                handle_update_status(handler)
            else:
                handler.send_error(404, "Endpoint not found")
        elif handler.command == 'POST':
            if handler.path == '/api/update/trigger':
                handle_update_trigger(handler)
            else:
                handler.send_error(404, "Endpoint not found")
        else:
            handler.send_error(405, "Method not allowed")
    except Exception as e:
        log(f"Error in handle_update_api: {e}")
        try:
            handler.send_error(500, f"Internal server error: {e}")
        except:
            pass