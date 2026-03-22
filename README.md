# 💀 GRIMOIRE v2.0

```
  ██████╗ ██████╗ ██╗███╗   ███╗ ██████╗ ██╗██████╗ ███████╗
 ██╔════╝ ██╔══██╗██║████╗ ████║██╔═══██╗██║██╔══██╗██╔════╝
 ██║  ███╗██████╔╝██║██╔████╔██║██║   ██║██║██████╔╝█████╗
 ██║   ██║██╔══██╗██║██║╚██╔╝██║██║   ██║██║██╔══██╗██╔══╝
 ╚██████╔╝██║  ██║██║██║ ╚═╝ ██║╚██████╔╝██║██║  ██║███████╗
  ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝
```

> *"I will write your name in this book."*

**The Death Note of the digital world.**

**Developer:** Light  
**Alias:** Neok1ra  
**GitHub:** https://github.com/ne0k1r4  
**Version:** 2.0.0

---

## Modules

| Module | Command | v2 Features |
|--------|---------|-------------|
| 🖥️ **Core** | `grimoire` | TUI dashboard, CLI dispatcher, op log |
| 📓 **Codex** | `grimoire codex` | Risk scoring, tags, findings, MD/HTML export |
| 👁️ **Wraith** | `grimoire wraith` | HTTP fingerprint, tech detection, port probe, reports |
| 🕸️ **Voxcrypt** | `grimoire voxcrypt` | HMAC integrity, zlib compress, BMP support |
| 💣 **Forge** | `grimoire forge` | 15 shells, 3 obfuscators, listener gen, save-to-file |
| 🔐 **Vault** | `grimoire vault` | KeePassXC CLI, search by tag |
| 🌐 **Phantom** | `grimoire phantom` | SSH command generator, ASCII chain map |
| ☠️ **Sovereign** | `grimoire sovereign` | Session history, per-session logs, rename |
| 🌍 **Web** | `grimoire web` | Live JS refresh, Codex page, full Neok1ra branding |

---

## Install

```bash
git clone git@github.com:ne0k1r4/grimoire.git
cd grimoire
pip install -e ".[web]" --break-system-packages
```

---

## Usage

```bash
grimoire                          # TUI dashboard
grimoire wraith target.com        # passive recon
grimoire wraith target.com --report  # recon + save markdown report
grimoire forge                    # payload generator
grimoire codex                    # target journal
grimoire codex report             # export engagement report
grimoire phantom                  # pivot tracker
grimoire sovereign                # C2 listener
grimoire vault                    # credential manager
grimoire web                      # http://localhost:1337
grimoire web 8080                 # custom port
```

---

## What's New in v2.0

### Wraith
- HTTP header fingerprinting (server, framework, CDN detection)
- Tech stack detection (Apache, Nginx, PHP, WordPress, Cloudflare, AWS...)
- `robots.txt` and `security.txt` harvesting
- Top-20 port probe
- Markdown + HTML report export to `~/.grimoire/reports/`

### Codex
- Risk scoring: `CRITICAL / HIGH / MEDIUM / LOW / INFO`
- Tags system: `web, network, ad, cloud, iot, api...`
- Per-target findings log
- Full status history per target
- `grimoire codex report` → Markdown engagement report

### Forge
- 15 reverse shell templates (added Socat TTY, Python PTY, Bash UDP, Awk, Java, PowerShell)
- 3 obfuscation layers (bash variable injection, PowerShell char concat, b64 eval)
- Listener command generator
- Save payload to `~/.grimoire/payloads/`

### Voxcrypt
- HMAC-SHA256 integrity check (detects tampering + wrong passphrase)
- `zlib` compress-before-encrypt (smaller payload, better entropy)
- BMP carrier support
- Format version byte in header

### Sovereign
- Per-session command history
- All I/O logged to `~/.grimoire/sessions/<sid>.log`
- Session rename (`rename <sid> <name>`)
- Better output buffering

### Phantom
- SSH command auto-generator (`-L / -R / -D / SOCKS5 / Chisel / Ligolo`)
- `gen` command to generate tunnel commands without adding a pivot
- Improved chain map visualization

### Web
- Live op log auto-refresh (JS, every 10s)
- `/codex` page with full target table
- `/api/oplog` endpoint
- Full Neok1ra branding in footer and meta

---

## Data Locations

```
~/.grimoire/
├── codex.json        # target journal
├── oplog.json        # op log
├── phantom.json      # pivot map
├── payloads/         # saved forge payloads
├── reports/          # wraith + codex reports
└── sessions/         # sovereign session logs
```

---

## Credits

See `CREDITS.md`

---

## License

MIT — see `LICENSE`

---

*"From here, I will change the world." — Light Yagami*
