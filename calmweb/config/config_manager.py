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

    def sync_to_legacy_settings(self, settings_module):
        """Sync current configuration to legacy settings module."""
        with self._lock:
            settings_module.block_enabled = self._block_enabled
            settings_module.block_ip_direct = self._block_ip_direct
            settings_module.block_http_traffic = self._block_http_traffic
            settings_module.block_http_other_ports = self._block_http_other_ports


# Global instance
config_manager = ConfigManager()