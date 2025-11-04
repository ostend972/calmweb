#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Log window for CalmWeb.
Provides a Tkinter-based log viewer window.
"""

import tkinter as tk
from tkinter.scrolledtext import ScrolledText

from ..config.settings import _SHUTDOWN_EVENT
from ..utils.logging import log, log_buffer, _LOG_LOCK


def show_log_window():
    """
    Tkinter window that displays the log_buffer and updates itself.
    """
    try:
        win = tk.Tk()
    except Exception as e:
        log(f"Unable to open Tkinter: {e}")
        return

    win.title("Calm Web - Activity Log")
    win.geometry("700x400")
    text_area = ScrolledText(win, wrap=tk.WORD)
    text_area.pack(expand=True, fill='both')
    text_area.config(state='disabled')

    def refresh_log():
        try:
            text_area.config(state='normal')
            with _LOG_LOCK:
                text_area.delete(1.0, tk.END)
                text_area.insert(tk.END, '\n'.join(log_buffer))
            text_area.see(tk.END)
            text_area.config(state='disabled')
        except Exception:
            pass
        if not _SHUTDOWN_EVENT.is_set():
            win.after(1000, refresh_log)
        else:
            try:
                win.destroy()
            except Exception:
                pass

    refresh_log()
    try:
        win.mainloop()
    except Exception:
        pass