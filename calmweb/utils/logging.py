#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Logging utilities for CalmWeb.
Provides thread-safe logging and dashboard statistics.
"""

import sys
import time
import threading
from collections import deque
from datetime import datetime

from ..config.settings import dashboard_stats, dashboard_lock

# Import des stats à vie (avec gestion des erreurs d'import circulaire)
try:
    from .lifetime_stats import update_lifetime_stats
except ImportError:
    update_lifetime_stats = None

# Logging setup
log_buffer = deque(maxlen=1000)
_LOG_LOCK = threading.Lock()


def _safe_str(obj):
    """Safely convert object to string."""
    try:
        return str(obj)
    except Exception:
        return f"<{type(obj).__name__} object>"


def log(msg):
    """Thread-safe logging function with buffer management."""
    try:
        timestamp = time.strftime("[%H:%M:%S]")
        try:
            # Force string conversion + replace unicode errors
            safe_msg = str(msg).encode("utf-8", errors="replace").decode("utf-8", errors="replace")
        except Exception:
            safe_msg = "Log message conversion error"

        line = f"{timestamp} {safe_msg}"

        with _LOG_LOCK:
            # Add to buffer (deque automatically manages max size)
            log_buffer.append(line)

            # Protected console output
            try:
                print(line, flush=True)
            except Exception:
                # stdout may be unavailable in some environments
                pass

    except Exception:
        # Last line of defense: no exception propagated
        try:
            # Minimal signal attempt to stderr
            sys.stderr.write("Logging internal error\n")
        except Exception:
            pass


def update_dashboard_stats(action, domain=None, ip=None):
    """
    Updates dashboard statistics in a thread-safe manner.
    action: 'allowed' or 'blocked'
    """
    try:
        global dashboard_stats
        with dashboard_lock:  # Thread-safe protection
            now = datetime.now()
            hour = now.hour

            dashboard_stats['total_requests'] += 1

            if action == 'blocked':
                dashboard_stats['blocked_today'] += 1
                dashboard_stats['activity_by_hour'][hour]['blocked'] += 1

                # Count blocked domains
                if domain and domain not in dashboard_stats['blocked_domains_count']:
                    dashboard_stats['blocked_domains_count'][domain] = 0
                if domain:
                    dashboard_stats['blocked_domains_count'][domain] += 1

            elif action == 'allowed':
                dashboard_stats['allowed_today'] += 1
                dashboard_stats['activity_by_hour'][hour]['allowed'] += 1

            # Mettre à jour les statistiques à vie
            if update_lifetime_stats:
                try:
                    update_lifetime_stats(action, domain)
                except Exception as e:
                    pass  # Ignorer les erreurs des stats à vie pour ne pas casser l'app

            # Add to recent activity
            dashboard_stats['recent_activity'].appendleft({
                'id': dashboard_stats['total_requests'],
                'timestamp': now.strftime('%H:%M:%S'),
                'action': 'Blocked' if action == 'blocked' else 'Allowed',
                'domain': domain or 'N/A',
                'ip': ip or 'N/A'
            })

    except Exception as e:
        log(f"Error update_dashboard_stats: {e}")