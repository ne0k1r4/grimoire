#!/usr/bin/env python3
"""
Apply grimoire fixes directly to your local repo.
Run from inside your grimoire-v2 directory:
    python apply_grimoire_fixes.py
"""

import sys
from pathlib import Path

RED   = "\033[91m"
GREEN = "\033[92m"
YEL   = "\033[93m"
DIM   = "\033[2m"
RESET = "\033[0m"
BOLD  = "\033[1m"

def patch(filepath, old, new, label):
    p = Path(filepath)
    if not p.exists():
        print(f"  {YEL}[SKIP]{RESET} {filepath} — file not found")
        return False
    content = p.read_text()
    if old not in content:
        print(f"  {YEL}[SKIP]{RESET} {label} — pattern not found (already patched?)")
        return False
    p.write_text(content.replace(old, new, 1))
    print(f"  {GREEN}[OK]{RESET}   {label}")
    return True


# ── wraith: reverse_dns crash fix ────────────────────────────────────────────

WRAITH_RDNS_OLD = '''def reverse_dns(ip: str) -> str:
    section("REVERSE DNS")
    try:
        host = socket.gethostbyaddr(ip)[0]
        print(f"  {C.CYAN}{ip}{C.RESET} => {host}")
        return host
    except socket.herror:
        print(f"  {C.DIM}No PTR record for {ip}{C.RESET}")
        return ""'''

WRAITH_RDNS_NEW = '''def reverse_dns(ip: str) -> str:
    section("REVERSE DNS")
    if not ip:
        print(f"  {C.DIM}No IP to resolve{C.RESET}")
        return ""
    try:
        host = socket.gethostbyaddr(ip)[0]
        print(f"  {C.CYAN}{ip}{C.RESET} => {host}")
        return host
    except (socket.herror, socket.gaierror):
        print(f"  {C.DIM}No PTR record for {ip}{C.RESET}")
        return ""'''

# ── wraith: cli_main --help fix ───────────────────────────────────────────────

WRAITH_CLI_OLD = '''def cli_main(args):
    if not args: _interactive()
    else: full_scan(args[0], save_report="--report" in args)'''

WRAITH_CLI_NEW = '''def cli_main(args):
    if not args:
        _interactive()
        return
    if "--help" in args or "-h" in args:
        print(f"""
  {C.RED}{C.BOLD}WRAITH — Passive Recon{C.RESET}
  {C.DIM}Usage:{C.RESET}
    grimoire wraith                     interactive mode
    grimoire wraith <target>            full passive recon scan
    grimoire wraith <target> --report   scan + save markdown report

  {C.DIM}Examples:{C.RESET}
    grimoire wraith example.com
    grimoire wraith example.com --report
""")
        return
    full_scan(args[0], save_report="--report" in args)'''

# ── forge: cli_main --help fix ────────────────────────────────────────────────

FORGE_CLI_OLD = '''def cli_main(args): _interactive()
def launch(): _interactive()'''

FORGE_CLI_NEW = '''def cli_main(args):
    if args and ("--help" in args or "-h" in args):
        print(f"""
  {C.RED}{C.BOLD}FORGE — Payload Generator{C.RESET}
  {C.DIM}Usage:{C.RESET}
    grimoire forge      interactive payload generator

  {C.DIM}Features:{C.RESET}
    15 reverse shell templates (bash, python, php, powershell, java...)
    5 encoders: base64, hex, url, unicode, base64_exec
    3 obfuscators: bash_var, ps_char, b64_exec
    Listener command generator
    Save payloads to ~/.grimoire/payloads/
""")
        return
    _interactive()

def launch(): _interactive()'''

# ── phantom: cli_main --help fix ──────────────────────────────────────────────

PHANTOM_CLI_OLD = '''def cli_main(args): _interactive()
def launch(): _interactive()'''

PHANTOM_CLI_NEW = '''def cli_main(args):
    if args and ("--help" in args or "-h" in args):
        print(f"""
  {C.RED}{C.BOLD}PHANTOM — Network Pivot Tracker{C.RESET}
  {C.DIM}Usage:{C.RESET}
    grimoire phantom    interactive pivot tracker

  {C.DIM}Commands (inside phantom):{C.RESET}
    list                  list all tracked pivots
    add                   add a new pivot hop
    gen                   generate SSH/Chisel/Ligolo command
    map                   ASCII chain map of active pivots
    show <id>             show pivot details + tunnel command
    update <id>           update pivot status
    remove <id>           remove a pivot
    exit                  quit phantom

  {C.DIM}Pivot types:{C.RESET} SSH_L · SSH_R · SSH_D · SOCKS5 · CHISEL · LIGOLO · MANUAL
""")
        return
    _interactive()

def launch(): _interactive()'''

# ── sovereign: cli_main --help fix ────────────────────────────────────────────

SOVEREIGN_CLI_OLD = '''def cli_main(args): _interactive()
def launch(): _interactive()'''

SOVEREIGN_CLI_NEW = '''def cli_main(args):
    if args and ("--help" in args or "-h" in args):
        print(f"""
  {C.RED}{C.BOLD}SOVEREIGN — C2 Manager{C.RESET}
  {C.DIM}Usage:{C.RESET}
    grimoire sovereign  interactive C2 session manager

  {C.DIM}Commands (inside sovereign):{C.RESET}
    listen <port>         start TCP listener on port
    sessions              list active sessions
    interact <sid>        drop into live shell session
    history <sid>         show command history for session
    rename <sid> <name>   rename a session
    kill <sid>            terminate a session
    stop                  stop the listener
    exit                  quit sovereign

  {C.DIM}Session logs saved to:{C.RESET} ~/.grimoire/sessions/<sid>.log
""")
        return
    _interactive()

def launch(): _interactive()'''

# ── voxcrypt: cli_main --help fix ─────────────────────────────────────────────

VOXCRYPT_CLI_OLD = '''def cli_main(args): _interactive()
def launch(): _interactive()'''

VOXCRYPT_CLI_NEW = '''def cli_main(args):
    if args and ("--help" in args or "-h" in args):
        print(f"""
  {C.RED}{C.BOLD}VOXCRYPT — Steganography Engine{C.RESET}
  {C.DIM}Usage:{C.RESET}
    grimoire voxcrypt   interactive stego + cipher tool

  {C.DIM}Commands (inside voxcrypt):{C.RESET}
    hide                  LSB encode payload into PNG/BMP image
    reveal                LSB decode payload from image
    wav-hide              LSB encode payload into WAV audio
    wav-reveal            LSB decode payload from WAV audio
    zwc-hide              zero-width character injection into text
    zwc-reveal            extract ZWC payload from text
    encrypt               XOR-SHA256 stream cipher (AES-grade)
    decrypt               decrypt XOR-SHA256 ciphertext
    exit                  quit voxcrypt

  {C.DIM}All ciphertext includes HMAC-SHA256 integrity verification.{C.RESET}
""")
        return
    _interactive()

def launch(): _interactive()'''

# ── codex: cli_main --help fix ────────────────────────────────────────────────

CODEX_CLI_OLD = '''def cli_main(args):
    if args and args[0] == "report":
        targets = _load()
        saved = export_report(targets)
        print(f"  {C.GREEN}[+] Report: {saved}{C.RESET}")
    else: _interactive()'''

CODEX_CLI_NEW = '''def cli_main(args):
    if args and ("--help" in args or "-h" in args):
        print(f"""
  {C.RED}{C.BOLD}CODEX — Target Journal{C.RESET}
  {C.DIM}Usage:{C.RESET}
    grimoire codex          interactive target journal
    grimoire codex report   export full engagement report to markdown

  {C.DIM}Commands (inside codex):{C.RESET}
    add                   add a new target
    list                  list all targets
    show <id>             show target details + findings
    find <query>          search by name, tag, or status
    finding <id>          add a finding to a target
    update <id>           update target status
    remove <id>           remove a target
    report                export markdown report
    exit                  quit codex

  {C.DIM}Risk levels:{C.RESET}  CRITICAL · HIGH · MEDIUM · LOW · INFO
  {C.DIM}Reports saved to:{C.RESET} ~/.grimoire/reports/
""")
        return
    if args and args[0] == "report":
        targets = _load()
        saved = export_report(targets)
        print(f"  {C.GREEN}[+] Report: {saved}{C.RESET}")
    else:
        _interactive()'''


# ── Run all patches ───────────────────────────────────────────────────────────

print(f"\n{BOLD}Grimoire Fix Script{RESET}\n")

base = Path("grimoire")
if not base.exists():
    print(f"{RED}[ERROR]{RESET} Run this script from inside your grimoire-v2 directory.")
    sys.exit(1)

results = []
results.append(patch(base / "wraith/__init__.py",   WRAITH_RDNS_OLD,      WRAITH_RDNS_NEW,      "wraith: reverse_dns gaierror crash fix"))
results.append(patch(base / "wraith/__init__.py",   WRAITH_CLI_OLD,       WRAITH_CLI_NEW,       "wraith: cli_main --help support"))
results.append(patch(base / "forge/__init__.py",    FORGE_CLI_OLD,        FORGE_CLI_NEW,        "forge:  cli_main --help support"))
results.append(patch(base / "phantom/__init__.py",  PHANTOM_CLI_OLD,      PHANTOM_CLI_NEW,      "phantom: cli_main --help support"))
results.append(patch(base / "sovereign/__init__.py",SOVEREIGN_CLI_OLD,    SOVEREIGN_CLI_NEW,    "sovereign: cli_main --help support"))
results.append(patch(base / "voxcrypt/__init__.py", VOXCRYPT_CLI_OLD,     VOXCRYPT_CLI_NEW,     "voxcrypt: cli_main --help support"))
results.append(patch(base / "codex/__init__.py",    CODEX_CLI_OLD,        CODEX_CLI_NEW,        "codex: cli_main --help support"))

applied = sum(results)
print(f"\n{BOLD}{applied}/{len(results)} fixes applied.{RESET}")
if applied == len(results):
    print(f"\n{GREEN}All done! Now run:{RESET}")
    print(f"  git add -A")
    print(f"  git commit -m 'fix: reverse_dns crash, add --help to all modules'")
    print(f"  git push\n")
else:
    print(f"\n{YEL}Some fixes were skipped — your local code may differ.{RESET}")
    print(f"Check the [SKIP] lines above and apply those manually.\n")
