#!/usr/bin/env python3
"""
Apply WRAITH v2.1 extensions to your local grimoire repo.
Run from inside grimoire-v2 directory:
    python apply_wraith_v2.1.py
"""
import sys, os
from pathlib import Path

RED="\033[91m"; GREEN="\033[92m"; YEL="\033[93m"; RESET="\033[0m"; BOLD="\033[1m"

target = Path("grimoire/wraith/__init__.py")
if not target.exists():
    print(f"{RED}[ERROR]{RESET} Run from inside your grimoire-v2 directory.")
    sys.exit(1)

content = target.read_text()

def patch(label, old, new):
    global content
    if old in content:
        content = content.replace(old, new, 1)
        print(f"  {GREEN}[OK]{RESET}   {label}")
        return True
    print(f"  {YEL}[SKIP]{RESET} {label} — already patched or pattern differs")
    return False

print(f"\n{BOLD}WRAITH v2.1 Apply Script{RESET}\n")

# 1. Header version bump
patch("Header v2.0 → v2.1",
    "#  GRIMOIRE v2.0 — wraith/__init__.py",
    "#  GRIMOIRE v2.1 — wraith/__init__.py")

patch("Header features list",
    "#    Markdown/HTML report export",
    """#    Certificate Transparency enumeration (crt.sh)
#    Subdomain Takeover detection (30 services)
#    WAF / CDN fingerprinting (9 providers)
#    Shodan host intelligence (API key required)
#    Markdown/HTML report export""")

# 2. Banner
patch("Banner v2.0 → v2.1",
    "W R A I T H  v2.0  —  Passive Recon",
    "W R A I T H  v2.1  —  Passive Recon")

patch("Banner subtitle",
    "DNS · WHOIS · Certs · HTTP · Tech · Ports · Reports",
    "DNS · WHOIS · Certs · HTTP · Ports · crt.sh · WAF · Takeover · Shodan")

# 3. _interactive command list hint
patch("_interactive hint line",
    'print(f"  {C.DIM}Commands: scan <target> | scan <target> --report | dns | cert | http | ports | sub | exit{C.RESET}\\n")',
    'print(f"  {C.DIM}Commands: scan | dns | cert | http | ports | sub | ip | crt | takeover | waf | shodan | exit{C.RESET}\\n")')

# 4. Add new commands to _interactive dispatch
patch("_interactive new command dispatch",
    '''        elif cmd == "ip"    and len(parts) >= 2: ip_info(parts[1])
        else:
            print(f"  {C.DIM}Try: scan <target> [--report] | dns | cert | http | ports | sub | exit{C.RESET}")''',
    '''        elif cmd == "ip"       and len(parts) >= 2: ip_info(parts[1])
        elif cmd == "crt"      and len(parts) >= 2: crtsh_enum(parts[1])
        elif cmd == "takeover" and len(parts) >= 2: subdomain_takeover(parts[1])
        elif cmd == "waf"      and len(parts) >= 2: waf_detect(parts[1])
        elif cmd == "shodan"   and len(parts) >= 2:
            key = parts[2] if len(parts) >= 3 else None
            shodan_lookup(parts[1], api_key=key)
        else:
            print(f"  {C.DIM}Commands: scan <t> [--report] | dns | cert | http | ports | sub | ip | crt | takeover | waf | shodan <ip> [key]{C.RESET}")''')

# 5. --help update
patch("--help new commands",
    '''    if "--help" in args or "-h" in args:
        print(f"""
  {C.RED}{C.BOLD}WRAITH — Passive Recon{C.RESET}
  {C.DIM}Usage:{C.RESET}
    grimoire wraith                     interactive mode
    grimoire wraith <target>            full passive recon scan
    grimoire wraith <target> --report   scan + save markdown report

  {C.DIM}Examples:{C.RESET}
    grimoire wraith example.com
    grimoire wraith example.com --report
""")''',
    '''    if "--help" in args or "-h" in args:
        print(f"""
  {C.RED}{C.BOLD}WRAITH v2.1 — Passive Recon{C.RESET}
  {C.DIM}Usage:{C.RESET}
    grimoire wraith                     interactive mode
    grimoire wraith <target>            full passive recon scan
    grimoire wraith <target> --report   scan + save markdown report

  {C.DIM}Interactive commands:{C.RESET}
    scan <target> [--report]    full recon scan
    dns <target>                DNS A/AAAA/MX lookup
    cert <target>               SSL/TLS cert + SANs
    http <target>               HTTP headers + tech stack
    ports <target>              top-20 port probe
    sub <target>                subdomain wordlist probe
    ip <ip>                     geolocation + ASN
    crt <domain>                crt.sh CT log enumeration
    waf <domain>                WAF / CDN fingerprinting
    takeover <domain>           subdomain takeover detection
    shodan <ip> [key]           Shodan host intelligence

  {C.DIM}Examples:{C.RESET}
    grimoire wraith example.com --report
""")''')

# 6. full_scan version string
patch("full_scan version string",
    'print(f"  {C.GREEN}Wraith v2.0 scan finished: {target}{C.RESET}")',
    'print(f"  {C.GREEN}Wraith v2.1 scan finished: {target}{C.RESET}")')

# 7. Append extension functions
MARKER = "# WRAITH v2.1 EXTENSIONS"
if MARKER in content:
    print(f"  {YEL}[SKIP]{RESET} Extension functions — already present")
else:
    # Read extension code from alongside this script
    ext_file = Path(__file__).parent / "wraith_ext_clean.py"
    if not ext_file.exists():
        # Try same directory as this script
        ext_file = Path(os.path.dirname(os.path.abspath(__file__))) / "wraith_ext_clean.py"
    if ext_file.exists():
        ext_code = ext_file.read_text()
        content += f"\n\n# {'='*62}\n# WRAITH v2.1 EXTENSIONS\n# crt.sh · Subdomain Takeover · WAF Detection · Shodan\n# {'='*62}\n\n" + ext_code
        print(f"  {GREEN}[OK]{RESET}   Extension functions appended ({len(ext_code.splitlines())} lines)")
    else:
        print(f"  {RED}[ERROR]{RESET} wraith_ext_clean.py not found next to this script")
        print(f"  {RED}        Download both files and keep them in the same folder{RESET}")

target.write_text(content)

print(f"\n{BOLD}Done. Now run:{RESET}")
print("  git add -A")
print("  git commit --no-gpg-sign -m 'feat(wraith): v2.1 — crt.sh, WAF, takeover, Shodan'")
print("  git push\n")
