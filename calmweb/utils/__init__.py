"""Utility modules for CalmWeb."""

from .logging import log, log_buffer, update_dashboard_stats
from .network import _set_socket_opts_for_perf, _relay_worker, full_duplex_relay
from .system import get_exe_icon, add_firewall_rule
from .proxy_manager import save_original_proxy_settings, restore_original_proxy_settings, set_system_proxy

__all__ = [
    'log', 'log_buffer', 'update_dashboard_stats',
    '_set_socket_opts_for_perf', '_relay_worker', 'full_duplex_relay',
    'get_exe_icon', 'add_firewall_rule',
    'save_original_proxy_settings', 'restore_original_proxy_settings', 'set_system_proxy'
]