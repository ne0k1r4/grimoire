# ═══════════════════════════════════════════════════════════════
#  GRIMOIRE v2.0 — phantom/__init__.py
#  Network Pivot Tracker
#
#  Developer  : Light
#  Alias      : Neok1ra
#  GitHub     : https://github.com/ne0k1r4
#  Tool       : GRIMOIRE — The Death Note of the digital world
#
#  Features:
#    Pivot chain tracking
#    SSH command generator (-L / -R / -D)
#    ASCII chain map visualization
#    Export pivot map to markdown
# ═══════════════════════════════════════════════════════════════

import json
from datetime import datetime
from pathlib import Path
from ..utils import C, section, uid, datestamp, ReportBuilder

DATA_DIR     = Path.home() / ".grimoire"
PHANTOM_FILE = DATA_DIR / "phantom.json"

BANNER = f"""
{C.RED}{C.BOLD}  ╔══════════════════════════════════════════════╗
  ║  P H A N T O M  v2.0  —  Pivot Tracker      ║
  ║  Developer: Light (Neok1ra)                  ║
  ╚══════════════════════════════════════════════╝{C.RESET}
  {C.DIM}SSH Tunnels · SOCKS · Chisel · Ligolo · Chain Map{C.RESET}
"""

PIVOT_TYPES    = ["SSH_L","SSH_R","SSH_D","SOCKS5","CHISEL","LIGOLO","MANUAL","OTHER"]
PIVOT_STATUSES = ["ACTIVE","CLOSED","BROKEN","PENDING"]

STATUS_COLORS = {
    "ACTIVE":  C.GREEN,
    "CLOSED":  C.DIM,
    "BROKEN":  C.YELLOW,
    "PENDING": C.CYAN,
}

def _ensure(): DATA_DIR.mkdir(parents=True, exist_ok=True)
def _load():
    _ensure()
    if not PHANTOM_FILE.exists(): return []
    try:
        with open(PHANTOM_FILE) as f: return json.load(f)
    except: return []
def _save(pivots):
    _ensure()
    with open(PHANTOM_FILE, "w") as f: json.dump(pivots, f, indent=2)

def _fmt_status(s):
    c = STATUS_COLORS.get(s, "")
    return f"{c}{s}{C.RESET}"


# ── SSH command generator ─────────────────────────────────────

def gen_ssh_command(ptype: str, local_port: str, remote_host: str,
                    remote_port: str, jump_host: str, ssh_user: str = "user") -> str:
    """
    Generate the actual SSH tunnel command for a pivot.
    -L  local forward  : access remote service via local port
    -R  remote forward : expose local service on remote
    -D  dynamic SOCKS5 : full SOCKS proxy through jump host
    """
    base = f"ssh -N -f"
    if ptype == "SSH_L":
        return f"{base} -L {local_port}:{remote_host}:{remote_port} {ssh_user}@{jump_host}"
    elif ptype == "SSH_R":
        return f"{base} -R {remote_port}:{remote_host}:{local_port} {ssh_user}@{jump_host}"
    elif ptype == "SSH_D":
        return f"{base} -D {local_port} {ssh_user}@{jump_host}"
    elif ptype == "SOCKS5":
        return f"# Via proxychains: proxychains4 -f /etc/proxychains4.conf <cmd>\n# Add to proxychains.conf: socks5 127.0.0.1 {local_port}"
    elif ptype == "CHISEL":
        return (f"# Server (attacker): chisel server -p 8888 --reverse\n"
                f"# Client (target):   chisel client {jump_host}:8888 R:{local_port}:{remote_host}:{remote_port}")
    elif ptype == "LIGOLO":
        return (f"# Agent  (target):   ./agent -connect {jump_host}:11601 -ignore-cert\n"
                f"# Proxy  (attacker): ./proxy -selfcert\n"
                f"# Tunnel: >> start  (in ligolo-ng console)")
    return "# Manual pivot — no command generated"


# ── List / visualize ──────────────────────────────────────────

def _list_pivots(pivots):
    if not pivots:
        print(f"  {C.DIM}[No pivots tracked]{C.RESET}"); return
    print(f"\n  {C.RED}{'ID':<8} {'SRC':<22} {'DST':<22} {'TYPE':<10} {'STATUS':<10} NOTE{C.RESET}")
    print(f"  {'─'*85}")
    for p in pivots:
        s = p.get("status","?")
        print(f"  {C.DIM}{p['id']:<8}{C.RESET} {p['src']:<22} {p['dst']:<22} "
              f"{C.CYAN}{p['ptype']:<10}{C.RESET} {_fmt_status(s):<{10+7}} {p.get('note','')[:25]}")
    print()

def _chain_map(pivots):
    """ASCII visualization of the full pivot chain."""
    section("PIVOT CHAIN MAP")
    active = [p for p in pivots if p.get("status") == "ACTIVE"]
    if not active:
        print(f"  {C.DIM}[No active pivots]{C.RESET}"); return
    print()
    attacker = "ATTACKER"
    nodes = {attacker}
    for p in active: nodes.update([p["src"], p["dst"]])
    chain = [attacker]
    remaining = list(active)
    while remaining:
        added = False
        for p in remaining:
            if p["src"] in chain or chain[-1] in p["src"]:
                if p["dst"] not in chain:
                    chain.append(p["dst"])
                    remaining.remove(p)
                    added = True
                    break
        if not added: break
    for i, node in enumerate(chain):
        color = C.RED if node == attacker else (C.GREEN if i == len(chain)-1 else C.CYAN)
        print(f"  {color}[ {node} ]{C.RESET}", end="")
        if i < len(chain) - 1:
            p = next((x for x in active if x["src"] == node or node in x["src"]), None)
            label = p["ptype"] if p else "???"
            print(f"  {C.DIM}──[{label}]──>{C.RESET}", end="")
    print("\n")
    # unlinked pivots
    linked = set()
    for node in chain:
        for p in active:
            if node in p["src"] or node in p["dst"]: linked.add(p["id"])
    for p in active:
        if p["id"] not in linked:
            print(f"  {C.YELLOW}[!] Unlinked: {p['src']} → {p['dst']} [{p['ptype']}]{C.RESET}")

def _show_pivot(p):
    section(f"PIVOT: {p['id']}")
    for k in ["id","src","dst","ptype","status","note","added"]:
        print(f"  {C.CYAN}{k:<10}{C.RESET} {p.get(k,'')}")
    if p.get("command"):
        print(f"\n  {C.RED}[TUNNEL COMMAND]{C.RESET}")
        for line in p["command"].splitlines():
            print(f"  {line}")
    print()


# ── Interactive ───────────────────────────────────────────────

def _interactive():
    print(BANNER)
    pivots = _load()
    _list_pivots(pivots)
    print(f"  {C.DIM}Commands: list | add | show <id> | update <id> | map | gen | remove <id> | exit{C.RESET}\n")
    while True:
        try:
            raw = input(f"  {C.RED}phantom>{C.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [Closing Phantom]"); break
        if not raw: continue
        parts = raw.split(None, 1)
        cmd   = parts[0].lower()

        if cmd in ("exit","quit","q"): break
        elif cmd == "list":
            pivots = _load(); _list_pivots(pivots)
        elif cmd == "map":
            _chain_map(_load())

        elif cmd == "add":
            src   = input(f"  {C.DIM}Source (host:port or alias):{C.RESET} ").strip()
            dst   = input(f"  {C.DIM}Destination (host:port):{C.RESET} ").strip()
            print(f"  Types: {', '.join(PIVOT_TYPES)}")
            ptype = input(f"  {C.DIM}Type [SSH_L]:{C.RESET} ").strip().upper() or "SSH_L"
            note  = input(f"  {C.DIM}Note:{C.RESET} ").strip()
            # auto-generate SSH command
            cmd_str = ""
            if ptype.startswith("SSH") or ptype in ("CHISEL","LIGOLO","SOCKS5"):
                lport  = input(f"  {C.DIM}Local port:{C.RESET} ").strip()
                rhost  = input(f"  {C.DIM}Remote host:{C.RESET} ").strip()
                rport  = input(f"  {C.DIM}Remote port:{C.RESET} ").strip()
                jhost  = input(f"  {C.DIM}Jump host IP:{C.RESET} ").strip()
                user   = input(f"  {C.DIM}SSH user [root]:{C.RESET} ").strip() or "root"
                cmd_str = gen_ssh_command(ptype, lport, rhost, rport, jhost, user)
                print(f"\n  {C.GREEN}[GENERATED COMMAND]{C.RESET}")
                for line in cmd_str.splitlines():
                    print(f"  {line}")
                print()
            pivot = {
                "id": uid(f"{src}{dst}")[:6],
                "src": src, "dst": dst, "ptype": ptype,
                "status": "PENDING", "note": note,
                "command": cmd_str,
                "added": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            pivots.append(pivot)
            _save(pivots)
            print(f"  {C.GREEN}[+] Pivot added: {src} => {dst} [{ptype}]{C.RESET}")
            from ..core.oplog import log
            log(f"Pivot: {src} => {dst} [{ptype}]", "phantom")

        elif cmd == "gen":
            print(f"  Types: {', '.join(PIVOT_TYPES)}")
            ptype  = input(f"  {C.DIM}Type:{C.RESET} ").strip().upper()
            lport  = input(f"  {C.DIM}Local port:{C.RESET} ").strip()
            rhost  = input(f"  {C.DIM}Remote host:{C.RESET} ").strip()
            rport  = input(f"  {C.DIM}Remote port:{C.RESET} ").strip()
            jhost  = input(f"  {C.DIM}Jump host IP:{C.RESET} ").strip()
            user   = input(f"  {C.DIM}SSH user [root]:{C.RESET} ").strip() or "root"
            result = gen_ssh_command(ptype, lport, rhost, rport, jhost, user)
            print(f"\n  {C.GREEN}[COMMAND]{C.RESET}")
            for line in result.splitlines():
                print(f"  {line}")
            print()

        elif cmd == "show" and len(parts) >= 2:
            pivots = _load()
            matches = [p for p in pivots if p["id"] == parts[1].strip()]
            for p in matches: _show_pivot(p)

        elif cmd == "update" and len(parts) >= 2:
            pivots = _load()
            matches = [p for p in pivots if p["id"] == parts[1].strip()]
            if not matches: print(f"  {C.YELLOW}[!] Not found{C.RESET}"); continue
            p = matches[0]
            print(f"  Options: {', '.join(PIVOT_STATUSES)}")
            ns = input(f"  {C.DIM}New status:{C.RESET} ").strip().upper()
            if ns in PIVOT_STATUSES:
                p["status"] = ns
                _save(pivots)
                print(f"  {C.GREEN}[+] {p['id']} => {ns}{C.RESET}")

        elif cmd == "remove" and len(parts) >= 2:
            pivots = _load()
            before = len(pivots)
            pivots = [p for p in pivots if p["id"] != parts[1].strip()]
            if len(pivots) < before:
                _save(pivots)
                print(f"  {C.YELLOW}[-] Removed{C.RESET}")

        else:
            print(f"  {C.DIM}Commands: list | add | show <id> | update <id> | map | gen | remove <id> | exit{C.RESET}")

def cli_main(args): _interactive()
def launch(): _interactive()
