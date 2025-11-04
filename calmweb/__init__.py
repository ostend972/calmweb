#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CalmWeb - Web filtering proxy with dashboard
Modular architecture for better maintainability
"""

__version__ = "1.1.0"
__author__ = "Tonton Jo"
__description__ = "Web filtering proxy with dashboard"

# Re-export main components for backward compatibility
from .main import main

__all__ = ['main', '__version__']