#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Automatic external lists updater for CalmWeb.
Handles periodic updates of blocklists and whitelists.
"""

import threading
import time
import datetime
import json
import os
from typing import Dict, Any, Optional

from .logging import log


class AutoUpdater:
    """Manages automatic updates of external domain lists."""

    def __init__(self):
        self._update_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._update_interval = 3600  # 1 hour in seconds
        self._last_update: Optional[datetime.datetime] = None
        self._update_status = "idle"  # idle, updating, success, error
        self._update_error: Optional[str] = None
        self._lock = threading.RLock()

        # Status file to persist update information
        self._status_file = os.path.join(
            os.path.expanduser("~"), "AppData", "Roaming", "CalmWeb", "update_status.json"
        )

        self._load_status()

    def _load_status(self):
        """Load update status from file."""
        try:
            if os.path.exists(self._status_file):
                with open(self._status_file, 'r') as f:
                    data = json.load(f)

                if 'last_update' in data:
                    self._last_update = datetime.datetime.fromisoformat(data['last_update'])

                self._update_status = data.get('status', 'idle')
                self._update_error = data.get('error', None)

                log(f"Update status loaded: last update {self._last_update}")
        except Exception as e:
            log(f"Error loading update status: {e}")

    def _save_status(self):
        """Save update status to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self._status_file), exist_ok=True)

            data = {
                'status': self._update_status,
                'error': self._update_error,
                'last_update': self._last_update.isoformat() if self._last_update else None
            }

            with open(self._status_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            log(f"Error saving update status: {e}")

    def start_auto_updates(self):
        """Start the automatic update thread."""
        if self._update_thread and self._update_thread.is_alive():
            log("Auto-updater already running")
            return

        self._stop_event.clear()
        self._update_thread = threading.Thread(
            target=self._update_loop,
            name="AutoUpdater",
            daemon=True
        )
        self._update_thread.start()
        log("🔄 Auto-updater started (1 hour interval)")

    def stop_auto_updates(self):
        """Stop the automatic update thread."""
        if self._update_thread:
            self._stop_event.set()
            self._update_thread.join(timeout=5)
            log("🛑 Auto-updater stopped")

    def _update_loop(self):
        """Main update loop running in background thread."""
        while not self._stop_event.is_set():
            try:
                # Check if it's time to update
                now = datetime.datetime.now()

                if self._should_update(now):
                    log("⏰ Time for automatic lists update")
                    self.update_external_lists()

                # Wait for next check (every 5 minutes to be responsive)
                if self._stop_event.wait(300):  # 5 minutes
                    break

            except Exception as e:
                log(f"Error in auto-update loop: {e}")
                # Continue running even if there's an error
                if self._stop_event.wait(300):
                    break

    def _should_update(self, now: datetime.datetime) -> bool:
        """Check if it's time to update the lists."""
        if self._last_update is None:
            return True  # First update

        time_since_update = now - self._last_update
        return time_since_update.total_seconds() >= self._update_interval

    def update_external_lists(self) -> bool:
        """Manually trigger an update of external lists."""
        with self._lock:
            if self._update_status == "updating":
                log("Update already in progress")
                return False

            self._update_status = "updating"
            self._update_error = None
            self._save_status()

        try:
            log("🔄 Starting external lists update...")

            # Import here to avoid circular imports
            from ..web.api_external_domains import force_update_external_domains

            # Perform the actual update
            force_update_external_domains()
            success = True

            with self._lock:
                if success:
                    self._update_status = "success"
                    self._last_update = datetime.datetime.now()
                    self._update_error = None
                    log("✅ External lists updated successfully")
                else:
                    self._update_status = "error"
                    self._update_error = "Failed to refresh external domains cache"
                    log("❌ Failed to update external lists")

                self._save_status()

            return success

        except Exception as e:
            error_msg = f"Update error: {e}"
            log(f"❌ {error_msg}")

            with self._lock:
                self._update_status = "error"
                self._update_error = error_msg
                self._save_status()

            return False

    def get_status(self) -> Dict[str, Any]:
        """Get current update status for dashboard."""
        with self._lock:
            return {
                "status": self._update_status,
                "last_update": self._last_update.isoformat() if self._last_update else None,
                "last_update_human": self._format_time_ago(self._last_update) if self._last_update else "Never",
                "error": self._update_error,
                "next_update": self._get_next_update_time(),
                "update_interval_hours": self._update_interval / 3600
            }

    def _format_time_ago(self, timestamp: datetime.datetime) -> str:
        """Format time difference in human readable format."""
        now = datetime.datetime.now()
        diff = now - timestamp

        if diff.total_seconds() < 60:
            return "Just now"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(diff.total_seconds() / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"

    def _get_next_update_time(self) -> Optional[str]:
        """Get the time of next scheduled update."""
        if self._last_update is None:
            return "Soon"

        next_update = self._last_update + datetime.timedelta(seconds=self._update_interval)
        return next_update.strftime("%H:%M")


# Global instance
auto_updater = AutoUpdater()