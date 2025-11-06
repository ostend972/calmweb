#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration settings and constants for CalmWeb.
"""

import os
import sys
from collections import deque
import threading

# Version
CALMWEB_VERSION = "1.1.0"

# Blocklist and whitelist URLs
BLOCKLIST_URLS = []  # Will be populated by get_blocklist_urls()

WHITELIST_URLS = [
    "https://raw.githubusercontent.com/Tontonjo/calmweb/refs/heads/main/filters/whitelist.txt"
]

# Default domain sets
manual_blocked_domains = {
    "add.blocked.domain"
}

whitelisted_domains = {
    "add.allowed.domain"
}

# Network configuration
RELOAD_INTERVAL = 3600
PROXY_BIND_IP = "127.0.0.1"
PROXY_PORT = 8080
DASHBOARD_PORT = 8081

# Installation paths
INSTALL_DIR = r"C:\Program Files\CalmWeb"
EXE_NAME = "calmweb.exe"
STARTUP_FOLDER = os.getenv('APPDATA', '') + r"\Microsoft\Windows\Start Menu\Programs\Startup"
CUSTOM_CFG_NAME = "custom.cfg"

# Dashboard directories
DASHBOARD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "calmweb-dashboard"
)

# React dashboard build directory (priorité)
# For PyInstaller, check if we're running from a bundle
if getattr(sys, 'frozen', False):
    # Running in PyInstaller bundle
    DASHBOARD_DIST_DIR = os.path.join(sys._MEIPASS, "calmweb-dashboard-dist")
else:
    # Running in development
    DASHBOARD_DIST_DIR = os.path.join(DASHBOARD_DIR, "dist")

# User configuration paths
USER_CFG_DIR = os.path.join(os.getenv('APPDATA') or os.path.expanduser("~"), "CalmWeb")
USER_CFG_PATH = os.path.join(USER_CFG_DIR, CUSTOM_CFG_NAME)
RED_FLAG_CACHE_PATH = os.path.join(USER_CFG_DIR, "red_flag_domains.txt")
RED_FLAG_TIMESTAMP_PATH = os.path.join(USER_CFG_DIR, "red_flag_last_update.txt")

# Global state variables
block_enabled = True
block_ip_direct = True      # Block direct IP access
block_http_traffic = True   # Block HTTP (non-HTTPS)
block_http_other_ports = True
configure_ie_proxy = True  # Configure Internet Explorer proxy (needed for system-wide proxy)

# Threading objects
_RESOLVER_LOADING = threading.Event()
_SHUTDOWN_EVENT = threading.Event()
_CONFIG_LOCK = threading.RLock()

# Dashboard statistics
dashboard_stats = {
    'blocked_today': 0,
    'allowed_today': 0,
    'total_requests': 0,
    'recent_activity': deque(maxlen=18),
    'blocked_domains_count': {},
    'activity_by_hour': [{'name': f'{i:02d}:00', 'allowed': 0, 'blocked': 0} for i in range(24)]
}

# Dashboard synchronization lock
dashboard_lock = threading.RLock()

# Original proxy settings backup
original_proxy_settings = {
    'winhttp_proxy': None,
    'http_proxy_env': None,
    'https_proxy_env': None,
    'registry_proxy_enable': None,
    'registry_proxy_server': None
}

# Check for Windows-specific modules
try:
    import win32ui
    import win32gui
    import win32con
    import win32com.client
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False