#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Centralized configuration manager for CalmWeb.
Ensures all modules use the same configuration state.
"""

import threading
from typing import Optional, Callable, List


class ConfigManager:
    """
    Singleton configuration manager that ensures all modules
    share the same configuration state.
    """

    _instance: Optional['ConfigManager'] = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        # Configuration values
        self._block_enabled = True
        self._block_ip_direct = True
        self._block_http_traffic = True
        self._block_http_other_ports = True
        self._configure_ie_proxy = True

        # Callbacks for when configuration changes
        self._change_callbacks: List[Callable] = []
        self._lock = threading.RLock()
        self._initialized = True

    @property
    def block_enabled(self) -> bool:
        with self._lock:
            return self._block_enabled

    @block_enabled.setter
    def block_enabled(self, value: bool):
        with self._lock:
            old_value = self._block_enabled
            self._block_enabled = value
            if old_value != value:
                self._notify_changes('block_enabled', old_value, value)

    @property
    def block_ip_direct(self) -> bool:
        with self._lock:
            return self._block_ip_direct

    @block_ip_direct.setter
    def block_ip_direct(self, value: bool):
        with self._lock:
            old_value = self._block_ip_direct
            self._block_ip_direct = value
            if old_value != value:
                self._notify_changes('block_ip_direct', old_value, value)

    @property
    def block_http_traffic(self) -> bool:
        with self._lock:
            return self._block_http_traffic

    @block_http_traffic.setter
    def block_http_traffic(self, value: bool):
        with self._lock:
            old_value = self._block_http_traffic
            self._block_http_traffic = value
            if old_value != value:
                self._notify_changes('block_http_traffic', old_value, value)

    @property
    def block_http_other_ports(self) -> bool:
        with self._lock:
            return self._block_http_other_ports

    @block_http_other_ports.setter
    def block_http_other_ports(self, value: bool):
        with self._lock:
            old_value = self._block_http_other_ports
            self._block_http_other_ports = value
            if old_value != value:
                self._notify_changes('block_http_other_ports', old_value, value)

    @property
    def configure_ie_proxy(self) -> bool:
        with self._lock:
            return self._configure_ie_proxy

    @configure_ie_proxy.setter
    def configure_ie_proxy(self, value: bool):
        with self._lock:
            old_value = self._configure_ie_proxy
            self._configure_ie_proxy = value
            if old_value != value:
                self._notify_changes('configure_ie_proxy', old_value, value)

    def add_change_callback(self, callback: Callable):
        """Add a callback that will be called when configuration changes."""
        with self._lock:
            if callback not in self._change_callbacks:
                self._change_callbacks.append(callback)

    def remove_change_callback(self, callback: Callable):
        """Remove a change callback."""
        with self._lock:
            if callback in self._change_callbacks:
                self._change_callbacks.remove(callback)

    def _notify_changes(self, setting_name: str, old_value, new_value):
        """Notify all registered callbacks of configuration changes."""
        for callback in self._change_callbacks[:]:  # Copy list to avoid modification during iteration
            try:
                callback(setting_name, old_value, new_value)
            except Exception as e:
                # Log error but don't let one callback break others
                print(f"Error in config change callback: {e}")

    def update_from_legacy_settings(self, settings_module):
        """Update configuration from legacy settings module."""
        with self._lock:
            self._block_enabled = getattr(settings_module, 'block_enabled', True)
            self._block_ip_direct = getattr(settings_module, 'block_ip_direct', True)
            self._block_http_traffic = getattr(settings_module, 'block_http_traffic', True)
            self._block_http_other_ports = getattr(settings_module, 'block_http_other_ports', True)
            self._configure_ie_proxy = getattr(settings_module, 'configure_ie_proxy', False)

    def sync_to_legacy_settings(self, settings_module):
        """Sync current configuration to legacy settings module."""
        with self._lock:
            settings_module.block_enabled = self._block_enabled
            settings_module.block_ip_direct = self._block_ip_direct
            settings_module.block_http_traffic = self._block_http_traffic
            settings_module.block_http_other_ports = self._block_http_other_ports
            settings_module.configure_ie_proxy = self._configure_ie_proxy

    def save_to_file(self):
        """Save protection settings to persistent file."""
        import json
        import os
        from ..utils.logging import log

        try:
            # Get config directory (Windows AppData)
            config_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "CalmWeb")
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            config_file = os.path.join(config_dir, "protection_settings.json")

            settings_data = {
                "block_enabled": self._block_enabled,
                "block_ip_direct": self._block_ip_direct,
                "block_http_traffic": self._block_http_traffic,
                "block_http_other_ports": self._block_http_other_ports,
                "configure_ie_proxy": self._configure_ie_proxy
            }

            with open(config_file, 'w') as f:
                json.dump(settings_data, f, indent=2)

            log(f"Protection settings saved to {config_file}")

        except Exception as e:
            log(f"Error saving protection settings: {e}")

    def load_from_file(self):
        """Load protection settings from persistent file."""
        import json
        import os
        from ..utils.logging import log

        try:
            config_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "CalmWeb")
            config_file = os.path.join(config_dir, "protection_settings.json")

            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    settings_data = json.load(f)

                with self._lock:
                    self._block_enabled = settings_data.get("block_enabled", True)
                    self._block_ip_direct = settings_data.get("block_ip_direct", True)
                    self._block_http_traffic = settings_data.get("block_http_traffic", True)
                    self._block_http_other_ports = settings_data.get("block_http_other_ports", True)
                    self._configure_ie_proxy = settings_data.get("configure_ie_proxy", True)

                log(f"Protection settings loaded from {config_file}")

        except Exception as e:
            log(f"Error loading protection settings: {e}")


# Global instance
config_manager = ConfigManager()