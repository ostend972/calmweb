"""Configuration module for CalmWeb."""

from .settings import *
from .custom_config import *

__all__ = [
    'BLOCKLIST_URLS', 'WHITELIST_URLS', 'PROXY_BIND_IP', 'PROXY_PORT',
    'DASHBOARD_PORT', 'INSTALL_DIR', 'USER_CFG_DIR', 'USER_CFG_PATH',
    'get_custom_cfg_path', 'parse_custom_cfg', 'write_default_custom_cfg',
    'load_custom_cfg_to_globals', 'ensure_custom_cfg_exists'
]