#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
System proxy management for CalmWeb.
Handles saving and restoring system proxy settings.
"""

import os
import platform
import subprocess

from ..config.settings import original_proxy_settings
from ..utils.logging import log


def save_original_proxy_settings():
    """
    Saves original proxy settings before modification.
    """
    global original_proxy_settings
    try:
        if platform.system().lower() != 'windows':
            return

        # Save environment variables
        original_proxy_settings['http_proxy_env'] = os.environ.get('HTTP_PROXY', '')
        original_proxy_settings['https_proxy_env'] = os.environ.get('HTTPS_PROXY', '')

        # Save Windows registry settings
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_READ)
            try:
                original_proxy_settings['registry_proxy_enable'] = winreg.QueryValueEx(key, "ProxyEnable")[0]
            except FileNotFoundError:
                original_proxy_settings['registry_proxy_enable'] = 0
            try:
                original_proxy_settings['registry_proxy_server'] = winreg.QueryValueEx(key, "ProxyServer")[0]
            except FileNotFoundError:
                original_proxy_settings['registry_proxy_server'] = ""
            winreg.CloseKey(key)
        except Exception as e:
            log(f"Error saving registry: {e}")

        # Save winhttp settings
        try:
            result = subprocess.run(["netsh", "winhttp", "show", "proxy"],
                                  capture_output=True, text=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0:
                original_proxy_settings['winhttp_proxy'] = result.stdout.strip()
            else:
                original_proxy_settings['winhttp_proxy'] = "Direct access (no proxy server)."
        except Exception as e:
            log(f"Error saving winhttp: {e}")
            original_proxy_settings['winhttp_proxy'] = "Direct access (no proxy server)."

        log("Original proxy settings saved")

    except Exception as e:
        log(f"Error save_original_proxy_settings: {e}")


def restore_original_proxy_settings():
    """
    Restores saved original proxy settings.
    """
    global original_proxy_settings
    try:
        if platform.system().lower() != 'windows':
            return

        log("Restoring original proxy settings...")

        # Restore winhttp
        if original_proxy_settings['winhttp_proxy']:
            try:
                if "Direct access" in original_proxy_settings['winhttp_proxy']:
                    subprocess.run(["netsh", "winhttp", "reset", "proxy"],
                                 check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    # Extract proxy from saved output if necessary
                    subprocess.run(["netsh", "winhttp", "reset", "proxy"],
                                 check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception as e:
                log(f"Error restoring winhttp: {e}")

        # Restore environment variables
        try:
            if original_proxy_settings['http_proxy_env'] is not None:
                if original_proxy_settings['http_proxy_env']:
                    subprocess.run(["setx", "HTTP_PROXY", original_proxy_settings['http_proxy_env']],
                                 check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    subprocess.run(["setx", "HTTP_PROXY", ""],
                                 check=False, creationflags=subprocess.CREATE_NO_WINDOW)

            if original_proxy_settings['https_proxy_env'] is not None:
                if original_proxy_settings['https_proxy_env']:
                    subprocess.run(["setx", "HTTPS_PROXY", original_proxy_settings['https_proxy_env']],
                                 check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    subprocess.run(["setx", "HTTPS_PROXY", ""],
                                 check=False, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            log(f"Error restoring environment variables: {e}")

        # Restore registry
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_SET_VALUE)

            if original_proxy_settings['registry_proxy_enable'] is not None:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD,
                                original_proxy_settings['registry_proxy_enable'])

            if original_proxy_settings['registry_proxy_server'] is not None:
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ,
                                original_proxy_settings['registry_proxy_server'])

            winreg.CloseKey(key)
        except Exception as e:
            log(f"Error restoring registry: {e}")

        log("Original proxy settings restored")

    except Exception as e:
        log(f"Error restore_original_proxy_settings: {e}")


def set_system_proxy(enable=True, host="127.0.0.1", port=8080):
    """
    Configure system proxy settings.
    """
    try:
        if platform.system().lower() != 'windows':
            log("set_system_proxy: non-Windows, skip.")
            return

        proxy_server = f"{host}:{port}"

        if enable:
            log(f"Configuring system proxy: {proxy_server}")

            # Configure winhttp proxy
            try:
                subprocess.run([
                    "netsh", "winhttp", "set", "proxy",
                    f"proxy-server={proxy_server}",
                    "bypass-list=localhost;127.0.0.1;*.local"
                ], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
                log("WinHTTP proxy configured")
            except Exception as e:
                log(f"Error configuring winhttp proxy: {e}")

            # Configure Internet Explorer proxy
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                   r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                                   0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy_server)
                winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "localhost;127.0.0.1;*.local")
                winreg.CloseKey(key)
                log("IE proxy configured")
            except Exception as e:
                log(f"Error configuring IE proxy: {e}")

            # Configure environment variables
            try:
                subprocess.run(["setx", "HTTP_PROXY", f"http://{proxy_server}"],
                             check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                subprocess.run(["setx", "HTTPS_PROXY", f"http://{proxy_server}"],
                             check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                log("Environment proxy variables set")
            except Exception as e:
                log(f"Error setting environment variables: {e}")

        else:
            log("Disabling system proxy")

            # Reset winhttp proxy
            try:
                subprocess.run(["netsh", "winhttp", "reset", "proxy"],
                             check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                log("WinHTTP proxy reset")
            except Exception as e:
                log(f"Error resetting winhttp proxy: {e}")

            # Disable IE proxy
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                   r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                                   0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
                log("IE proxy disabled")
            except Exception as e:
                log(f"Error disabling IE proxy: {e}")

            # Clear environment variables
            try:
                subprocess.run(["setx", "HTTP_PROXY", ""],
                             check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                subprocess.run(["setx", "HTTPS_PROXY", ""],
                             check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                log("Environment proxy variables cleared")
            except Exception as e:
                log(f"Error clearing environment variables: {e}")

    except Exception as e:
        log(f"Error set_system_proxy: {e}")