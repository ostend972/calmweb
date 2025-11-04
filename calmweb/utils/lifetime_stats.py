#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestionnaire des statistiques à vie de CalmWeb.
Persiste les données dans un fichier JSON pour survivre aux redémarrages.
"""

import json
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from pathlib import Path

# Fichier de persistance des stats dans le dossier de configuration utilisateur
CONFIG_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "CalmWeb")
STATS_FILE = os.path.join(CONFIG_DIR, "lifetime_stats.json")

# Lock pour thread safety
_stats_lock = threading.RLock()

# Structure des statistiques à vie
_lifetime_stats = {
    "installation_date": None,
    "total_blocked_lifetime": 0,
    "total_allowed_lifetime": 0,
    "total_requests_lifetime": 0,
    "total_sessions": 0,
    "current_session_start": None,
    "last_updated": None,
    "top_blocked_domains": {},  # {domain: count}
    "days_active": 0,
    "last_active_date": None
}

def _load_lifetime_stats():
    """Charge les statistiques depuis le fichier JSON."""
    global _lifetime_stats

    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                saved_stats = json.load(f)
                _lifetime_stats.update(saved_stats)
                print(f"📊 Loaded lifetime stats: {_lifetime_stats['total_requests_lifetime']} total requests")
        else:
            # Première installation
            _lifetime_stats["installation_date"] = datetime.now().isoformat()
            _save_lifetime_stats()
            print("📊 Created new lifetime stats file")
    except Exception as e:
        print(f"❌ Error loading lifetime stats: {e}")

def _save_lifetime_stats():
    """Sauvegarde les statistiques dans le fichier JSON."""
    global _lifetime_stats

    try:
        _lifetime_stats["last_updated"] = datetime.now().isoformat()

        # Créer le dossier si nécessaire
        os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)

        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(_lifetime_stats, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Error saving lifetime stats: {e}")

def initialize_lifetime_stats():
    """Initialise les statistiques à vie (appelé au démarrage)."""
    global _lifetime_stats

    with _stats_lock:
        _load_lifetime_stats()

        # Démarrer une nouvelle session
        _lifetime_stats["total_sessions"] += 1
        _lifetime_stats["current_session_start"] = datetime.now().isoformat()

        # Mettre à jour les jours actifs
        today = datetime.now().date().isoformat()
        if _lifetime_stats["last_active_date"] != today:
            _lifetime_stats["days_active"] += 1
            _lifetime_stats["last_active_date"] = today

        _save_lifetime_stats()
        print(f"📊 Session #{_lifetime_stats['total_sessions']} started")

def update_lifetime_stats(action: str, domain: str = None):
    """Met à jour les statistiques à vie."""
    global _lifetime_stats

    with _stats_lock:
        _lifetime_stats["total_requests_lifetime"] += 1

        if action == 'blocked':
            _lifetime_stats["total_blocked_lifetime"] += 1

            # Compter les domaines bloqués
            if domain:
                if domain not in _lifetime_stats["top_blocked_domains"]:
                    _lifetime_stats["top_blocked_domains"][domain] = 0
                _lifetime_stats["top_blocked_domains"][domain] += 1

        elif action == 'allowed':
            _lifetime_stats["total_allowed_lifetime"] += 1

        # Sauvegarder périodiquement (toutes les 100 requêtes) pour réduire les écritures disque
        if _lifetime_stats["total_requests_lifetime"] % 100 == 0:
            _save_lifetime_stats()

def get_lifetime_stats() -> Dict[str, Any]:
    """Retourne les statistiques à vie."""
    with _stats_lock:
        stats = _lifetime_stats.copy()

        # Calculer la durée depuis l'installation
        if stats["installation_date"]:
            install_date = datetime.fromisoformat(stats["installation_date"])
            days_since_install = (datetime.now() - install_date).days
            stats["days_since_installation"] = max(1, days_since_install)  # Au minimum 1
        else:
            stats["days_since_installation"] = 1

        # Calculer la durée de session actuelle
        if stats["current_session_start"]:
            session_start = datetime.fromisoformat(stats["current_session_start"])
            session_duration = datetime.now() - session_start
            stats["current_session_duration_hours"] = round(session_duration.total_seconds() / 3600, 2)
        else:
            stats["current_session_duration_hours"] = 0

        # Top 10 des domaines bloqués
        top_blocked = sorted(
            stats["top_blocked_domains"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        stats["top_blocked_domains_list"] = [{"domain": d, "count": c} for d, c in top_blocked]

        # Moyennes
        stats["avg_requests_per_day"] = round(stats["total_requests_lifetime"] / stats["days_since_installation"], 1)
        stats["avg_blocked_per_day"] = round(stats["total_blocked_lifetime"] / stats["days_since_installation"], 1)
        stats["avg_allowed_per_day"] = round(stats["total_allowed_lifetime"] / stats["days_since_installation"], 1)

        # Pourcentages
        if stats["total_requests_lifetime"] > 0:
            stats["blocked_percentage"] = round((stats["total_blocked_lifetime"] / stats["total_requests_lifetime"]) * 100, 1)
            stats["allowed_percentage"] = round((stats["total_allowed_lifetime"] / stats["total_requests_lifetime"]) * 100, 1)
        else:
            stats["blocked_percentage"] = 0
            stats["allowed_percentage"] = 0

        return stats

def force_save_lifetime_stats():
    """Force la sauvegarde des statistiques (appelé à l'arrêt)."""
    with _stats_lock:
        _save_lifetime_stats()
        print("📊 Lifetime stats saved on shutdown")

def sync_lifetime_stats_with_dashboard(dashboard_stats):
    """Synchronise les statistiques à vie avec les données actuelles du dashboard."""
    global _lifetime_stats

    with _stats_lock:
        # Mettre à jour avec les données actuelles du dashboard
        _lifetime_stats["total_blocked_lifetime"] += dashboard_stats.get('blocked_today', 0)
        _lifetime_stats["total_allowed_lifetime"] += dashboard_stats.get('allowed_today', 0)
        _lifetime_stats["total_requests_lifetime"] += dashboard_stats.get('total_requests', 0)

        # Fusionner les domaines bloqués
        for domain, count in dashboard_stats.get('blocked_domains_count', {}).items():
            if domain not in _lifetime_stats["top_blocked_domains"]:
                _lifetime_stats["top_blocked_domains"][domain] = 0
            _lifetime_stats["top_blocked_domains"][domain] += count

        _save_lifetime_stats()
        print(f"📊 Lifetime stats synchronized: {_lifetime_stats['total_requests_lifetime']} total requests")

def reset_lifetime_stats():
    """Remet à zéro les statistiques à vie (utilisé pour les tests)."""
    global _lifetime_stats

    with _stats_lock:
        _lifetime_stats = {
            "installation_date": datetime.now().isoformat(),
            "total_blocked_lifetime": 0,
            "total_allowed_lifetime": 0,
            "total_requests_lifetime": 0,
            "total_sessions": 1,
            "current_session_start": datetime.now().isoformat(),
            "last_updated": None,
            "top_blocked_domains": {},
            "days_active": 1,
            "last_active_date": datetime.now().date().isoformat()
        }
        _save_lifetime_stats()
        print("📊 Lifetime stats reset")