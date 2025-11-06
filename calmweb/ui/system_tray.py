#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
System tray interface for CalmWeb.
Provides a system tray icon with menu options.
"""

import os
import sys
import platform
import subprocess
import threading
import webbrowser
from PIL import Image, ImageDraw
from pystray import Icon, MenuItem, Menu

from ..config.config_manager import config_manager
from ..config.settings import (
    CALMWEB_VERSION, INSTALL_DIR, DASHBOARD_PORT, _SHUTDOWN_EVENT
)
from ..config.custom_config import get_custom_cfg_path, write_default_custom_cfg, load_custom_cfg_to_globals
from ..utils.logging import log
from ..utils.system import get_exe_icon
# Removed log_window import to avoid Tkinter crashes

# Global variables that will be set by main module
current_resolver = None
set_system_proxy = None
restore_original_proxy_settings = None
stop_proxy_server = None

# Global system tray icon reference
global_tray_icon = None
stop_dashboard_server = None


def create_image():
    """
    Creates a generic icon if icon extraction fails.
    """
    try:
        image = Image.new('RGB', (64, 64), (255, 255, 255))
        d = ImageDraw.Draw(image)
        d.rectangle([(8, 16), (56, 48)], outline=(0, 0, 0))
        d.text((18, 22), "CW", fill=(0, 0, 0))
        return image
    except Exception:
        return None


def open_config_in_editor(path):
    """
    Opens the config file in the default editor (non-blocking).
    """
    try:
        if not os.path.exists(path):
            log(f"custom.cfg missing, creating before opening: {path}")
            from ..config.settings import manual_blocked_domains, whitelisted_domains
            write_default_custom_cfg(path, manual_blocked_domains, whitelisted_domains)

        # Open with default editor on separate thread to not block UI
        def _open():
            try:
                if platform.system().lower() == 'windows':
                    # Use os.startfile which opens with default application
                    os.startfile(path)
                    log(f"File opened with default editor: {path}")
                else:
                    # fallback for non-windows: try xdg-open
                    if hasattr(os, "startfile"):
                        os.startfile(path)
                        log(f"File opened with default editor: {path}")
                    else:
                        subprocess.Popen(['xdg-open', path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        log(f"File opened with xdg-open: {path}")
            except Exception as e:
                log(f"Error opening default editor for {path}: {e}")
                # Fallback: try notepad as last resort on Windows
                try:
                    if platform.system().lower() == 'windows':
                        log(f"Attempting fallback with notepad.exe...")
                        subprocess.Popen(['notepad.exe', path])
                        log(f"File opened with Notepad: {path}")
                    else:
                        # Try nano or vim
                        log(f"Attempting fallback with nano...")
                        subprocess.Popen(['nano', path])
                        log(f"File opened with nano: {path}")
                except Exception as e2:
                    log(f"ERROR: Unable to open {path} with any editor. {e2}")
                    log(f"Please manually open the file: {path}")

        threading.Thread(target=_open, daemon=True).start()
        log(f"Opening configuration file: {path}")
    except Exception as e:
        log(f"Error opening editor for {path}: {e}")


def reload_config_action(icon=None, item=None):
    """
    Reloads the custom.cfg file and relaunches complete loading of blocklists and whitelists.
    """
    try:
        cfg_path = get_custom_cfg_path(INSTALL_DIR)
        if not os.path.exists(cfg_path):
            log(f"No custom.cfg found to reload: {cfg_path}")
            return

        # Reload global variables from custom.cfg file
        load_custom_cfg_to_globals(cfg_path)
        log("Local configuration reloaded from user file.")

        # Also update config_manager to ensure synchronization
        try:
            from ..config.config_manager import config_manager
            from ..config import settings
            config_manager.update_from_legacy_settings(settings)
            log("Config manager synchronized after reload")
        except Exception as e:
            log(f"Warning: Could not sync config_manager after reload: {e}")

        global current_resolver
        if current_resolver:
            # Launch both reloads (blocklist + whitelist) in parallel
            threading.Thread(target=current_resolver._load_blocklist, daemon=True).start()
            threading.Thread(target=current_resolver._load_whitelist, daemon=True).start()
            log("Request for complete reload of external blocklists and whitelists (thread).")
        else:
            log("[WARN] No active resolver for reload.")

    except Exception as e:
        log(f"Error during configuration reload: {e}")


def open_dashboard(icon=None, item=None):
    """
    Opens the dashboard in the default browser.
    """
    try:
        dashboard_url = f"http://127.0.0.1:{DASHBOARD_PORT}"
        webbrowser.open(dashboard_url)
        log(f"Dashboard opened in browser: {dashboard_url}")
    except Exception as e:
        log(f"Error opening dashboard: {e}")

def open_logs(icon=None, item=None):
    """
    Opens the dashboard logs page in the default browser.
    """
    try:
        logs_url = f"http://127.0.0.1:{DASHBOARD_PORT}?tab=logs"
        webbrowser.open(logs_url)
        log(f"Logs page opened in browser: {logs_url}")
    except Exception as e:
        log(f"Error opening logs page: {e}")


def toggle_block(icon, item):
    """Toggle blocking on/off."""
    config_manager.block_enabled = not config_manager.block_enabled

    state = "enabled" if config_manager.block_enabled else "disabled"
    log(f"Calm Web: blocking {state}")
    try:
        if set_system_proxy:
            set_system_proxy(enable=config_manager.block_enabled)
    except Exception as e:
        log(f"Error setting system proxy on toggle: {e}")
    update_menu(icon)


def update_menu(icon):
    """
    Rebuilds the systray menu. Safe: completely encapsulates callbacks to avoid unhandled exceptions.
    """
    try:
        icon.menu = Menu(
            MenuItem(f"Calm Web v{CALMWEB_VERSION}", lambda: None, enabled=False),
            MenuItem(f"🔒 Blocking: {'✅ Enabled' if config_manager.block_enabled else '❌ Disabled'}", lambda: None, enabled=False),
            MenuItem("❌ Disable Blocking" if config_manager.block_enabled else "✅ Enable Blocking", toggle_block),
            MenuItem("📊 Open Dashboard", open_dashboard),
            MenuItem("⚙️ Config", Menu(
                MenuItem("✏️ Open / Edit config", lambda icon, item: threading.Thread(target=open_config_in_editor, args=(get_custom_cfg_path(INSTALL_DIR),), daemon=True).start()),
                MenuItem("🔄 Reload config", reload_config_action)
            )),
            MenuItem("📄 Show Logs", open_logs),
            MenuItem("🚪 Quit", quit_app)
        )
        try:
            icon.update_menu()
        except Exception:
            # pystray may throw if icon stopped; ignore
            pass
    except Exception as e:
        log(f"update_menu error: {e}")


def update_tray_from_api():
    """
    Update the system tray icon menu when protection status changes via API.
    This function can be called from API handlers to sync the system tray.
    """
    global global_tray_icon
    if global_tray_icon:
        try:
            update_menu(global_tray_icon)
            log("System tray updated from API")
        except Exception as e:
            log(f"Error updating system tray from API: {e}")
    else:
        log("System tray icon not available for update")


def quit_app(icon=None, item=None):
    """
    Cleanup and clean exit.
    """
    try:
        log("Shutdown requested.")
        _SHUTDOWN_EVENT.set()

        # Restore original proxy settings
        try:
            if restore_original_proxy_settings:
                restore_original_proxy_settings()
                log("Original proxy settings restored.")
        except Exception as e:
            log(f"Error restoring proxy settings: {e}")

        # Stop servers
        try:
            if stop_proxy_server:
                stop_proxy_server()
        except Exception as e:
            log(f"Error stopping proxy server: {e}")

        try:
            if stop_dashboard_server:
                stop_dashboard_server()
        except Exception as e:
            log(f"Error stopping dashboard server: {e}")

        # Stop system tray icon
        if icon:
            try:
                icon.stop()
                log("System tray icon stopped.")
            except Exception as e:
                log(f"Error stopping icon: {e}")

        log("CalmWeb shutdown complete.")

        # Final exit
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

    except Exception as e:
        log(f"Error during shutdown: {e}")
        try:
            os._exit(1)
        except:
            pass


def create_system_tray():
    """Create and run the system tray icon."""
    try:
        # Try to get executable icon
        icon_image = None
        try:
            if getattr(sys, 'frozen', False):
                # If running as executable
                exe_path = sys.executable
                icon_image = get_exe_icon(exe_path)
                if icon_image:
                    log("Executable icon extracted successfully.")
        except Exception as e:
            log(f"Error extracting executable icon: {e}")

        # Fallback to generic icon
        if not icon_image:
            icon_image = create_image()
            log("Using generic icon.")

        if not icon_image:
            log("ERROR: Unable to create any icon.")
            return

        # Create system tray icon
        global global_tray_icon
        icon = Icon("CalmWeb", icon_image)
        global_tray_icon = icon
        update_menu(icon)

        # Register callback for automatic tray updates when config changes
        def on_config_change(setting_name, old_value, new_value):
            if setting_name == 'block_enabled' and global_tray_icon:
                try:
                    update_menu(global_tray_icon)
                    log(f"System tray updated: {setting_name} changed from {old_value} to {new_value}")
                except Exception as e:
                    log(f"Error auto-updating system tray: {e}")

        config_manager.add_change_callback(on_config_change)

        log("System tray icon created. Starting...")
        icon.run()

    except Exception as e:
        log(f"Error creating system tray: {e}")