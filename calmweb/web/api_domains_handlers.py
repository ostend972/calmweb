#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API handlers for CalmWeb domain management.
Manages manual blocked and whitelisted domains with persistence.
"""

import json
import re
from typing import Dict, Any, List

from ..config.settings import (
    manual_blocked_domains, whitelisted_domains, _CONFIG_LOCK
)
from ..config.custom_config import write_domains_to_custom_cfg, load_custom_cfg_to_globals
from ..utils.logging import log

# Global resolver instance injected by main.py
current_resolver = None


def validate_domain(domain: str) -> bool:
    """Validate domain format."""
    if not domain or not isinstance(domain, str):
        return False

    # Remove leading/trailing whitespace and dots
    domain = domain.strip().lower().strip('.')

    # Check length
    if len(domain) == 0 or len(domain) > 253:
        return False

    # Basic domain regex - allows subdomains, not strict RFC validation
    domain_pattern = re.compile(
        r'^[a-z0-9]([a-z0-9\-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]*[a-z0-9])?)*$'
    )

    return bool(domain_pattern.match(domain))


def handle_domains_add(handler) -> None:
    """Handle POST /api/domains/add - Add domain to blocklist or whitelist."""
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
        if 'domain' not in data or 'list_type' not in data:
            handler.send_error(400, "Missing 'domain' or 'list_type' parameter")
            return

        domain = data['domain'].strip().lower().strip('.')
        list_type = data['list_type'].lower()

        # Validate domain
        if not validate_domain(domain):
            handler.send_error(400, f"Invalid domain format: {domain}")
            return

        # Validate list type
        if list_type not in ['blocked', 'allowed']:
            handler.send_error(400, "list_type must be 'blocked' or 'allowed'")
            return

        # Add domain to appropriate list thread-safely
        with _CONFIG_LOCK:
            if list_type == 'blocked':
                # Remove from whitelist if present
                whitelisted_domains.discard(domain)
                manual_blocked_domains.add(domain)
                target_list = "blocked"
            else:  # allowed
                # Remove from blocklist if present
                manual_blocked_domains.discard(domain)
                whitelisted_domains.add(domain)
                target_list = "allowed"

        # Persist to config file
        try:
            write_domains_to_custom_cfg()
            log(f"Domain '{domain}' added to {target_list} list by dashboard")
        except Exception as e:
            log(f"Error persisting domain addition: {e}")

        # Send response
        response_data = {
            "success": True,
            "domain": domain,
            "list_type": target_list,
            "message": f"Domain '{domain}' added to {target_list} list"
        }

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps(response_data).encode('utf-8'))

    except Exception as e:
        log(f"Error in handle_domains_add: {e}")
        try:
            handler.send_error(500, f"Internal server error: {e}")
        except:
            pass


def handle_domains_remove(handler) -> None:
    """Handle POST /api/domains/remove - Remove domain from blocklist or whitelist."""
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
        if 'domain' not in data or 'list_type' not in data:
            handler.send_error(400, "Missing 'domain' or 'list_type' parameter")
            return

        domain = data['domain'].strip().lower().strip('.')
        list_type = data['list_type'].lower()

        # Validate list type
        if list_type not in ['blocked', 'allowed']:
            handler.send_error(400, "list_type must be 'blocked' or 'allowed'")
            return

        # Remove domain from appropriate list thread-safely
        removed = False
        with _CONFIG_LOCK:
            if list_type == 'blocked':
                if domain in manual_blocked_domains:
                    manual_blocked_domains.remove(domain)
                    removed = True
            else:  # allowed
                if domain in whitelisted_domains:
                    whitelisted_domains.remove(domain)
                    removed = True

        if not removed:
            handler.send_error(404, f"Domain '{domain}' not found in {list_type} list")
            return

        # Persist to config file
        try:
            write_domains_to_custom_cfg()
            log(f"Domain '{domain}' removed from {list_type} list by dashboard")
        except Exception as e:
            log(f"Error persisting domain removal: {e}")

        # Send response
        response_data = {
            "success": True,
            "domain": domain,
            "list_type": list_type,
            "message": f"Domain '{domain}' removed from {list_type} list"
        }

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps(response_data).encode('utf-8'))

    except Exception as e:
        log(f"Error in handle_domains_remove: {e}")
        try:
            handler.send_error(500, f"Internal server error: {e}")
        except:
            pass


def handle_domains_list(handler) -> None:
    """Handle GET /api/domains - Get current domains including external lists."""
    try:
        # Get manual domains
        with _CONFIG_LOCK:
            manual_blocked = sorted(list(manual_blocked_domains))
            manual_allowed = sorted(list(whitelisted_domains))

        # Get external blocked domains using direct download approach
        external_blocked = []
        external_allowed = []

        try:
            from .api_external_domains import (
                get_external_blocked_domains,
                get_external_allowed_domains,
                get_external_domains_count
            )

            # Get limited sample for display
            external_blocked = get_external_blocked_domains(limit=1000)
            external_allowed = get_external_allowed_domains(limit=100)

            # Get total counts
            total_blocked_count, total_allowed_count = get_external_domains_count()

            log(f"✅ Retrieved {len(external_blocked)} external blocked domains (of {total_blocked_count} total)")
            log(f"✅ Retrieved {len(external_allowed)} external allowed domains (of {total_allowed_count} total)")

        except Exception as e:
            log(f"❌ Error getting external domains: {e}")
            import traceback
            log(f"Traceback: {traceback.format_exc()}")

        # Combine all domains with source information
        all_blocked = []
        all_allowed = []

        # Add external domains first
        external_blocked_set = set(external_blocked)
        external_allowed_set = set(external_allowed)

        for domain in external_blocked:
            all_blocked.append({
                "domain": domain,
                "source": "external",
                "removable": False
            })

        for domain in external_allowed:
            all_allowed.append({
                "domain": domain,
                "source": "external",
                "removable": False
            })

        # Add manual domains ONLY if they're not already in external lists
        for domain in manual_blocked:
            if domain not in external_blocked_set:
                all_blocked.append({
                    "domain": domain,
                    "source": "manual",
                    "removable": True
                })

        for domain in manual_allowed:
            if domain not in external_allowed_set:
                all_allowed.append({
                    "domain": domain,
                    "source": "manual",
                    "removable": True
                })

        # Add "more domains" indicator if we have more than displayed
        try:
            total_blocked_count, total_allowed_count = get_external_domains_count()

            if total_blocked_count > len(external_blocked):
                remaining = total_blocked_count - len(external_blocked)
                all_blocked.append({
                    "domain": f"... and {remaining:,} more external domains",
                    "source": "external",
                    "removable": False
                })

            if total_allowed_count > len(external_allowed):
                remaining = total_allowed_count - len(external_allowed)
                all_allowed.append({
                    "domain": f"... and {remaining:,} more external domains",
                    "source": "external",
                    "removable": False
                })

        except Exception:
            pass  # Counts not available

        # Get real total counts for statistics
        try:
            total_external_blocked, total_external_allowed = get_external_domains_count()
        except Exception:
            total_external_blocked = len(external_blocked)
            total_external_allowed = len(external_allowed)

        domains_data = {
            "blocked": all_blocked,
            "allowed": all_allowed,
            "manual_blocked": manual_blocked,  # Keep for backward compatibility
            "manual_allowed": manual_allowed,  # Keep for backward compatibility
            "counts": {
                "total_blocked": len(manual_blocked) + total_external_blocked,
                "manual_blocked": len(manual_blocked),
                "external_blocked": total_external_blocked,
                "total_allowed": len(manual_allowed) + total_external_allowed,
                "manual_allowed": len(manual_allowed),
                "external_allowed": total_external_allowed
            },
            "display_limited": total_external_blocked > len(external_blocked) or total_external_allowed > len(external_allowed)
        }

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.send_header('Cache-Control', 'no-cache')
        handler.end_headers()
        handler.wfile.write(json.dumps(domains_data).encode('utf-8'))

    except Exception as e:
        log(f"Error in handle_domains_list: {e}")
        try:
            handler.send_error(500, f"Internal server error: {e}")
        except:
            pass


def handle_domains_clear(handler) -> None:
    """Handle POST /api/domains/clear - Clear all domains from a list."""
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
        if 'list_type' not in data:
            handler.send_error(400, "Missing 'list_type' parameter")
            return

        list_type = data['list_type'].lower()

        # Validate list type
        if list_type not in ['blocked', 'allowed', 'both']:
            handler.send_error(400, "list_type must be 'blocked', 'allowed', or 'both'")
            return

        # Clear appropriate lists thread-safely
        cleared_count = 0
        with _CONFIG_LOCK:
            if list_type == 'blocked' or list_type == 'both':
                cleared_count += len(manual_blocked_domains)
                manual_blocked_domains.clear()

            if list_type == 'allowed' or list_type == 'both':
                cleared_count += len(whitelisted_domains)
                whitelisted_domains.clear()

        # Persist to config file
        try:
            write_domains_to_custom_cfg()
            log(f"Cleared {cleared_count} domains from {list_type} list(s) by dashboard")
        except Exception as e:
            log(f"Error persisting domain clearing: {e}")

        # Send response
        response_data = {
            "success": True,
            "list_type": list_type,
            "cleared_count": cleared_count,
            "message": f"Cleared {cleared_count} domains from {list_type} list(s)"
        }

        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps(response_data).encode('utf-8'))

    except Exception as e:
        log(f"Error in handle_domains_clear: {e}")
        try:
            handler.send_error(500, f"Internal server error: {e}")
        except:
            pass


def handle_domains_api(handler) -> None:
    """Route domain API requests based on method and path."""
    try:
        if handler.command == 'GET':
            handle_domains_list(handler)
        elif handler.command == 'POST':
            # Route based on specific endpoint
            if handler.path == '/api/domains/add':
                handle_domains_add(handler)
            elif handler.path == '/api/domains/remove':
                handle_domains_remove(handler)
            elif handler.path == '/api/domains/clear':
                handle_domains_clear(handler)
            else:
                handler.send_error(404, "Endpoint not found")
        else:
            handler.send_error(405, "Method not allowed")
    except Exception as e:
        log(f"Error in handle_domains_api: {e}")
        try:
            handler.send_error(500, f"Internal server error: {e}")
        except:
            pass