# cli dispatcher
# entry point for all grimoire subcommands

import sys
import os
import argparse
from .banner import GRIMOIRE_BANNER, VERSION, AUTHOR, ALIAS, TAGLINE, GITHUB
from grimoire.arsenal_omega import get_omega_parser


def _print_banner():
    # skip banner when called from apocalypse sub-invocations
    if os.environ.get('GRIMOIRE_NO_BANNER') == '1':
        return
    RED   = "\033[91m"
    DIM   = "\033[2m"
    RESET = "\033[0m"
    BOLD  = "\033[1m"
    CREAM = "\033[38;2;232;213;196m"
    print(RED + BOLD + GRIMOIRE_BANNER + RESET)
    print(f"  {BOLD}{RED}v{VERSION}{RESET}  {DIM}|  {CREAM}{AUTHOR} ({ALIAS}){RESET}  {DIM}|  {GITHUB}{RESET}")
    print(f"  {DIM}{TAGLINE}{RESET}\n")


def _dispatch(args):
    mod = args.module

    if mod in ("tui", None):
        from .tui import launch_tui
        launch_tui()
    elif mod == "codex":
        from ..codex import cli_main
        cli_main(args.args)
    elif mod == "wraith":
        from ..wraith import cli_main
        cli_main(args.args)
    elif mod == "voxcrypt":
        from ..voxcrypt import cli_main
        cli_main(args.args)
    elif mod == "forge":
        from ..forge import cli_main
        cli_main(args.args)
    elif mod == "vault":
        from ..vault import cli_main
        cli_main(args.args)
    elif mod == "phantom":
        from ..phantom import cli_main
        cli_main(args.args)
    elif mod == "sovereign":
        from ..sovereign import cli_main
        cli_main(args.args)
    elif mod == "sentinel":
        from ..sentinel import cli_main
        cli_main(args.args)
    elif mod == "web":
        from ..web import launch
        launch()
    elif mod == "omega":
        omega_parser = get_omega_parser()
        omega_args = omega_parser.parse_args(args.args)
        if hasattr(omega_args, 'func'):
            omega_args.func(omega_args)
        else:
            omega_parser.print_help()
    elif mod == "version":
        print(f"GRIMOIRE v{VERSION}  |  {AUTHOR} ({ALIAS})  |  {GITHUB}")
    else:
        print(f"[!] Unknown module: {mod}")
        print("    Run `grimoire --help` for usage.")
        sys.exit(1)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="grimoire",
        description=f"GRIMOIRE v{VERSION} — {TAGLINE}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
  Developer : {AUTHOR} ({ALIAS})
  GitHub    : {GITHUB}

MODULES:
  tui          Launch the TUI dashboard (default)
  codex        Target journal — risk scoring, tags, report export
  wraith       Passive recon — DNS, WHOIS, HTTP fingerprint, tech detection
  voxcrypt     Steganography — LSB image/audio, ZWC text, HMAC integrity
  forge        Payload generator — 15 shells, obfuscation, save-to-file
  vault        Credential manager — KeePassXC integration
  phantom      Network pivot tracker — SSH command generator, chain map
  sovereign    C2 manager — multi-session reverse shell handler
  sentinel     Blue team — log analysis, IOC scanner, anomaly detection
  web          Local web dashboard on localhost:1337
  omega        Arsenal Omega — Ghost Hollow, Silicon Death, Data Harvester

EXAMPLES:
  grimoire                             launch TUI dashboard
  grimoire wraith example.com          full passive recon scan
  grimoire forge                       interactive payload generator
  grimoire web                         start web UI
  grimoire omega ghost-hollow          post-exploitation + persistence
  grimoire omega silicon-death         security annihilation
  grimoire omega data-harvester        mass data exfiltration
        """,
    )
    parser.add_argument("module", nargs="?", default=None)
    parser.add_argument("args", nargs=argparse.REMAINDER)
    parser.add_argument("-v", "--version", action="version",
                        version=f"GRIMOIRE v{VERSION} by {AUTHOR} ({ALIAS})")

    parsed = parser.parse_args(argv)
    _print_banner()
    _dispatch(parsed)
