<div align="center">

![GRIMOIRE Banner](banner.png)

<br>

[![Version](https://img.shields.io/badge/version-2.0.0-cc0000?style=for-the-badge&labelColor=0a0000)](https://github.com/ne0k1r4/grimoire/releases)
[![Python](https://img.shields.io/badge/python-3.8+-cc0000?style=for-the-badge&logo=python&logoColor=white&labelColor=0a0000)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-cc0000?style=for-the-badge&labelColor=0a0000)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux-cc0000?style=for-the-badge&labelColor=0a0000)](https://archlinux.org)
[![Author](https://img.shields.io/badge/author-Neok1ra-cc0000?style=for-the-badge&labelColor=0a0000)](https://github.com/ne0k1r4)

<br>

```
  ██████╗ ██████╗ ██╗███╗   ███╗ ██████╗ ██╗██████╗ ███████╗
 ██╔════╝ ██╔══██╗██║████╗ ████║██╔═══██╗██║██╔══██╗██╔════╝
 ██║  ███╗██████╔╝██║██╔████╔██║██║   ██║██║██████╔╝█████╗  
 ██║   ██║██╔══██╗██║██║╚██╔╝██║██║   ██║██║██╔══██╗██╔══╝  
 ╚██████╔╝██║  ██║██║██║ ╚═╝ ██║╚██████╔╝██║██║  ██║███████╗
  ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝
```

*"I will write your name in this book."*

**The Death Note of the digital world.**<br>
A unified red team operator suite — TUI dashboard, passive recon, steganography,<br>
payload generation, credential management, network pivot tracking, and C2 management.

</div>

---

## Overview

**GRIMOIRE** is a modular, Death Note-themed operator suite built entirely from scratch by **Light (Neok1ra)**.  
Every module was designed, architected, and coded as part of the Neok1ra tool ecosystem — built to be used, not just shown.

It runs in three modes simultaneously:
- **TUI** — a full curses dashboard with live system stats and module launcher
- **CLI** — direct subcommand access for every module (`grimoire wraith target.com`)
- **Web** — a local Flask dashboard at `localhost:1337` with live op log refresh

---

## Modules

| Module | Command | Description |
|--------|---------|-------------|
| 🖥️ **Core** | `grimoire` | TUI dashboard · CLI dispatcher · op log |
| 📓 **Codex** | `grimoire codex` | Target journal · risk scoring · tags · findings · MD report |
| 👁️ **Wraith** | `grimoire wraith` | Passive recon · HTTP fingerprint · tech detection · port probe |
| 🕸️ **Voxcrypt** | `grimoire voxcrypt` | LSB PNG/WAV stego · ZWC text · AES cipher · HMAC integrity |
| 💣 **Forge** | `grimoire forge` | 15 reverse shells · 3 obfuscators · listener gen · save-to-file |
| 🔐 **Vault** | `grimoire vault` | KeePassXC CLI · credential retrieval · search |
| 🌐 **Phantom** | `grimoire phantom` | Pivot tracker · SSH `-L/-R/-D` generator · ASCII chain map |
| ☠️ **Sovereign** | `grimoire sovereign` | C2 listener · multi-session · command history · disk logs |
| 🌍 **Web** | `grimoire web` | Local web dashboard · live JS refresh · `/api/*` endpoints |

---

## Install

```bash
git clone git@github.com:ne0k1r4/grimoire.git
cd grimoire
pip install -e . --break-system-packages
```

> Flask is the only external dependency — used only by `grimoire web`.  
> All other modules run on Python stdlib alone.

---

## Usage

```bash
# Launch TUI dashboard
grimoire

# Passive recon
grimoire wraith target.com

# Recon + save markdown report
grimoire wraith target.com --report

# Payload generator
grimoire forge

# Target journal
grimoire codex

# Export engagement report
grimoire codex report

# Steganography
grimoire voxcrypt

# Network pivot tracker
grimoire phantom

# C2 listener
grimoire sovereign

# Credential manager
grimoire vault

# Web dashboard
grimoire web              # http://localhost:1337
grimoire web 8080         # custom port
```

---

## Module Details

<details>
<summary><b>📓 CODEX — Target Journal</b></summary>
<br>

Write names. Track operations. Export reports.

- Add targets with **risk scoring** (`CRITICAL / HIGH / MEDIUM / LOW / INFO`)
- Tag targets by category (`web`, `network`, `ad`, `cloud`, `iot`, `api`...)
- Log **findings** per target with timestamps
- Full **status history** (`WATCHING → ACTIVE → OWNED → CLOSED`)
- Export full engagement report to **Markdown** (`~/.grimoire/reports/`)

```bash
grimoire codex             # interactive journal
grimoire codex report      # export markdown report
```

</details>

<details>
<summary><b>👁️ WRAITH — Passive Recon</b></summary>
<br>

No active scanning. All passive queries.

- DNS resolution (A / AAAA / MX) + Reverse DNS
- SSL/TLS certificate inspection (SANs, issuer, cipher, expiry)
- HTTP header fingerprinting (server, framework, CDN)
- Tech stack detection (Apache, Nginx, PHP, WordPress, Cloudflare, AWS...)
- `robots.txt` and `security.txt` harvesting
- IP geolocation + ASN lookup
- WHOIS lookup
- Top-20 port probe
- 60-word subdomain probe
- Markdown + HTML report export

```bash
grimoire wraith target.com
grimoire wraith target.com --report
```

</details>

<details>
<summary><b>🕸️ VOXCRYPT — Steganography Engine</b></summary>
<br>

Hide payloads in plain sight.

- **LSB encoding** into PNG and BMP images
- **LSB encoding** into WAV audio files
- **Zero-width character** injection into plain text
- **XOR-SHA256 stream cipher** (AES-grade key derivation via SHA-256)
- **HMAC-SHA256 integrity check** — detects tampering and wrong passphrase
- **zlib compression** before encryption — smaller payload, higher entropy

```bash
grimoire voxcrypt
# Commands: hide | reveal | wav-hide | wav-reveal | zwc-hide | zwc-reveal
```

</details>

<details>
<summary><b>💣 FORGE — Payload Generator</b></summary>
<br>

Generate, encode, obfuscate, deploy.

**15 shell templates:**
`bash_tcp` · `bash_udp` · `python3_tcp` · `python3_pty` · `python3_win` ·
`nc_mkfifo` · `nc_e` · `socat_tcp` · `socat_tty` · `php_proc` · `perl_tcp` ·
`ruby_tcp` · `awk` · `powershell` · `java`

**5 encoders:** `base64` · `base64_exec` · `hex` · `url` · `unicode`

**3 obfuscators:** `bash_var` · `ps_char` · `b64_exec`

**+ Listener command generator** + **save-to-file** (`~/.grimoire/payloads/`)

</details>

<details>
<summary><b>🌐 PHANTOM — Pivot Tracker</b></summary>
<br>

Map your route through the network.

- Track pivot hops with source, destination, type, notes
- **SSH command generator** for `-L` (local forward), `-R` (remote forward), `-D` (SOCKS5 dynamic)
- **Chisel** and **Ligolo** command templates
- ASCII chain map visualization of full active pivot path
- Status tracking: `PENDING → ACTIVE → BROKEN → CLOSED`

```bash
grimoire phantom
# Commands: list | add | gen | map | show | update | remove
```

</details>

<details>
<summary><b>☠️ SOVEREIGN — C2 Manager</b></summary>
<br>

Multi-session reverse shell handler.

- TCP listener with multi-connection support
- Each session gets a unique SID
- **Per-session command history**
- **All I/O logged to disk** (`~/.grimoire/sessions/<sid>.log`)
- Session rename, background, kill
- `interact <sid>` to drop into live shell

```bash
grimoire sovereign
# Commands: listen <port> | sessions | interact <sid> | history <sid> | rename | kill | stop
```

</details>

---

## Data Locations

```
~/.grimoire/
├── codex.json          targets and findings
├── oplog.json          op log (last 2000 entries)
├── phantom.json        pivot map
├── payloads/           forge-generated payloads
├── reports/            wraith + codex exports
└── sessions/           sovereign shell logs
```

---

## TUI Keybinds

| Key | Action |
|-----|--------|
| `↑` `↓` | Navigate modules |
| `ENTER` | Launch module |
| `H` | Toggle help |
| `R` | Refresh system stats |
| `Q` | Quit |

---

## Architecture

```
grimoire/
├── core/         TUI · CLI · banner · sysinfo · oplog
├── utils/        Color engine · ReportBuilder · uid helpers
├── codex/        Target journal
├── wraith/       Passive recon
├── voxcrypt/     Steganography engine
├── forge/        Payload generator
├── vault/        KeePassXC wrapper
├── phantom/      Network pivot tracker
├── sovereign/    C2 session manager
└── web/          Flask local dashboard
```

---

## Credits

| Field | Value |
|-------|-------|
| Developer | Light |
| Alias | Neok1ra |
| GitHub | [github.com/ne0k1r4](https://github.com/ne0k1r4) |
| Version | 2.0.0 |
| License | MIT |

Part of the **Neok1ra tool ecosystem** alongside:
- [LightScan v2.0 "PHANTOM"](https://github.com/ne0k1r4) — Async network scanner
- [GhostRecon v3.0](https://github.com/ne0k1r4) — Passive recon framework

---

## Disclaimer

For authorized penetration testing and CTF use only.  
The developer is not responsible for misuse of this tool.

---

<div align="center">
<br>
<i>"From here, I will change the world." — Light Yagami</i>
<br><br>

[![GitHub](https://img.shields.io/badge/github.com%2Fne0k1r4-cc0000?style=flat-square&labelColor=0a0000&logo=github&logoColor=white)](https://github.com/ne0k1r4)

</div>
