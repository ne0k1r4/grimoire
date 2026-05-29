# tui dashboard — curses
# this thing breaks if terminal is under 80x24, dont bother fixing it

import curses
import time
import threading
import random
from datetime import datetime

from .banner  import GRIMOIRE_BANNER_SMALL, KIRA_QUOTES, KIRA_MOTD, VERSION, AUTHOR, ALIAS, GITHUB
from .sysinfo import get_all as get_sys
from .oplog   import log, get_recent, init as init_log

# ── Colour pair IDs ───────────────────────────
C_RED       = 1
C_DIM       = 2
C_NORMAL    = 3
C_HIGHLIGHT = 4
C_BORDER    = 5
C_TITLE     = 6
C_WARN      = 7
C_SUCCESS   = 8
C_CREAM     = 9

MODULES = [
    ("codex",     "CODEX",     "Target Journal       ", "risk scoring · tags · reports"),
    ("wraith",    "WRAITH",    "Passive Recon         ", "HTTP · tech · ports · reports"),
    ("voxcrypt",  "VOXCRYPT",  "Stego Engine          ", "LSB · WAV · ZWC · HMAC"),
    ("forge",     "FORGE",     "Payload Generator     ", "15 shells · obfuscate · save"),
    ("vault",     "VAULT",     "Credential Manager    ", "KeePassXC CLI"),
    ("phantom",   "PHANTOM",   "Network Pivot Tracker ", "SSH gen · chain map"),
    ("sovereign", "SOVEREIGN", "C2 Manager            ", "sessions · history · logs"),
    ("web",       "WEB UI",    "Local Dashboard       ", "localhost:1337 · live refresh"),
]

HELP_LINES = [
    f"  GRIMOIRE v{VERSION}  —  {AUTHOR} ({ALIAS})",
    f"  {GITHUB}",
    "",
    "  NAVIGATION",
    "  ─────────────────────────────────────",
    "  UP / DOWN     Navigate modules",
    "  ENTER         Launch selected module",
    "  Q             Quit",
    "  H             Toggle this help panel",
    "  R             Refresh system stats",
    "",
    "  MODULES",
    "  ─────────────────────────────────────",
    "  CODEX         Target journal — risk, tags, report",
    "  WRAITH        Passive recon + HTTP fingerprint",
    "  VOXCRYPT      Stego engine (PNG/WAV/ZWC)",
    "  FORGE         15 reverse shells + obfuscation",
    "  VAULT         KeePassXC credential manager",
    "  PHANTOM       Pivot tracker + SSH cmd gen",
    "  SOVEREIGN     C2 multi-session manager",
    "  WEB UI        Dashboard at localhost:1337",
    "",
    "  DATA",
    "  ─────────────────────────────────────",
    "  ~/.grimoire/codex.json     targets",
    "  ~/.grimoire/phantom.json   pivots",
    "  ~/.grimoire/oplog.json     op log",
    "  ~/.grimoire/reports/       exports",
    "  ~/.grimoire/sessions/      C2 logs",
    "",
    "  Press H to close.",
]


class GrimoireTUI:

    def __init__(self, stdscr):
        self.scr        = stdscr
        self.cursor     = 0
        self.show_help  = False
        self._sys       = {}
        self._running   = True
        self._lock      = threading.Lock()
        self._motd      = random.choice(KIRA_MOTD)
        self._quote     = random.choice(KIRA_QUOTES)
        self._tick      = 0

    # ── curses setup ──────────────────────────

    def _init_colors(self):
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(C_RED,       curses.COLOR_RED,     -1)
        curses.init_pair(C_DIM,       curses.COLOR_WHITE,   -1)
        curses.init_pair(C_NORMAL,    curses.COLOR_WHITE,   -1)
        curses.init_pair(C_HIGHLIGHT, curses.COLOR_BLACK,   curses.COLOR_RED)
        curses.init_pair(C_BORDER,    curses.COLOR_RED,     -1)
        curses.init_pair(C_TITLE,     curses.COLOR_RED,     -1)
        curses.init_pair(C_WARN,      curses.COLOR_YELLOW,  -1)
        curses.init_pair(C_SUCCESS,   curses.COLOR_GREEN,   -1)
        curses.init_pair(C_CREAM,     curses.COLOR_WHITE,   -1)

    def _init_curses(self):
        curses.curs_set(0)
        curses.noecho()
        curses.cbreak()
        self.scr.keypad(True)
        self.scr.nodelay(True)
        self._init_colors()

    # ── safe draw ─────────────────────────────

    def _put(self, win, y, x, text, attr=0):
        h, w = win.getmaxyx()
        if y < 0 or y >= h or x < 0: return
        cut = w - x - 1
        if cut <= 0: return
        try:
            win.addstr(y, x, text[:cut], attr)
        except curses.error:
            pass

    def _box(self, win, title=""):
        try: win.box()
        except curses.error: pass
        if title:
            self._put(win, 0, 2, f" {title} ",
                      curses.color_pair(C_TITLE) | curses.A_BOLD)

    # ── panels ────────────────────────────────

    def _draw_statusbar(self, win):
        h, w = win.getmaxyx()
        bar = "  Q:quit   ENTER:launch   ↑↓:navigate   H:help   R:refresh  "
        self._put(win, 0, 0, bar.ljust(w - 1), curses.color_pair(C_HIGHLIGHT))

    def _draw_header(self, win):
        self._box(win)
        h, w = win.getmaxyx()
        lines = GRIMOIRE_BANNER_SMALL.split("\n")
        for i, line in enumerate(lines[1:], 1):
            if i >= h - 2: break
            cx = max(0, (w - len(line)) // 2)
            self._put(win, i, cx, line, curses.color_pair(C_RED) | curses.A_BOLD)
        info = f"v{VERSION}  |  {AUTHOR} ({ALIAS})  |  {GITHUB}  |  {self._motd}"
        self._put(win, h - 2, max(0, (w - len(info)) // 2), info,
                  curses.color_pair(C_DIM))

    def _draw_modules(self, win):
        self._box(win, "MODULES")
        h, w = win.getmaxyx()
        for i, (key, name, _, hint) in enumerate(MODULES):
            row = 2 + i
            if row >= h - 1: break
            if i == self.cursor:
                bg = curses.color_pair(C_HIGHLIGHT) | curses.A_BOLD
                self._put(win, row, 1, " " * (w - 2), bg)
                self._put(win, row, 2, f"▶ {name}", bg)
            else:
                self._put(win, row, 2, f"  {name}",
                          curses.color_pair(C_NORMAL))

    def _draw_output(self, win):
        key, name, desc, hint = MODULES[self.cursor]
        self._box(win, f"MODULE  {name}")
        h, w = win.getmaxyx()

        # module title
        self._put(win, 2, 3, name,
                  curses.color_pair(C_RED) | curses.A_BOLD)
        self._put(win, 3, 3, desc.strip(),
                  curses.color_pair(C_NORMAL))
        self._put(win, 4, 3, hint,
                  curses.color_pair(C_DIM))

        # separator
        self._put(win, 6, 3, "─" * min(w - 6, 50),
                  curses.color_pair(C_BORDER))

        # current targets (from codex) shown in codex panel
        if key == "codex":
            try:
                from ..codex import _load
                targets = _load()
                self._put(win, 7, 3, f"Targets in Codex: {len(targets)}",
                          curses.color_pair(C_SUCCESS))
                risk_counts = {}
                for t in targets:
                    r = t.get("risk","?")
                    risk_counts[r] = risk_counts.get(r, 0) + 1
                row = 8
                for r, n in risk_counts.items():
                    if row >= h - 1: break
                    self._put(win, row, 5, f"{r}: {n}",
                              curses.color_pair(C_WARN) if r in ("CRITICAL","HIGH") else curses.color_pair(C_DIM))
                    row += 1
            except Exception:
                pass

        elif key == "sovereign":
            try:
                from ..sovereign import _sessions
                n = len(_sessions)
                self._put(win, 7, 3, f"Active sessions: {n}",
                          curses.color_pair(C_SUCCESS) if n > 0 else curses.color_pair(C_DIM))
            except Exception:
                pass

        elif key == "phantom":
            try:
                from ..phantom import _load
                pivots = _load()
                active = [p for p in pivots if p.get("status") == "ACTIVE"]
                self._put(win, 7, 3, f"Pivots tracked: {len(pivots)}  Active: {len(active)}",
                          curses.color_pair(C_SUCCESS) if active else curses.color_pair(C_DIM))
            except Exception:
                pass

        # kira quote
        quote_row = h - 3
        if quote_row > 8:
            self._put(win, quote_row, 3, f'"{self._quote}"',
                      curses.color_pair(C_RED))
        self._put(win, h - 2, 3, "Press ENTER to launch",
                  curses.color_pair(C_DIM))

    def _draw_sysinfo(self, win):
        self._box(win, "SYSTEM")
        h, w = win.getmaxyx()
        s = self._sys
        now = datetime.now().strftime("%H:%M:%S")
        fields = [
            ("HOST",   s.get("host","?")),
            ("IP",     s.get("ip","?")),
            ("CPU",    s.get("cpu","?")),
            ("RAM",    f"{s.get('ram_used','?')}/{s.get('ram_total','?')} ({s.get('ram_pct','?')})"),
            ("↑↓NET",  f"{s.get('net_up','?')} / {s.get('net_down','?')}"),
            ("UPTIME", s.get("uptime","?")),
            ("TIME",   now),
        ]
        col, row = 2, 1
        for label, val in fields:
            entry = f"{label}: {val}"
            if col + len(entry) + 4 > w - 2:
                col = 2; row += 1
            if row >= h - 1: break
            self._put(win, row, col, f"{label}:", curses.color_pair(C_RED))
            self._put(win, row, col + len(label) + 2, val, curses.color_pair(C_NORMAL))
            col += len(entry) + 4

    def _draw_oplog(self, win):
        self._box(win, "OP LOG")
        h, w = win.getmaxyx()
        entries = get_recent(h - 3)
        for i, e in enumerate(entries, 2):
            if i >= h - 1: break
            ts  = e.get("ts","??:??")
            mod = e.get("module","core").upper()[:8]
            msg = e.get("msg","")
            lvl = e.get("level","INFO")
            line = f"[{ts}] [{mod:<8}] {msg}"
            attr = curses.color_pair(C_DIM)
            if lvl == "WARN":  attr = curses.color_pair(C_WARN)
            if lvl == "ERROR": attr = curses.color_pair(C_RED)
            self._put(win, i, 2, line, attr)

    def _draw_help(self, win):
        self._box(win, "HELP")
        h, w = win.getmaxyx()
        for i, line in enumerate(HELP_LINES, 2):
            if i >= h - 1: break
            attr = curses.color_pair(C_NORMAL)
            if "GRIMOIRE" in line and "v" in line:
                attr = curses.color_pair(C_RED) | curses.A_BOLD
            elif line.strip().startswith("─"):
                attr = curses.color_pair(C_BORDER)
            elif line.strip().startswith("~"):
                attr = curses.color_pair(C_DIM)
            elif line.strip().isupper() and len(line.strip()) < 20:
                attr = curses.color_pair(C_TITLE) | curses.A_BOLD
            self._put(win, i, 2, line, attr)

    # ── layout ────────────────────────────────

    def _build_layout(self):
        H, W = self.scr.getmaxyx()
        STAT_H   = 1
        HEAD_H   = 7
        SYS_H    = 4
        LOG_H    = max(5, H // 5)
        BODY_H   = H - STAT_H - HEAD_H - SYS_H - LOG_H
        MOD_W    = 18
        OUT_W    = W - MOD_W
        y0 = 0
        wins = {}
        wins["status"]  = curses.newwin(STAT_H, W,     y0, 0)
        wins["header"]  = curses.newwin(HEAD_H, W,     y0 + STAT_H, 0)
        wins["modules"] = curses.newwin(BODY_H, MOD_W, y0 + STAT_H + HEAD_H, 0)
        wins["output"]  = curses.newwin(BODY_H, OUT_W, y0 + STAT_H + HEAD_H, MOD_W)
        wins["sysinfo"] = curses.newwin(SYS_H,  W,     y0 + STAT_H + HEAD_H + BODY_H, 0)
        wins["oplog"]   = curses.newwin(LOG_H,  W,     y0 + STAT_H + HEAD_H + BODY_H + SYS_H, 0)
        return wins

    # ── background ────────────────────────────

    def _bg_refresh(self):
        while self._running:
            with self._lock:
                self._sys = get_sys()
            time.sleep(2)

    # ── input ─────────────────────────────────

    def _handle_key(self, key):
        if key in (ord("q"), ord("Q")):
            self._running = False
        elif key == curses.KEY_UP:
            self.cursor = (self.cursor - 1) % len(MODULES)
        elif key == curses.KEY_DOWN:
            self.cursor = (self.cursor + 1) % len(MODULES)
        elif key in (curses.KEY_ENTER, 10, 13):
            self._launch(MODULES[self.cursor][0])
        elif key in (ord("h"), ord("H")):
            self.show_help = not self.show_help
        elif key in (ord("r"), ord("R")):
            with self._lock: self._sys = get_sys()
            log("Stats refreshed", "core")

    def _launch(self, mod: str):
        log(f"Launching: {mod.upper()}", mod)
        try:
            if mod == "codex":       from ..codex     import launch
            elif mod == "wraith":    from ..wraith    import launch
            elif mod == "voxcrypt":  from ..voxcrypt  import launch
            elif mod == "forge":     from ..forge     import launch
            elif mod == "vault":     from ..vault     import launch
            elif mod == "phantom":   from ..phantom   import launch
            elif mod == "sovereign": from ..sovereign import launch
            elif mod == "web":       from ..web       import launch
            else: return
            curses.endwin()
            launch()
            self.scr = curses.initscr()
            self._init_curses()
            self._quote = random.choice(KIRA_QUOTES)
        except Exception as e:
            log(f"Module error: {e}", mod, "ERROR")

    # ── main loop ─────────────────────────────

    def run(self):
        init_log()
        self._init_curses()
        self._sys = get_sys()
        threading.Thread(target=self._bg_refresh, daemon=True).start()
        log(f"GRIMOIRE v{VERSION} initialized — {AUTHOR} ({ALIAS})", "core")

        while self._running:
            try:
                H, W = self.scr.getmaxyx()
                if H < 24 or W < 80:
                    self.scr.clear()
                    msg = "Terminal too small — resize to at least 80x24"
                    try: self.scr.addstr(0, 0, msg)
                    except: pass
                    self.scr.refresh()
                    time.sleep(0.3)
                    key = self.scr.getch()
                    if key in (ord("q"), ord("Q")): self._running = False
                    continue

                wins = self._build_layout()
                for w in wins.values(): w.erase()

                self._draw_statusbar(wins["status"])
                self._draw_header(wins["header"])
                self._draw_modules(wins["modules"])
                if self.show_help:
                    self._draw_help(wins["output"])
                else:
                    self._draw_output(wins["output"])
                self._draw_sysinfo(wins["sysinfo"])
                self._draw_oplog(wins["oplog"])

                for w in wins.values():
                    try: w.noutrefresh()
                    except curses.error: pass
                curses.doupdate()

                key = self.scr.getch()
                if key != -1: self._handle_key(key)
                time.sleep(0.05)

            except curses.error:
                pass
            except KeyboardInterrupt:
                self._running = False


def launch_tui():
    def _main(stdscr):
        GrimoireTUI(stdscr).run()
    curses.wrapper(_main)
