# GRIMOIRE

*"I will write your name in this book."*

A modular, TUI-driven post-exploitation and recon suite with a Death Note aesthetic.

![Dashboard](dashboard.png)

## Modules
- **Core**: Curses-based TUI dashboard and oplog.
- **Wraith**: Passive recon (DNS, SSL, WAF, Takeover, Shodan).
- **Forge**: Interactive payload generator (15+ templates, obfuscation).
- **Voxcrypt**: Steganography engine (LSB image/audio, ZWC text).
- **Phantom**: Network pivot chain tracker.
- **Sovereign**: C2 multi-session TCP shell handler.
- **Codex**: Target journal with risk scoring.
- **Sentinel**: Log analysis and IOC scanning (AbuseIPDB/VT).
- **Vault**: KeePassXC wrapper.
- **Web**: Flask operational dashboard.
- **Omega**: Post-exploitation posturing modules.

## Setup
```bash
git clone https://github.com/ne0k1r4/grimoire.git
cd grimoire
pip install -e .
# Optional Windows Event Log support: pip install -e .[evtx]
```

## Quick Start
- Launch TUI: `grimoire`
- Launch Web: `grimoire web`
- Direct command: `grimoire wraith <target>`

All logs and reports are saved to `~/.grimoire/`.

---
*Educational and authorized testing use only.*
