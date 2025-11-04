#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main entry point for CalmWeb - Standalone version for PyInstaller.
Uses absolute imports and handles PyInstaller environment.
"""

import sys
import os
import time
import signal
import threading

# Setup paths for PyInstaller
if getattr(sys, 'frozen', False):
    # Running in PyInstaller bundle
    bundle_dir = sys._MEIPASS
    sys.path.insert(0, bundle_dir)
    sys.path.insert(0, os.path.join(bundle_dir, 'calmweb'))
else:
    # Running in development
    bundle_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, bundle_dir)
    sys.path.insert(0, os.path.join(bundle_dir, 'calmweb'))

# Import all necessary modules with error handling
def safe_import():
    """Safely import all required modules."""
    modules = {}

    # Try multiple import patterns
    try:
        # Pattern 1: From calmweb package
        from calmweb.config import settings
        from calmweb.config.custom_config import (
            ensure_custom_cfg_exists, load_custom_cfg_to_globals, get_blocklist_urls
        )
        from calmweb.core.blocklist_manager import BlocklistResolver
        from calmweb.core.proxy_server import start_proxy_server, stop_proxy_server
        from calmweb.web.dashboard import start_dashboard_server, stop_dashboard_server
        from calmweb.ui.system_tray import create_system_tray, quit_app
        from calmweb.utils.logging import log
        from calmweb.utils.proxy_manager import (
            save_original_proxy_settings, restore_original_proxy_settings, set_system_proxy
        )
        from calmweb.installer.install import install, uninstall

        modules.update({
            'settings': settings,
            'ensure_custom_cfg_exists': ensure_custom_cfg_exists,
            'load_custom_cfg_to_globals': load_custom_cfg_to_globals,
            'get_blocklist_urls': get_blocklist_urls,
            'BlocklistResolver': BlocklistResolver,
            'start_proxy_server': start_proxy_server,
            'stop_proxy_server': stop_proxy_server,
            'start_dashboard_server': start_dashboard_server,
            'stop_dashboard_server': stop_dashboard_server,
            'create_system_tray': create_system_tray,
            'quit_app': quit_app,
            'log': log,
            'save_original_proxy_settings': save_original_proxy_settings,
            'restore_original_proxy_settings': restore_original_proxy_settings,
            'set_system_proxy': set_system_proxy,
            'install': install,
            'uninstall': uninstall
        })

    except ImportError as e:
        print(f"Pattern 1 failed: {e}")

        try:
            # Pattern 2: Direct imports
            import config.settings as settings
            from config.custom_config import (
                ensure_custom_cfg_exists, load_custom_cfg_to_globals, get_blocklist_urls
            )
            from core.blocklist_manager import BlocklistResolver
            from core.proxy_server import start_proxy_server, stop_proxy_server
            from web.dashboard import start_dashboard_server, stop_dashboard_server
            from ui.system_tray import create_system_tray, quit_app
            from utils.logging import log
            from utils.proxy_manager import (
                save_original_proxy_settings, restore_original_proxy_settings, set_system_proxy
            )
            from installer.install import install, uninstall

            modules.update({
                'settings': settings,
                'ensure_custom_cfg_exists': ensure_custom_cfg_exists,
                'load_custom_cfg_to_globals': load_custom_cfg_to_globals,
                'get_blocklist_urls': get_blocklist_urls,
                'BlocklistResolver': BlocklistResolver,
                'start_proxy_server': start_proxy_server,
                'stop_proxy_server': stop_proxy_server,
                'start_dashboard_server': start_dashboard_server,
                'stop_dashboard_server': stop_dashboard_server,
                'create_system_tray': create_system_tray,
                'quit_app': quit_app,
                'log': log,
                'save_original_proxy_settings': save_original_proxy_settings,
                'restore_original_proxy_settings': restore_original_proxy_settings,
                'set_system_proxy': set_system_proxy,
                'install': install,
                'uninstall': uninstall
            })

        except ImportError as e2:
            print(f"Pattern 2 failed: {e2}")
            print(f"Available modules in sys.modules: {list(sys.modules.keys())[:10]}...")
            return None

    return modules

# Global resolver instance
current_resolver = None

def setup_module_dependencies(modules):
    """Setup cross-module dependencies."""
    global current_resolver

    try:
        # Try to get proxy_server module
        try:
            import calmweb.core.proxy_server as proxy_server
        except ImportError:
            import core.proxy_server as proxy_server

        proxy_server.current_resolver = current_resolver

        # Try to get system_tray module
        try:
            import calmweb.ui.system_tray as system_tray
        except ImportError:
            import ui.system_tray as system_tray

        system_tray.current_resolver = current_resolver
        system_tray.set_system_proxy = modules['set_system_proxy']
        system_tray.restore_original_proxy_settings = modules['restore_original_proxy_settings']
        system_tray.stop_proxy_server = modules['stop_proxy_server']
        system_tray.stop_dashboard_server = modules['stop_dashboard_server']

        # Try to get api_domains_handlers module
        try:
            import calmweb.web.api_domains_handlers as api_domains_handlers
        except ImportError:
            try:
                import web.api_domains_handlers as api_domains_handlers
            except ImportError:
                print("Warning: Could not import api_domains_handlers")
                return

        api_domains_handlers.current_resolver = current_resolver

    except Exception as e:
        print(f"Warning: Could not setup all dependencies: {e}")

def run_calmweb():
    """Main entry point to run Calm Web."""
    global current_resolver

    # Import all modules
    modules = safe_import()
    if not modules:
        print("FATAL: Could not import required modules")
        return

    settings = modules['settings']
    log = modules['log']

    # Save original proxy settings before starting
    modules['save_original_proxy_settings']()

    try:
        cfg_path = modules['ensure_custom_cfg_exists'](
            settings.INSTALL_DIR,
            settings.manual_blocked_domains,
            settings.whitelisted_domains
        )
        modules['load_custom_cfg_to_globals'](cfg_path)
    except Exception as e:
        log(f"Error loading initial config: {e}")

    # Initialize centralized config manager with legacy settings
    try:
        try:
            from calmweb.config.config_manager import config_manager
        except ImportError:
            from config.config_manager import config_manager

        config_manager.update_from_legacy_settings(settings)
        log("Config manager initialized with legacy settings")
    except Exception as e:
        log(f"Error initializing config manager: {e}")

    # Initialize lifetime statistics
    try:
        try:
            from calmweb.utils.lifetime_stats import initialize_lifetime_stats
        except ImportError:
            from utils.lifetime_stats import initialize_lifetime_stats

        initialize_lifetime_stats()
    except Exception as e:
        log(f"Warning: Could not initialize lifetime stats: {e}")

    try:
        resolver = modules['BlocklistResolver'](modules['get_blocklist_urls'](), settings.RELOAD_INTERVAL)
        current_resolver = resolver
    except Exception as e:
        log(f"Error creating resolver: {e}")

    # Setup module dependencies after resolver is created
    setup_module_dependencies(modules)

    try:
        modules['start_proxy_server'](settings.PROXY_BIND_IP, settings.PROXY_PORT)
    except Exception as e:
        log(f"Error starting proxy server: {e}")

    try:
        modules['start_dashboard_server']("127.0.0.1", settings.DASHBOARD_PORT)
    except Exception as e:
        log(f"Error starting dashboard server: {e}")

    try:
        modules['set_system_proxy'](enable=settings.block_enabled)
    except Exception as e:
        log(f"Error setting system proxy: {e}")

    # Start systray icon
    try:
        log(f"Calm Web started. Proxy on {settings.PROXY_BIND_IP}:{settings.PROXY_PORT}, blocking {'enabled' if settings.block_enabled else 'disabled'}.")

        # Hook signals to allow graceful termination
        def _signal_handler(signum, frame):
            log(f"Signal {signum} received, stopping.")
            try:
                modules['restore_original_proxy_settings']()
                log("Proxy settings restored after interruption.")
            except Exception as e:
                log(f"Error restoring proxy during interruption: {e}")
            modules['quit_app'](None)

        try:
            signal.signal(signal.SIGINT, _signal_handler)
            signal.signal(signal.SIGTERM, _signal_handler)
            if hasattr(signal, 'SIGBREAK'):  # Windows
                signal.signal(signal.SIGBREAK, _signal_handler)
        except Exception:
            pass

        # Try to start system tray
        modules['create_system_tray']()

    except Exception as e:
        log(f"Error systray / run: {e}")
        # If systray fails, keep server in background
        def _headless_signal_handler(signum, frame):
            log(f"Signal {signum} received in headless mode, stopping.")
            try:
                modules['restore_original_proxy_settings']()
                log("Proxy settings restored after interruption.")
            except Exception as e:
                log(f"Error restoring proxy during interruption: {e}")
            modules['quit_app'](None)

        try:
            signal.signal(signal.SIGINT, _headless_signal_handler)
            signal.signal(signal.SIGTERM, _headless_signal_handler)
            if hasattr(signal, 'SIGBREAK'):  # Windows
                signal.signal(signal.SIGBREAK, _headless_signal_handler)
        except Exception:
            pass

        try:
            while not settings._SHUTDOWN_EVENT.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            try:
                modules['restore_original_proxy_settings']()
                log("Proxy settings restored after KeyboardInterrupt.")
            except Exception as e:
                log(f"Error restoring proxy during KeyboardInterrupt: {e}")
            modules['quit_app'](None)

def robust_main():
    """Robust main function with error handling."""
    modules = safe_import()
    if not modules:
        print("FATAL: Could not import required modules")
        try:
            input("Press Enter to exit...")
        except (EOFError, OSError, RuntimeError):
            # Handle case where stdin is not available (e.g., PyInstaller executable)
            import time
            time.sleep(3)
        sys.exit(1)

    try:
        if len(sys.argv) > 1:
            if sys.argv[1].lower() == "install":
                modules['install']()
                return
            elif sys.argv[1].lower() == "uninstall":
                modules['uninstall']()
                return

        # Default: run CalmWeb
        run_calmweb()

    except KeyboardInterrupt:
        print("Interrupted by user")
        try:
            modules['restore_original_proxy_settings']()
        except Exception:
            pass
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error in main: {e}")
        try:
            modules['restore_original_proxy_settings']()
        except Exception:
            pass
        sys.exit(1)

def main():
    """Main entry point for the application."""
    robust_main()

if __name__ == "__main__":
    main()