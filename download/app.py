#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""app.py – Entry point for MTC Novel Downloader."""
import os, sys, time, threading
from pathlib import Path

from download.config import log, EXIT_RELOAD, ROOT_DIR
from download.ui import App

# ── Hot-reload watcher ────────────────────────────────────────────────────────
_WATCH_DIR = ROOT_DIR / "download"

def _file_watcher(app: App):
    """Poll .py files every 2s, exit on change for restart."""
    snapshots = {}
    for f in list(_WATCH_DIR.glob("*.py")):
        try:
            snapshots[f] = f.stat().st_mtime
        except OSError:
            pass
    log.debug(f"File watcher: tracking {len(snapshots)} files")

    while True:
        time.sleep(2)
        for f in list(_WATCH_DIR.glob("*.py")):
            try:
                mt = f.stat().st_mtime
            except OSError:
                continue
            old = snapshots.get(f)
            if old is not None and mt > old:
                log.info(f"File changed: {f.name} — reloading...")
                app.after(0, lambda: _do_reload(app))
                return
            snapshots[f] = mt

def _do_reload(app: App):
    log.info("Hot-reload: shutting down for restart")
    try:
        app.destroy()
    except Exception:
        pass
    os._exit(EXIT_RELOAD)


if __name__ == "__main__":
    log.info("=== MTC Novel Downloader started ===")
    app = App()
    if os.environ.get("MTC_HOT_RELOAD", "0") == "1":
        log.info("Hot-reload enabled")
        threading.Thread(target=_file_watcher, args=(app,), daemon=True).start()
    app.mainloop()
