#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Point d'entrée principal pour CalmWeb quand exécuté comme package.
Ce fichier permet l'exécution via python -m calmweb ou en exécutable.
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
if __name__ == "__main__":
    # Pour l'exécution directe ou PyInstaller
    if getattr(sys, 'frozen', False):
        # Exécuté via PyInstaller
        bundle_dir = sys._MEIPASS
    else:
        # Exécuté directement
        bundle_dir = os.path.dirname(os.path.abspath(__file__))

    # Ajouter le répertoire calmweb au path
    parent_dir = os.path.dirname(bundle_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    # Importer et exécuter main
    from main import robust_main
    robust_main()