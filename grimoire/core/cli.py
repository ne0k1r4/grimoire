# ═══════════════════════════════════════════════════════════════
#  GRIMOIRE v2.0 — core/cli.py
#  CLI dispatcher — entry point for all subcommands
#
#  Developer  : Light
#  Alias      : Neok1ra
#  GitHub     : https://github.com/ne0k1r4
#  Tool       : GRIMOIRE — The Death Note of the digital world
# ═══════════════════════════════════════════════════════════════

import sys
import argparse
from .banner import GRIMOIRE_BANNER, VERSION, AUTHOR, ALIAS, TAGLINE, GITHUB


def _print_banner():
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
    elif mod == "web":
        from ..web import launch
        launch()
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
  web          Local web dashboard on localhost:1337

EXAMPLES:
  grimoire                        launch TUI dashboard
  grimoire wraith example.com     full passive recon scan
  grimoire forge                  interactive payload generator
  grimoire codex report           export engagement report
  grimoire web                    start web UI
        """,
    )
    parser.add_argument("module", nargs="?", default=None)
    parser.add_argument("args", nargs=argparse.REMAINDER)
    parser.add_argument("-v", "--version", action="version",
                        version=f"GRIMOIRE v{VERSION} by {AUTHOR} ({ALIAS})")

    parsed = parser.parse_args(argv)
    _print_banner()
    _dispatch(parsed)
