#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API handlers for CalmWeb external blocklist management.
Manages external blocklist and whitelist URLs with integration to BlocklistResolver.
"""

import json
import threading
from typing import Dict, Any, List
from urllib.parse import urlparse

from ..config.settings import WHITELIST_URLS, _CONFIG_LOCK
from ..config.custom_config import get_blocklist_urls, write_blocklists_to_custom_cfg
from ..utils.logging import log


# Global variable to store current blocklist URLs
_CURRENT_BLOCKLIST_URLS = []
_BLOCKLIST_LOCK = threading.RLock()

# Default blocklists with names
DEFAULT_BLOCKLISTS = [
    {
        "url": "https://raw.githubusercontent.com/StevenBlack/hosts/refs/heads/master/hosts",
        "name": "Steven Black's Unified Hosts",
        "enabled": True
    },
    {
        "url": "https://raw.githubusercontent.com/easylist/listefr/refs/heads/master/hosts.txt",
        "name": "EasyList French",
        "enabled": True
    },
    {
        "url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/ultimate.txt",
        "name": "Hagezi Ultimate",
        "enabled": True
    },
    {
        "url": "https://raw.githubusercontent.com/Tontonjo/calmweb/refs/heads/main/filters/blocklist.txt",
        "name": "CalmWeb Official",
        "enabled": True
    },
    {
        "url": "https://urlhaus.abuse.ch/downloads/csv/",
        "name": "URLhaus Malware",
        "enabled": True
    }
]

DEFAULT_WHITELISTS = [
    {
        "url": "https://raw.githubusercontent.com/Tontonjo/calmweb/refs/heads/main/filters/whitelist.txt",
        "name": "CalmWeb Whitelist",
        "enabled": True
    }
]


def initialize_blocklists() -> None:
    """Initialize blocklist URLs from configuration."""
    global _CURRENT_BLOCKLIST_URLS
    try:
        with _BLOCKLIST_LOCK:
            _CURRENT_BLOCKLIST_URLS = get_blocklist_urls()
    except Exception as e:
        log(f"Error initializing blocklists: {e}")
        _CURRENT_BLOCKLIST_URLS = [item["url"] for item in DEFAULT_BLOCKLISTS]


def validate_url(url: str) -> bool:
    """Validate URL format."""
    if not url or not isinstance(url, str):
        return False

    url = url.strip()
    if len(url) > 2000:  # Reasonable URL length limit
        return False

    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc and parsed.scheme in ['http', 'https'])
    except Exception:
        return False


def get_url_name(url: str) -> str:
    """Extract a readable name from URL."""
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')

        # Try to get meaningful name from path
        if path_parts and path_parts[-1]:
            filename = path_parts[-1]
            if '.' in filename:
                return filename.split('.')[0].replace('-', ' ').replace('_', ' ').title()

        # Fallback to domain
        return parsed.netloc.replace('www.', '')
    except Exception:
        return url[:50] + "..." if len(url) > 50 else url


def trigger_blocklist_reload() -> None:
    """Trigger reload of blocklists in the main application."""
    try:
        # Import here to avoid circular imports
        from ..core.blocklist_manager import BlocklistResolver
        from ..main import current_resolver

        if hasattr(current_resolver, 'maybe_reload_background'):
            # Trigger background reload
            threading.Thread(
                target=current_resolver.maybe_reload_background,
                daemon=True,
                name="BlocklistReload"
            ).start()
            log("Triggered blocklist reload after configuration change")
    except Exception as e:
        log(f"Error triggering blocklist reload: {e}")


def handle_blocklists_get(handler) -> None:
    """Handle GET /api/blocklists - Get current blocklists and whitelists."""
    try:
        with _BLOCKLIST_LOCK:
            current_blocklists = list(_CURRENT_BLOCKLIST_URLS)

        # Build blocklists with metadata
        blocklists = []
        for i, url in enumerate(current_blocklists):
            # Find matching default for metadata
            default_match = next((item for item in DEFAULT_BLOCKLISTS if item["url"] == url), None)
            blocklists.append({
                "id": i + 1,
                "url": url,
                "name": default_match["name"] if default_match else get_url_name(url),
                "enabled": True  # All loaded URLs are considered enabled
            })

        # Build whitelists with metadata
        whitelists = []
        for i, url in enumerate(WHITELIST_URLS):
            default_match = next((item for item in DEFAULT_WHITELISTS if item["url"] == url), None)
            whitelists.append({
                "id": i + 1,
                "url": url,
                "name": default_match["name"] if default_match else get_url_name(url),
                "enabled": True
            })

        # Get manual domains
        from ..config.settings import manual_blocked_domains, whitelisted_domains
        with _CONFIG_LOCK:
            manual_blocked = sorted(list(manual_blocked_domains))
            manual_allowed = sorted(list(whitelisted_domains))

        response_data = {
            "blocklists": blocklists,
            "whitelists": whitelists,
            "manual_blocked": manual_blocked,
            "manual_allowed": manual_allowed,
            "counts": {
                "external_blocklists": len(blocklists),
                "external_whitelists": len(whitelists),
                "manual_blocked": len(manual_blocked),
                "manual_allowed": len(manual_allowed)
            }
        }

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.send_header('Cache-Control', 'no-cache')
        handler.end_headers()
        handler.wfile.write(json.dumps(response_data).encode('utf-8'))

    except Exception as e:
        log(f"Error in handle_blocklists_get: {e}")
        try:
            handler.send_error(500, f"Internal server error: {e}")
        except:
            pass


def handle_blocklists_add(handler) -> None:
    """Handle POST /api/blocklists/add - Add new external list."""
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

        # Validate parameters
        if 'url' not in data or 'list_type' not in data:
            handler.send_error(400, "Missing 'url' or 'list_type' parameter")
            return

        url = data['url'].strip()
        list_type = data['list_type'].lower()

        # Validate URL
        if not validate_url(url):
            handler.send_error(400, f"Invalid URL format: {url}")
            return

        # Validate list type
        if list_type not in ['blocklist', 'whitelist']:
            handler.send_error(400, "list_type must be 'blocklist' or 'whitelist'")
            return

        # Add to appropriate list
        added = False
        if list_type == 'blocklist':
            with _BLOCKLIST_LOCK:
                if url not in _CURRENT_BLOCKLIST_URLS:
                    _CURRENT_BLOCKLIST_URLS.append(url)
                    added = True
        else:  # whitelist
            if url not in WHITELIST_URLS:
                WHITELIST_URLS.append(url)
                added = True

        if not added:
            handler.send_error(409, f"URL already exists in {list_type}")
            return

        # Persist to config file
        try:
            write_blocklists_to_custom_cfg()
            log(f"Added {list_type} URL: {url}")

            # Trigger reload
            trigger_blocklist_reload()
        except Exception as e:
            log(f"Error persisting blocklist addition: {e}")

        # Send response
        response_data = {
            "success": True,
            "url": url,
            "list_type": list_type,
            "name": get_url_name(url),
            "message": f"Added {list_type} URL successfully"
        }

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps(response_data).encode('utf-8'))

    except Exception as e:
        log(f"Error in handle_blocklists_add: {e}")
        try:
            handler.send_error(500, f"Internal server error: {e}")
        except:
            pass


def handle_blocklists_remove(handler) -> None:
    """Handle POST /api/blocklists/remove - Remove external list."""
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

        # Validate parameters
        if 'url' not in data or 'list_type' not in data:
            handler.send_error(400, "Missing 'url' or 'list_type' parameter")
            return

        url = data['url'].strip()
        list_type = data['list_type'].lower()

        # Validate list type
        if list_type not in ['blocklist', 'whitelist']:
            handler.send_error(400, "list_type must be 'blocklist' or 'whitelist'")
            return

        # Remove from appropriate list
        removed = False
        if list_type == 'blocklist':
            with _BLOCKLIST_LOCK:
                if url in _CURRENT_BLOCKLIST_URLS:
                    _CURRENT_BLOCKLIST_URLS.remove(url)
                    removed = True
        else:  # whitelist
            if url in WHITELIST_URLS:
                WHITELIST_URLS.remove(url)
                removed = True

        if not removed:
            handler.send_error(404, f"URL not found in {list_type}")
            return

        # Persist to config file
        try:
            write_blocklists_to_custom_cfg()
            log(f"Removed {list_type} URL: {url}")

            # Trigger reload
            trigger_blocklist_reload()
        except Exception as e:
            log(f"Error persisting blocklist removal: {e}")

        # Send response
        response_data = {
            "success": True,
            "url": url,
            "list_type": list_type,
            "message": f"Removed {list_type} URL successfully"
        }

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps(response_data).encode('utf-8'))

    except Exception as e:
        log(f"Error in handle_blocklists_remove: {e}")
        try:
            handler.send_error(500, f"Internal server error: {e}")
        except:
            pass


def handle_blocklists_reset(handler) -> None:
    """Handle POST /api/blocklists/reset - Reset to default lists."""
    try:
        # Reset to defaults
        with _BLOCKLIST_LOCK:
            _CURRENT_BLOCKLIST_URLS.clear()
            _CURRENT_BLOCKLIST_URLS.extend([item["url"] for item in DEFAULT_BLOCKLISTS])

        WHITELIST_URLS.clear()
        WHITELIST_URLS.extend([item["url"] for item in DEFAULT_WHITELISTS])

        # Persist to config file
        try:
            write_blocklists_to_custom_cfg()
            log("Reset blocklists to defaults by dashboard")

            # Trigger reload
            trigger_blocklist_reload()
        except Exception as e:
            log(f"Error persisting blocklist reset: {e}")

        # Send response
        response_data = {
            "success": True,
            "message": "Reset to default blocklists",
            "blocklist_count": len(DEFAULT_BLOCKLISTS),
            "whitelist_count": len(DEFAULT_WHITELISTS)
        }

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps(response_data).encode('utf-8'))

    except Exception as e:
        log(f"Error in handle_blocklists_reset: {e}")
        try:
            handler.send_error(500, f"Internal server error: {e}")
        except:
            pass


def handle_blocklists_api(handler) -> None:
    """Route blocklist API requests based on method and path."""
    try:
        if handler.command == 'GET':
            handle_blocklists_get(handler)
        elif handler.command == 'POST':
            # Route based on specific endpoint
            if handler.path == '/api/blocklists/add':
                handle_blocklists_add(handler)
            elif handler.path == '/api/blocklists/remove':
                handle_blocklists_remove(handler)
            elif handler.path == '/api/blocklists/reset':
                handle_blocklists_reset(handler)
            else:
                handler.send_error(404, "Endpoint not found")
        else:
            handler.send_error(405, "Method not allowed")
    except Exception as e:
        log(f"Error in handle_blocklists_api: {e}")
        try:
            handler.send_error(500, f"Internal server error: {e}")
        except:
            pass


# Initialize on module load
initialize_blocklists()