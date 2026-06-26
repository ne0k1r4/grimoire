# vault — credentials storage manager, wrapper around keepassxc-cli
import os, subprocess, getpass
from pathlib import Path
from ..utils import C, section

DEFAULT_VAULT = Path.home() / "creds" / "vaults" / "neok1ra_vault.kdbx"

BANNER = f"""
{C.RED}{C.BOLD}  ╔══════════════════════════════════════════════╗
  ║  V A U L T  v2.1  —  Credential Manager     ║
  ║  Developer: Light (Neok1ra)                  ║
  ╚══════════════════════════════════════════════╝{C.RESET}
  {C.DIM}KeePassXC CLI · neok1ra_vault.kdbx · search by tag{C.RESET}
"""

def _run(*args, vault=None, password=None):
    vault = vault or str(DEFAULT_VAULT)
    cmd = ["keepassxc-cli"] + list(args) + [vault]
    try:
        proc = subprocess.run(cmd,
            input=(password + "\n").encode() if password else None,
            capture_output=True, timeout=10)
        return proc.returncode, proc.stdout.decode(errors="replace"), proc.stderr.decode(errors="replace")
    except FileNotFoundError:
        return -1, "", "keepassxc-cli not found. Install KeePassXC."
    except Exception as e:
        return -3, "", str(e)

def _getpw(vault=None):
    return getpass.getpass(f"  {C.RED}Vault password:{C.RESET} ")

def _interactive(vault=None):
    print(BANNER)
    v = vault or str(DEFAULT_VAULT)
    print(f"  {C.DIM}Vault: {v}{C.RESET}")
    if not Path(v).exists():
        print(f"  {C.YELLOW}[!] Vault not found at {v}{C.RESET}")
        custom = input(f"  {C.DIM}Enter vault path (blank=abort):{C.RESET} ").strip()
        if not custom: return
        v = custom
    print(f"  {C.DIM}Commands: list | show <entry> | pass <entry> | search <tag> | unlock | lock | exit{C.RESET}\n")
    pw_cache = None
    while True:
        try:
            raw = input(f"  {C.RED}vault>{C.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [Closing Vault]"); break
        if not raw: continue
        parts = raw.split(None, 1)
        cmd   = parts[0].lower()
        if cmd in ("exit","quit","q"): break
        elif cmd == "unlock":
            pw_cache = _getpw(v)
            print(f"  {C.GREEN}[+] Vault unlocked{C.RESET}")
        elif cmd == "lock":
            pw_cache = None
            print(f"  {C.DIM}[Vault locked]{C.RESET}")
        elif cmd == "list":
            if not pw_cache: pw_cache = _getpw(v)
            rc, out, err = _run("ls", "--recursive", vault=v, password=pw_cache)
            if rc != 0: print(f"  {C.YELLOW}[!] {err.strip()}{C.RESET}"); continue
            for line in out.splitlines():
                if line.strip(): print(f"  {C.CYAN}•{C.RESET} {line.strip()}")
        elif cmd == "show" and len(parts) >= 2:
            if not pw_cache: pw_cache = _getpw(v)
            rc, out, err = _run("show", parts[1], vault=v, password=pw_cache)
            if rc != 0: print(f"  {C.YELLOW}[!] {err.strip()}{C.RESET}"); continue
            for line in out.splitlines():
                if ":" in line:
                    k, _, val = line.partition(":")
                    print(f"  {C.CYAN}{k.strip():<16}{C.RESET} {val.strip()}")
        elif cmd == "pass" and len(parts) >= 2:
            if not pw_cache: pw_cache = _getpw(v)
            rc, out, err = _run("show", "-s", "-a", "password", parts[1], vault=v, password=pw_cache)
            if rc != 0: print(f"  {C.YELLOW}[!] {err.strip()}{C.RESET}"); continue
            lines = [l.strip() for l in out.splitlines() if l.strip()]
            if lines: print(f"  {C.GREEN}[PASSWORD]{C.RESET} {lines[-1]}")
            from ..core.oplog import log
            log(f"Password retrieved: {parts[1]}", "vault")
        elif cmd == "search" and len(parts) >= 2:
            if not pw_cache: pw_cache = _getpw(v)
            rc, out, err = _run("ls", "--recursive", vault=v, password=pw_cache)
            if rc != 0: print(f"  {C.YELLOW}[!] {err.strip()}{C.RESET}"); continue
            q = parts[1].lower()
            matches = [l.strip() for l in out.splitlines() if q in l.lower()]
            if matches:
                for m in matches: print(f"  {C.CYAN}•{C.RESET} {m}")
            else:
                print(f"  {C.DIM}[No matches for '{q}']{C.RESET}")
        else:
            print(f"  {C.DIM}Commands: list | show <entry> | pass <entry> | search <tag> | unlock | lock | exit{C.RESET}")

def cli_main(args): _interactive()
def launch(): _interactive()
