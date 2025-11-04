#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Helper module to fetch external domains from blocklists and whitelists.
Downloads and parses external lists to provide domain data for the API.
"""

import urllib3
import ssl
import time
import threading
from typing import Set, List, Tuple

from ..config.custom_config import get_blocklist_urls
from ..config.settings import WHITELIST_URLS
from ..utils.logging import log


class ExternalDomainsProvider:
    """Provides access to external domains from blocklists and whitelists."""

    def __init__(self):
        self.external_blocked = set()
        self.external_allowed = set()
        self.last_update = 0
        self.update_interval = 300  # 5 minutes cache
        self._lock = threading.RLock()
        self._updating = False

    def _parse_hosts_file(self, content: str) -> Set[str]:
        """Parse hosts file content and extract domains."""
        domains = set()

        for line in content.splitlines():
            try:
                # Remove comments
                line = line.split('#', 1)[0].strip()
                if not line:
                    continue

                parts = line.split()
                domain = None

                if len(parts) == 1:
                    # Single domain
                    domain = parts[0]
                elif len(parts) >= 2:
                    # hosts format: IP domain
                    if not self._looks_like_ip(parts[0]):
                        domain = parts[0]
                    else:
                        domain = parts[1]

                if domain:
                    domain = domain.lower().lstrip('.')
                    if domain and not self._looks_like_ip(domain) and len(domain) <= 253:
                        domains.add(domain)

            except Exception:
                continue

        return domains

    def _looks_like_ip(self, s: str) -> bool:
        """Check if string looks like an IP address."""
        try:
            import ipaddress
            ipaddress.ip_address(s)
            return True
        except Exception:
            return False

    def _download_list(self, url: str) -> Set[str]:
        """Download and parse a single blocklist/whitelist."""
        try:
            http = urllib3.PoolManager(
                cert_reqs='CERT_REQUIRED',
                ssl_context=ssl.create_default_context()
            )

            # Handle local files
            if url.startswith("file://"):
                file_path = url[7:]
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception as e:
                    log(f"Could not read local file {file_path}: {e}")
                    return set()
            else:
                # Download HTTP/HTTPS
                response = http.request(
                    "GET", url,
                    timeout=urllib3.Timeout(connect=10.0, read=30.0)
                )

                if response.status != 200:
                    log(f"HTTP {response.status} for {url}")
                    return set()

                content = response.data.decode("utf-8", errors='ignore')

            # Parse content
            domains = self._parse_hosts_file(content)
            log(f"Parsed {len(domains)} domains from {url}")
            return domains

        except Exception as e:
            log(f"Error downloading {url}: {e}")
            return set()

    def _update_external_domains(self):
        """Update external domains from all sources."""
        if self._updating:
            return

        self._updating = True
        try:
            log("🔄 Updating external domains...")

            # Get blocklist URLs
            blocklist_urls = get_blocklist_urls()

            # Download blocklists
            new_blocked = set()
            for url in blocklist_urls[:3]:  # Limit to first 3 for performance
                domains = self._download_list(url)
                new_blocked.update(domains)

                # Limit total domains for performance
                if len(new_blocked) > 100000:
                    log(f"Limiting blocked domains to 100k for performance")
                    break

            # Download whitelists
            new_allowed = set()
            for url in WHITELIST_URLS:
                domains = self._download_list(url)
                new_allowed.update(domains)

            # Update with lock
            with self._lock:
                self.external_blocked = new_blocked
                self.external_allowed = new_allowed
                self.last_update = time.time()

            log(f"✅ Updated external domains: {len(new_blocked)} blocked, {len(new_allowed)} allowed")

        except Exception as e:
            log(f"❌ Error updating external domains: {e}")
        finally:
            self._updating = False

    def get_external_domains(self) -> Tuple[List[str], List[str]]:
        """Get external blocked and allowed domains."""
        # Check if update needed
        if time.time() - self.last_update > self.update_interval:
            # Start update in background
            threading.Thread(
                target=self._update_external_domains,
                daemon=True,
                name="ExternalDomainsUpdate"
            ).start()

        # Return current data
        with self._lock:
            blocked = sorted(list(self.external_blocked))
            allowed = sorted(list(self.external_allowed))

        return blocked, allowed

    def get_sample_domains(self, max_blocked: int = 1000, max_allowed: int = 100) -> Tuple[List[str], List[str]]:
        """Get a sample of external domains for display."""
        blocked, allowed = self.get_external_domains()

        # Return limited samples
        return blocked[:max_blocked], allowed[:max_allowed]


# Global instance
_external_provider = ExternalDomainsProvider()

def get_external_blocked_domains(limit: int = 1000) -> List[str]:
    """Get external blocked domains (limited for performance)."""
    blocked, _ = _external_provider.get_sample_domains(max_blocked=limit)
    return blocked

def get_external_allowed_domains(limit: int = 100) -> List[str]:
    """Get external allowed domains (limited for performance)."""
    _, allowed = _external_provider.get_sample_domains(max_allowed=limit)
    return allowed

def get_external_domains_count() -> Tuple[int, int]:
    """Get total count of external domains."""
    blocked, allowed = _external_provider.get_external_domains()
    return len(blocked), len(allowed)

def force_update_external_domains():
    """Force immediate update of external domains."""
    _external_provider._update_external_domains()