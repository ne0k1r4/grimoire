# ═══════════════════════════════════════════════════════════════
#  GRIMOIRE v2.0 — utils/__init__.py
#  Shared utilities: colors, reporting, banners
#
#  Developer  : Light
#  Alias      : Neok1ra
#  GitHub     : https://github.com/ne0k1r4
#  Tool       : GRIMOIRE — The Death Note of the digital world
# ═══════════════════════════════════════════════════════════════

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

# ── ANSI color engine ─────────────────────────────────────────

class C:
    RED     = "\033[91m"
    RED2    = "\033[31m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    CREAM   = "\033[38;2;232;213;196m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    ITALIC  = "\033[3m"
    UNDER   = "\033[4m"
    BLINK   = "\033[5m"
    RESET   = "\033[0m"

    @staticmethod
    def rgb(r, g, b, text):
        return f"\033[38;2;{r};{g};{b}m{text}\033[0m"

    @staticmethod
    def strip(text):
        import re
        return re.sub(r'\033\[[0-9;]*m', '', text)


# ── Risk scoring ──────────────────────────────────────────────

RISK_COLORS = {
    "CRITICAL": C.RED + C.BOLD,
    "HIGH":     C.RED,
    "MEDIUM":   C.YELLOW,
    "LOW":      C.CYAN,
    "INFO":     C.DIM,
}

def risk_label(level: str) -> str:
    c = RISK_COLORS.get(level.upper(), C.DIM)
    return f"{c}[{level.upper()}]{C.RESET}"


# ── Section header printer ────────────────────────────────────

def section(title: str, width: int = 50):
    bar = "─" * width
    print(f"\n  {C.RED}{C.BOLD}[{title}]{C.RESET}")
    print(f"  {C.DIM}{bar}{C.RESET}")


def banner_line(text: str):
    print(f"  {C.RED}{'═' * 52}{C.RESET}")
    pad = (52 - len(text)) // 2
    print(f"  {C.RED}║{' ' * pad}{C.BOLD}{text}{C.RESET}{C.RED}{' ' * (52 - pad - len(text))}║{C.RESET}")
    print(f"  {C.RED}{'═' * 52}{C.RESET}")


# ── Markdown report engine ────────────────────────────────────

class ReportBuilder:
    """
    Builds a Markdown/HTML engagement report.
    Developer: Light (Neok1ra)
    """

    def __init__(self, title: str = "GRIMOIRE Engagement Report"):
        self.title    = title
        self.sections = []
        self.meta     = {
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tool":      "GRIMOIRE v2.0",
            "author":    "Light (Neok1ra)",
        }

    def add_section(self, heading: str, content: str):
        self.sections.append({"heading": heading, "content": content})
        return self

    def add_table(self, heading: str, headers: list, rows: list):
        lines = [f"| {' | '.join(headers)} |"]
        lines.append(f"| {' | '.join(['---'] * len(headers))} |")
        for row in rows:
            lines.append(f"| {' | '.join(str(c) for c in row)} |")
        self.sections.append({"heading": heading, "content": "\n".join(lines)})
        return self

    def to_markdown(self) -> str:
        lines = [
            f"# {self.title}",
            "",
            f"> Generated: {self.meta['generated']}  ",
            f"> Tool: {self.meta['tool']}  ",
            f"> Author: {self.meta['author']}  ",
            "",
            "---",
            "",
        ]
        for sec in self.sections:
            lines.append(f"## {sec['heading']}")
            lines.append("")
            lines.append(sec["content"])
            lines.append("")
            lines.append("---")
            lines.append("")
        return "\n".join(lines)

    def to_html(self) -> str:
        md = self.to_markdown()
        # minimal inline conversion
        import re
        html = md
        html = re.sub(r'^# (.+)$',  r'<h1>\1</h1>', html, flags=re.M)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.M)
        html = re.sub(r'^> (.+)$',  r'<blockquote>\1</blockquote>', html, flags=re.M)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
        html = re.sub(r'^---$', r'<hr>', html, flags=re.M)
        html = html.replace("\n", "<br>\n")
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{self.title}</title>
<style>
  body{{background:#0a0000;color:#e8d5c4;font-family:'Courier New',monospace;padding:32px;max-width:900px;margin:auto}}
  h1,h2{{color:#cc0000}} hr{{border-color:#330000}} code{{background:#1a0000;padding:2px 6px}}
  blockquote{{border-left:3px solid #cc0000;padding-left:12px;color:#6a5a52;margin:4px 0}}
  table{{border-collapse:collapse;width:100%}} td,th{{border:1px solid #330000;padding:6px 10px}}
  th{{color:#cc0000;background:#120000}}
</style>
</head>
<body>{html}</body>
</html>"""

    def save(self, path: str, fmt: str = "md") -> str:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "html":
            p.with_suffix(".html").write_text(self.to_html())
            return str(p.with_suffix(".html"))
        else:
            p.with_suffix(".md").write_text(self.to_markdown())
            return str(p.with_suffix(".md"))


# ── Timestamp helper ──────────────────────────────────────────

def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def datestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def uid(seed: str = "") -> str:
    raw = f"{seed}{datetime.now().isoformat()}{os.urandom(4).hex()}"
    return hashlib.md5(raw.encode()).hexdigest()[:8].upper()
