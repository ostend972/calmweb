#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
System utilities for CalmWeb.
Handles Windows-specific functionality like icons and firewall rules.
"""

import platform
import subprocess

# Import PIL seulement si disponible
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Imports conditionnels pour PyInstaller
try:
    from ..config.settings import WIN32_AVAILABLE
    from ..utils.logging import log
except ImportError:
    # Import alternatif pour PyInstaller
    try:
        from config.settings import WIN32_AVAILABLE
        from utils.logging import log
    except ImportError:
        WIN32_AVAILABLE = False
        def log(msg):
            print(msg)

if WIN32_AVAILABLE:
    import win32ui
    import win32gui
    import win32con


def get_exe_icon(path, size=(64, 64)):
    """
    Retrieves the executable icon and converts it to PIL.Image.
    Returns None if impossible. Compatible non-Windows (returns None).
    """
    if not WIN32_AVAILABLE or not PIL_AVAILABLE:
        return None
    try:
        large, small = win32gui.ExtractIconEx(path, 0)
    except Exception as e:
        log(f"get_exe_icon: ExtractIconEx error: {e}")
        return None

    if (not small) and (not large):
        return None

    try:
        hicon = large[0] if large else small[0]
    except Exception:
        return None

    # Create compatible DC
    try:
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hdc_mem = hdc.CreateCompatibleDC()
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, size[0], size[1])
        hdc_mem.SelectObject(hbmp)
        win32gui.DrawIconEx(hdc_mem.GetSafeHdc(), 0, 0, hicon, size[0], size[1], 0, 0, win32con.DI_NORMAL)
        bmpinfo = hbmp.GetInfo()
        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )
    except Exception as e:
        log(f"get_exe_icon: conversion error: {e}")
        img = None
    finally:
        try:
            win32gui.DestroyIcon(hicon)
        except Exception:
            pass
        try:
            hdc_mem.DeleteDC()
            hdc.DeleteDC()
            win32gui.ReleaseDC(0, 0)
        except Exception:
            pass
    return img


def add_firewall_rule(target_file):
    """
    Attempts to add a firewall rule via netsh. Captures errors.
    """
    try:
        if platform.system().lower() != 'windows':
            log("add_firewall_rule: non-Windows, skip.")
            return
        subprocess.run([
            "netsh", "advfirewall", "firewall", "add", "rule",
            "name=CalmWeb", "dir=in", "action=allow",
            "program=" + target_file, "profile=any"
        ], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        log("Firewall rules added.")
    except Exception as e:
        log(f"Firewall error: {e}")