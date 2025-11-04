#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Custom configuration file handling for CalmWeb.
Manages custom.cfg parsing, writing, and red flag domains.
"""

import os
import sys
from datetime import datetime
import urllib3

from .settings import (
    USER_CFG_DIR, USER_CFG_PATH, CUSTOM_CFG_NAME,
    RED_FLAG_CACHE_PATH, RED_FLAG_TIMESTAMP_PATH,
    manual_blocked_domains, whitelisted_domains,
    block_ip_direct, block_http_traffic, block_http_other_ports,
    _CONFIG_LOCK
)
from ..utils.logging import log


def get_custom_cfg_path(install_dir=None):
    """
    Returns the path to custom.cfg: prioritizes APPDATA, then install_dir, then current directory.
    """
    try:
        if USER_CFG_DIR:
            return USER_CFG_PATH
    except Exception:
        pass
    if install_dir and os.path.isdir(install_dir):
        return os.path.join(install_dir, CUSTOM_CFG_NAME)
    return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), CUSTOM_CFG_NAME)


def write_default_custom_cfg(path, blocked_set, whitelist_set):
    """
    Writes a default custom.cfg file. Does not raise exceptions.
    Includes block_ip_direct, block_http_traffic and block_http_other_ports options.
    """
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            # --- BLOCK Section ---
            f.write("[BLOCK]\n")
            for d in sorted(blocked_set):
                f.write(f"{d}\n")

            # --- WHITELIST Section ---
            f.write("\n[WHITELIST]\n")
            for d in sorted(whitelist_set):
                f.write(f"{d}\n")

            # --- OPTIONS Section ---
            f.write("\n[OPTIONS]\n")
            f.write("block_ip_direct = 1\n")
            f.write("block_http_traffic = 1\n")
            f.write("block_http_other_ports = 1\n")

        log(f"Configuration file created: {path}")
    except Exception as e:
        log(f"Error writing custom.cfg {path}: {e}")


def parse_custom_cfg(path):
    """
    Parses a simple custom.cfg file. Returns (blocked_set, whitelist_set).
    Error tolerant.
    """
    from .settings import block_ip_direct, block_http_traffic, block_http_other_ports

    blocked = set()
    whitelist = set()

    # Default values
    block_ip_direct = True
    block_http_traffic = True
    block_http_other_ports = True

    if not os.path.exists(path):
        log(f"custom.cfg not found at {path}")
        return blocked, whitelist

    section = None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for raw in f:
                try:
                    line = raw.strip()
                    if not line or line.startswith('#'):
                        continue
                    up = line.upper()
                    if up == "[BLOCK]":
                        section = "BLOCK"
                        continue
                    elif up == "[WHITELIST]":
                        section = "WHITELIST"
                        continue
                    elif up == "[OPTIONS]":
                        section = "OPTIONS"
                        continue

                    if section == "BLOCK":
                        blocked.add(line.lower().lstrip('.'))
                    elif section == "WHITELIST":
                        whitelist.add(line.lower().lstrip('.'))
                    elif section == "OPTIONS":
                        try:
                            key, val = line.split('=', 1)
                            key = key.strip().lower()
                            val = val.strip().lower()
                            enabled = val in ("1", "true", "yes", "on")
                            if key == "block_ip_direct":
                                block_ip_direct = enabled
                            elif key == "block_http_traffic":
                                block_http_traffic = enabled
                            elif key == "block_http_other_ports":
                                block_http_other_ports = enabled
                        except Exception:
                            # Malformed line -> ignore
                            pass
                    else:
                        blocked.add(line.lower().lstrip('.'))
                except Exception:
                    # Ignore problematic line
                    continue

        log(
            f"custom.cfg loaded: {len(blocked)} blocked, {len(whitelist)} whitelist, "
            f"IP block={block_ip_direct}, HTTP block={block_http_traffic}, "
            f"HTTP other ports={block_http_other_ports}"
        )
    except Exception as e:
        log(f"Error reading custom.cfg {path}: {e}")

    return blocked, whitelist


def ensure_custom_cfg_exists(install_dir, default_blocked, default_whitelist):
    """
    Ensures custom.cfg exists in APPDATA preferentially, otherwise in installation directory.
    Returns the path used.
    """
    try:
        if not os.path.isdir(USER_CFG_DIR):
            os.makedirs(USER_CFG_DIR, exist_ok=True)
        if not os.path.exists(USER_CFG_PATH):
            write_default_custom_cfg(USER_CFG_PATH, default_blocked, default_whitelist)
        return USER_CFG_PATH
    except Exception as e:
        log(f"Error ensure_custom_cfg_exists (APPDATA): {e}")

    cfg_path = get_custom_cfg_path(install_dir)
    if not os.path.exists(cfg_path):
        try:
            write_default_custom_cfg(cfg_path, default_blocked, default_whitelist)
        except Exception as e:
            log(f"Error writing fallback custom.cfg {cfg_path}: {e}")
    return cfg_path


def load_custom_cfg_to_globals(path):
    """
    Loads user config to global variables.
    """
    from .settings import manual_blocked_domains, whitelisted_domains

    blocked, whitelist = parse_custom_cfg(path)
    with _CONFIG_LOCK:
        if blocked:
            manual_blocked_domains.clear()
            manual_blocked_domains.update(blocked)
        if whitelist:
            whitelisted_domains.clear()
            whitelisted_domains.update(whitelist)
    return manual_blocked_domains, whitelisted_domains


# === Red Flag Domains Auto-Update ===

def should_update_red_flag_domains():
    """Checks if red.flag.domains should be updated (daily)"""
    try:
        if not os.path.exists(RED_FLAG_TIMESTAMP_PATH):
            return True

        with open(RED_FLAG_TIMESTAMP_PATH, 'r') as f:
            last_update_str = f.read().strip()

        last_update = datetime.fromisoformat(last_update_str)
        now = datetime.now()

        # Update if more than 24h or new day
        return (now - last_update).total_seconds() > 86400 or now.date() > last_update.date()

    except Exception as e:
        log(f"Error checking red.flag.domains timestamp: {e}")
        return True


def download_red_flag_domains():
    """Downloads and caches red.flag.domains locally"""
    try:
        log("📥 Downloading red.flag.domains...")

        # Create directory if necessary
        os.makedirs(USER_CFG_DIR, exist_ok=True)

        # Download with urllib3
        http = urllib3.PoolManager()
        response = http.request(
            "GET",
            "https://dl.red.flag.domains/pihole/red.flag.domains.txt",
            timeout=urllib3.Timeout(connect=10.0, read=30.0)
        )

        if response.status == 200:
            # Save file
            with open(RED_FLAG_CACHE_PATH, 'wb') as f:
                f.write(response.data)

            # Mark update date
            with open(RED_FLAG_TIMESTAMP_PATH, 'w') as f:
                f.write(datetime.now().isoformat())

            log(f"✅ red.flag.domains updated ({len(response.data)} bytes)")
            return True
        else:
            log(f"❌ Failed downloading red.flag.domains: HTTP {response.status}")
            return False

    except Exception as e:
        log(f"❌ Error downloading red.flag.domains: {e}")
        return False


def get_red_flag_domains_path():
    """Returns path to red.flag.domains cache file"""
    return RED_FLAG_CACHE_PATH


def get_blocklist_urls():
    """Returns the list of blocklist URLs including red.flag.domains if available

    Domains listed in these lists: All credits to them!
    """
    # Configuration demandée : 6 listes spécifiques
    urls = [
        "https://raw.githubusercontent.com/StevenBlack/hosts/refs/heads/master/hosts",
        "https://raw.githubusercontent.com/easylist/listefr/refs/heads/master/hosts.txt",
        "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/ultimate.txt",
        "https://raw.githubusercontent.com/Tontonjo/calmweb/refs/heads/main/filters/blocklist.txt",
        "https://dl.red.flag.domains/pihole/red.flag.domains.txt",
        "https://urlhaus.abuse.ch/downloads/csv/"
    ]

    # Note: red.flag.domains is already included in the URL list above

    return urls


def write_settings_to_custom_cfg():
    """Write current settings to custom.cfg file."""
    from .settings import (
        block_enabled, block_ip_direct, block_http_traffic, block_http_other_ports,
        manual_blocked_domains, whitelisted_domains, _CONFIG_LOCK
    )

    try:
        cfg_path = get_custom_cfg_path()

        # Ensure directory exists
        os.makedirs(os.path.dirname(cfg_path), exist_ok=True)

        with _CONFIG_LOCK:
            with open(cfg_path, 'w', encoding='utf-8') as f:
                # Header
                f.write("# CalmWeb Custom Configuration\n")
                f.write("# Generated automatically - edit with caution\n\n")

                # Settings section
                f.write("[SETTINGS]\n")
                f.write(f"block_enabled={'true' if block_enabled else 'false'}\n")
                f.write(f"block_ip_direct={'true' if block_ip_direct else 'false'}\n")
                f.write(f"block_http_traffic={'true' if block_http_traffic else 'false'}\n")
                f.write(f"block_http_other_ports={'true' if block_http_other_ports else 'false'}\n\n")

                # Blocked domains section
                f.write("[BLOCK]\n")
                for domain in sorted(manual_blocked_domains):
                    f.write(f"{domain}\n")
                f.write("\n")

                # Whitelisted domains section
                f.write("[WHITELIST]\n")
                for domain in sorted(whitelisted_domains):
                    f.write(f"{domain}\n")
                f.write("\n")

        log(f"Settings and domains written to {cfg_path}")

    except Exception as e:
        log(f"Error writing settings to custom.cfg: {e}")
        raise


def write_domains_to_custom_cfg():
    """Write only domains to custom.cfg file, preserving other settings."""
    write_settings_to_custom_cfg()  # For simplicity, write everything


def write_blocklists_to_custom_cfg():
    """Write blocklists configuration to custom.cfg file."""
    from .settings import WHITELIST_URLS, _CONFIG_LOCK
    from ..web.api_blocklists_handlers import _CURRENT_BLOCKLIST_URLS, _BLOCKLIST_LOCK

    try:
        cfg_path = get_custom_cfg_path()

        # Read existing config to preserve other sections
        existing_sections = {}
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    current_section = None
                    for line in f:
                        line = line.strip()
                        if line.startswith('[') and line.endswith(']'):
                            current_section = line[1:-1].upper()
                            if current_section not in ['BLOCKLISTS', 'WHITELISTS']:
                                existing_sections[current_section] = []
                        elif current_section and current_section not in ['BLOCKLISTS', 'WHITELISTS']:
                            if line and not line.startswith('#'):
                                existing_sections[current_section].append(line)
            except Exception as e:
                log(f"Error reading existing config: {e}")

        # Write updated config
        os.makedirs(os.path.dirname(cfg_path), exist_ok=True)

        with open(cfg_path, 'w', encoding='utf-8') as f:
            # Header
            f.write("# CalmWeb Custom Configuration\n")
            f.write("# Generated automatically - edit with caution\n\n")

            # Write preserved sections
            for section, lines in existing_sections.items():
                f.write(f"[{section}]\n")
                for line in lines:
                    f.write(f"{line}\n")
                f.write("\n")

            # Write blocklists section
            f.write("[BLOCKLISTS]\n")
            with _BLOCKLIST_LOCK:
                for url in _CURRENT_BLOCKLIST_URLS:
                    f.write(f"{url}\n")
            f.write("\n")

            # Write whitelists section
            f.write("[WHITELISTS]\n")
            for url in WHITELIST_URLS:
                f.write(f"{url}\n")
            f.write("\n")

        log(f"Blocklists written to {cfg_path}")

    except Exception as e:
        log(f"Error writing blocklists to custom.cfg: {e}")
        raise


def load_enhanced_custom_cfg(path):
    """Load enhanced custom.cfg with support for all sections."""
    from .settings import (
        manual_blocked_domains, whitelisted_domains, WHITELIST_URLS,
        block_enabled, block_ip_direct, block_http_traffic, block_http_other_ports,
        _CONFIG_LOCK
    )
    from ..web.api_blocklists_handlers import _CURRENT_BLOCKLIST_URLS, _BLOCKLIST_LOCK

    if not os.path.exists(path):
        log(f"Enhanced config not found at {path}")
        return

    section = None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for raw in f:
                try:
                    line = raw.strip()
                    if not line or line.startswith('#'):
                        continue

                    # Section headers
                    if line.startswith('[') and line.endswith(']'):
                        section = line[1:-1].upper()
                        continue

                    # Process content based on section
                    if section == "SETTINGS":
                        if '=' in line:
                            key, val = line.split('=', 1)
                            key = key.strip().lower()
                            val = val.strip().lower()
                            enabled = val in ("1", "true", "yes", "on")

                            # Update settings module directly
                            import calmweb.config.settings as settings
                            with _CONFIG_LOCK:
                                if key == "block_enabled":
                                    settings.block_enabled = enabled
                                elif key == "block_ip_direct":
                                    settings.block_ip_direct = enabled
                                elif key == "block_http_traffic":
                                    settings.block_http_traffic = enabled
                                elif key == "block_http_other_ports":
                                    settings.block_http_other_ports = enabled

                    elif section == "BLOCK":
                        domain = line.lower().lstrip('.')
                        if domain:
                            with _CONFIG_LOCK:
                                manual_blocked_domains.add(domain)

                    elif section == "WHITELIST":
                        domain = line.lower().lstrip('.')
                        if domain:
                            with _CONFIG_LOCK:
                                whitelisted_domains.add(domain)

                    elif section == "BLOCKLISTS":
                        url = line.strip()
                        if url.startswith('http'):
                            with _BLOCKLIST_LOCK:
                                if url not in _CURRENT_BLOCKLIST_URLS:
                                    _CURRENT_BLOCKLIST_URLS.append(url)

                    elif section == "WHITELISTS":
                        url = line.strip()
                        if url.startswith('http'):
                            if url not in WHITELIST_URLS:
                                WHITELIST_URLS.append(url)

                except Exception:
                    # Ignore malformed lines
                    continue

        log(f"Enhanced config loaded from {path}")

    except Exception as e:
        log(f"Error loading enhanced config: {e}")


def ensure_enhanced_custom_cfg_exists():
    """Ensure enhanced custom.cfg exists with all sections."""
    try:
        cfg_path = get_custom_cfg_path()
        if not os.path.exists(cfg_path):
            # Create default config with all sections
            write_settings_to_custom_cfg()
            write_blocklists_to_custom_cfg()
        return cfg_path
    except Exception as e:
        log(f"Error ensuring enhanced config exists: {e}")
        return get_custom_cfg_path()