# ═══════════════════════════════════════════════════════════════
#  GRIMOIRE v2.0 — codex/__init__.py
#  Target Journal — The Death Note
#
#  Developer  : Light
#  Alias      : Neok1ra
#  GitHub     : https://github.com/ne0k1r4
#  Tool       : GRIMOIRE — The Death Note of the digital world
#
#  Features:
#    Target tracking with risk scoring (CRITICAL/HIGH/MEDIUM/LOW)
#    Tags system (web, network, ad, cloud, iot, etc.)
#    Markdown + HTML report export
#    Full history log per target
#    Search by name, tag, status, risk
# ═══════════════════════════════════════════════════════════════

import json, os, hashlib, readline
from datetime import datetime
from pathlib import Path
from ..utils import C, section, ReportBuilder, uid, datestamp

DATA_DIR   = Path.home() / ".grimoire"
CODEX_FILE = DATA_DIR / "codex.json"

BANNER = f"""
{C.RED}{C.BOLD}  ╔══════════════════════════════════════════════╗
  ║  C O D E X  v2.0  —  The Death Note         ║
  ║  Developer: Light (Neok1ra)                  ║
  ╚══════════════════════════════════════════════╝{C.RESET}
  {C.DIM}Write a name. Assign risk. Begin the operation.{C.RESET}
"""

STATUSES = ["WATCHING","ACTIVE","OWNED","CLOSED","PENDING"]
RISKS    = ["CRITICAL","HIGH","MEDIUM","LOW","INFO"]
TAGS     = ["web","network","ad","cloud","iot","api","mobile","internal","external","dmz"]

RISK_COLORS = {
    "CRITICAL": C.RED + C.BOLD,
    "HIGH":     C.RED,
    "MEDIUM":   C.YELLOW,
    "LOW":      C.CYAN,
    "INFO":     C.DIM,
}
STATUS_COLORS = {
    "WATCHING": C.YELLOW,
    "ACTIVE":   C.RED,
    "OWNED":    C.GREEN,
    "CLOSED":   C.DIM,
    "PENDING":  C.CYAN,
}

def _ensure(): DATA_DIR.mkdir(parents=True, exist_ok=True)

def _load() -> list:
    _ensure()
    if not CODEX_FILE.exists(): return []
    try:
        with open(CODEX_FILE) as f: return json.load(f)
    except: return []

def _save(targets):
    _ensure()
    with open(CODEX_FILE, "w") as f: json.dump(targets, f, indent=2)

def _fmt_risk(r):
    c = RISK_COLORS.get(r, C.DIM)
    return f"{c}{r}{C.RESET}"

def _fmt_status(s):
    c = STATUS_COLORS.get(s, C.DIM)
    return f"{c}{s}{C.RESET}"

def _list_targets(targets, filter_tag=None, filter_status=None, filter_risk=None):
    filtered = targets
    if filter_tag:    filtered = [t for t in filtered if filter_tag in t.get("tags",[])]
    if filter_status: filtered = [t for t in filtered if t.get("status") == filter_status.upper()]
    if filter_risk:   filtered = [t for t in filtered if t.get("risk") == filter_risk.upper()]
    if not filtered:
        print(f"  {C.DIM}[No entries]{C.RESET}"); return
    print(f"\n  {C.RED}{'#':>3}  {'ID':<10} {'TARGET':<28} {'RISK':<10} {'STATUS':<10} {'TAGS':<20} {'ADDED'}{C.RESET}")
    print(f"  {'─'*90}")
    for i, t in enumerate(filtered):
        risk   = t.get("risk","LOW")
        status = t.get("status","WATCHING")
        tags   = ",".join(t.get("tags",[]))[:18]
        rc = RISK_COLORS.get(risk, C.DIM)
        sc = STATUS_COLORS.get(status, C.DIM)
        print(f"  {str(i+1):>3}  {C.DIM}{t['id']:<10}{C.RESET} {t['name']:<28} "
              f"{rc}{risk:<10}{C.RESET} {sc}{status:<10}{C.RESET} "
              f"{C.DIM}{tags:<20}{C.RESET} {t['added']}")
    print()

def _add_target(name, notes="", status="WATCHING", risk="MEDIUM", tags=None):
    return {
        "id":      uid(name)[:8],
        "name":    name,
        "status":  status.upper(),
        "risk":    risk.upper(),
        "notes":   notes,
        "tags":    tags or [],
        "added":   datestamp(),
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "history": [],
        "findings":[],
    }

def _show_target(t):
    section(f"TARGET: {t['name']}")
    print(f"  {C.CYAN}ID       {C.RESET} {t['id']}")
    print(f"  {C.CYAN}Risk     {C.RESET} {_fmt_risk(t.get('risk','MEDIUM'))}")
    print(f"  {C.CYAN}Status   {C.RESET} {_fmt_status(t.get('status','WATCHING'))}")
    print(f"  {C.CYAN}Tags     {C.RESET} {', '.join(t.get('tags',[]))}")
    print(f"  {C.CYAN}Notes    {C.RESET} {t.get('notes','')}")
    print(f"  {C.CYAN}Added    {C.RESET} {t['added']}")
    print(f"  {C.CYAN}Updated  {C.RESET} {t['updated']}")
    if t.get("findings"):
        print(f"\n  {C.RED}Findings:{C.RESET}")
        for f in t["findings"]:
            print(f"  {C.DIM}  [{f['ts']}] {f['text']}{C.RESET}")
    if t.get("history"):
        print(f"\n  {C.RED}History:{C.RESET}")
        for h in t["history"][-5:]:
            print(f"  {C.DIM}  [{h['ts']}] Status => {h['status']}{C.RESET}")
    print()

def export_report(targets) -> str:
    rb = ReportBuilder("GRIMOIRE Engagement Report — Codex")
    # summary table
    rb.add_table("Target Summary",
        ["ID","Name","Risk","Status","Tags","Added"],
        [[t["id"], t["name"], t.get("risk","?"), t.get("status","?"),
          ",".join(t.get("tags",[])), t["added"]] for t in targets])
    # per target detail
    for t in targets:
        lines = [
            f"**Risk:** {t.get('risk','?')}  ",
            f"**Status:** {t.get('status','?')}  ",
            f"**Tags:** {', '.join(t.get('tags',[]))}  ",
            f"**Notes:** {t.get('notes','')}  ",
        ]
        if t.get("findings"):
            lines.append("\n**Findings:**")
            for f in t["findings"]:
                lines.append(f"- `[{f['ts']}]` {f['text']}")
        rb.add_section(f"Target: {t['name']}", "\n".join(lines))
    out_dir = DATA_DIR / "reports"
    saved = rb.save(str(out_dir / f"codex_report_{datetime.now().strftime('%Y%m%d_%H%M')}"), "md")
    return saved

def _interactive():
    print(BANNER)
    targets = _load()
    _list_targets(targets)
    print(f"  {C.DIM}Commands: add | list | show <id> | update <id> | find <entry> | report | exit{C.RESET}\n")
    while True:
        try:
            raw = input(f"  {C.RED}codex>{C.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [Closing Codex]"); break
        if not raw: continue
        parts = raw.split(None, 2)
        cmd   = parts[0].lower()

        if cmd in ("exit","quit","q"): break

        elif cmd == "list":
            targets = _load()
            tag = status = risk = None
            for p in parts[1:]:
                if p.startswith("tag:"):    tag    = p[4:]
                elif p.startswith("status:"):status = p[7:]
                elif p.startswith("risk:"):  risk   = p[5:]
            _list_targets(targets, tag, status, risk)

        elif cmd == "add":
            name   = input(f"  {C.DIM}Name/IP/Domain:{C.RESET} ").strip()
            if not name: continue
            print(f"  Risk: {', '.join(RISKS)}")
            risk   = input(f"  {C.DIM}Risk [MEDIUM]:{C.RESET} ").strip().upper() or "MEDIUM"
            print(f"  Status: {', '.join(STATUSES)}")
            status = input(f"  {C.DIM}Status [WATCHING]:{C.RESET} ").strip().upper() or "WATCHING"
            print(f"  Tags: {', '.join(TAGS)}")
            tags   = [t.strip() for t in input(f"  {C.DIM}Tags (comma sep):{C.RESET} ").split(",") if t.strip()]
            notes  = input(f"  {C.DIM}Notes:{C.RESET} ").strip()
            t = _add_target(name, notes, status, risk, tags)
            targets.append(t)
            _save(targets)
            rc = RISK_COLORS.get(risk, C.DIM)
            print(f"  {C.GREEN}[+] Written: {name} — {rc}{risk}{C.RESET}")
            from ..core.oplog import log
            log(f"Target added: {name} [{risk}]", "codex")

        elif cmd == "show" and len(parts) >= 2:
            targets = _load()
            try:
                idx = int(parts[1]) - 1
                _show_target(targets[idx])
            except (ValueError, IndexError):
                matches = [t for t in targets if parts[1].lower() in t["name"].lower()]
                for t in matches: _show_target(t)

        elif cmd == "update" and len(parts) >= 2:
            targets = _load()
            try:
                idx = int(parts[1]) - 1
                t = targets[idx]
                print(f"  Current: risk={t.get('risk')} status={t.get('status')}")
                new_risk   = input(f"  {C.DIM}New risk (blank=keep):{C.RESET} ").strip().upper()
                new_status = input(f"  {C.DIM}New status (blank=keep):{C.RESET} ").strip().upper()
                finding    = input(f"  {C.DIM}Add finding (blank=skip):{C.RESET} ").strip()
                if new_risk   in RISKS:    t["risk"]   = new_risk
                if new_status in STATUSES:
                    t["history"].append({"status": t["status"], "ts": t["updated"]})
                    t["status"] = new_status
                if finding:
                    t.setdefault("findings", []).append({"ts": datetime.now().strftime("%H:%M %d/%m"), "text": finding})
                t["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                _save(targets)
                print(f"  {C.GREEN}[+] Updated: {t['name']}{C.RESET}")
            except (ValueError, IndexError):
                print(f"  {C.YELLOW}[!] Invalid ID{C.RESET}")

        elif cmd == "find" and len(parts) >= 2:
            targets = _load()
            q = parts[1].lower()
            matches = [t for t in targets if q in t["name"].lower() or q in " ".join(t.get("tags",[])).lower()]
            _list_targets(matches)

        elif cmd == "report":
            targets = _load()
            if not targets:
                print(f"  {C.DIM}[No targets to report]{C.RESET}"); continue
            saved = export_report(targets)
            print(f"  {C.GREEN}[+] Report exported: {saved}{C.RESET}")

        else:
            print(f"  {C.DIM}Commands: add | list [tag:X] [risk:X] | show <id> | update <id> | find <q> | report | exit{C.RESET}")

def cli_main(args):
    if args and args[0] == "report":
        targets = _load()
        saved = export_report(targets)
        print(f"  {C.GREEN}[+] Report: {saved}{C.RESET}")
    else: _interactive()

def launch(): _interactive()
