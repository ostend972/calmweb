#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web dashboard server for CalmWeb.
Provides a modern React interface to monitor filtering activity and statistics.
"""

import os
import mimetypes
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Tuple

from ..config.settings import (
    dashboard_stats, dashboard_lock, DASHBOARD_PORT,
    DASHBOARD_DIST_DIR, DASHBOARD_DIR
)
from ..utils.logging import log
from .api_handlers import handle_config_api, handle_logs_api, handle_data_api
from .api_settings_handlers import handle_protection_toggle, handle_settings_api
from .api_domains_handlers import handle_domains_api
from .api_blocklists_handlers import handle_blocklists_api
from .templates import get_dashboard_html

# Global variables
dashboard_server = None
dashboard_server_thread = None


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the CalmWeb dashboard."""

    def validate_request(self) -> Tuple[bool, str]:
        """Validate incoming request for security."""
        try:
            # Basic validation - check if client is local
            client_ip = self.client_address[0]
            if client_ip not in ['127.0.0.1', '::1', 'localhost']:
                return False, f"Non-local access denied from {client_ip}"

            # Check path length
            if len(self.path) > 1000:
                return False, "Path too long"

            return True, "Valid request"
        except Exception as e:
            return False, f"Validation error: {e}"

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self) -> None:
        """Handle POST requests (for config save)."""
        try:
            # Full request validation
            is_valid, validation_message = self.validate_request()
            if not is_valid:
                log(f"Request invalidated: {validation_message} - IP: {self.client_address[0]}")
                self.send_error(400, "Bad request")
                return

            if self.path == '/api/config':
                # Save custom.cfg file
                handle_config_api(self)
            elif self.path == '/api/protection/toggle':
                # Toggle protection on/off
                handle_protection_toggle(self)
            elif self.path == '/api/settings/update':
                # Update settings
                handle_settings_api(self)
            elif self.path in ['/api/domains/add', '/api/domains/remove', '/api/domains/clear']:
                # Domain management
                handle_domains_api(self)
            elif self.path in ['/api/blocklists/add', '/api/blocklists/remove', '/api/blocklists/reset']:
                # Blocklist management
                handle_blocklists_api(self)
            else:
                self.send_error(404, "Endpoint not found")

        except ConnectionAbortedError:
            pass
        except BrokenPipeError:
            pass
        except Exception as e:
            log(f"Error in POST handler: {e}")
            try:
                if not hasattr(self, 'headers_sent') or not self.headers_sent:
                    self.send_error(500, "Internal server error")
            except:
                pass

    def do_GET(self) -> None:
        """Handle GET requests."""
        try:
            # Full request validation
            is_valid, validation_message = self.validate_request()
            if not is_valid:
                log(f"Request invalidated: {validation_message} - IP: {self.client_address[0]}")
                self.send_error(400, "Bad request")
                return

            # API endpoints (highest priority)
            if self.path == '/data.json':
                # Generate dashboard data
                handle_data_api(self, dashboard_stats, dashboard_lock)

            elif self.path == '/api/config':
                # Read custom.cfg file
                handle_config_api(self)

            elif self.path == '/api/logs':
                # Return logs from buffer
                handle_logs_api(self)

            elif self.path == '/api/settings':
                # Get current settings
                handle_settings_api(self)

            elif self.path == '/api/domains':
                # Get domains lists
                handle_domains_api(self)

            elif self.path == '/api/blocklists':
                # Get blocklists and whitelists
                handle_blocklists_api(self)

            # React app routes
            elif self.path == '/' or self.path == '/index.html' or self.path.startswith('/?'):
                # Serve React dashboard or fallback to simple dashboard (including with query parameters)
                self.serve_dashboard()

            elif self.path.startswith('/assets/'):
                # Serve React static assets
                self.serve_react_file(self.path[1:])  # Remove leading /

            elif self.path in ['/dashboard', '/logs', '/config', '/stats']:
                # SPA routing fallback - serve index.html for React routes
                self.serve_dashboard()

            elif self.path.startswith('/') and not self.path.startswith('/api/'):
                # Try to serve other React files (CSS, images, etc.)
                self.serve_react_file(self.path[1:])  # Remove leading /

            else:
                # File not found
                self.send_error(404, "File not found")

        except ConnectionAbortedError:
            # Client closed connection - normal, don't log
            pass
        except BrokenPipeError:
            # Connection interrupted - normal, don't log
            pass
        except Exception as e:
            log(f"Error DashboardHandler: {e}")
            try:
                if not hasattr(self, 'headers_sent') or not self.headers_sent:
                    self.send_error(500, "Internal server error")
            except:
                pass

    def serve_dashboard(self) -> None:
        """Serve the main dashboard (React if available, fallback to HTML)."""
        try:
            # Try React first
            if os.path.exists(DASHBOARD_DIST_DIR) and os.path.exists(os.path.join(DASHBOARD_DIST_DIR, "index.html")):
                self.serve_react_file("index.html")
            else:
                # Fallback to simple HTML dashboard
                log("React dashboard not found, falling back to simple dashboard")
                self.serve_simple_dashboard()
        except Exception as e:
            log(f"Error serving dashboard, falling back to simple: {e}")
            try:
                self.serve_simple_dashboard()
            except Exception as e2:
                log(f"Error serving fallback dashboard: {e2}")
                self.send_error(500, "Dashboard generation error")

    def serve_react_file(self, filepath: str) -> None:
        """Serve a React build file from the dist directory."""
        try:
            # Security: prevent directory traversal
            if '..' in filepath or filepath.startswith('/') or '\\' in filepath:
                self.send_error(403, "Access denied")
                return

            # Build full path
            full_path = os.path.join(DASHBOARD_DIST_DIR, filepath)

            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                raise FileNotFoundError(f"React file not found: {full_path}")

            # Determine MIME type
            mime_type = self._get_mime_type(filepath)

            # Read file content
            mode = 'rb' if self._is_binary_file(filepath) else 'r'
            encoding = None if mode == 'rb' else 'utf-8'

            with open(full_path, mode, encoding=encoding) as f:
                content = f.read()

            # Send response
            self.send_response(200)
            self.send_header('Content-type', mime_type)

            # Cache headers
            if filepath.endswith(('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg')):
                self.send_header('Cache-Control', 'public, max-age=3600')
            else:
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')

            self.end_headers()

            # Write content
            if isinstance(content, str):
                self.wfile.write(content.encode('utf-8'))
            else:
                self.wfile.write(content)

        except FileNotFoundError:
            log(f"React file not found: {filepath}")
            self.send_error(404, "File not found")
        except Exception as e:
            log(f"Error serving React file {filepath}: {e}")
            self.send_error(500, "Internal server error")

    def serve_simple_dashboard(self) -> None:
        """Serve the embedded HTML dashboard (fallback)."""
        try:
            html_content = get_dashboard_html()

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()

            self.wfile.write(html_content.encode('utf-8'))
        except Exception as e:
            log(f"Error serving simple dashboard: {e}")
            self.send_error(500, "Error serving dashboard")

    def _get_mime_type(self, filepath: str) -> str:
        """Get MIME type for a file."""
        mime_type, _ = mimetypes.guess_type(filepath)

        if mime_type is None:
            # Custom mappings for specific extensions
            ext = os.path.splitext(filepath)[1].lower()
            mime_types = {
                '.js': 'application/javascript',
                '.mjs': 'application/javascript',
                '.jsx': 'application/javascript',
                '.ts': 'application/javascript',
                '.tsx': 'application/javascript',
                '.css': 'text/css',
                '.html': 'text/html',
                '.htm': 'text/html',
                '.json': 'application/json',
                '.svg': 'image/svg+xml',
                '.ico': 'image/x-icon',
            }
            mime_type = mime_types.get(ext, 'application/octet-stream')

        return mime_type

    def _is_binary_file(self, filepath: str) -> bool:
        """Check if file should be read in binary mode."""
        text_extensions = {'.html', '.htm', '.css', '.js', '.jsx', '.ts', '.tsx',
                          '.json', '.txt', '.md', '.svg', '.xml'}
        ext = os.path.splitext(filepath)[1].lower()
        return ext not in text_extensions

    def log_message(self, format, *args) -> None:
        """Override to silence HTTP server logs."""
        return


def start_dashboard_server(bind_ip: str = "127.0.0.1", port: int = DASHBOARD_PORT) -> bool:
    """Start the dashboard web server."""
    global dashboard_server, dashboard_server_thread
    try:
        # Stop existing server if running
        if dashboard_server:
            try:
                dashboard_server.shutdown()
                dashboard_server.server_close()
            except Exception:
                pass
            dashboard_server = None

        if dashboard_server_thread and dashboard_server_thread.is_alive():
            try:
                dashboard_server_thread.join(timeout=2)
            except Exception:
                pass

        # Log dashboard mode
        if os.path.exists(DASHBOARD_DIST_DIR) and os.path.exists(os.path.join(DASHBOARD_DIST_DIR, "index.html")):
            log(f"✅ React dashboard found at {DASHBOARD_DIST_DIR}")
        else:
            log(f"⚠️  React dashboard not found, using fallback HTML dashboard")

        # Create new server
        dashboard_server = ThreadingHTTPServer((bind_ip, port), DashboardHandler)
        dashboard_server_thread = threading.Thread(
            target=dashboard_server.serve_forever,
            daemon=True,
            name="DashboardServer"
        )
        dashboard_server_thread.start()
        log(f"✅ Dashboard server started on http://{bind_ip}:{port}")
        return True
    except Exception as e:
        log(f"❌ Error starting dashboard server: {e}")
        return False


def stop_dashboard_server() -> None:
    """Stop the dashboard web server."""
    global dashboard_server, dashboard_server_thread
    try:
        if dashboard_server:
            dashboard_server.shutdown()
            dashboard_server.server_close()
            dashboard_server = None
            log("✅ Dashboard server stopped")
    except Exception as e:
        log(f"Error stopping dashboard server: {e}")

    try:
        if dashboard_server_thread and dashboard_server_thread.is_alive():
            dashboard_server_thread.join(timeout=2)
            dashboard_server_thread = None
    except Exception as e:
        log(f"Error joining dashboard thread: {e}")