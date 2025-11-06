#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Installation and uninstallation functions for CalmWeb.
Handles file copying, firewall rules, scheduled tasks, and configuration.
"""

import os
import sys
import shutil
import subprocess
import tempfile
import threading
import winreg

from ..config.settings import INSTALL_DIR, EXE_NAME, manual_blocked_domains, whitelisted_domains
from ..config.custom_config import ensure_custom_cfg_exists
from ..utils.logging import log
from ..utils.system import add_firewall_rule
from ..ui.log_window import show_log_window


def install():
    """
    Installation: copy, firewall rule, scheduled task, config, and launch.
    """
    try:
        win = threading.Thread(target=show_log_window, daemon=True)
        win.start()
    except Exception:
        pass

    log("Starting Calm Web installation...")

    try:
        if not os.path.exists(INSTALL_DIR):
            os.makedirs(INSTALL_DIR, exist_ok=True)
            log(f"Directory created: {INSTALL_DIR}")
    except Exception as e:
        log(f"Unable to create INSTALL_DIR {INSTALL_DIR}: {e}")

    # Create custom.cfg in APPDATA if missing (with embedded domains as base)
    cfg_path = ensure_custom_cfg_exists(INSTALL_DIR, manual_blocked_domains, whitelisted_domains)

    # Copy the script/exe
    try:
        current_file = sys.argv[0] if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
        target_file = os.path.join(INSTALL_DIR, EXE_NAME)
        try:
            shutil.copy(current_file, target_file)
            log(f"Copy completed: {target_file}")
        except Exception as e:
            log(f"Error copying file to {target_file}: {e}")
    except Exception as e:
        log(f"Error determining current_file: {e}")

    add_firewall_rule(os.path.join(INSTALL_DIR, EXE_NAME))

    # XML for the task to create
    xml_content = '''<?xml version="1.0" encoding="utf-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2025-10-26T10:16:48</Date>
    <Author>Tonton Jo</Author>
    <URI>CalmWeb</URI>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <StartBoundary>2025-10-26T10:16:00</StartBoundary>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <GroupId>S-1-5-32-544</GroupId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>false</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>true</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>"C:\\Program Files\\CalmWeb\\calmweb.exe"</Command>
    </Exec>
  </Actions>
</Task>'''

    def add_task_from_xml(xml_content_inner):
        tmp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-16') as tmp_file:
                tmp_file.write(xml_content_inner)
                tmp_file_path = tmp_file.name
            if os.path.exists(tmp_file_path):
                try:
                    subprocess.run(["schtasks", "/Create", "/tn", "CalmWeb", "/XML", tmp_file_path, "/F"], check=True)
                    log(f"Scheduled task added successfully.")
                except subprocess.CalledProcessError as e:
                    log(f"Error adding scheduled task: {e}")
                except Exception as e:
                    log(f"Unexpected schtasks error: {e}")
            else:
                log(f"Error: temporary XML file could not be created at {tmp_file_path}")
        except Exception as e:
            log(f"Error add_task_from_xml: {e}")
        finally:
            if tmp_file_path and os.path.exists(tmp_file_path):
                try:
                    os.unlink(tmp_file_path)
                except Exception:
                    pass

    add_task_from_xml(xml_content)

    # Add registry entry for Windows startup applications
    try:
        target_file = os.path.join(INSTALL_DIR, EXE_NAME)
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "CalmWeb", 0, winreg.REG_SZ, target_file)
            log("Registry startup entry added successfully.")
    except Exception as e:
        log(f"Error adding registry startup entry: {e}")

    log("✅ Installation completed! CalmWeb will start automatically at system startup.")
    log("📊 Dashboard available at: http://127.0.0.1:8081")
    log("⚙️  Configuration file location: %APPDATA%\\CalmWeb\\custom.cfg")
    log("")
    log("🚀 Starting CalmWeb now...")

    # Start CalmWeb after installation
    try:
        from ..main import run_calmweb
        run_calmweb()
    except Exception as e:
        log(f"Error starting CalmWeb: {e}")


def uninstall():
    """
    Uninstallation: remove files, scheduled task, and firewall rules.
    """
    log("Starting CalmWeb uninstallation...")

    # Remove registry startup entry
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE) as key:
            winreg.DeleteValue(key, "CalmWeb")
            log("Registry startup entry removed successfully.")
    except FileNotFoundError:
        log("No registry startup entry found to remove.")
    except Exception as e:
        log(f"Error removing registry startup entry: {e}")

    # Remove scheduled task
    try:
        subprocess.run(["schtasks", "/Delete", "/tn", "CalmWeb", "/F"], check=True)
        log("Scheduled task removed successfully.")
    except subprocess.CalledProcessError as e:
        log(f"Error removing scheduled task: {e}")
    except Exception as e:
        log(f"Unexpected error removing task: {e}")

    # Remove firewall rule
    try:
        subprocess.run([
            "netsh", "advfirewall", "firewall", "delete", "rule",
            "name=CalmWeb"
        ], check=True)
        log("Firewall rule removed successfully.")
    except subprocess.CalledProcessError as e:
        log(f"Error removing firewall rule: {e}")
    except Exception as e:
        log(f"Unexpected error removing firewall rule: {e}")

    # Remove installation directory
    try:
        if os.path.exists(INSTALL_DIR):
            shutil.rmtree(INSTALL_DIR)
            log(f"Installation directory removed: {INSTALL_DIR}")
    except Exception as e:
        log(f"Error removing installation directory: {e}")

    log("✅ Uninstallation completed!")
    log("Note: User configuration files in %APPDATA%\\CalmWeb have been preserved.")