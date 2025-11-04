#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main entry point for CalmWeb.
Coordinates all modules and provides the main application logic.
"""

import sys
import time
import signal
import threading

from .config.settings import (
    PROXY_BIND_IP, PROXY_PORT, DASHBOARD_PORT, RELOAD_INTERVAL,
    INSTALL_DIR, block_enabled, _SHUTDOWN_EVENT,
    manual_blocked_domains, whitelisted_domains
)
from .config.custom_config import (
    ensure_custom_cfg_exists, load_custom_cfg_to_globals, get_blocklist_urls
)
from .core.blocklist_manager import BlocklistResolver
from .core.proxy_server import start_proxy_server, stop_proxy_server
from .web.dashboard import start_dashboard_server, stop_dashboard_server
from .ui.system_tray import create_system_tray, quit_app
from .utils.logging import log
from .utils.proxy_manager import save_original_proxy_settings, restore_original_proxy_settings, set_system_proxy
from .installer.install import install, uninstall

# Global resolver instance
current_resolver = None

# Inject dependencies into modules that need them
def setup_module_dependencies():
    """Setup cross-module dependencies."""
    global current_resolver

    # Inject into proxy_server module
    from .core import proxy_server
    proxy_server.current_resolver = current_resolver

    # Inject into system_tray module
    from .ui import system_tray
    system_tray.current_resolver = current_resolver
    system_tray.set_system_proxy = set_system_proxy
    system_tray.restore_original_proxy_settings = restore_original_proxy_settings
    system_tray.stop_proxy_server = stop_proxy_server
    system_tray.stop_dashboard_server = stop_dashboard_server

    # Inject into web modules
    from .web import api_domains_handlers
    api_domains_handlers.current_resolver = current_resolver


def run_calmweb():
    """
    Main entry point to run Calm Web in user mode.
    """
    global current_resolver

    # Save original proxy settings before starting
    save_original_proxy_settings()

    try:
        cfg_path = ensure_custom_cfg_exists(INSTALL_DIR, manual_blocked_domains, whitelisted_domains)
        load_custom_cfg_to_globals(cfg_path)
    except Exception as e:
        log(f"Error loading initial config: {e}")

    # Initialize centralized config manager with legacy settings
    try:
        from .config.config_manager import config_manager
        from .config import settings
        config_manager.update_from_legacy_settings(settings)
        log("Config manager initialized with legacy settings")
    except Exception as e:
        log(f"Error initializing config manager: {e}")

    # Initialiser les statistiques à vie
    try:
        from .utils.lifetime_stats import initialize_lifetime_stats
        initialize_lifetime_stats()
    except Exception as e:
        log(f"Warning: Could not initialize lifetime stats: {e}")

    try:
        resolver = BlocklistResolver(get_blocklist_urls(), RELOAD_INTERVAL)
        current_resolver = resolver
    except Exception as e:
        log(f"Error creating resolver: {e}")

    # Setup module dependencies after resolver is created
    setup_module_dependencies()

    try:
        start_proxy_server(PROXY_BIND_IP, PROXY_PORT)
    except Exception as e:
        log(f"Error starting proxy server: {e}")

    try:
        start_dashboard_server("127.0.0.1", DASHBOARD_PORT)
    except Exception as e:
        log(f"Error starting dashboard server: {e}")

    try:
        set_system_proxy(enable=block_enabled)
    except Exception as e:
        log(f"Error setting system proxy: {e}")

    # Start systray icon
    try:
        log(f"Calm Web started. Proxy on {PROXY_BIND_IP}:{PROXY_PORT}, blocking {'enabled' if block_enabled else 'disabled'}.")

        # Hook signals to allow graceful termination
        def _signal_handler(signum, frame):
            log(f"Signal {signum} received, stopping.")
            try:
                # Immediately restore proxy settings
                restore_original_proxy_settings()
                log("Proxy settings restored after interruption.")
            except Exception as e:
                log(f"Error restoring proxy during interruption: {e}")
            quit_app(None)

        try:
            signal.signal(signal.SIGINT, _signal_handler)
            signal.signal(signal.SIGTERM, _signal_handler)
            if hasattr(signal, 'SIGBREAK'):  # Windows
                signal.signal(signal.SIGBREAK, _signal_handler)
        except Exception:
            pass

        # Try to start system tray
        create_system_tray()

    except Exception as e:
        log(f"Error systray / run: {e}")
        # If systray fails (e.g., environment without GUI), keep server in background
        def _headless_signal_handler(signum, frame):
            log(f"Signal {signum} received in headless mode, stopping.")
            try:
                restore_original_proxy_settings()
                log("Proxy settings restored after interruption.")
            except Exception as e:
                log(f"Error restoring proxy during interruption: {e}")
            quit_app(None)

        try:
            signal.signal(signal.SIGINT, _headless_signal_handler)
            signal.signal(signal.SIGTERM, _headless_signal_handler)
            if hasattr(signal, 'SIGBREAK'):  # Windows
                signal.signal(signal.SIGBREAK, _headless_signal_handler)
        except Exception:
            pass

        try:
            while not _SHUTDOWN_EVENT.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            try:
                restore_original_proxy_settings()
                log("Proxy settings restored after KeyboardInterrupt.")
            except Exception as e:
                log(f"Error restoring proxy during KeyboardInterrupt: {e}")
            quit_app(None)


def robust_main():
    """
    Robust main function with error handling.
    """
    try:
        if len(sys.argv) > 1:
            if sys.argv[1].lower() == "install":
                install()
                return
            elif sys.argv[1].lower() == "uninstall":
                uninstall()
                return

        # Default: run CalmWeb
        run_calmweb()

    except KeyboardInterrupt:
        log("Interrupted by user")
        try:
            restore_original_proxy_settings()
        except Exception:
            pass
        sys.exit(0)
    except Exception as e:
        log(f"Unexpected error in main: {e}")
        try:
            restore_original_proxy_settings()
        except Exception:
            pass
        sys.exit(1)


def main():
    """Main entry point for the application."""
    robust_main()


if __name__ == "__main__":
    main()