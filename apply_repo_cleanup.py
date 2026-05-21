#!/usr/bin/env python3
"""
Clean up and professionalise the GRIMOIRE repo.
Run from inside grimoire-v2 directory:
    python apply_repo_cleanup.py
"""
import sys, shutil
from pathlib import Path

GREEN="\033[92m"; YEL="\033[93m"; RED="\033[91m"; RESET="\033[0m"; BOLD="\033[1m"

here = Path(__file__).parent
repo = Path(".")

if not (repo / "grimoire").exists():
    print(f"{RED}[ERROR]{RESET} Run from inside your grimoire-v2 directory.")
    sys.exit(1)

print(f"\n{BOLD}GRIMOIRE Repo Cleanup{RESET}\n")

def copy(src, dst, label):
    s = here / src
    d = (repo / dst).resolve()
    if not s.exists():
        print(f"  {YEL}[SKIP]{RESET} {label} — {src} not found next to this script")
        return
    if s.resolve() == d:
        print(f"  {YEL}[SKIP]{RESET} {label} — same file, skipping")
        return
    shutil.copy(s, d)
    print(f"  {GREEN}[OK]{RESET}   {label}")

# Files to copy
copy("README.md",    "README.md",    "README.md updated to v2.1")
copy("CHANGELOG.md", "CHANGELOG.md", "CHANGELOG.md created")
copy("setup.py",     "setup.py",     "setup.py bumped to v2.1.0")
copy(".gitignore",   ".gitignore",   ".gitignore updated")

# Remove dev scripts from repo root
to_remove = [
    "apply_grimoire_fixes.py",
    "apply_wraith_v2.1.py",
    "wraith_ext_clean.py",
    "add_sentinel.py",
    "sentinel_module.py",
]
for f in to_remove:
    p = repo / f
    if p.exists():
        p.unlink()
        print(f"  {GREEN}[OK]{RESET}   Removed {f}")
    else:
        print(f"  {YEL}[SKIP]{RESET} {f} — not present")

print(f"\n{BOLD}Done. Now run:{RESET}")
print("  git add -A")
print("  git commit --no-gpg-sign -m 'chore: v2.1.0 — clean repo, update README/CHANGELOG/setup'")
print("  git push\n")
