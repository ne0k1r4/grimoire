#!/usr/bin/env python3
"""
Add SENTINEL module to your local grimoire repo.
Run from inside grimoire-v2 directory:
    python add_sentinel.py
"""
import sys, shutil
from pathlib import Path

RED="\033[91m"; GREEN="\033[92m"; YEL="\033[93m"; RESET="\033[0m"; BOLD="\033[1m"

base = Path("grimoire")
if not base.exists():
    print(f"{RED}[ERROR]{RESET} Run from inside your grimoire-v2 directory.")
    sys.exit(1)

print(f"\n{BOLD}Sentinel Install Script{RESET}\n")

# ── 1. Copy sentinel module ───────────────────────────────────
sentinel_src = Path(__file__).parent / "sentinel_module.py"
sentinel_dst = base / "sentinel" / "__init__.py"

if not sentinel_src.exists():
    print(f"{RED}[ERROR]{RESET} sentinel_module.py not found next to this script.")
    sys.exit(1)

sentinel_dst.parent.mkdir(exist_ok=True)
shutil.copy(sentinel_src, sentinel_dst)
print(f"  {GREEN}[OK]{RESET}   sentinel/__init__.py created")

# ── 2. Register in CLI dispatcher ────────────────────────────
cli_path = base / "core" / "cli.py"
cli = cli_path.read_text()

if "sentinel" in cli:
    print(f"  {YEL}[SKIP]{RESET} CLI dispatcher — sentinel already registered")
else:
    cli = cli.replace(
        '    elif mod == "web":',
        '    elif mod == "sentinel":\n        from ..sentinel import cli_main\n        cli_main(args.args)\n    elif mod == "web":'
    )
    cli = cli.replace(
        "  sovereign    C2 manager — multi-session reverse shell handler",
        "  sovereign    C2 manager — multi-session reverse shell handler\n  sentinel     Blue team — log analysis, IOC scanner, anomaly detection"
    )
    cli_path.write_text(cli)
    print(f"  {GREEN}[OK]{RESET}   CLI dispatcher updated")

print(f"\n{BOLD}Done. Now run:{RESET}")
print("  git add -A")
print("  git commit --no-gpg-sign -m 'feat: add sentinel blue team module'")
print("  git push\n")
