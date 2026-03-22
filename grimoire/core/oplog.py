# ═══════════════════════════════════════════════════════════════
#  GRIMOIRE v2.0 — core/oplog.py
#  Op Log — thread-safe, persistent, ring-buffered
#
#  Developer  : Light
#  Alias      : Neok1ra
#  GitHub     : https://github.com/ne0k1r4
#  Tool       : GRIMOIRE — The Death Note of the digital world
# ═══════════════════════════════════════════════════════════════

import os, json, threading
from datetime import datetime
from pathlib import Path

LOG_DIR  = Path.home() / ".grimoire"
LOG_FILE = LOG_DIR / "oplog.json"

_lock    = threading.Lock()
_entries = []
MAX_MEM  = 300


def _ts(): return datetime.now().strftime("%H:%M:%S")


def _ensure(): LOG_DIR.mkdir(parents=True, exist_ok=True)


def _flush(entry):
    _ensure()
    try:
        existing = []
        if LOG_FILE.exists():
            with open(LOG_FILE) as f: existing = json.load(f)
        existing.append(entry)
        existing = existing[-2000:]
        with open(LOG_FILE, "w") as f: json.dump(existing, f, indent=2)
    except Exception:
        pass


def log(msg: str, module: str = "core", level: str = "INFO"):
    entry = {
        "ts":     _ts(),
        "date":   datetime.now().strftime("%Y-%m-%d"),
        "module": module,
        "level":  level,
        "msg":    msg,
    }
    with _lock:
        _entries.append(entry)
        if len(_entries) > MAX_MEM: _entries.pop(0)
    threading.Thread(target=_flush, args=(entry,), daemon=True).start()


def warn(msg, module="core"):  log(msg, module, "WARN")
def error(msg, module="core"): log(msg, module, "ERROR")


def get_recent(n: int = 20) -> list:
    with _lock: return list(_entries[-n:])


def init():
    global _entries
    _ensure()
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE) as f: disk = json.load(f)
            with _lock: _entries = disk[-MAX_MEM:]
        except Exception: pass
    log(f"GRIMOIRE v2.0 initialized — Light (Neok1ra)", "core")
