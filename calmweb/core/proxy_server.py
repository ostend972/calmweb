#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTTP/HTTPS proxy server for CalmWeb.
Handles request filtering based on blocklists and whitelists.
"""

import socket
import threading
import traceback
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

from ..config.config_manager import config_manager
from ..config.settings import (
    PROXY_BIND_IP, PROXY_PORT
)
from ..utils.logging import log, update_dashboard_stats
from ..utils.network import _set_socket_opts_for_perf, full_duplex_relay

# Global variables that will be set by main module
current_resolver = None
proxy_server = None
proxy_server_thread = None


def resolve_ip(hostname):
    """Résout l'adresse IP d'un nom de domaine."""
    try:
        if hostname:
            ip = socket.gethostbyname(hostname)
            return ip
    except Exception:
        pass
    return hostname  # Retourne le hostname si la résolution échoue


class BlockProxyHandler(BaseHTTPRequestHandler):
    timeout = 10
    rbufsize = 0
    protocol_version = "HTTP/1.1"
    VOIP_ALLOWED_PORTS = {80, 443, 3478, 5060, 5061}  # allowed VOIP/STUN/SIP ports

    def _extract_hostname_from_path(self, path):
        try:
            parsed = urllib.parse.urlparse(path)
            return parsed.hostname
        except Exception:
            return None

    def do_CONNECT(self):
        host_port = self.path
        target_host, target_port = host_port.split(':', 1)
        target_port = int(target_port)
        hostname = target_host.lower() if target_host else None
        try:
            if current_resolver:
                current_resolver.maybe_reload_background()

            # If whitelisted, bypass ALL restrictions (ports, http flags, blocklist)
            try:
                if current_resolver and current_resolver.is_whitelisted(hostname):
                    log(f"✅ [WHITELIST BYPASS CONNECT] {hostname}:{target_port}")
                    # create connection and relay as usual without further checks
                    remote = socket.create_connection((target_host, target_port), timeout=10)
                    self.send_response(200, "Connection Established")
                    self.send_header('Connection', 'close')
                    self.end_headers()

                    conn = self.connection
                    _set_socket_opts_for_perf(conn)
                    _set_socket_opts_for_perf(remote)
                    conn.settimeout(None)
                    remote.settimeout(None)
                    conn.setblocking(True)
                    remote.setblocking(True)
                    full_duplex_relay(conn, remote)
                    return
            except Exception as e:
                # if whitelist check fails, continue to secure checks rather than allow everything
                log(f"[WARN] whitelist check error in CONNECT for {hostname}: {e}")

            # blocking based on blocklist
            if config_manager.block_enabled and current_resolver and current_resolver._is_blocked(hostname):
                log(f"🚫 [Proxy BLOCK HTTPS] {hostname}")
                real_ip = resolve_ip(target_host)
                update_dashboard_stats('blocked', hostname, real_ip)
                self.send_error(403, "Blocked by security")
                return

            # If target is whitelisted, bypass all controls
            if current_resolver and current_resolver.is_whitelisted(hostname):
                log(f"✅ [WHITELIST BYPASS CONNECT] {hostname}:{target_port}")
                try:
                    remote = socket.create_connection((target_host, target_port), timeout=10)
                    self.send_response(200, "Connection Established")
                    self.send_header('Connection', 'close')
                    self.end_headers()

                    conn = self.connection
                    _set_socket_opts_for_perf(conn)
                    _set_socket_opts_for_perf(remote)
                    conn.settimeout(None)
                    remote.settimeout(None)
                    conn.setblocking(True)
                    remote.setblocking(True)
                    full_duplex_relay(conn, remote)
                    return
                except Exception as e:
                    log(f"[Whitelist bypass CONNECT error] {e}")
                    self.send_error(502, "Bad Gateway")
                    return

            # otherwise apply normal rules
            if config_manager.block_http_other_ports and target_port not in self.VOIP_ALLOWED_PORTS:
                log(f"🚫 [Proxy BLOCK other port] {target_host}:{target_port}")
                self.send_error(403, "non-standard port blocked by security")
                return

            # Normal authorization — establish tunnel
            log(f"✅ [Proxy ALLOW HTTPS] {hostname}")
            real_ip = resolve_ip(target_host)
            update_dashboard_stats('allowed', hostname, real_ip)

            remote = socket.create_connection((target_host, target_port), timeout=10)
            self.send_response(200, "Connection Established")
            self.send_header('Connection', 'close')
            self.end_headers()

            conn = self.connection
            _set_socket_opts_for_perf(conn)
            _set_socket_opts_for_perf(remote)
            conn.settimeout(None)
            remote.settimeout(None)
            conn.setblocking(True)
            remote.setblocking(True)
            full_duplex_relay(conn, remote)

        except Exception as e:
            log(f"[Proxy CONNECT error] {e}")
            try:
                self.send_error(502, "Bad Gateway")
            except Exception:
                pass

    def _handle_http_method(self):
        if current_resolver:
            current_resolver.maybe_reload_background()

        hostname = self._extract_hostname_from_path(self.path)
        if not hostname:
            host_header = self.headers.get('Host', '')
            hostname = host_header.split(':', 1)[0] if host_header else None
        if hostname:
            hostname = hostname.lower().strip()

        # Centralize whitelist verification via current_resolver
        is_whitelisted = False
        try:
            if current_resolver and current_resolver.is_whitelisted(hostname):
                is_whitelisted = True
        except Exception as e:
            log(f"_handle_http_method whitelist check error for {hostname}: {e}")

        # If whitelisted => complete bypass: don't apply block_http_traffic, ports or blocklist
        if is_whitelisted:
            # Skip logging for localhost to avoid spam
            if hostname not in ['127.0.0.1', 'localhost']:
                log(f"✅ [WHITELIST BYPASS HTTP] {hostname} ({self.command} {self.path})")
            # Continue to normal forwarding (don't send 403 even if block_enabled)
        else:
            # if not whitelisted, apply normal protections
            if config_manager.block_enabled and current_resolver and current_resolver._is_blocked(hostname):
                log(f"🚫 [Proxy BLOCK HTTP] {hostname} ({self.command} {self.path})")
                real_ip = resolve_ip(hostname)
                update_dashboard_stats('blocked', hostname, real_ip)
                self.send_error(403, "Blocked by security")
                return

        try:
            # Extract target_host, target_port, path_only from request
            if isinstance(self.path, str) and self.path.startswith(("http://", "https://")):
                parsed = urllib.parse.urlparse(self.path)
                scheme = parsed.scheme
                target_host = parsed.hostname
                target_port = parsed.port or (443 if scheme == "https" else 80)
                path_only = parsed.path or "/"
                if parsed.query:
                    path_only += "?" + parsed.query
            else:
                host_hdr = self.headers.get('Host', '')
                if ':' in host_hdr:
                    target_host, port_str = host_hdr.split(':', 1)
                    try:
                        target_port = int(port_str)
                    except Exception:
                        target_port = 80
                else:
                    target_host = host_hdr
                    target_port = 80
                path_only = self.path
                scheme = "http"

            if not target_host:
                self.send_error(400, "Bad Request - target host unknown")
                return

            # If not whitelisted and non-authorized port -> block if flag active
            if (not is_whitelisted) and config_manager.block_http_other_ports and target_port not in self.VOIP_ALLOWED_PORTS:
                log(f"🚫 [BLOCK other port] {target_host}:{target_port}")
                self.send_error(403, "non-standard port blocked by security")
                return

            # If not whitelisted and direct HTTP blocking enabled
            if (not is_whitelisted) and config_manager.block_enabled and config_manager.block_http_traffic and isinstance(self.path, str) and self.path.startswith("http://"):
                log(f"🚫 [Proxy BLOCK HTTP Traffic] {hostname}")
                self.send_error(403, "HTTP blocked by security")
                return

            # Skip logging for localhost to avoid spam
            if target_host not in ['127.0.0.1', 'localhost']:
                log(f"✅ [Proxy ALLOW HTTP] {target_host}:{target_port} -> {self.command} {path_only}")
                real_ip = resolve_ip(target_host)
                update_dashboard_stats('allowed', target_host, real_ip)

            # Build headers to forward
            hop_by_hop = {"proxy-connection","connection","keep-alive","transfer-encoding","te","trailers","upgrade","proxy-authorization"}
            header_lines = []
            host_header_value = target_host
            if (scheme == "http" and target_port != 80) or (scheme == "https" and target_port != 443):
                host_header_value = f"{target_host}:{target_port}"

            for k, v in self.headers.items():
                try:
                    if k.lower() in hop_by_hop:
                        continue
                    if k.lower() == 'host':
                        header_lines.append(f"Host: {host_header_value}")
                    else:
                        header_lines.append(f"{k}: {v}")
                except Exception:
                    continue

            header_lines = [line for line in header_lines if not line.lower().startswith('connection:')]
            header_lines.append("Connection: close")

            request_line = f"{self.command} {path_only} {self.request_version}\r\n"
            request_headers_raw = "\r\n".join(header_lines) + "\r\n\r\n"
            request_bytes = request_line.encode('utf-8') + request_headers_raw.encode('utf-8')

            remote = socket.create_connection((target_host, target_port), timeout=10)

            _set_socket_opts_for_perf(self.connection)
            _set_socket_opts_for_perf(remote)

            # Remove timeout after connection
            self.connection.settimeout(None)
            remote.settimeout(None)
            self.connection.setblocking(True)
            remote.setblocking(True)

            try:
                remote.sendall(request_bytes)
            except Exception as e:
                log(f"[Proxy send headers error] {e}")
                try:
                    remote.close()
                except Exception:
                    pass
                self.send_error(502, "Bad Gateway")
                return

            full_duplex_relay(self.connection, remote)
            try:
                remote.close()
            except Exception:
                pass

            log(f"[Proxy FORWARD DIRECT] {target_host}:{target_port} -> {self.command} {path_only}")

        except Exception as e:
            log(f"[Proxy forward error] {e}\n{traceback.format_exc()}")
            try:
                self.send_error(502, "Bad Gateway")
            except Exception:
                pass

    # shortcuts for HTTP methods
    def do_GET(self): self._handle_http_method()
    def do_POST(self): self._handle_http_method()
    def do_PUT(self): self._handle_http_method()
    def do_DELETE(self): self._handle_http_method()
    def do_HEAD(self): self._handle_http_method()
    def log_message(self, format, *args): return  # silence


def start_proxy_server(bind_ip=PROXY_BIND_IP, port=PROXY_PORT):
    """Start the proxy server."""
    global proxy_server, proxy_server_thread
    try:
        # Stop existing server if running
        if proxy_server:
            try:
                proxy_server.shutdown()
                proxy_server.server_close()
            except Exception:
                pass
            proxy_server = None

        if proxy_server_thread and proxy_server_thread.is_alive():
            try:
                proxy_server_thread.join(timeout=2)
            except Exception:
                pass

        # Create new server
        proxy_server = ThreadingHTTPServer((bind_ip, port), BlockProxyHandler)
        proxy_server_thread = threading.Thread(
            target=proxy_server.serve_forever,
            daemon=True,
            name="ProxyServer"
        )
        proxy_server_thread.start()
        log(f"✅ Proxy server started on {bind_ip}:{port}")
        return True
    except Exception as e:
        log(f"❌ Error starting proxy server: {e}")
        return False


def stop_proxy_server():
    """Stop the proxy server."""
    global proxy_server, proxy_server_thread
    try:
        if proxy_server:
            proxy_server.shutdown()
            proxy_server.server_close()
            proxy_server = None
            log("✅ Proxy server stopped")
    except Exception as e:
        log(f"Error stopping proxy server: {e}")

    try:
        if proxy_server_thread and proxy_server_thread.is_alive():
            proxy_server_thread.join(timeout=2)
            proxy_server_thread = None
    except Exception as e:
        log(f"Error joining proxy thread: {e}")