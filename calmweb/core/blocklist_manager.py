#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Blocklist management for CalmWeb.
Handles downloading, parsing, and checking domains against blocklists and whitelists.
"""

import time
import threading
import traceback
import ipaddress
import urllib3
import ssl

from ..config.settings import (
    WHITELIST_URLS, manual_blocked_domains, whitelisted_domains,
    block_ip_direct, _RESOLVER_LOADING
)
from ..utils.logging import log


def _safe_str(obj):
    """Safely convert object to string."""
    try:
        return str(obj)
    except Exception:
        return f"<{type(obj).__name__} object>"


class BlocklistResolver:
    def __init__(self, blocklist_urls, reload_interval=3600):
        self.blocklist_urls = list(blocklist_urls)
        self.reload_interval = max(60, int(reload_interval or 3600))
        self.blocked_domains = set()
        self.last_reload = 0
        self._lock = threading.Lock()
        self._loading_lock = threading.Lock()

        # Dedicated structures for whitelist:
        # - whitelisted_domains: domain names / hosts (string)
        # - whitelisted_networks: ip_network objects for CIDR
        # Both are protected by self._lock
        self.whitelisted_domains_local = set()   # non-global copy; will merge with global if necessary
        self.whitelisted_networks = set()       # set(ipaddress.ip_network(...))

        # Initial loading (tolerant)
        try:
            self._load_blocklist()
            self._load_whitelist()
        except Exception as e:
            log(f"BlocklistResolver init error: {e}")

    def _load_blocklist(self):
        """
        Downloads and parses blocklists. Robustness: retries, timeouts, chunking.
        Defines self.blocked_domains atomically.
        """
        if self._loading_lock.locked():
            log("Blocklist load already in progress, skip.")
            return
        with self._loading_lock:
            _RESOLVER_LOADING.set()
            try:
                domains = set()
                http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ssl_context=ssl.create_default_context())
                for url in self.blocklist_urls:
                    success = False
                    for attempt in range(3):
                        try:
                            log(f"⬇️ Loading blocklist {url} (attempt {attempt+1})")

                            # Support local files (file://)
                            if url.startswith("file://"):
                                file_path = url[7:]  # Remove "file://"
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                            else:
                                # Classic HTTP/HTTPS download
                                response = http.request("GET", url, timeout=urllib3.Timeout(connect=5.0, read=10.0))
                                if response.status != 200:
                                    raise Exception(f"HTTP {response.status}")
                                content = response.data.decode("utf-8", errors='ignore')

                            for line in content.splitlines():
                                try:
                                    line = line.split('#', 1)[0].strip()
                                    if not line:
                                        continue
                                    parts = line.split()
                                    domain = None
                                    if len(parts) == 1:
                                        domain = parts[0]
                                    elif len(parts) >= 2:
                                        if not self._looks_like_ip(parts[0]):
                                            domain = parts[0]
                                        else:
                                            domain = parts[1]
                                    if not domain:
                                        continue
                                    domain = domain.lower().lstrip('.')
                                    if not domain or self._looks_like_ip(domain):
                                        continue
                                    if len(domain) > 253:
                                        continue
                                    # Skip very short domains (TLDs) to prevent false positives
                                    if len(domain) < 3 or '.' not in domain:
                                        continue
                                    domains.add(domain)
                                except Exception:
                                    continue
                            success = True
                            break
                        except Exception as e:
                            log(f"[Error] Loading {url} attempt {attempt+1}: {e}")
                            time.sleep(1 + attempt * 2)
                    if not success:
                        log(f"[⚠️] Failed downloading blocklist from {url}")

                with self._lock:
                    self.blocked_domains = domains
                    self.last_reload = time.time()
                log(f"✅ {len(domains)} blocked domains loaded.")
            except Exception as e:
                log(f"Error _load_blocklist: {e}\n{traceback.format_exc()}")
            finally:
                _RESOLVER_LOADING.clear()

    def _load_whitelist(self):
        """
        Downloads & parses whitelists and updates self.whitelisted_domains_local and self.whitelisted_networks.
        - supports: exact domains, *.example.com (stored as "example.com"), CIDR (1.2.3.0/24), IPs.
        - atomic update of structures protected by self._lock.
        """
        try:
            http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ssl_context=ssl.create_default_context())
            new_domains = set()
            new_networks = set()

            # If a global whitelisted_domains set exists (global), take it as base
            try:
                # copy global domains if defined
                if 'whitelisted_domains' in globals():
                    for d in whitelisted_domains:
                        if isinstance(d, str) and d:
                            new_domains.add(d.lower().lstrip('.'))
            except Exception:
                pass

            for url in WHITELIST_URLS:
                for attempt in range(3):
                    try:
                        log(f"⬇️ Downloading whitelist {url} (attempt {attempt+1})")
                        response = http.request("GET", url, timeout=urllib3.Timeout(connect=5.0, read=10.0))
                        if response.status != 200:
                            raise Exception(f"HTTP {response.status}")
                        content = response.data.decode("utf-8", errors='ignore')
                        for line in content.splitlines():
                            try:
                                line = line.split('#', 1)[0].strip()
                                if not line:
                                    continue
                                entry = line.lower().strip()
                                # wildcard *.example.com -> store example.com
                                if entry.startswith("*."):
                                    domain = entry[2:].lstrip('.')
                                    if domain and not self._looks_like_ip(domain):
                                        new_domains.add(domain)
                                    continue
                                # CIDR or IP network
                                if '/' in entry:
                                    try:
                                        net = ipaddress.ip_network(entry, strict=False)
                                        new_networks.add(net)
                                        continue
                                    except Exception:
                                        # maybe malformed, skip
                                        continue
                                # plain IP
                                if self._looks_like_ip(entry):
                                    new_domains.add(entry)
                                    continue
                                # plain domain
                                entry = entry.lstrip('.')
                                if entry and not self._looks_like_ip(entry) and len(entry) <= 253:
                                    new_domains.add(entry)
                            except Exception:
                                continue
                        break
                    except Exception as e:
                        log(f"[⚠️] Loading whitelist failed {url} attempt {attempt+1}: {e}")
                        time.sleep(1 + attempt * 2)

            # atomic update
            with self._lock:
                self.whitelisted_domains_local = new_domains
                self.whitelisted_networks = new_networks

                # if you want to reflect in a global 'whitelisted_domains', do it here atomically:
                try:
                    if 'whitelisted_domains' in globals():
                        whitelisted_domains.clear()
                        whitelisted_domains.update(new_domains)
                except Exception:
                    pass

            log(f"✅ {len(self.whitelisted_domains_local)} whitelisted domains loaded, {len(self.whitelisted_networks)} CIDR networks.")
        except Exception as e:
            log(f"[Error] _load_whitelist: {e}\n{traceback.format_exc()}")

    def _looks_like_ip(self, s):
        try:
            ipaddress.ip_address(s)
            return True
        except Exception:
            return False

    def is_whitelisted(self, hostname):
        """
        Checks if hostname is explicitly whitelisted (domain, parent domain, wildcard),
        or belongs to a whitelisted CIDR network.
        - hostname can be an IP (string) or an fqdn.
        - handles subdomains: if 'example.com' is in whitelist, 'sub.a.example.com' is allowed.
        """
        try:
            if not hostname:
                return False
            host = hostname.strip().lower().rstrip('.')
            if not host:
                return False

            # Direct IP -> check networks and exact IP whitelist
            try:
                if self._looks_like_ip(host):
                    ip_obj = ipaddress.ip_address(host)
                    with self._lock:
                        # exact IP in domain whitelist?
                        if host in self.whitelisted_domains_local:
                            return True
                        # any network contains?
                        for net in self.whitelisted_networks:
                            if ip_obj in net:
                                return True
                    return False
            except Exception:
                pass

            parts = host.split('.')
            with self._lock:
                # Check candidate suffixes: host, parent, ... top-level domain excluded if empty
                for i in range(len(parts)):
                    candidate = '.'.join(parts[i:])
                    if candidate in self.whitelisted_domains_local:
                        return True

            return False
        except Exception as e:
            log(f"is_whitelisted error for {hostname}: {e}")
            return False

    def _is_blocked(self, hostname):
        """
        Returns True if hostname should be blocked.
        Priority: whitelist -> always allow.
        Then: Direct IP: uses block_ip_direct flag.
        Then: check blocked_domains and manual_blocked_domains (parents included).
        """
        try:
            if not hostname:
                return False

            host = hostname.strip().lower().rstrip('.')
            if not host:
                return False

            # 1) Whitelist has absolute priority
            try:
                if self.is_whitelisted(host):
                    log(f"✅ [WHITELIST ALLOW] {_safe_str(hostname)} matched whitelist")
                    return False
            except Exception as e:
                log(f"_is_blocked: whitelist check failed for {hostname}: {e}")
                # in case of error, don't block
                return False

            # 2) Direct IP handling
            try:
                if self._looks_like_ip(host):
                    # If IP explicitly in global whitelisted_domains (string), allow
                    if 'whitelisted_domains' in globals() and host in whitelisted_domains:
                        log(f"✅ [WHITELIST ALLOW IP] {hostname}")
                        return False
                    # otherwise rely on flag block_ip_direct
                    return bool(block_ip_direct)
            except Exception:
                # if problem during IP detection, continue as hostname
                pass

            parts = host.split('.')
            # 3) Blocklist check (with parents)
            try:
                with self._lock:
                    # check exact host (host) and global manual blocked
                    if host in self.blocked_domains or host in manual_blocked_domains:
                        log(f"[DEBUG BLOCK] {host} found in blocklist (exact match)")
                        return True
                    # check parents (but skip TLDs and very short domains to avoid false positives)
                    for i in range(1, len(parts)):
                        parent = '.'.join(parts[i:])
                        # Skip TLDs and very short domains (< 3 chars) to prevent false positives
                        if len(parent) >= 3 and '.' in parent:
                            if parent in self.blocked_domains or parent in manual_blocked_domains:
                                log(f"[DEBUG BLOCK] {host} blocked because parent '{parent}' is in blocklist")
                                return True
            except Exception as e:
                log(f"_is_blocked blocklist check error for {hostname}: {e}")
                return False

            return False
        except Exception as e:
            log(f"_is_blocked error for {hostname}: {e}")
            return False

    def maybe_reload_background(self):
        """
        Reloads blocklist and whitelist in background if necessary.
        """
        try:
            if time.time() - self.last_reload > self.reload_interval:
                if self._loading_lock.locked():
                    return
                t1 = threading.Thread(target=self._load_blocklist, daemon=True)
                t2 = threading.Thread(target=self._load_whitelist, daemon=True)
                t1.start()
                t2.start()
        except Exception as e:
            log(f"maybe_reload_background error: {e}")