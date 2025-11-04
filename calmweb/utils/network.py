#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Network utilities for CalmWeb.
Provides socket optimization and relay functions.
"""

import socket
import threading
import platform

from ..config.settings import _SHUTDOWN_EVENT


def _set_socket_opts_for_perf(sock):
    """Optimize socket for performance."""
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        # Windows-specific keepalive tuning (optional)
        if platform.system().lower() == 'windows':
            # tuple: (on/off, keepalive_time_ms, keepalive_interval_ms)
            sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 60000, 10000))
    except Exception:
        pass


def _relay_worker(src, dst, buffer_size=65536):
    """
    Unidirectional relay: src -> dst. Tolerates errors and closes sockets cleanly.
    """
    try:
        while not _SHUTDOWN_EVENT.is_set():
            try:
                data = src.recv(buffer_size)
            except Exception:
                break
            if not data:
                try:
                    dst.shutdown(socket.SHUT_WR)
                except Exception:
                    pass
                break
            try:
                dst.sendall(data)
            except Exception:
                break
    except Exception:
        pass
    finally:
        try:
            dst.shutdown(socket.SHUT_WR)
        except Exception:
            pass


def full_duplex_relay(a_sock, b_sock):
    """
    Launches two threads to relay a->b and b->a in blocking mode.
    Returns when both directions are finished.
    """
    t1 = threading.Thread(target=_relay_worker, args=(a_sock, b_sock), daemon=True)
    t2 = threading.Thread(target=_relay_worker, args=(b_sock, a_sock), daemon=True)
    t1.start()
    t2.start()
    # Wait for natural thread completion (no timeout)
    t1.join()
    t2.join()
    # Best-effort close
    try:
        a_sock.close()
    except Exception:
        pass
    try:
        b_sock.close()
    except Exception:
        pass